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
        """Busca um mapa de CNPJ para company_id."""
        companies = session.query(Company.id, Company.cnpj).all()
        return {cnpj.replace(r'\D', ''): company_id for company_id, cnpj in companies if cnpj}

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
        
        model_columns = [c.name for c in CapitalStructure.__table__.columns if c.name not in ['id', 'created_at']]
        df_to_save = df_capital.loc[:, df_capital.columns.isin(model_columns)]

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
            'CNPJ_Companhia': 'cnpj', 'Data_Referencia': 'reference_date', 'Acionista': 'name', 
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
    
    def process_financial_statements(self, doc_type: str, year: int):
        """
        Processa e salva os demonstrativos financeiros (DFP ou ITR) de um ano específico.
        """
        if doc_type.upper() not in ['DFP', 'ITR']:
            raise ValueError("doc_type deve ser 'DFP' ou 'ITR'")

        url = f"{self.base_url}/CIA_ABERTA/DOC/{doc_type.upper()}/DADOS/{doc_type.lower()}_cia_aberta_{year}.zip"
        
        all_dataframes = self._download_and_extract_zip(url)
        if not all_dataframes:
            logger.warning(f"Nenhum dado encontrado para {doc_type} em {year}.")
            return

        consolidated_dfs = [df for name, df in all_dataframes.items() if '_con_' in name]

        if not consolidated_dfs:
            logger.warning(f"Nenhum arquivo CONSOLIDADO encontrado para {doc_type} em {year}. Pulando.")
            return
            
        df_combined = pd.concat(consolidated_dfs, ignore_index=True)
        logger.info(f"Arquivos consolidados combinados. Total de {len(df_combined)} linhas brutas para {doc_type} {year}.")

        df_combined.rename(columns={
            'CD_CVM': 'cvm_code', 'DT_REFER': 'reference_date', 'VERSAO': 'version',
            'DENOM_CIA': 'company_name', 'CD_CONTA': 'account_code',
            'DS_CONTA': 'account_name', 'VL_CONTA': 'account_value',
            'ORDEM_EXERC': 'fiscal_year_order'
        }, inplace=True)
        
        df_combined = df_combined[df_combined['fiscal_year_order'] == 'ÚLTIMO'].copy()
        df_combined.dropna(subset=['account_code'], inplace=True)

        df_combined['account_value'] = pd.to_numeric(df_combined['account_value'], errors='coerce').fillna(0)
        df_combined['reference_date'] = pd.to_datetime(df_combined['reference_date'], errors='coerce')
        df_combined.dropna(subset=['reference_date'], inplace=True)

        logger.info("Iniciando pivotação da tabela...")
        df_pivot = df_combined.pivot_table(
            index=['cvm_code', 'company_name', 'reference_date', 'version'],
            columns='account_code', values='account_value', aggfunc='first'
        ).reset_index()

        logger.info(f"Tabela pivotada. Transformando {len(df_pivot)} registros para o formato do banco.")

        with get_db_session() as session:
            company_map = self._get_company_map(session)
            all_records_to_save = []

            for _, row in df_pivot.iterrows():
                cvm_code = str(row.get('cvm_code'))
                if cvm_code not in company_map:
                    continue

                record_data = {
                    "company_id": company_map[cvm_code],
                    "cvm_code": int(cvm_code),
                    "report_type": doc_type.upper(),
                    "reference_date": row.get('reference_date'),
                    "version": int(row.get('version')),
                    "data": {
                        col: val for col, val in row.items() 
                        if col not in ['cvm_code', 'company_name', 'reference_date', 'version'] and pd.notna(val)
                    }
                }
                financial_statement = FinancialStatement(**record_data)
                all_records_to_save.append(financial_statement)
            
            if all_records_to_save:
                logger.info(f"Salvando {len(all_records_to_save)} registros no banco de dados...")
                
                dates_to_delete = list(set(r.reference_date for r in all_records_to_save))
                cvm_codes_to_delete = list(set(r.cvm_code for r in all_records_to_save))
                
                session.query(FinancialStatement).filter(
                    FinancialStatement.report_type == doc_type.upper(),
                    FinancialStatement.reference_date.in_(dates_to_delete),
                    FinancialStatement.cvm_code.in_(cvm_codes_to_delete)
                ).delete(synchronize_session=False)

                session.bulk_save_objects(all_records_to_save)
                logger.info("Registros salvos com sucesso.")
            else:
                logger.info("Nenhum registro novo para salvar.")

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
                time.sleep(2)
        logger.info("--- Carga histórica de demonstrativos financeiros concluída ---")

