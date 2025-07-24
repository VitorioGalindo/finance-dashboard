
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

def process_and_load_chunk(df_chunk, connection):
    df_chunk.columns = [col.lower() for col in df_chunk.columns]
    
    date_columns = ['data_referencia', 'data_entrega']
    for col in date_columns:
        df_chunk[col] = pd.to_datetime(df_chunk[col], errors='coerce')

    # Mapeamento para os nomes de coluna em inglês do novo modelo CvmDocument
    column_mapping = {
        'cnpj_companhia': 'company_cnpj',
        'nome_companhia': 'company_name',
        'codigo_cvm': 'cvm_code',
        'categoria': 'category',
        'tipo': 'doc_type',
        'especie': 'species',
        'assunto': 'subject',
        'data_referencia': 'reference_date',
        'data_entrega': 'delivery_date',
        'protocolo_entrega': 'delivery_protocol',
        'link_download': 'download_link'
    }
    
    df_chunk = df_chunk.rename(columns=column_mapping)
    
    # Garante que o CNPJ seja apenas números
    if 'company_cnpj' in df_chunk.columns:
        df_chunk['company_cnpj'] = df_chunk['company_cnpj'].str.replace(r'\D', '', regex=True)
        
    final_columns = list(column_mapping.values())
    df_final = df_chunk[[col for col in final_columns if col in df_chunk.columns]]

    df_final.to_sql(
        'cvm_documents',  # CORREÇÃO: Aponta para a nova tabela correta
        connection, 
        if_exists='append', 
        index=False, 
        method='multi'
    )

def run_ipe_etl_pipeline():
    print("--- INICIANDO PIPELINE ETL PARA 'cvm_documents' ---")
    engine = get_db_engine_vm()
    
    # TRUNCATE não funciona em tabelas que não existem. O ideal é deixar o SQLAlchemy criar.
    # A lógica de criação da tabela está em `backend/app.py` (db.create_all()).
    # Para garantir uma carga limpa, podemos tentar apagar e recriar.
    print("Garantindo que a tabela 'cvm_documents' esteja limpa...")
    try:
        with engine.begin() as connection:
            # Apaga a tabela se ela existir, junto com quaisquer dependências
            connection.execute(text("DROP TABLE IF EXISTS cvm_documents CASCADE;"))
            print("Tabela 'cvm_documents' antiga (se existiu) removida.")
            # O SQLAlchemy irá recriar a tabela com o esquema correto na inicialização do app
    except SQLAlchemyError as e:
        print(f"AVISO: Não foi possível apagar a tabela 'cvm_documents'. Pode ser a primeira execução. Erro: {e}")


    print("Execute o aplicativo Flask principal (`backend/app.py`) em um terminal separado para criar a tabela 'cvm_documents' antes de prosseguir com a carga de dados.")
    input("Pressione Enter quando o aplicativo Flask estiver em execução e a tabela tiver sido criada...")


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
                                batch_size = 10000

                                for i, row in enumerate(reader):
                                    batch.append(row)
                                    if len(batch) >= batch_size:
                                        try:
                                            with engine.begin() as connection:
                                                df_chunk = pd.DataFrame(batch, columns=header)
                                                process_and_load_chunk(df_chunk, connection)
                                        except SQLAlchemyError as e:
                                            print(f"     -> ERRO em lote. Lote ignorado. Detalhes: {str(e)[:200]}...")
                                        finally:
                                            batch = []
                                
                                if batch:
                                    try:
                                        with engine.begin() as connection:
                                            df_chunk = pd.DataFrame(batch, columns=header)
                                            process_and_load_chunk(df_chunk, connection)
                                    except SQLAlchemyError as e:
                                        print(f"     -> ERRO no lote final. Lote ignorado. Detalhes: {str(e)[:200]}...")
                        except Exception as e:
                            print(f"     -> ERRO CRÍTICO ao processar o arquivo {file_info.filename}: {e}")

        except requests.exceptions.RequestException as e:
            print(f"  -> ERRO DE REDE ao baixar o ZIP do ano {ano}: {e}")
        except Exception as e:
            print(f"  -> ERRO DESCONHECIDO no processamento do ano {ano}: {e}")

    print("--- CARGA COMPLETA PARA 'cvm_documents' CONCLUÍDA! ---")

if __name__ == "__main__":
    run_ipe_etl_pipeline()
