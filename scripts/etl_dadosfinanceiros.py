# scripts/etl_dadosfinanceiros.py

import os
import requests
import zipfile
import io
import pandas as pd
import logging
from sqlalchemy.orm import sessionmaker, inspect
from sqlalchemy import text
from tqdm import tqdm
import time

# Ajuste para importar a partir da raiz do projeto
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.config import get_db_engine
from backend.models import FinancialStatement, Company

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/"
BASE_URL_ITR = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/"
START_YEAR = 2023
END_YEAR = 2025

# Mapeamento CORRETO para os atributos da classe FinancialStatement
COLUMN_MAPPING = {
    'CNPJ_CIA': 'company_cnpj',
    'DENOM_CIA': 'company_name',
    'CD_CVM': 'cvm_code',
    'VERSAO': 'report_version',
    'DT_REFER': 'reference_date',
    'DT_INI_EXERC': 'fiscal_year_start',
    'DT_FIM_EXERC': 'fiscal_year_end',
    'CD_CONTA': 'account_code',
    'DS_CONTA': 'account_description',
    'VL_CONTA': 'account_value',
    'ESCALA_MOEDA': 'currency_scale',
    'MOEDA': 'currency',
    'ORDEM_EXERC': 'fiscal_year_order',
    'TIPO_DEMONSTRACAO': 'report_type',
    'PERIODO': 'period'
}

def download_and_process_file(url, file_type, year):
    """Baixa um arquivo, descompacta e processa em um DataFrame."""
    try:
        logging.info(f"--> Tentando baixar {file_type} para o ano {year}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()

        logging.info("    + Download concluído. Processando...")
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        all_dfs = []
        
        csv_files = [f for f in zip_file.namelist() if f.endswith('.csv')]
        if not csv_files:
            logging.warning(f"    - AVISO: Nenhum arquivo CSV encontrado no zip para o ano {year}.")
            return None

        for file_name in csv_files:
            with zip_file.open(file_name) as f:
                try:
                    df = pd.read_csv(f, sep=';', encoding='latin1', dtype={'CD_CVM': str, 'CNPJ_CIA': str})
                    all_dfs.append(df)
                except UnicodeDecodeError:
                    logging.warning(f"    - AVISO: Falha ao ler {file_name} com latin1, tentando utf-8...")
                    f.seek(0)
                    df = pd.read_csv(f, sep=';', encoding='utf-8', dtype={'CD_CVM': str, 'CNPJ_CIA': str})
                    all_dfs.append(df)

        consolidated_df = pd.concat(all_dfs, ignore_index=True)
        logging.info(f"    + DataFrame criado com sucesso ({len(consolidated_df)} linhas).")
        return consolidated_df

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logging.warning(f"    - AVISO: Arquivo não encontrado (404). Pulando.")
        else:
            logging.error(f"    - ERRO: Falha no download. Status: {e.response.status_code}. URL: {url}")
    except Exception as e:
        logging.error(f"    - ERRO: Falha ao processar o arquivo para o ano {year}. Detalhes: {e}")
    return None

def load_data(session, df, batch_size=50000):
    """
    Carrega os dados do DataFrame para o banco de dados em lotes (batches).
    """
    logging.info("Limpando a tabela 'cvm_dados_financeiros' para a carga completa...")
    session.execute(text("TRUNCATE TABLE cvm_dados_financeiros RESTART IDENTITY;"))
    session.commit()

    # Renomeia as colunas do DataFrame para corresponderem aos atributos do modelo
    df.rename(columns=COLUMN_MAPPING, inplace=True)
    
    # Converte colunas de data
    date_columns = ['reference_date', 'fiscal_year_start', 'fiscal_year_end']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    df.dropna(subset=['reference_date'], inplace=True)
    
    total_rows = len(df)
    logging.info(f"Iniciando a preparação e carga de {total_rows} registros em lotes de {batch_size}...")

    for start in tqdm(range(0, total_rows, batch_size), desc="Carregando dados para o BD"):
        end = min(start + batch_size, total_rows)
        batch_df = df.iloc[start:end]
        
        # ============================================================================
        # CORREÇÃO: A lógica de filtro defeituosa foi removida.
        # Agora, simplesmente convertemos o DataFrame para dicionários.
        # O SQLAlchemy se encarregará de usar as chaves que correspondem aos
        # atributos do modelo e ignorar as que não correspondem.
        # ============================================================================
        data_to_insert = batch_df.to_dict(orient='records')
        
        if not data_to_insert:
            continue

        try:
            session.bulk_insert_mappings(FinancialStatement, data_to_insert)
            session.commit()
        except Exception as e:
            logging.error(f"ERRO ao inserir o lote {start+1}-{end}: {e}")
            session.rollback()

def process_historical_financial_reports():
    """Orquestra o processo de ETL para os relatórios financeiros."""
    logging.info("Iniciando o script de ETL para dados financeiros...")
    print("="*80)
    print(f"INICIANDO PROCESSO DE CARGA HISTÓRICA COMPLETA")
    print(f"Período: {START_YEAR} a {END_YEAR} | Documentos: ['DFP', 'ITR']")
    print("="*80)
    
    all_dataframes = []
    doc_types = [
        {'type': 'DFP', 'url_base': BASE_URL},
        {'type': 'ITR', 'url_base': BASE_URL_ITR}
    ]

    for year in range(START_YEAR, END_YEAR + 1):
        for doc in doc_types:
            file_url = f"{doc['url_base']}{doc['type'].lower()}_cia_aberta_{year}.zip"
            df = download_and_process_file(file_url, doc['type'], year)
            if df is not None:
                if 'GRUPO_DFP' in df.columns:
                    df['TIPO_DEMONSTRACAO'] = df['GRUPO_DFP'].apply(
                        lambda x: x.split(' - ')[1] if isinstance(x, str) and ' - ' in x else x
                    )
                else:
                    df['TIPO_DEMONSTRACAO'] = 'N/A'
                df['PERIODO'] = 'ANUAL' if doc['type'] == 'DFP' else 'TRIMESTRAL'
                all_dataframes.append(df)

    if not all_dataframes:
        logging.error("Nenhum dado foi baixado. Encerrando o processo.")
        return

    logging.info("Concatenando todos os dataframes baixados...")
    df_consolidated = pd.concat(all_dataframes, ignore_index=True)
    logging.info(f"Total de {len(df_consolidated)} registros brutos encontrados.")

    engine = get_db_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        logging.info("Buscando a lista de empresas válidas no banco de dados...")
        companies = session.query(Company.cnpj).all()
        valid_cnpjs = {c.cnpj for c in companies}
        logging.info(f"Encontradas {len(valid_cnpjs)} empresas na tabela 'companies'.")
        
        df_consolidated['CNPJ_CIA'] = df_consolidated['CNPJ_CIA'].str.replace(r'[./-]', '', regex=True).str.zfill(14)
        
        logging.info("Filtrando registros para CNPJs válidos...")
        df_filtered = df_consolidated[df_consolidated['CNPJ_CIA'].isin(valid_cnpjs)].copy()
        
        discarded_count = len(df_consolidated) - len(df_filtered)
        if discarded_count > 0:
            logging.warning(f"{discarded_count} registros foram descartados por não corresponderem a uma empresa na tabela 'companies'.")

        if df_filtered.empty:
            logging.warning("Nenhum registro corresponde a uma empresa válida. Encerrando.")
            return
        
        load_data(session, df_filtered, batch_size=50000)
                
        print("\n" + "="*80)
        print("PROCESSO DE CARGA HISTÓRICA CONCLUÍDO COM SUCESSO!")
        print("="*80)

    except Exception as e:
        logging.error(f"ERRO GERAL no processo de ETL: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    process_historical_financial_reports()