# scripts/etl_dadosfinanceiros.py
import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import time

# Importa os modelos do nosso backend.
# Adicionamos o diretório raiz ao path para que o script possa encontrar o módulo 'backend'.
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.models import FinancialStatement

# --- CONFIGURAÇÃO E CONEXÃO COM O BANCO DE DADOS ---
print("Iniciando o script de ETL para dados financeiros...")
load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
    print("ERRO: As variáveis de ambiente do banco de dados não estão configuradas.")
    print("Verifique o seu arquivo .env.")
    exit()

# String de conexão com o banco de dados
DATABASE_URI = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?sslmode=require"
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

def truncate_table(session):
    """Apaga todos os dados da tabela para evitar duplicatas antes da nova carga."""
    print("Limpando a tabela 'cvm_dados_financeiros' (TRUNCATE)...")
    session.execute(f'TRUNCATE TABLE {FinancialStatement.__tablename__} RESTART IDENTITY CASCADE;')
    session.commit()
    print("Tabela limpa com sucesso.")

def load_data(session, df):
    """Carrega os dados do DataFrame para o banco de dados usando o modelo FinancialStatement."""
    objects_to_load = []
    total_rows = len(df)
    print(f"Iniciando a preparação de {total_rows} registros para a carga...")

    start_time = time.time()
    for index, row in df.iterrows():
        # Cria um objeto do modelo para cada linha do DataFrame
        statement = FinancialStatement(
            company_cnpj=row.get('CNPJ_CIA'),
            company_name=row.get('DENOM_CIA'),
            cvm_code=row.get('CD_CVM'),
            report_version=int(row.get('VERSAO')) if pd.notna(row.get('VERSAO')) else None,
            reference_date=pd.to_datetime(row.get('DT_REFER')).date() if pd.notna(row.get('DT_REFER')) else None,
            fiscal_year_start=pd.to_datetime(row.get('DT_INI_EXERC')).date() if pd.notna(row.get('DT_INI_EXERC')) else None,
            fiscal_year_end=pd.to_datetime(row.get('DT_FIM_EXERC')).date() if pd.notna(row.get('DT_FIM_EXERC')) else None,
            account_code=row.get('CD_CONTA'),
            account_description=row.get('DS_CONTA'),
            account_value=float(row.get('VL_CONTA')) if pd.notna(row.get('VL_CONTA')) else None,
            currency_scale=row.get('ESCALA_MOEDA'),
            currency=row.get('MOEDA'),
            fiscal_year_order=row.get('ORDEM_EXERC'),
            report_type=row.get('GRUPO_DFP'),
            period=row.get('MOEDA') # Ajuste se houver uma coluna específica para o período
        )
        objects_to_load.append(statement)

        # Log de progresso
        if (index + 1) % 1000 == 0:
            print(f"Preparou {index + 1}/{total_rows} registros...")

    end_time = time.time()
    print(f"Preparação de objetos concluída em {end_time - start_time:.2f} segundos.")

    if objects_to_load:
        print(f"Iniciando a carga de {len(objects_to_load)} registros no banco de dados. Isso pode levar alguns minutos...")
        start_bulk_time = time.time()
        
        # O método bulk_save_objects é altamente eficiente para cargas em massa.
        session.bulk_save_objects(objects_to_load)
        session.commit()
        
        end_bulk_time = time.time()
        print(f"Carga em lote concluída com sucesso em {end_bulk_time - start_bulk_time:.2f} segundos.")
    else:
        print("Nenhum objeto para carregar.")


def process_financial_reports():
    """Função principal para o ETL dos dados financeiros."""
    # Define os caminhos para os arquivos de dados
    path = './'
    files = {
        'dre': os.path.join(path, 'DFs Consolidados - DRE/DRE_con_2024.csv'),
        # Adicione outros arquivos aqui se necessário (BPA, BPP, etc.)
    }

    try:
        # Lê o arquivo CSV com o encoding correto e tratando erros de linhas
        df_dre = pd.read_csv(files['dre'], sep=';', encoding='latin-1', on_bad_lines='skip')
        print(f"Arquivo DRE lido com sucesso. {len(df_dre)} linhas encontradas.")

        session = Session()
        try:
            truncate_table(session)
            load_data(session, df_dre)
        finally:
            session.close() # Garante que a sessão seja sempre fechada

    except FileNotFoundError:
        print(f"ERRO: O arquivo {files['dre']} não foi encontrado.")
        print("Verifique se o arquivo está no diretório correto.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado durante o processo de ETL: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    process_financial_reports()
    print("Script de ETL finalizado.")
