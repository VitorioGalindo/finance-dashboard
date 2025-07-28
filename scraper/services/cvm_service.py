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
    FinancialStatement, Company, CapitalStructure, Shareholder, CompanyAdministrator
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CVMDataCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(REQUESTS_HEADERS)
        self.base_url = CVM_DADOS_ABERTOS_URL

    def _download_and_extract_zip(self, url: str) -> Dict[str, pd.DataFrame]:
        # ... (código existente)
        pass

    def _get_company_map(self, session) -> Dict[str, int]:
        # ... (código existente)
        pass

    def _process_capital_structure(self, session, dataframes: Dict[str, pd.DataFrame], company_map: Dict[str, int], year: int):
        # ... (código existente)
        pass

    def _process_shareholders(self, session, dataframes: Dict[str, pd.DataFrame], company_map: Dict[str, int], year: int):
        # ... (código existente)
        pass

    def _process_administrators(self, session, dataframes: Dict[str, pd.DataFrame], company_map: Dict[str, int], year: int):
        logger.info("--- Processando Administradores ---")
        file_key = f'fre_cia_aberta_administrador_membro_conselho_fiscal_{year}.csv'
        df_admins = next((df for name, df in dataframes.items() if file_key in name), None)

        if df_admins is None:
            logger.warning(f"Arquivo '{file_key}' não encontrado no ZIP do FRE.")
            return

        df_admins.rename(columns={
            'CNPJ_Companhia': 'cnpj', 'Data_Referencia': 'reference_date', 'Nome': 'name',
            'CPF': 'document', 'Orgao_Administracao': 'position', 
            'Cargo_Eletivo_Ocupado': 'role', 'Data_Eleicao': 'election_date', 
            'Prazo_Mandato': 'term_of_office', 'Experiencia_Profissional': 'professional_background'
        }, inplace=True)

        df_admins['cnpj'] = df_admins['cnpj'].str.replace(r'\D', '', regex=True)
        date_cols = ['reference_date', 'election_date']
        for col in date_cols:
            df_admins[col] = pd.to_datetime(df_admins[col], errors='coerce')

        df_admins['company_id'] = df_admins['cnpj'].map(company_map)
        df_admins.dropna(subset=['company_id', 'reference_date', 'name'], inplace=True)
        df_admins['company_id'] = df_admins['company_id'].astype(int)

        model_columns = [c.name for c in CompanyAdministrator.__table__.columns if c.name not in ['id', 'created_at']]
        df_to_save = df_admins.loc[:, df_admins.columns.isin(model_columns)]
        
        records_to_save = df_to_save.to_dict(orient='records')

        if records_to_save:
            logger.info(f"Salvando {len(records_to_save)} registros de administradores...")
            session.query(CompanyAdministrator).filter(extract('year', CompanyAdministrator.reference_date) == year).delete(synchronize_session=False)
            session.bulk_insert_mappings(CompanyAdministrator, records_to_save)
            logger.info("Registros de administradores salvos com sucesso.")
        else:
            logger.info("Nenhum registro de administradores para salvar.")

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
            self._process_administrators(session, dataframes, company_map, year) # NOVA CHAMADA
            session.commit()
        logger.info(f"--- Processamento do FRE para o ano {year} concluído. ---")

    def run_historical_fre_load(self):
        # ... (código existente)
        pass
    
    def run_historical_financial_load(self):
        # ... (código existente)
        pass
    
    # Adicione aqui os métodos _download_and_extract_zip, _get_company_map, 
    # process_financial_statements, _process_capital_structure, _process_shareholders
    # e run_historical_financial_load completos das versões anteriores
    
