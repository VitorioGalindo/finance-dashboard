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
        Baixa um arquivo ZIP e lê os CSVs com tratamento de erro para parsing.
        """
        try:
            logger.info(f"Tentando baixar arquivo de: {url}")
            response = self.session.get(url, timeout=300)
            response.raise_for_status()

            zip_file = zipfile.ZipFile(BytesIO(response.content))
            dataframes = {}
            for filename in zip_file.namelist():
                if filename.endswith('.csv'):
                    content = zip_file.read(filename)
                    try:
                        # Tenta com o motor 'c' que é mais rápido
                        df = pd.read_csv(io.BytesIO(content), sep=';', encoding='latin1', dtype=str, low_memory=False)
                        dataframes[filename] = df
                    except pd.errors.ParserError as e:
                        # Se falhar, tenta com o motor 'python' que é mais robusto
                        logger.warning(f"Falha no parsing de {filename} com motor 'c': {e}. Tentando com motor 'python'.")
                        df = pd.read_csv(io.BytesIO(content), sep=';', encoding='latin1', dtype=str, engine='python', on_bad_lines='warn')
                        dataframes[filename] = df
            
            logger.info(f"Sucesso ao baixar e extrair de {url}")
            return dataframes
            
        except requests.exceptions.HTTPError as e:
            if e.response is not None:
                logger.error(f"ERRO HTTP ao baixar {url}. Status Code: {e.response.status_code}.")
            return {}
        except Exception as e:
            logger.error(f"Erro inesperado ao processar {url}: {e}", exc_info=True)
            return {}

    def _get_company_map(self, session) -> Dict[str, int]:
        """Busca um mapa de CNPJ para company_id."""
        companies = session.query(Company.id, Company.cnpj).all()
        return {cnpj.replace(r'\D', ''): company_id for company_id, cnpj in companies}

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

        # **CORREÇÃO**: Selecionar apenas as colunas que o modelo CapitalStructure espera
        model_columns = [c.name for c in CapitalStructure.__table__.columns if c.name != 'id' and c.name != 'created_at']
        df_to_save = df_capital[model_columns]

        records_to_save = df_to_save.to_dict(orient='records')

        if records_to_save:
            logger.info(f"Salvando {len(records_to_save)} registros de estrutura de capital...")
            session.query(CapitalStructure).filter(extract('year', CapitalStructure.approval_date) == year).delete(synchronize_session=False)
            session.bulk_insert_mappings(CapitalStructure, records_to_save)
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
            df_shareholders[col] = pd.to_numeric(df_shareholders[col].str.replace(',', '.'), errors='coerce')
            
        df_shareholders['company_id'] = df_shareholders['cnpj'].map(company_map)
        df_shareholders.dropna(subset=['company_id', 'reference_date'], inplace=True)
        df_shareholders['company_id'] = df_shareholders['company_id'].astype(int)

        # **CORREÇÃO**: Selecionar apenas as colunas que o modelo Shareholder espera
        model_columns = [c.name for c in Shareholder.__table__.columns if c.name != 'id' and c.name != 'created_at']
        df_to_save = df_shareholders[model_columns]

        records_to_save = df_to_save.to_dict(orient='records')

        if records_to_save:
            logger.info(f"Salvando {len(records_to_save)} registros de acionistas...")
            session.query(Shareholder).filter(extract('year', Shareholder.reference_date) == year).delete(synchronize_session=False)
            session.bulk_insert_mappings(Shareholder, records_to_save)
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
            time.sleep(2)
        logger.info("--- Carga histórica de dados do FRE concluída ---")
        
    def run_historical_financial_load(self):
        """
        Executa a carga histórica completa para DFP e ITR.
        """
        current_year = datetime.now().year
        for year in range(START_YEAR_HISTORICAL_LOAD, current_year + 1):
            for doc_type in ['DFP', 'ITR']:
                logger.info(f"--- Processando {doc_type} para o ano de {year} ---")
                try:
                    self.process_financial_statements(doc_type, year)
                except Exception as e:
                    logger.error(f"Erro fatal ao processar {doc_type} para {year}: {e}", exc_info=True)
                # Pausa para não sobrecarregar o servidor da CVM
                time.sleep(2)
        logger.info("--- Carga histórica de demonstrativos financeiros concluída ---")
    
    # ... (restante da classe, incluindo process_financial_statements)
