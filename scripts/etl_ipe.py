# teste_etl_ipe.py (Versão Final - Leitura Linha a Linha)
import os
import pandas as pd
from sqlalchemy import create_engine, text
import requests
import zipfile
import io
from datetime import datetime
from dotenv import load_dotenv
import csv

def get_db_engine_vm():
    """Lê as credenciais do .env e cria uma engine de conexão para o RDS."""
    load_dotenv()
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    dbname = os.getenv("DB_NAME", "postgres")
    if not all([user, password, host]):
        raise ValueError("Credenciais do banco não encontradas no arquivo .env")
    conn_str = f"postgresql+psycopg2://{user}:{password}@{host}/{dbname}?sslmode=require"
    return create_engine(conn_str)

def process_and_load_chunk(df_chunk, engine):
    """
    Transforma um único pedaço (chunk) de DataFrame e o carrega no banco.
    """
    try:
        df_chunk.columns = [col.lower() for col in df_chunk.columns]
        
        colunas_data = ['data_referencia', 'data_entrega']
        for col in colunas_data:
            df_chunk[col] = pd.to_datetime(df_chunk[col], errors='coerce')

        colunas_finais = {
            'cnpj_companhia': 'cnpj_companhia', 'nome_companhia': 'nome_companhia', 'codigo_cvm': 'codigo_cvm',
            'categoria': 'categoria', 'tipo': 'tipo', 'especie': 'especie',
            'assunto': 'assunto', 'data_referencia': 'data_referencia', 'data_entrega': 'data_entrega',
            'protocolo_entrega': 'protocolo_entrega', 'link_download': 'link_download'
        }
        df_chunk = df_chunk[list(colunas_finais.keys())].rename(columns=colunas_finais)

        df_chunk.to_sql(
            'cvm_documentos_ipe', 
            engine, 
            if_exists='append', 
            index=False, 
            chunksize=5000,
            method='multi'
        )
    except Exception as e:
        print(f"     -> ERRO ao processar um chunk: {e}")

def process_file_line_by_line(csv_file_in_zip, zip_object, engine):
    """
    Lê um CSV de dentro do ZIP linha por linha para economizar memória.
    """
    file_name = csv_file_in_zip.filename
    print(f"  -> Lendo arquivo linha a linha: {file_name}...")
    
    try:
        with zip_object.open(file_name) as f:
            # Decodifica o arquivo para texto para que o leitor de CSV funcione
            f_text = io.TextIOWrapper(f, encoding='latin-1')
            reader = csv.reader(f_text, delimiter=';')
            
            header = next(reader) # Pega o cabeçalho
            batch = []
            batch_size = 20000 # Processa em lotes de 20.000 linhas

            for i, row in enumerate(reader):
                batch.append(row)
                if len(batch) >= batch_size:
                    print(f"     -> Processando lote de {len(batch)} linhas...")
                    df_chunk = pd.DataFrame(batch, columns=header)
                    process_and_load_chunk(df_chunk, engine)
                    batch = [] # Limpa o lote da memória

            # Processa o último lote restante
            if batch:
                print(f"     -> Processando lote final de {len(batch)} linhas...")
                df_chunk = pd.DataFrame(batch, columns=header)
                process_and_load_chunk(df_chunk, engine)

        print(f"  -> Arquivo {file_name} carregado com sucesso!")

    except Exception as e:
        print(f"     -> ERRO CRÍTICO ao ler ou processar o arquivo {file_name}: {e}")

def run_ipe_etl_pipeline():
    """
    Orquestra o pipeline de ETL para documentos IPE.
    """
    print("--- INICIANDO PIPELINE ETL DE DOCUMENTOS IPE (LEITURA LINHA A LINHA) ---")
    engine = get_db_engine_vm()
    
    print("Limpando a tabela de destino 'cvm_documentos_ipe'...")
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE cvm_documentos_ipe RESTART IDENTITY;"))
    
    anos_para_buscar = range(2010, datetime.now().year + 1)
    
    for ano in anos_para_buscar:
        print(f"\n--- Processando documentos IPE para o ano: {ano} ---")
        try:
            url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_{ano}.zip"
            response = requests.get(url, timeout=180)
            if response.status_code != 200:
                print(f"  -> Arquivo ZIP para o ano {ano} não encontrado. Pulando.")
                continue

            zip_buffer = io.BytesIO(response.content)
            with zipfile.ZipFile(zip_buffer) as z:
                for file_info in z.infolist():
                    if file_info.filename.endswith('.csv'):
                        process_file_line_by_line(file_info, z, engine)

        except Exception as e:
            print(f"  -> ERRO CRÍTICO ao baixar ou abrir o ZIP do ano {ano}: {e}")

    print("\n--- CARGA COMPLETA DE DOCUMENTOS IPE CONCLUÍDA! ---")

if __name__ == "__main__":
    run_ipe_etl_pipeline()