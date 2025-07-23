# scripts/etl_dadosfinanceiros.py
import os
import pandas as pd
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import time
import glob # Módulo para encontrar arquivos com padrões

# Adiciona o diretório raiz ao path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importações do nosso backend
from backend.models import FinancialStatement
from backend.app import create_app
from backend import db

# --- CONFIGURAÇÃO ---
print("Iniciando o script de ETL para dados financeiros...")
load_dotenv()
app = create_app()

def truncate_table(session):
    print("Limpando a tabela 'cvm_dados_financeiros' (TRUNCATE)...")
    session.execute(f'TRUNCATE TABLE {FinancialStatement.__tablename__} RESTART IDENTITY CASCADE;')
    session.commit()
    print("Tabela limpa com sucesso.")

def load_data(session, df):
    # (O corpo desta função permanece o mesmo, está correto)
    objects_to_load = []
    total_rows = len(df)
    print(f"Iniciando a preparação de {total_rows} registros para a carga...")
    start_time = time.time()
    for index, row in df.iterrows():
        statement = FinancialStatement(
            company_cnpj=row.get('CNPJ_CIA'), company_name=row.get('DENOM_CIA'),
            cvm_code=row.get('CD_CVM'),
            report_version=int(row.get('VERSAO')) if pd.notna(row.get('VERSAO')) else None,
            reference_date=pd.to_datetime(row.get('DT_REFER')).date() if pd.notna(row.get('DT_REFER')) else None,
            fiscal_year_start=pd.to_datetime(row.get('DT_INI_EXERC')).date() if pd.notna(row.get('DT_INI_EXERC')) else None,
            fiscal_year_end=pd.to_datetime(row.get('DT_FIM_EXERC')).date() if pd.notna(row.get('DT_FIM_EXERC')) else None,
            account_code=row.get('CD_CONTA'), account_description=row.get('DS_CONTA'),
            account_value=float(row.get('VL_CONTA')) if pd.notna(row.get('VL_CONTA')) else None,
            currency_scale=row.get('ESCALA_MOEDA'), currency=row.get('MOEDA'),
            fiscal_year_order=row.get('ORDEM_EXERC'), report_type=row.get('GRUPO_DFP'),
            period=row.get('ORDEM_EXERC')
        )
        objects_to_load.append(statement)
        if (index + 1) % 10000 == 0: print(f"  Preparou {index + 1}/{total_rows} registros...")
    end_time = time.time()
    print(f"Preparação de objetos concluída em {end_time - start_time:.2f} segundos.")
    if objects_to_load:
        print(f"Iniciando a carga de {len(objects_to_load)} registros no banco de dados...")
        start_bulk_time = time.time()
        session.bulk_save_objects(objects_to_load)
        session.commit()
        end_bulk_time = time.time()
        print(f"Carga em lote concluída com sucesso em {end_bulk_time - start_bulk_time:.2f} segundos.")
    else: print("Nenhum objeto para carregar.")

def find_data_file(data_path):
    """Encontra dinamicamente o primeiro arquivo .csv no diretório especificado."""
    if not os.path.isdir(data_path):
        print(f"ERRO CRÍTICO: O diretório de dados '{data_path}' não foi encontrado.")
        print("Por favor, crie este diretório e coloque os arquivos CSV da CVM dentro dele.")
        return None
    
    # Busca por qualquer arquivo que termine com .csv
    csv_files = glob.glob(os.path.join(data_path, '*.csv'))
    if not csv_files:
        print(f"ERRO CRÍTICO: Nenhum arquivo .csv foi encontrado no diretório '{data_path}'.")
        return None
    
    # Retorna o primeiro arquivo encontrado
    found_file = csv_files[0]
    print(f"Arquivo de dados encontrado: {found_file}")
    return found_file

def process_financial_reports():
    """Função principal para o ETL dos dados financeiros."""
    data_directory = 'DFs Consolidados - DRE'
    
    try:
        data_file = find_data_file(data_directory)
        if not data_file:
            return # Encerra o script se nenhum arquivo for encontrado

        with app.app_context():
            # CORREÇÃO: Usando a nova sintaxe recomendada 'db.engine'
            db_engine = db.engine
            Session = sessionmaker(bind=db_engine)
            session = Session()

            try:
                df = pd.read_csv(data_file, sep=';', encoding='latin-1', on_bad_lines='skip', low_memory=False)
                print(f"Arquivo lido com sucesso. {len(df)} linhas encontradas.")
                
                truncate_table(session)
                load_data(session, df)
            finally:
                session.close()

    except Exception as e:
        print(f"Ocorreu um erro inesperado durante o processo de ETL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    process_financial_reports()
    print("Script de ETL finalizado.")
