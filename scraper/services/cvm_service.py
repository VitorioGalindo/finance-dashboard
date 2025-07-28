# scraper/services/cvm_service.py
import requests
import pandas as pd
import logging
from datetime import datetime
from io import BytesIO, StringIO
import zipfile
import time
from typing import Dict, List, Optional
import io

from scraper.config import CVM_DADOS_ABERTOS_URL, REQUESTS_HEADERS, START_YEAR_HISTORICAL_LOAD
from scraper.database import get_db_session
from scraper.models import FinancialStatement, Company

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CVMDataCollector:
    """
    Serviço central para coletar, processar e armazenar dados da CVM.
    """
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(REQUESTS_HEADERS)
        self.base_url = CVM_DADOS_ABERTOS_URL

    def _download_and_extract_zip(self, url: str) -> Dict[str, pd.DataFrame]:
        """
        Baixa um arquivo ZIP, descompacta em memória e lê os CSVs.
        """
        try:
            logger.info(f"Baixando arquivo de: {url}")
            response = self.session.get(url, timeout=300)
            response.raise_for_status()

            zip_file = zipfile.ZipFile(BytesIO(response.content))
            
            file_list = zip_file.namelist()
            logger.debug(f"Arquivos encontrados no ZIP: {file_list}")

            dataframes = {}
            for filename in file_list:
                if filename.endswith('.csv'):
                    try:
                        content = zip_file.read(filename)
                        df = pd.read_csv(io.BytesIO(content), sep=';', encoding='latin1', dtype=str, low_memory=False)
                        dataframes[filename] = df
                    except Exception as e:
                        logger.warning(f"Não foi possível ler o arquivo {filename}: {e}")
            
            logger.info(f"Sucesso ao baixar e extrair de {url}")
            return dataframes
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de rede ao baixar {url}: {e}")
        except zipfile.BadZipFile:
            logger.error(f"Erro: O arquivo baixado de {url} não é um ZIP válido.")
        except Exception as e:
            logger.error(f"Erro inesperado ao processar {url}: {e}")
        return {}

    def _get_company_map(self, session) -> Dict[str, int]:
        """Busca no banco um mapa de CVM_CODE para o ID da empresa."""
        companies = session.query(Company.cvm_code, Company.id).all()
        return {str(cvm_code): company_id for cvm_code, company_id in companies}

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

        # --- CORREÇÃO: Lógica de combinação de arquivos inspirada nos scripts antigos ---
        # 1. Filtrar apenas os dataframes CONSOLIDADOS ('_con_').
        consolidated_dfs = [df for name, df in all_dataframes.items() if '_con_' in name]

        if not consolidated_dfs:
            logger.warning(f"Nenhum arquivo CONSOLIDADO encontrado para {doc_type} em {year}. Pulando.")
            return
            
        # 2. Combinar todos os dataframes consolidados em um só.
        df_combined = pd.concat(consolidated_dfs, ignore_index=True)
        logger.info(f"Arquivos consolidados combinados. Total de {len(df_combined)} linhas brutas para {doc_type} {year}.")

        # --- Lógica de Transformação (ETL) ---
        df_combined.rename(columns={
            'CD_CVM': 'cvm_code', 'DT_REFER': 'reference_date', 'VERSAO': 'version',
            'DENOM_CIA': 'company_name', 'CD_CONTA': 'account_code',
            'DS_CONTA': 'account_name', 'VL_CONTA': 'account_value',
            'ORDEM_EXERC': 'fiscal_year_order'
        }, inplace=True)
        
        # Filtra apenas o último período fiscal e remove linhas sem código de conta
        df_combined = df_combined[df_combined['fiscal_year_order'] == 'ÚLTIMO'].copy()
        df_combined.dropna(subset=['account_code'], inplace=True)

        df_combined['account_value'] = pd.to_numeric(df_combined['account_value'], errors='coerce').fillna(0)
        df_combined['reference_date'] = pd.to_datetime(df_combined['reference_date'], errors='coerce')
        df_combined.dropna(subset=['reference_date'], inplace=True)

        # Pivotar a tabela para que cada conta vire uma coluna
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

                # Mapeamento dinâmico das contas para o modelo
                record_data = {
                    "company_id": company_map[cvm_code],
                    "cvm_code": int(cvm_code),
                    "report_type": doc_type.upper(),
                    "reference_date": row.get('reference_date'),
                    "version": int(row.get('version')),
                    "data": {
                        # Adiciona todas as colunas que não são do índice no campo JSON
                        col: val for col, val in row.items() 
                        if col not in ['cvm_code', 'company_name', 'reference_date', 'version'] and pd.notna(val)
                    }
                }

                # Cria o objeto do modelo com os dados extraídos
                # Esta parte foi simplificada para usar o campo 'data' JSON,
                # que é mais flexível do que mapear cada conta para uma coluna.
                # Adapte se o seu modelo final tiver colunas nomeadas.
                financial_statement = FinancialStatement(**record_data)
                all_records_to_save.append(financial_statement)
            
            if all_records_to_save:
                logger.info(f"Salvando {len(all_records_to_save)} registros no banco de dados...")
                
                # Para ser idempotente, delete os registros antigos que seriam substituídos
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
                # Pausa para não sobrecarregar o servidor da CVM
                time.sleep(2)
        logger.info("--- Carga histórica de demonstrativos financeiros concluída ---")
