
import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import requests
import zipfile
import io
from datetime import datetime
from dotenv import load_dotenv
import csv

def get_db_engine_vm():
    load_dotenv()
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    dbname = os.getenv("DB_NAME", "postgres")
    if not all([user, password, host]):
        raise ValueError("Credenciais do banco não encontradas no arquivo .env")
    # echo=False para não poluir o log com os comandos SQL
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}/{dbname}?sslmode=require", echo=False)

def process_and_load_chunk(df_chunk, connection):
    """
    Transforma um chunk e usa a conexão fornecida para carregá-lo no banco.
    A transação é gerenciada pela função que chama esta.
    """
    df_chunk.columns = [col.lower() for col in df_chunk.columns]
    
    date_columns = ['data_referencia', 'data_entrega']
    for col in date_columns:
        df_chunk[col] = pd.to_datetime(df_chunk[col], errors='coerce')

    column_mapping = {
        'cnpj_companhia': 'company_cnpj', 'nome_companhia': 'company_name', 'codigo_cvm': 'cvm_code',
        'categoria': 'category', 'tipo': 'doc_type', 'especie': 'species',
        'assunto': 'subject', 'data_referencia': 'reference_date', 'data_entrega': 'delivery_date',
        'protocolo_entrega': 'delivery_protocol', 'link_download': 'download_link'
    }
    
    df_chunk = df_chunk.rename(columns=column_mapping)
    
    final_columns = list(column_mapping.values())
    df_chunk = df_chunk[[col for col in final_columns if col in df_chunk.columns]]

    df_chunk.to_sql(
        'filings', 
        connection, 
        if_exists='append', 
        index=False, 
        chunksize=5000,
        method='multi'
    )

def run_ipe_etl_pipeline():
    print("--- INICIANDO PIPELINE ETL DE DOCUMENTOS IPE (ROBUSTO) ---")
    engine = get_db_engine_vm()
    
    print("Limpando a tabela 'filings' e dependências (CASCADE)...")
    try:
        with engine.begin() as connection:
            connection.execute(text("TRUNCATE TABLE filings RESTART IDENTITY CASCADE;"))
        print("Tabela 'filings' limpa com sucesso.")
    except SQLAlchemyError as e:
        print(f"ERRO CRÍTICO ao limpar a tabela 'filings': {e}")
        return # Aborta se não conseguir limpar a tabela

    anos_para_buscar = range(2010, datetime.now().year + 1)
    
    for ano in anos_para_buscar:
        print(f"--- Processando IPE para o ano: {ano} ---")
        try:
            url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_{ano}.zip"
            response = requests.get(url, timeout=180)
            if response.status_code != 200:
                print(f"  -> Arquivo ZIP para o ano {ano} não encontrado (Status: {response.status_code}). Pulando.")
                continue

            zip_buffer = io.BytesIO(response.content)
            with zipfile.ZipFile(zip_buffer) as z:
                for file_info in z.infolist():
                    if file_info.filename.endswith('.csv'):
                        print(f"  -> Processando arquivo: {file_info.filename}...")
                        try:
                            with z.open(file_info.filename) as f:
                                f_text = io.TextIOWrapper(f, encoding='latin-1')
                                reader = csv.reader(f_text, delimiter=';')
                                
                                header = next(reader)
                                batch = []
                                batch_size = 10000 # Reduzindo o lote para isolar melhor os erros

                                for i, row in enumerate(reader):
                                    batch.append(row)
                                    if len(batch) >= batch_size:
                                        # CORREÇÃO: Envolve cada lote em sua própria transação
                                        try:
                                            with engine.begin() as connection:
                                                df_chunk = pd.DataFrame(batch, columns=header)
                                                process_and_load_chunk(df_chunk, connection)
                                        except SQLAlchemyError as e:
                                            print(f"     -> ERRO em lote de {len(batch)} linhas. Lote ignorado. Detalhes: {e}")
                                        finally:
                                            batch = [] # Limpa o lote
                                
                                # Processa o último lote restante
                                if batch:
                                    try:
                                        with engine.begin() as connection:
                                            df_chunk = pd.DataFrame(batch, columns=header)
                                            process_and_load_chunk(df_chunk, connection)
                                    except SQLAlchemyError as e:
                                        print(f"     -> ERRO no lote final de {len(batch)} linhas. Lote ignorado. Detalhes: {e}")
                        except Exception as e:
                            print(f"     -> ERRO CRÍTICO ao processar o arquivo {file_info.filename}: {e}")

        except requests.exceptions.RequestException as e:
            print(f"  -> ERRO DE REDE ao baixar o ZIP do ano {ano}: {e}")
        except Exception as e:
            print(f"  -> ERRO DESCONHECIDO no processamento do ano {ano}: {e}")

    print("--- CARGA COMPLETA DE DOCUMENTOS IPE CONCLUÍDA! ---")

if __name__ == "__main__":
    run_ipe_etl_pipeline()
