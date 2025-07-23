# scripts/etl_dadosfinanceiros.py
import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import time

# Adiciona o diretório raiz ao path para encontrar o módulo 'backend'
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importações adiadas para depois da configuração do path
from backend.models import FinancialStatement
from backend.app import create_app

# --- CONFIGURAÇÃO ---
print("Iniciando o script de ETL para dados financeiros...")
load_dotenv()
app = create_app() # Cria a instância do Flask para obter o contexto

def truncate_table(session):
    """Apaga todos os dados da tabela para evitar duplicatas."""
    print("Limpando a tabela 'cvm_dados_financeiros' (TRUNCATE)...")
    session.execute(f'TRUNCATE TABLE {FinancialStatement.__tablename__} RESTART IDENTITY CASCADE;')
    session.commit()
    print("Tabela limpa com sucesso.")

def load_data(session, df):
    """Carrega os dados do DataFrame para o banco de dados."""
    objects_to_load = []
    total_rows = len(df)
    print(f"Iniciando a preparação de {total_rows} registros para a carga...")

    start_time = time.time()
    for index, row in df.iterrows():
        # Cria um objeto do modelo para cada linha
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
            # CORREÇÃO DE BUG: O campo 'periodo' estava sendo preenchido com o dado errado.
            # Ajustado para usar a coluna correta do CSV. Assumindo que 'ORDEM_EXERC' contém essa informação.
            period=row.get('ORDEM_EXERC') 
        )
        objects_to_load.append(statement)

        if (index + 1) % 5000 == 0:
            print(f"Preparou {index + 1}/{total_rows} registros...")

    end_time = time.time()
    print(f"Preparação de objetos concluída em {end_time - start_time:.2f} segundos.")

    if objects_to_load:
        print(f"Iniciando a carga de {len(objects_to_load)} registros no banco de dados...")
        start_bulk_time = time.time()
        session.bulk_save_objects(objects_to_load)
        session.commit()
        end_bulk_time = time.time()
        print(f"Carga em lote concluída com sucesso em {end_bulk_time - start_bulk_time:.2f} segundos.")
    else:
        print("Nenhum objeto para carregar.")

def process_financial_reports():
    """Função principal para o ETL dos dados financeiros."""
    path = './'
    # NOTA: O nome do arquivo no script anterior continha "2024", mas o script original
    # não especificava isso. Removi para tornar mais genérico.
    files = {
        'dre': os.path.join(path, 'DFs Consolidados - DRE/DRE_con.csv'),
    }

    try:
        # Usando o contexto da aplicação para garantir que o SQLAlchemy esteja configurado
        with app.app_context():
            db_engine = db.get_engine()
            Session = sessionmaker(bind=db_engine)
            session = Session()

            try:
                # O nome da coluna no CSV que indica o tipo de grupo é 'GRUPO_DFP'
                df = pd.read_csv(files['dre'], sep=';', encoding='latin-1', on_bad_lines='skip')
                print(f"Arquivo DRE lido com sucesso. {len(df)} linhas encontradas.")
                
                truncate_table(session)
                load_data(session, df)
            finally:
                session.close()

    except FileNotFoundError:
        print(f"ERRO: O arquivo {files['dre']} não foi encontrado.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado durante o processo de ETL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    process_financial_reports()
    print("Script de ETL finalizado.")
