# scraper/services/cvm_service.py
import requests
import pandas as pd
import logging
from datetime import datetime
from io import BytesIO
import zipfile
import time
from typing import Dict
import io
from sqlalchemy import extract

from scraper.config import CVM_DADOS_ABERTOS_URL, REQUESTS_HEADERS, START_YEAR_HISTORICAL_LOAD
from scraper.database import get_db_session
from scraper.models import (
    FinancialStatement, Company, CapitalStructure, Shareholder
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CVMDataCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(REQUESTS_HEADERS)
        self.base_url = CVM_DADOS_ABERTOS_URL

    def _download_and_extract_zip(self, url: str) -> Dict[str, pd.DataFrame]:
        """
        Baixa um arquivo ZIP, descompacta em memória e lê os CSVs.
        LOGGING MELHORADO para diagnosticar falhas de download.
        """
        try:
            logger.info(f"Tentando baixar arquivo de: {url}")
            response = self.session.get(url, timeout=300)
            response.raise_for_status()  # Isso irá gerar um erro para status 4xx ou 5xx

            zip_file = zipfile.ZipFile(BytesIO(response.content))
            file_list = zip_file.namelist()
            
            if not file_list:
                logger.warning(f"O arquivo ZIP de {url} foi baixado mas está vazio.")
                return {}

            logger.debug(f"Arquivos encontrados no ZIP: {file_list}")
            dataframes = {}
            for filename in file_list:
                if filename.endswith('.csv'):
                    content = zip_file.read(filename)
                    df = pd.read_csv(io.BytesIO(content), sep=';', encoding='latin1', dtype=str, low_memory=False)
                    dataframes[filename] = df
            
            if not dataframes:
                logger.warning(f"ZIP baixado de {url}, mas nenhum arquivo .csv foi encontrado dentro dele.")
                return {}

            logger.info(f"Sucesso ao baixar e extrair de {url}")
            return dataframes
            
        except requests.exceptions.HTTPError as e:
            # LOG CRÍTICO: Informa o status code do erro.
            if e.response is not None:
                logger.error(f"ERRO HTTP ao baixar {url}. Status Code: {e.response.status_code}.")
            else:
                logger.error(f"ERRO HTTP ao baixar {url}: {e}")
            return {} # Retorna dicionário vazio em caso de erro HTTP
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de rede (não-HTTP) ao baixar {url}: {e}")
            return {}
        except zipfile.BadZipFile:
            logger.error(f"Erro: O arquivo baixado de {url} não é um ZIP válido.")
            return {}
        except Exception as e:
            logger.error(f"Erro inesperado ao processar {url}: {e}", exc_info=True)
            return {}

    def _get_company_map(self, session) -> Dict[str, int]:
        """Busca um mapa de CNPJ para company_id."""
        companies = session.query(Company.id, Company.cnpj).all()
        return {cnpj.replace(r'\D', ''): company_id for company_id, cnpj in companies}

    def process_financial_statements(self, doc_type: str, year: int):
        # ... (código existente)
        pass

    def _process_capital_structure(self, session, dataframes: Dict[str, pd.DataFrame], company_map: Dict[str, int], year: int):
        logger.info("--- Processando Estrutura de Capital ---")
        df_capital = next((df for name, df in dataframes.items() if f'capital_social_{year}.csv' in name), None)

        if df_capital is None:
            logger.warning("Arquivo 'capital_social' não encontrado no ZIP do FRE.")
            return

        df_capital = df_capital.rename(columns={
            'CNPJ_Companhia': 'cnpj', 'Data_Autorizacao_Aprovacao': 'approval_date', 
            'Tipo_Capital': 'event_type', 'Valor_Capital': 'value', 
            'Quantidade_Acoes_Ordinarias': 'qty_ordinary_shares', 
            'Quantidade_Acoes_Preferenciais': 'qty_preferred_shares', 
            'Quantidade_Total_Acoes': 'qty_total_shares'
        })
        
        df_capital['cnpj'] = df_capital['cnpj'].str.replace(r'\D', '', regex=True)
        df_capital['approval_date'] = pd.to_datetime(df_capital['approval_date'], errors='coerce')
        numeric_cols = ['value', 'qty_ordinary_shares', 'qty_preferred_shares', 'qty_total_shares']
        for col in numeric_cols:
            df_capital[col] = pd.to_numeric(df_capital[col], errors='coerce')
        
        df_capital.dropna(subset=['cnpj', 'approval_date'], inplace=True)
        
        df_capital['company_id'] = df_capital['cnpj'].map(company_map)
        df_capital.dropna(subset=['company_id'], inplace=True)
        df_capital['company_id'] = df_capital['company_id'].astype(int)

        records_to_save = [CapitalStructure(**row) for row in df_capital.to_dict(orient='records') if 'company_id' in row and row['company_id']]

        if records_to_save:
            logger.info(f"Salvando {len(records_to_save)} registros de estrutura de capital...")
            date_to_delete = datetime(year, 1, 1)
            session.query(CapitalStructure).filter(extract('year', CapitalStructure.approval_date) == year).delete(synchronize_session=False)
            session.bulk_save_objects(records_to_save)
            logger.info("Registros de estrutura de capital salvos.")

    def _process_shareholders(self, session, dataframes: Dict[str, pd.DataFrame], company_map: Dict[str, int], year: int):
        logger.info("--- Processando Composição Acionária ---")
        df_shareholders = next((df for name, df in dataframes.items() if f'posicao_acionaria_{year}.csv' in name), None)

        if df_shareholders is None:
            logger.warning("Arquivo 'posicao_acionaria' não encontrado no ZIP.")
            return
            
        df_shareholders = df_shareholders.rename(columns={
            'CNPJ_Companhia': 'cnpj', 'Data_Composicao_Capital_Social': 'reference_date', 'Acionista': 'name', 
            'Tipo_Pessoa_Acionista': 'person_type', 'CPF_CNPJ_Acionista': 'document', 
            'Acionista_Controlador': 'is_controller', 
            'Percentual_Acao_Ordinaria_Circulacao': 'pct_ordinary_shares', 
            'Percentual_Acao_Preferencial_Circulacao': 'pct_preferred_shares'
        })
        
        df_shareholders['cnpj'] = df_shareholders['cnpj'].str.replace(r'\D', '', regex=True)
        df_shareholders['reference_date'] = pd.to_datetime(df_shareholders['reference_date'], errors='coerce')
        df_shareholders['is_controller'] = df_shareholders['is_controller'] == 'S'
        
        numeric_cols = ['pct_ordinary_shares', 'pct_preferred_shares']
        for col in numeric_cols:
            df_shareholders[col] = pd.to_numeric(df_shareholders[col], errors='coerce')
            
        df_shareholders['company_id'] = df_shareholders['cnpj'].map(company_map)
        df_shareholders.dropna(subset=['company_id', 'reference_date'], inplace=True)
        df_shareholders['company_id'] = df_shareholders['company_id'].astype(int)
        
        records_to_save = [Shareholder(**row) for row in df_shareholders.to_dict(orient='records') if 'company_id' in row and row['company_id']]

        if records_to_save:
            logger.info(f"Salvando {len(records_to_save)} registros de acionistas...")
            session.query(Shareholder).filter(extract('year', Shareholder.reference_date) == year).delete(synchronize_session=False)
            session.bulk_save_objects(records_to_save)
            logger.info("Registros de acionistas salvos.")

    def process_fre_data(self, year: int):
        logger.info(f"--- INICIANDO PROCESSAMENTO DE DADOS DO FRE PARA O ANO: {year} ---")
        url = f"{self.base_url}/CIA_ABERTA/DOC/FRE/DADOS/fre_cia_aberta_{year}.zip"
        
        dataframes = self._download_and_extract_zip(url)
        if not dataframes:
            logger.warning(f"Não foi possível baixar ou processar o arquivo ZIP do FRE para {year}.")
            return

        with get_db_session() as session:
            company_map = self._get_company_map(session)
            self._process_capital_structure(session, dataframes, company_map, year)
            self._process_shareholders(session, dataframes, company_map, year)
            session.commit()
        logger.info(f"--- Processamento do FRE para o ano {year} concluído. ---")

    def run_historical_fre_load(self):
        current_year = datetime.now().year
        for year in range(START_YEAR_HISTORICAL_LOAD, current_year + 1):
            self.process_fre_data(year)
            time.sleep(2) # Pausa amigável
        logger.info("--- Carga histórica de dados do FRE concluída ---")
