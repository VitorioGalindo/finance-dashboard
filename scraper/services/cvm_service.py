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
        # ... (código existente, robusto com fallback para engine 'python')
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
                        df = pd.read_csv(io.BytesIO(content), sep=';', encoding='latin1', dtype=str, low_memory=False)
                        dataframes[filename] = df
                    except pd.errors.ParserError as e:
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
        return {cnpj.replace(r'\D', ''): company_id for company_id, cnpj in companies if cnpj}

    def _process_capital_structure(self, session, dataframes: Dict[str, pd.DataFrame], company_map: Dict[str, int], year: int):
        # ... (código existente, já corrigido)
        pass

    def _process_shareholders(self, session, dataframes: Dict[str, pd.DataFrame], company_map: Dict[str, int], year: int):
        logger.info("--- Processando Composição Acionária ---")
        df_shareholders = next((df for name, df in dataframes.items() if f'posicao_acionaria_{year}.csv' in name), None)

        if df_shareholders is None:
            logger.warning("Arquivo 'posicao_acionaria' não encontrado no ZIP.")
            return
            
        # **CORREÇÃO DEFINITIVA**: Mapeia a coluna correta para a data de referência.
        df_shareholders = df_shareholders.rename(columns={
            'CNPJ_Companhia': 'cnpj', 
            'Data_Referencia': 'reference_date', # CORRIGIDO AQUI
            'Acionista': 'name', 
            'Tipo_Pessoa_Acionista': 'person_type', 
            'CPF_CNPJ_Acionista': 'document', 
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
        
        model_columns = [c.name for c in Shareholder.__table__.columns if c.name != 'id' and c.name != 'created_at']
        df_to_save = df_shareholders.loc[:, df_shareholders.columns.isin(model_columns)]

        records_to_save = df_to_save.to_dict(orient='records')

        if records_to_save:
            logger.info(f"Salvando {len(records_to_save)} registros de acionistas...")
            session.query(Shareholder).filter(extract('year', Shareholder.reference_date) == year).delete(synchronize_session=False)
            session.bulk_insert_mappings(Shareholder, records_to_save)
            logger.info("Registros de acionistas salvos.")
        else:
            logger.info("Nenhum registro de acionistas para salvar após os filtros.")

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
    
    # ... resto da classe
