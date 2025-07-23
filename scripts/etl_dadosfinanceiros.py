# scripts/etl_dadosfinanceiros.py
import os
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv
import time
import requests
import zipfile
import io
import re
from datetime import datetime

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.models import FinancialStatement, Company
from backend.app import create_app
from backend import db

print("Iniciando o script de ETL para dados financeiros...")
load_dotenv()
app = create_app()

def clean_cnpj(cnpj):
    if not isinstance(cnpj, str): return None
    return re.sub(r'[^0-9]', '', cnpj)

def download_and_extract_data(year, doc_type):
    """
    Tenta baixar e extrair os dados DRE para um ano e tipo de documento (DFP ou ITR) específico.
    """
    base_url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/{doc_type.upper()}/DADOS/"
    zip_filename = f"{doc_type.lower()}_cia_aberta_{year}.zip"
    
    # CORREÇÃO CRÍTICA: O nome do arquivo CSV agora é dinâmico, baseado no doc_type.
    csv_filename = f"{doc_type.lower()}_cia_aberta_DRE_con_{year}.csv"
    
    url = f"{base_url}{zip_filename}"

    print(f"--> Tentando baixar {doc_type.upper()} para o ano {year}...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, stream=True)
        if response.status_code == 404:
            print(f"    - AVISO: Arquivo não encontrado (404). Pulando.")
            return None
        response.raise_for_status()

        print(f"    + Download concluído. Processando...")
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            if csv_filename not in z.namelist():
                print(f"    - ERRO: Arquivo CSV esperado '{csv_filename}' não foi encontrado no ZIP. Pulando.")
                return None
            with z.open(csv_filename) as csv_file:
                df = pd.read_csv(csv_file, sep=';', encoding='latin-1', on_bad_lines='skip', low_memory=False)
                print(f"    + DataFrame criado com sucesso ({len(df)} linhas).")
                return df
    except requests.exceptions.RequestException as e:
        print(f"    - ERRO DE REDE: {e}")
    except zipfile.BadZipFile:
        print(f"    - ERRO: O arquivo baixado não é um ZIP válido.")
    except Exception as e:
        print(f"    - ERRO inesperado: {e}")
    return None

def truncate_table(session):
    print("Limpando a tabela 'cvm_dados_financeiros' para a carga completa...")
    session.execute(text(f'TRUNCATE TABLE {FinancialStatement.__tablename__} RESTART IDENTITY CASCADE;'))
    session.commit()

def load_data(session, df):
    # (Esta função está correta e permanece a mesma)
    objects_to_load = []
    total_rows = len(df)
    print(f"Iniciando a preparação de {total_rows} registros para a carga...")
    start_time = time.time()
    for index, row in df.iterrows():
        statement = FinancialStatement(
            company_cnpj=row['CNPJ_CIA'], company_name=row.get('DENOM_CIA'), cvm_code=row.get('CD_CVM'),
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
    end_time = time.time()
    print(f"Preparação de objetos concluída em {end_time - start_time:.2f}s.")
    if objects_to_load:
        print("Iniciando a carga em lote no banco de dados...")
        start_bulk_time = time.time()
        session.bulk_save_objects(objects_to_load)
        session.commit()
        end_bulk_time = time.time()
        print(f"Carga completa concluída com sucesso em {end_bulk_time - start_bulk_time:.2f}s.")

def process_historical_financial_reports():
    START_YEAR = 2010
    end_year = datetime.now().year
    report_types = ['DFP', 'ITR']
    all_dfs = []

    print("="*80)
    print("INICIANDO PROCESSO DE CARGA HISTÓRICA COMPLETA")
    print(f"Período: {START_YEAR} a {end_year} | Documentos: {report_types}")
    print("="*80)

    for year in range(START_YEAR, end_year + 1):
        for doc_type in report_types:
            df = download_and_extract_data(year, doc_type)
            if df is not None:
                all_dfs.append(df)

    if not all_dfs:
        print("FALHA NO ETL: Nenhum dado foi baixado. Abortando.")
        return

    print("Concatenando todos os dataframes baixados...")
    final_df = pd.concat(all_dfs, ignore_index=True)
    print(f"Total de {len(final_df)} registros brutos encontrados.")

    with app.app_context():
        db_engine = db.engine
        Session = sessionmaker(bind=db_engine)
        session = Session()
        try:
            print("Buscando a lista de empresas válidas no banco de dados...")
            valid_cnpjs = {c.cnpj for c in session.query(Company.cnpj).all()}
            print(f"Encontradas {len(valid_cnpjs)} empresas na tabela 'companies'.")

            print("Limpando e validando CNPJs do DataFrame consolidado...")
            original_rows = len(final_df)
            final_df['CNPJ_CIA'] = final_df['CNPJ_CIA'].apply(clean_cnpj)
            df_filtered = final_df[final_df['CNPJ_CIA'].isin(valid_cnpjs)]
            filtered_rows = len(df_filtered)
            if filtered_rows < original_rows:
                print(f"AVISO: {original_rows - filtered_rows} registros foram descartados por não corresponderem a uma empresa na tabela 'companies'.")

            if df_filtered.empty:
                print("Nenhum registro válido para carregar após o filtro. Abortando.")
                return

            truncate_table(session)
            load_data(session, df_filtered)
        finally:
            session.close()

if __name__ == '__main__':
    process_historical_financial_reports()
    print("Script de ETL finalizado.")
