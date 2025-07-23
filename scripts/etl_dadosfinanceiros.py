# scripts/etl_dadosfinanceiros.py
import os
import pandas as pd
from sqlalchemy.orm import sessionmaker
# CORREÇÃO: Importar a função 'text' para comandos SQL literais
from sqlalchemy import text 
from dotenv import load_dotenv
import time
import requests
import zipfile
import io
from datetime import datetime

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

def download_and_extract_data(year):
    base_url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/"
    zip_filename = f"dfp_cia_aberta_{year}.zip"
    csv_filename = f"dfp_cia_aberta_DRE_con_{year}.csv"
    url = f"{base_url}{zip_filename}"
    
    print(f"Tentando baixar dados para o ano {year} de: {url}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(url, headers=headers, stream=True)
    
    if response.status_code == 404:
        print(f"AVISO: Arquivo para o ano {year} não encontrado (404).")
        return None
    response.raise_for_status()

    print(f"Download para {year} concluído. Processando arquivo ZIP em memória...")
    try:
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            if csv_filename not in z.namelist():
                print(f"ERRO CRÍTICO: O arquivo CSV esperado '{csv_filename}' não foi encontrado dentro de '{zip_filename}'.")
                return None
            
            print(f"Extraindo '{csv_filename}' do ZIP...")
            with z.open(csv_filename) as csv_file:
                df = pd.read_csv(csv_file, sep=';', encoding='latin-1', on_bad_lines='skip', low_memory=False)
                print(f"DataFrame para {year} criado com sucesso ({len(df)} linhas).")
                return df
                
    except zipfile.BadZipFile:
        print("ERRO CRÍTICO: O arquivo baixado não é um ZIP válido.")
        return None

def truncate_table(session):
    """Apaga todos os dados da tabela para evitar duplicatas antes da nova carga."""
    print("Limpando a tabela 'cvm_dados_financeiros'...")
    # CORREÇÃO: Envelopa o comando SQL literal com a função text()
    command = text(f'TRUNCATE TABLE {FinancialStatement.__tablename__} RESTART IDENTITY CASCADE;')
    session.execute(command)
    session.commit()

def load_data(session, df):
    # (Esta função permanece inalterada)
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
    """Função principal e robusta para o ETL dos dados financeiros."""
    current_year = datetime.now().year
    years_to_try = [current_year, current_year - 1]
    df = None

    for year in years_to_try:
        try:
            df = download_and_extract_data(year)
            if df is not None:
                print(f"Dados para o ano {year} foram baixados e processados com sucesso.")
                break
        except requests.exceptions.RequestException as e:
            print(f"ERRO DE REDE ao tentar baixar dados para o ano {year}: {e}")
            df = None; break

    if df is None:
        print("FALHA NO ETL: Não foi possível baixar os dados financeiros dos últimos anos. Abortando.")
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

if __name__ == '__main__':
    process_financial_reports()
    print("Script de ETL finalizado.")
