# scraper/services/cvm_service.py
import requests
import pandas as pd
import logging
from datetime import datetime
from io import BytesIO, StringIO
import zipfile
import time
from typing import Dict, List, Optional

from scraper.config import CVM_DADOS_ABERTOS_URL, REQUESTS_HEADERS, START_YEAR_HISTORICAL_LOAD
from scraper.database import get_db_session
from scraper.models import FinancialStatement, Company  # Supondo que o modelo seja FinancialStatement

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CVMDataCollector:
    """
    Serviço central para coletar, processar e armazenar dados da CVM.
    Combina as melhores práticas dos scrapers anteriores em uma classe unificada.
    """
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(REQUESTS_HEADERS)
        self.base_url = CVM_DADOS_ABERTOS_URL

    def _download_and_extract_zip(self, url: str) -> Dict[str, pd.DataFrame]:
        """
        Baixa um arquivo ZIP da CVM, descompacta em memória e lê os CSVs.
        Retorna um dicionário onde as chaves são os nomes dos arquivos e os valores são DataFrames.
        """
        try:
            logger.info(f"Baixando arquivo de: {url}")
            response = self.session.get(url, timeout=300)  # Timeout de 5 minutos
            response.raise_for_status()

            zip_file = zipfile.ZipFile(BytesIO(response.content))
            dataframes = {}
            for filename in zip_file.namelist():
                if filename.endswith('.csv'):
                    logger.info(f"Lendo arquivo: {filename}")
                    # Ler com latin-1, que é o encoding comum da CVM, e especificar o separador
                    content = zip_file.read(filename).decode('latin-1')
                    df = pd.read_csv(StringIO(content), sep=';', dtype=str, low_memory=False)
                    dataframes[filename] = df
            
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
        
        dataframes = self._download_and_extract_zip(url)
        if not dataframes:
            logger.warning(f"Nenhum dado encontrado para {doc_type} em {year}.")
            return

        # Pegar o dataframe consolidado (con) - é o mais importante
        df_main_name = f'{doc_type.lower()}_cia_aberta_con_{year}.csv'
        df_main = next((df for name, df in dataframes.items() if df_main_name in name), None)

        if df_main is None:
            logger.error(f"DataFrame principal '{df_main_name}' não encontrado no ZIP.")
            return

        # --- Lógica de Transformação (ETL) ---
        logger.info(f"Iniciando transformação de {len(df_main)} registros para {doc_type} {year}.")
        
        # Renomear colunas para o padrão do banco
        df_main.rename(columns={
            'CD_CVM': 'cvm_code',
            'DT_REFER': 'reference_date',
            'VERSAO': 'version',
            'DENOM_CIA': 'company_name',
            'CD_CONTA': 'account_code',
            'DS_CONTA': 'account_name',
            'VL_CONTA': 'account_value',
            'ORDEM_EXERC': 'fiscal_year_order'
        }, inplace=True)
        
        # Pegar apenas o último exercício ('ÚLTIMO')
        df_main = df_main[df_main['fiscal_year_order'] == 'ÚLTIMO'].copy()

        # Normalização dos dados
        df_main['account_value'] = pd.to_numeric(df_main['account_value'], errors='coerce').fillna(0)
        df_main['reference_date'] = pd.to_datetime(df_main['reference_date'])
        
        # Pivotar a tabela para que cada conta vire uma coluna
        df_pivot = df_main.pivot_table(
            index=['cvm_code', 'company_name', 'reference_date', 'version'],
            columns='account_code',
            values='account_value',
            aggfunc='first' # Usar 'first' para evitar problemas com duplicatas
        ).reset_index()

        logger.info(f"Tabela pivotada. Transformando {len(df_pivot)} registros para o formato do banco.")

        with get_db_session() as session:
            company_map = self._get_company_map(session)
            records_to_save = []

            for _, row in df_pivot.iterrows():
                cvm_code = str(row['cvm_code'])
                if cvm_code not in company_map:
                    continue  # Pula empresas que não estão na nossa lista mestre

                # Mapeamento das contas para colunas do modelo (exemplo)
                # Este é um ponto crucial que precisa ser expandido com base no scraper/models_extended.py
                record = {
                    "company_id": company_map[cvm_code],
                    "cvm_code": int(cvm_code),
                    "report_type": doc_type.upper(),
                    "reference_date": row['reference_date'],
                    "version": int(row['version']),
                    "total_assets": row.get('1'),
                    "current_assets": row.get('1.01'),
                    "non_current_assets": row.get('1.02'),
                    "total_liabilities": row.get('2'),
                    "current_liabilities": row.get('2.01'),
                    "non_current_liabilities": row.get('2.02'),
                    "shareholders_equity": row.get('2.03'),
                    "revenue": row.get('3.01'),
                    "net_income": row.get('3.11'),
                    # Adicione outros mapeamentos aqui
                }
                
                # Filtrar chaves com valores nulos que não são permitidos no banco
                final_record = {k: v for k, v in record.items() if pd.notna(v)}
                records_to_save.append(FinancialStatement(**final_record))
            
            if records_to_save:
                logger.info(f"Salvando {len(records_to_save)} registros no banco de dados...")
                # Deletar registros antigos para o mesmo período/tipo antes de inserir (garante idempotência)
                session.query(FinancialStatement).filter(
                    FinancialStatement.report_type == doc_type.upper(),
                    FinancialStatement.reference_date.in_([r.reference_date for r in records_to_save])
                ).delete(synchronize_session=False)

                session.add_all(records_to_save)
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
                self.process_financial_statements(doc_type, year)
                time.sleep(5) # Pausa para não sobrecarregar o servidor da CVM
        logger.info("--- Carga histórica de demonstrativos financeiros concluída ---")
