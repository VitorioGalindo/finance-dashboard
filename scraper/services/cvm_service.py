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
    FinancialStatement, Company, CapitalStructure, Shareholder, CompanyAdministrator, CompanyRiskFactor
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CVMDataCollector:
    # ... __init__, _download_and_extract_zip, _get_company_map ...
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(REQUESTS_HEADERS)
        self.base_url = CVM_DADOS_ABERTOS_URL

    def _download_and_extract_zip(self, url: str) -> Dict[str, pd.DataFrame]:
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
                    except (pd.errors.ParserError, ValueError) as e:
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
        companies = session.query(Company.id, Company.cnpj).all()
        return {cnpj.replace(r'\D', ''): company_id for company_id, cnpj in companies if cnpj}

    def _process_textual_fre_data(self, session, dataframes: Dict[str, pd.DataFrame], company_map: Dict[str, int], year: int):
        logger.info("--- Processando Dados Textuais (Atividades e Riscos) ---")
        
        # Processar Descrição de Atividades
        df_activities = next((df for name, df in dataframes.items() if f'preenchimento_item_2_{year}.csv' in name), None)
        if df_activities is not None:
            df_activities.rename(columns={'CNPJ_Companhia': 'cnpj', 'Atividades_Emissor': 'activity_description'}, inplace=True)
            df_activities['cnpj'] = df_activities['cnpj'].str.replace(r'\D', '', regex=True)
            df_activities = df_activities[['cnpj', 'activity_description']].dropna()
            
            for _, row in df_activities.iterrows():
                company_id = company_map.get(row['cnpj'])
                if company_id:
                    session.query(Company).filter(Company.id == company_id).update({'activity_description': row['activity_description']})
            logger.info(f"Atualizadas as descrições de atividades para {len(df_activities)} empresas.")
        
        # Processar Fatores de Risco
        df_risks = next((df for name, df in dataframes.items() if f'preenchimento_item_4_{year}.csv' in name), None)
        if df_risks is not None:
            df_risks.rename(columns={'CNPJ_Companhia': 'cnpj', 'Data_Referencia': 'reference_date', 'Tipo_Fator_Risco': 'risk_type', 'Fator_Risco': 'risk_description', 'Cobertura_Risco': 'mitigation_measures'}, inplace=True)
            
            df_risks['cnpj'] = df_risks['cnpj'].str.replace(r'\D', '', regex=True)
            df_risks['reference_date'] = pd.to_datetime(df_risks['reference_date'], errors='coerce')
            df_risks['company_id'] = df_risks['cnpj'].map(company_map)
            df_risks.dropna(subset=['company_id', 'reference_date'], inplace=True)
            df_risks['company_id'] = df_risks['company_id'].astype(int)

            model_columns = [c.name for c in CompanyRiskFactor.__table__.columns if c.name not in ['id', 'created_at']]
            df_to_save = df_risks.loc[:, df_risks.columns.isin(model_columns)]

            records_to_save = df_to_save.to_dict(orient='records')

            if records_to_save:
                logger.info(f"Salvando {len(records_to_save)} registros de fatores de risco...")
                session.query(CompanyRiskFactor).filter(extract('year', CompanyRiskFactor.reference_date) == year).delete(synchronize_session=False)
                session.bulk_insert_mappings(CompanyRiskFactor, records_to_save)
                logger.info("Registros de fatores de risco salvos.")
        else:
            logger.warning("Arquivo de fatores de risco não encontrado.")

    # ... Métodos existentes: _process_capital_structure, _process_shareholders, etc.
    def _process_capital_structure(self, session, dataframes: Dict[str, pd.DataFrame], company_map: Dict[str, int], year: int):
        # ...
        pass

    def _process_shareholders(self, session, dataframes: Dict[str, pd.DataFrame], company_map: Dict[str, int], year: int):
        # ...
        pass

    def _process_administrators(self, session, dataframes: Dict[str, pd.DataFrame], company_map: Dict[str, int], year: int):
        # ...
        pass
        
    def process_fre_data(self, year: int):
        logger.info(f"--- INICIANDO PROCESSAMENTO DE DADOS DO FRE PARA O ANO: {year} ---")
        url = f"{self.base_url}/CIA_ABERTA/DOC/FRE/DADOS/fre_cia_aberta_{year}.zip"
        
        dataframes = self._download_and_extract_zip(url)
        if not dataframes:
            logger.warning(f"Não foi possível baixar ou processar o arquivo ZIP do FRE para {year}.")
            return

        with get_db_session() as session:
            company_map = self._get_company_map(session)
            # Chamadas para os métodos existentes
            self._process_capital_structure(session, dataframes, company_map, year)
            self._process_shareholders(session, dataframes, company_map, year)
            self._process_administrators(session, dataframes, company_map, year)
            # NOVA CHAMADA para os dados textuais
            self._process_textual_fre_data(session, dataframes, company_map, year)
            session.commit()
        logger.info(f"--- Processamento do FRE para o ano {year} concluído. ---")

    def run_historical_fre_load(self):
        current_year = datetime.now().year
        for year in range(START_YEAR_HISTORICAL_LOAD, current_year + 1):
            self.process_fre_data(year)
            time.sleep(2)
        logger.info("--- Carga histórica de dados do FRE concluída ---")

    def run_historical_financial_load(self):
        # ...
        pass
