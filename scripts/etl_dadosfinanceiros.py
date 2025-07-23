import os
import pandas as pd
from sqlalchemy import create_engine, text
import requests
import zipfile
import io
from datetime import datetime
from dotenv import load_dotenv

def get_db_engine_vm():
    """Lê as credenciais do .env e cria uma engine de conexão para o RDS."""
    load_dotenv()
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    dbname = os.getenv("DB_NAME", "postgres")
    if not all([user, password, host]):
        raise ValueError("Credenciais do banco não encontradas no .env")
    conn_str = f"postgresql+psycopg2://{user}:{password}@{host}/{dbname}?sslmode=require"
    return create_engine(conn_str)

def fetch_and_process_cvm_data(url_template, anos, periodo, tipo_relatorio):
    """Função genérica para buscar e processar dados DFP ou ITR."""
    for ano in anos:
        print(f"\nBuscando dados {periodo} para o ano: {ano}...")
        try:
            url = url_template.format(ano=ano)
            response = requests.get(url, timeout=180)
            if response.status_code != 200:
                print(f"  -> Arquivo para o ano {ano} não encontrado. Pulando.")
                continue

            zip_buffer = io.BytesIO(response.content)
            with zipfile.ZipFile(zip_buffer) as z:
                # Retorna um gerador de DataFrames, um para cada arquivo CSV no ZIP
                for report_prefix in ['DRE_con', 'BPA_con', 'BPP_con', 'DFC_MI_con']:
                    file_name = f'{tipo_relatorio}_cia_aberta_{report_prefix}_{ano}.csv'
                    if file_name in z.namelist():
                        print(f"  -> Processando arquivo: {file_name}")
                        with z.open(file_name) as f:
                            df = pd.read_csv(f, sep=';', encoding='latin-1', dtype=str)
                            df['tipo_demonstracao'] = report_prefix.split('_')[0]
                            df['periodo'] = periodo.upper()
                            yield df # Usa 'yield' para retornar um gerador, economizando memória
        except Exception as e:
            print(f"  -> ERRO ao processar o ano {ano}: {e}")
            
# Substitua a função antiga por esta no seu arquivo teste_etl_cvm.py

def transform_and_load(df_chunk, engine):
    """Transforma um pedaço de DataFrame e o carrega no banco de dados."""
    print(f"  Transformando e carregando um lote de {len(df_chunk)} linhas...")
    
    # --- CORREÇÃO APLICADA AQUI ---
    # 1. Primeiro, convertemos TODOS os nomes de coluna para minúsculas.
    df_chunk.columns = df_chunk.columns.str.lower()
    
    # 2. Agora, com os nomes já em minúsculas, podemos filtrar e criar a cópia.
    df_transformed = df_chunk[df_chunk['ordem_exerc'] == 'ÚLTIMO'].copy()
    
    # 3. As transformações seguintes agora funcionam na cópia.
    df_transformed.loc[:, 'vl_conta'] = pd.to_numeric(df_transformed['vl_conta'].str.replace(',', '.'), errors='coerce')
    df_transformed.loc[:, 'dt_fim_exerc'] = pd.to_datetime(df_transformed['dt_fim_exerc'], errors='coerce')

    colunas_tabela = [
        'cnpj_cia', 'denom_cia', 'cd_cvm', 'versao', 'dt_refer', 'dt_ini_exerc', 
        'dt_fim_exerc', 'cd_conta', 'ds_conta', 'vl_conta', 'escala_moeda', 
        'moeda', 'ordem_exerc', 'tipo_demonstracao', 'periodo'
    ]
    # O rename não é mais necessário, pois já convertemos para minúsculas
    df_transformed = df_transformed[[col for col in colunas_tabela if col in df_transformed.columns]]

    df_transformed.to_sql(
        'cvm_dados_financeiros', 
        engine, 
        if_exists='append', 
        index=False,
        chunksize=10000 
    )
    
def run_etl_pipeline():
    print("--- INICIANDO PIPELINE ETL DA CVM (OTIMIZADO PARA MEMÓRIA) ---")
    engine = get_db_engine_vm()
    
    # Limpa a tabela uma única vez no início
    print("Limpando a tabela de destino...")
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE cvm_dados_financeiros;"))
        conn.commit()
    
    anos = range(2010, datetime.now().year + 1)
    
    # Processa dados anuais (DFP)
    dfp_url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{ano}.zip"
    dfp_generator = fetch_and_process_cvm_data(dfp_url, anos, 'ANUAL', 'dfp')
    for df_chunk in dfp_generator:
        transform_and_load(df_chunk, engine)

    # Processa dados trimestrais (ITR)
    itr_url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_{ano}.zip"
    itr_generator = fetch_and_process_cvm_data(itr_url, anos, 'TRIMESTRAL', 'itr')
    for df_chunk in itr_generator:
        transform_and_load(df_chunk, engine)

    print("\n--- CARGA DE DADOS DA CVM CONCLUÍDA COM SUCESSO! ---")

if __name__ == "__main__":
    run_etl_pipeline()