
import os
import requests
import zipfile
import io
import pandas as pd
import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from tqdm import tqdm
import time

# Ajuste para importar a partir da raiz do projeto
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.config import get_db_engine
from backend.models import CvmDadosFinanceiros, Company

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/"
BASE_URL_ITR = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/"
START_YEAR = 2010
END_YEAR = 2025 # Ano atual + 1 para garantir que pegamos os dados mais recentes

# Mapeamento de colunas para o modelo SQLAlchemy
COLUMN_MAPPING = {
    'CNPJ_CIA': 'cnpj_cia',
    'DENOM_CIA': 'denom_cia',
    'CD_CVM': 'cd_cvm',
    'VERSAO': 'versao',
    'DT_REFER': 'dt_refer',
    'DT_INI_EXERC': 'dt_ini_exerc',
    'DT_FIM_EXERC': 'dt_fim_exerc',
    'CD_CONTA': 'cd_conta',
    'DS_CONTA': 'ds_conta',
    'VL_CONTA': 'vl_conta',
    'ESCALA_MOEDA': 'escala_moeda',
    'MOEDA': 'moeda',
    'ORDEM_EXERC': 'ordem_exerc'
}

def download_and_process_file(url, file_type, year):
    """Baixa um arquivo, descompacta e processa em um DataFrame."""
    try:
        logging.info(f"--> Tentando baixar {file_type} para o ano {year}...")
        response = requests.get(url)
        response.raise_for_status()

        logging.info("    + Download concluído. Processando...")
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        all_dfs = []
        for file_name in zip_file.namelist():
            if file_name.endswith('.csv'):
                with zip_file.open(file_name) as f:
                    try:
                        # Tenta ler com encoding 'latin1' que é comum em dados brasileiros
                        df = pd.read_csv(f, sep=';', encoding='latin1', dtype={'CD_CVM': str})
                        all_dfs.append(df)
                    except UnicodeDecodeError:
                        logging.warning(f"    - AVISO: Falha ao ler {file_name} com latin1, tentando utf-8...")
                        f.seek(0)
                        df = pd.read_csv(f, sep=';', encoding='utf-8', dtype={'CD_CVM': str})
                        all_dfs.append(df)

        if not all_dfs:
            logging.warning(f"    - AVISO: Nenhum arquivo CSV encontrado no zip para o ano {year}.")
            return None

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

def load_data(session, df, batch_size=10000):
    """
    Carrega os dados do DataFrame para o banco de dados em lotes (batches),
    com otimizações para performance.
    """
    logging.info("Limpando a tabela 'cvm_dados_financeiros' para a carga completa...")
    # Usamos TRUNCATE para resetar a tabela de forma eficiente e reiniciar a contagem de ID.
    session.execute(text("TRUNCATE TABLE cvm_dados_financeiros RESTART IDENTITY;"))
    session.commit()

    total_rows = len(df)
    logging.info(f"Iniciando a preparação e carga de {total_rows} registros em lotes de {batch_size}...")
    
    start_time_total = time.time()
    
    # Prepara as colunas de data
    df['DT_REFER'] = pd.to_datetime(df['DT_REFER'], errors='coerce')
    df['DT_INI_EXERC'] = pd.to_datetime(df['DT_INI_EXERC'], errors='coerce')
    df['DT_FIM_EXERC'] = pd.to_datetime(df['DT_FIM_EXERC'], errors='coerce')

    # Itera sobre o DataFrame em lotes
    for start in range(0, total_rows, batch_size):
        end = min(start + batch_size, total_rows)
        batch_df = df.iloc[start:end]
        
        logging.info(f"Processando lote: {start+1}-{end} de {total_rows}")
        
        # Converte o lote para uma lista de dicionários
        data_to_insert = batch_df.to_dict(orient='records')
        
        try:
            # Usa bulk_insert_mappings para eficiência
            session.bulk_insert_mappings(CvmDadosFinanceiros, data_to_insert)
            session.commit()
        except Exception as e:
            logging.error(f"ERRO ao inserir o lote {start+1}-{end}: {e}")
            session.rollback()
            # Opcional: parar o processo em caso de erro
            # raise e
            
    end_time_total = time.time()
    logging.info(f"Carga em lote concluída em {end_time_total - start_time_total:.2f} segundos.")


def process_historical_financial_reports():
    """Orquestra o processo de ETL para os relatórios financeiros."""
    logging.info("Iniciando o script de ETL para dados financeiros...")
    print("================================================================================")
    print(f"INICIANDO PROCESSO DE CARGA HISTÓRICA COMPLETA")
    print(f"Período: {START_YEAR} a {END_YEAR} | Documentos: ['DFP', 'ITR']")
    print("================================================================================")
    
    all_dataframes = []
    doc_types = [
        {'type': 'DFP', 'url_base': BASE_URL},
        {'type': 'ITR', 'url_base': BASE_URL_ITR}
    ]

    for year in range(START_YEAR, END_YEAR + 1):
        for doc in doc_types:
            file_url = f"{doc['url_base']}dfp_cia_aberta_{year}.zip" if doc['type'] == 'DFP' else f"{doc['url_base']}itr_cia_aberta_{year}.zip"
            
            # Condição especial para ITR, que tem nomes de arquivos diferentes
            if doc['type'] == 'ITR':
                file_url = f"{doc['url_base']}itr_cia_aberta_{year}.zip"
                # Adicionar os arquivos consolidados BPA, BPP, DFC_MD, DFC_MI, DMPL, DRE, DVA
                for report_type in ['BPA', 'BPP', 'DFC_MD', 'DFC_MI', 'DMPL', 'DRE', 'DVA']:
                    file_name = f"itr_cia_aberta_{report_type}_con_{year}.csv"
                    # Aqui, a lógica de download precisaria ser ajustada para arquivos CSV individuais
                    # Por simplicidade, vamos manter o ZIP por enquanto, mas cientes da estrutura.
                    
            df = download_and_process_file(file_url, doc['type'], year)
            if df is not None:
                # Adiciona uma coluna para identificar o tipo de demonstrativo (DFP/ITR)
                df['TIPO_DEMONSTRACAO'] = df['GRUPO_DFP'].apply(lambda x: x.split(' - ')[1] if ' - ' in x else x)
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
        
        # Limpando e formatando o CNPJ no DataFrame
        df_consolidated['CNPJ_CIA'] = df_consolidated['CNPJ_CIA'].str.replace(r'[./-]', '', regex=True).str.zfill(14)
        
        initial_count = len(df_consolidated)
        logging.info("Limpando e validando CNPJs do DataFrame consolidado...")
        df_filtered = df_consolidated[df_consolidated['CNPJ_CIA'].isin(valid_cnpjs)].copy()
        
        discarded_count = initial_count - len(df_filtered)
        if discarded_count > 0:
            logging.warning(f"{discarded_count} registros foram descartados por não corresponderem a uma empresa na tabela 'companies'.")

        if df_filtered.empty:
            logging.warning("Nenhum registro corresponde a uma empresa válida. Encerrando.")
            return

        # Renomear colunas para corresponder ao modelo
        df_filtered.rename(columns=COLUMN_MAPPING, inplace=True)
        
        # Garantir que todas as colunas do modelo existam no DataFrame
        # Adiciona colunas faltantes com None se não existirem
        model_columns = [c.name for c in CvmDadosFinanceiros.__table__.columns if c.name != 'id']
        for col in model_columns:
            if col not in df_filtered.columns:
                df_filtered[col] = None

        # Manter apenas as colunas que existem no modelo
        df_final = df_filtered[model_columns]

        load_data(session, df_final)
                
        print("===============================================================================")
        print("PROCESSO DE CARGA HISTÓRICA CONCLUÍDO COM SUCESSO!")
        print("================================================================================")

    except Exception as e:
        logging.error(f"ERRO GERAL no processo de ETL: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    process_historical_financial_reports()
