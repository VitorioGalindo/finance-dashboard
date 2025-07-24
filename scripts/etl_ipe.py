
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
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}/{dbname}?sslmode=require", echo=False)

def process_and_load_chunk(df_chunk, connection, cnpjs_to_process):
    """
    Filtra, mapeia, transforma e carrega um chunk de dados.
    """
    df_chunk.columns = [col.lower() for col in df_chunk.columns]
    
    # Garante que a coluna de CNPJ exista antes de filtrar
    if 'cnpj_companhia' not in df_chunk.columns:
        return # Se o chunk não tem a coluna, não há o que fazer

    # Limpa a coluna CNPJ para fazer a correspondência
    df_chunk['cnpj_companhia'] = df_chunk['cnpj_companhia'].str.replace(r'\D', '', regex=True)

    # **LÓGICA CORRETA**: Filtra o DataFrame para manter apenas os CNPJs de interesse
    df_chunk_filtered = df_chunk[df_chunk['cnpj_companhia'].isin(cnpjs_to_process)]

    # Se o lote ficou vazio após o filtro, não há mais nada a fazer
    if df_chunk_filtered.empty:
        return

    df_to_load = df_chunk_filtered.copy()

    date_columns = ['data_referencia', 'data_entrega']
    for col in date_columns:
        df_to_load[col] = pd.to_datetime(df_to_load[col], errors='coerce')

    column_mapping = {
        'cnpj_companhia': 'company_cnpj', 'nome_companhia': 'company_name', 'codigo_cvm': 'cvm_code',
        'categoria': 'category', 'tipo': 'doc_type', 'especie': 'species',
        'assunto': 'subject', 'data_referencia': 'reference_date', 'data_entrega': 'delivery_date',
        'protocolo_entrega': 'delivery_protocol', 'link_download': 'download_link'
    }
    
    df_to_load = df_to_load.rename(columns=column_mapping)
        
    final_columns = list(column_mapping.values())
    df_final = df_to_load[[col for col in final_columns if col in df_to_load.columns]]

    df_final.to_sql(
        'cvm_documents',
        connection, 
        if_exists='append', 
        index=False, 
        method='multi'
    )

def run_ipe_etl_pipeline():
    print("--- INICIANDO PIPELINE ETL OTIMIZADO PARA 'cvm_documents' ---")
    engine = get_db_engine_vm()

    # --- PASSO 1: Obter a lista de CNPJs de interesse ---
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT cnpj FROM companies;"))
            # Usa um set para uma busca O(1), que é extremamente rápida
            company_cnpjs_set = {row[0] for row in result}
        print(f"Encontradas {len(company_cnpjs_set)} empresas na tabela 'companies' para processar.")
    except SQLAlchemyError as e:
        print(f"ERRO CRÍTICO: Não foi possível ler a tabela 'companies'. Detalhes: {e}")
        return

    # --- PASSO 2: Limpar a tabela de destino antes de uma nova carga ---
    try:
        with engine.begin() as connection:
            # Não precisamos mais de CASCADE, pois não estamos tocando em 'companies'
            connection.execute(text("TRUNCATE TABLE cvm_documents RESTART IDENTITY;"))
        print("Tabela 'cvm_documents' limpa e pronta para nova carga.")
    except SQLAlchemyError as e:
        print(f"AVISO: A tabela 'cvm_documents' não pôde ser limpa (pode não existir). Erro: {e}")

    # --- PASSO 3: Processar os arquivos da CVM filtrando pelos CNPJs de interesse ---
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
                                batch_size = 20000

                                for i, row in enumerate(reader):
                                    batch.append(row)
                                    if len(batch) >= batch_size:
                                        try:
                                            with engine.begin() as connection:
                                                df_chunk = pd.DataFrame(batch, columns=header)
                                                process_and_load_chunk(df_chunk, connection, company_cnpjs_set)
                                        except SQLAlchemyError as e:
                                            print(f"     -> ERRO em lote. Lote ignorado. Detalhes: {str(e)[:200]}...")
                                        finally:
                                            batch = []
                                
                                if batch:
                                    try:
                                        with engine.begin() as connection:
                                            df_chunk = pd.DataFrame(batch, columns=header)
                                            process_and_load_chunk(df_chunk, connection, company_cnpjs_set)
                                    except SQLAlchemyError as e:
                                        print(f"     -> ERRO no lote final. Lote ignorado. Detalhes: {str(e)[:200]}...")
                        except Exception as e:
                            print(f"     -> ERRO CRÍTICO ao processar o arquivo {file_info.filename}: {e}")
        except Exception as e:
            print(f"  -> ERRO DESCONHECIDO no processamento do ano {ano}: {e}")

    print("--- CARGA COMPLETA E OTIMIZADA PARA 'cvm_documents' CONCLUÍDA! ---")

if __name__ == "__main__":
    run_ipe_etl_pipeline()
