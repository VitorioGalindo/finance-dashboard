# scripts/etl_dadosfinanceiros.py
import os
import pandas as pd
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import time
import requests  # Para fazer o download do arquivo
import zipfile # Para lidar com arquivos .zip
import io      # Para tratar o arquivo em memória

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

def download_and_extract_data(url):
    """
    Baixa um arquivo ZIP da URL, extrai o primeiro CSV encontrado em memória
    e o retorna como um DataFrame do pandas.
    """
    print(f"Baixando dados de: {url}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers, stream=True)
    
    # Verifica se o download foi bem-sucedido
    if response.status_code != 200:
        print(f"ERRO CRÍTICO: Falha ao baixar os dados. Status code: {response.status_code}")
        return None

    print("Download concluído. Processando arquivo ZIP em memória...")
    
    try:
        # Abre o arquivo ZIP diretamente do conteúdo da resposta HTTP
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # Encontra o primeiro arquivo .csv dentro do zip
            csv_filename = next((name for name in z.namelist() if name.endswith('.csv')), None)
            
            if not csv_filename:
                print("ERRO CRÍTICO: Nenhum arquivo .csv encontrado dentro do arquivo ZIP.")
                return None
            
            print(f"Arquivo CSV encontrado no ZIP: {csv_filename}")
            # Abre o arquivo CSV de dentro do ZIP e o carrega no pandas
            with z.open(csv_filename) as csv_file:
                df = pd.read_csv(csv_file, sep=';', encoding='latin-1', on_bad_lines='skip', low_memory=False)
                print(f"Arquivo CSV lido com sucesso para o DataFrame. {len(df)} linhas encontradas.")
                return df
                
    except zipfile.BadZipFile:
        print("ERRO CRÍTICO: O arquivo baixado não é um ZIP válido.")
        return None

def truncate_table(session):
    print("Limpando a tabela 'cvm_dados_financeiros'...")
    session.execute(f'TRUNCATE TABLE {FinancialStatement.__tablename__} RESTART IDENTITY CASCADE;')
    session.commit()

def load_data(session, df):
    # (Esta função está correta e permanece a mesma)
    objects_to_load = []
    total_rows = len(df)
    print(f"Iniciando a preparação de {total_rows} registros para a carga...")
    start_time = time.time()
    for index, row in df.iterrows():
        statement = FinancialStatement(
            company_cnpj=row.get('CNPJ_CIA'), company_name=row.get('DENOM_CIA'), cvm_code=row.get('CD_CVM'),
            report_version=int(row.get('VERSAO')) if pd.notna(row.get('VERSAO')) else None,
            reference_date=pd.to_datetime(row.get('DT_REFER')).date() if pd.notna(row.get('DT_REFER')) else None,
            fiscal_year_start=pd.to_datetime(row.get('DT_INI_EXERC')).date() if pd.notna(row.get('DT_INI_EXERC')) else None,
            fiscal_year_end=pd.to_datetime(row.get('DT_FIM_EXERC')).date() if pd.notna(row.get('DT_FIM_EXERC')) else None,
            account_code=row.get('CD_CONTA'), account_description=row.get('DS_CONTA'),
            account_value=float(row.get('VL_CONTA')) if pd.notna(row.get('VL_CONTA')) else None,
            currency_scale=row.get('ESCALA_MOEDA'), currency=row.get('MOEDA'),
            fiscal_year_order=row.get('ORDEM_EXERC'), report_type=row.get('GRUPO_DFP'), period=row.get('ORDEM_EXERC')
        )
        objects_to_load.append(statement)
        if (index + 1) % 10000 == 0: print(f"  Preparou {index + 1}/{total_rows} registros...")
    end_time = time.time()
    print(f"Preparação de objetos concluída em {end_time - start_time:.2f}s.")
    if objects_to_load:
        print("Iniciando a carga em lote no banco de dados...")
        start_bulk_time = time.time()
        session.bulk_save_objects(objects_to_load)
        session.commit()
        end_bulk_time = time.time()
        print(f"Carga concluída com sucesso em {end_bulk_time - start_bulk_time:.2f}s.")

def process_financial_reports():
    """Função principal para o ETL dos dados financeiros."""
    # URL para os dados DFP (Demonstrações Financeiras Padronizadas) da CVM
    # Exemplo para o ano de 2023. Podemos tornar o ano dinâmico no futuro.
    cvm_url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_DRE_con_2023.zip"
    
    try:
        df = download_and_extract_data(cvm_url)
        if df is None:
            print("Processo de ETL interrompido devido a falha no download ou extração.")
            return

        with app.app_context():
            db_engine = db.engine
            Session = sessionmaker(bind=db_engine)
            session = Session()

            try:
                truncate_table(session)
                load_data(session, df)
            finally:
                session.close()

    except Exception as e:
        print(f"Ocorreu um erro inesperado e fatal durante o processo de ETL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    process_financial_reports()
    print("Script de ETL finalizado.")
