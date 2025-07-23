from pathlib import Path
from core.ingestor import CVMDataIngestor
from core.downloader import PDFDownloader
from core.parser import PDFParser
from core.transformer import DataTransformer
from core.loader import SupabaseLoader
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURAÇÕES DE AMBIENTE E DO SCRAPER ---
# Substitua com suas credenciais reais do Supabase
SUPABASE_URL = "https://jcvwnitmrjdjeocxgmiy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpjdnduaXRtcmpkamVvY3hnbWl5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjA5MjQ3NywiZXhwIjoyMDY3NjY4NDc3fQ.oF6enp5M3WrJxOGa4lLkKUMgc8zT8fA_GzRtigCa--8"
TEMP_PDF_DIR = Path("data/temp_pdfs")

# Define o intervalo de anos a serem processados
YEARS_TO_PROCESS = range(2020, datetime.now().year + 1)

def create_safe_filename(row: pd.Series) -> str:
    """Cria um nome de arquivo único e seguro a partir dos metadados da CVM."""
    protocolo = row.get('Protocolo_Entrega', 'N/A')
    versao = row.get('Versao', '1')
    return f"CVM_{protocolo}_v{versao}.pdf"

def main():
    """Orquestrador principal do pipeline de dados 'PDF-First' de produção."""
    print("--- INICIANDO SCRAPER DE PRODUÇÃO 'PDF-FIRST' ---")
    
    try:
        loader = SupabaseLoader(supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)
        downloader = PDFDownloader(save_directory=TEMP_PDF_DIR)
        processed_files_response = loader.supabase.table('processed_documents').select('file_name').execute()
        processed_files = {item['file_name'] for item in processed_files_response.data}
        print(f"Encontrados {len(processed_files)} documentos já processados no banco de dados.")

        all_new_transactions = []

        for year in YEARS_TO_PROCESS:
            separator = "=" * 20
            print(f"\n{separator} PROCESSANDO ANO: {year} {separator}")
            
            try:
                ingestor = CVMDataIngestor(year=year)
                df_index = ingestor.get_document_metadata()
                
                link_column = 'Link_Download'
                required_cols = [link_column, 'Protocolo_Entrega', 'Versao', 'CNPJ_Companhia', 'Nome_Companhia', 'Data_Referencia']
                
                if not all(col in df_index.columns for col in required_cols):
                    print(f"AVISO: Colunas necessárias ({required_cols}) não encontradas no índice de {year}. Pulando.")
                    continue

                for _, row in df_index.iterrows():
                    file_name = create_safe_filename(row)
                    
                    if file_name not in processed_files:
                        print(f"\n-- Processando novo arquivo: {file_name} --")
                        
                        doc_url = row[link_column]
                        downloaded_path = downloader.download(url=doc_url, filename=file_name)
                        
                        if downloaded_path:
                            context_data = {
                                "cnpj_companhia": row['CNPJ_Companhia'], "nome_companhia": row['Nome_Companhia'], "data_referencia": row['Data_Referencia']
                            }
                            parser = PDFParser(pdf_path=downloaded_path, context=context_data)
                            parsed_data = parser.parse()
                            
                            if parsed_data['metadata']['has_transactions']:
                                transformer = DataTransformer(parsed_data=parsed_data)
                                clean_df = transformer.transform_to_transactions_schema()
                                if not clean_df.empty:
                                    all_new_transactions.append(clean_df)
                            
                            loader.supabase.table('processed_documents').insert({'file_name': file_name}).execute()
                            print(f"'{file_name}' registrado como processado.")
                            os.remove(downloaded_path)
                        else:
                             loader.supabase.table('processed_documents').insert({'file_name': file_name, 'processed_at': '1970-01-01'}).execute()
                             print(f"'{file_name}' registrado como FALHA no download.")

            except Exception as e:
                print(f"--- FALHA AO PROCESSAR O ANO {year}: {e} ---")

        if all_new_transactions:
            final_df_to_load = pd.concat(all_new_transactions, ignore_index=True)
            
            # --- CORREÇÃO APLICADA AQUI ---
            separator = "=" * 20
            print(f"\n\n{separator} CARREGAMENTO FINAL {separator}")
            print(f"Total de {len(final_df_to_load)} novas transações para carregar no banco de dados.")
            
            loader.load_transactions(df=final_df_to_load, mode='append')
        else:
            print("\nNenhuma nova transação encontrada nos documentos processados.")

    except Exception as e:
        print(f"FALHA CRÍTICA NO PIPELINE: {e}")
    
    print("\n--- PIPELINE FINALIZADO ---")

if __name__ == "__main__":
    main()
