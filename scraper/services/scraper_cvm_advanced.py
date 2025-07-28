"""
Scraper Avançado da CVM - Sistema completo para extração de dados financeiros
Captura DFPs, ITRs, FREs, FCAs e outros documentos estruturados da CVM
"""
import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from io import StringIO, BytesIO
import zipfile
import os
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CVMDataset:
    """Representa um dataset da CVM"""
    name: str
    code: str
    description: str
    url: str
    years_available: List[int]
    data_types: List[str]

class CVMAdvancedScraper:
    """Scraper avançado para todos os dados estruturados da CVM"""
    
    def __init__(self):
        self.base_url = "https://dados.cvm.gov.br/dados"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Datasets disponíveis na CVM
        self.datasets = {
            'dfp': CVMDataset(
                name="Demonstrações Financeiras Padronizadas",
                code="dfp",
                description="Balanço Patrimonial, DRE, DFC, DVA, etc.",
                url="CIA_ABERTA/DOC/DFP/DADOS",
                years_available=list(range(2020, 2026)),
                data_types=['BPA', 'BPP', 'DRE', 'DFC_MD', 'DFC_MI', 'DVA', 'DRA', 'DMPL']
            ),
            'itr': CVMDataset(
                name="Informações Trimestrais",
                code="itr",
                description="Demonstrações financeiras trimestrais",
                url="CIA_ABERTA/DOC/ITR/DADOS",
                years_available=list(range(2020, 2026)),
                data_types=['BPA', 'BPP', 'DRE', 'DFC_MD', 'DFC_MI', 'DVA', 'DRA']
            ),
            'fre': CVMDataset(
                name="Formulário de Referência",
                code="fre",
                description="Informações detalhadas sobre a empresa",
                url="CIA_ABERTA/DOC/FRE/DADOS",
                years_available=list(range(2020, 2026)),
                data_types=['general', 'stockholders', 'management', 'related_parties']
            ),
            'fca': CVMDataset(
                name="Formulário Cadastral",
                code="fca",
                description="Dados cadastrais das empresas",
                url="CIA_ABERTA/DOC/FCA/DADOS",
                years_available=list(range(2020, 2026)),
                data_types=['cadastral']
            )
        }
    
    def get_available_files(self, dataset_code: str, year: int) -> List[str]:
        """Lista arquivos disponíveis para um dataset e ano"""
        try:
            dataset = self.datasets[dataset_code]
            zip_url = f"{self.base_url}/{dataset.url}/{dataset_code}_cia_aberta_{year}.zip"
            
            logger.info(f"Verificando arquivos para {dataset.name} - {year}")
            
            # Fazer download do ZIP
            response = self.session.get(zip_url, timeout=30)
            response.raise_for_status()
            
            # Listar conteúdo do ZIP
            with zipfile.ZipFile(BytesIO(response.content)) as zip_file:
                files = zip_file.namelist()
                logger.info(f"Encontrados {len(files)} arquivos no dataset {dataset_code}_{year}")
                return files
                
        except Exception as e:
            logger.error(f"Erro ao listar arquivos {dataset_code}_{year}: {str(e)}")
            return []
    
    def download_and_extract_dataset(self, dataset_code: str, year: int) -> Dict[str, pd.DataFrame]:
        """Download e extração de um dataset completo"""
        try:
            dataset = self.datasets[dataset_code]
            zip_url = f"{self.base_url}/{dataset.url}/{dataset_code}_cia_aberta_{year}.zip"
            
            logger.info(f"Baixando {dataset.name} - {year}")
            logger.info(f"URL: {zip_url}")
            
            # Download do arquivo ZIP
            response = self.session.get(zip_url, timeout=60)
            response.raise_for_status()
            
            # Extrair e processar CSVs
            dataframes = {}
            
            with zipfile.ZipFile(BytesIO(response.content)) as zip_file:
                csv_files = [f for f in zip_file.namelist() if f.endswith('.csv')]
                
                logger.info(f"Processando {len(csv_files)} arquivos CSV")
                
                for csv_file in csv_files:
                    try:
                        # Extrair e ler CSV
                        csv_content = zip_file.read(csv_file)
                        csv_text = csv_content.decode('latin-1', errors='ignore')
                        
                        # Converter para DataFrame
                        df = pd.read_csv(StringIO(csv_text), sep=';', encoding='latin-1')
                        
                        # Limpar nome do arquivo
                        file_key = csv_file.replace('.csv', '').split('/')[-1]
                        dataframes[file_key] = df
                        
                        logger.info(f"Processado {file_key}: {len(df)} registros")
                        
                    except Exception as e:
                        logger.warning(f"Erro ao processar {csv_file}: {str(e)}")
                        continue
            
            return dataframes
            
        except Exception as e:
            logger.error(f"Erro ao baixar dataset {dataset_code}_{year}: {str(e)}")
            return {}
    
    def extract_company_financial_data(self, cvm_code: str, year: int = 2024) -> Dict[str, Any]:
        """Extrai dados financeiros completos de uma empresa específica"""
        try:
            logger.info(f"Extraindo dados financeiros da empresa CVM {cvm_code} - {year}")
            
            company_data = {
                'cvm_code': cvm_code,
                'year': year,
                'dfp_data': {},
                'itr_data': {},
                'fre_data': {},
                'extracted_at': datetime.now()
            }
            
            # 1. DFP - Demonstrações Financeiras Padronizadas
            dfp_data = self.download_and_extract_dataset('dfp', year)
            if dfp_data:
                company_dfp = self._filter_company_data(dfp_data, cvm_code)
                company_data['dfp_data'] = company_dfp
                logger.info(f"DFP extraído: {len(company_dfp)} datasets")
            
            # 2. ITR - Informações Trimestrais
            itr_data = self.download_and_extract_dataset('itr', year)
            if itr_data:
                company_itr = self._filter_company_data(itr_data, cvm_code)
                company_data['itr_data'] = company_itr
                logger.info(f"ITR extraído: {len(company_itr)} datasets")
            
            # 3. FRE - Formulário de Referência
            fre_data = self.download_and_extract_dataset('fre', year)
            if fre_data:
                company_fre = self._filter_company_data(fre_data, cvm_code)
                company_data['fre_data'] = company_fre
                logger.info(f"FRE extraído: {len(company_fre)} datasets")
            
            return company_data
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados da empresa {cvm_code}: {str(e)}")
            return {}
    
    def _filter_company_data(self, datasets: Dict[str, pd.DataFrame], cvm_code: str) -> Dict[str, pd.DataFrame]:
        """Filtra dados por código CVM"""
        filtered_data = {}
        
        for dataset_name, df in datasets.items():
            try:
                # Tentar diferentes colunas que podem conter o código CVM
                cvm_columns = ['CD_CVM', 'CNPJ_CIA', 'DENOM_CIA', 'CD_EMPRESA']
                
                for col in cvm_columns:
                    if col in df.columns:
                        # Filtrar por código CVM
                        company_df = df[df[col].astype(str).str.contains(str(cvm_code), na=False)]
                        
                        if not company_df.empty:
                            filtered_data[dataset_name] = company_df
                            logger.debug(f"Filtrado {dataset_name}: {len(company_df)} registros")
                            break
                        
            except Exception as e:
                logger.warning(f"Erro ao filtrar {dataset_name}: {str(e)}")
                continue
        
        return filtered_data
    
    def get_all_companies_basic_data(self, year: int = 2024) -> pd.DataFrame:
        """Extrai dados básicos de todas as empresas de um ano"""
        try:
            logger.info(f"Extraindo dados básicos de todas as empresas - {year}")
            
            # Baixar DFP do ano (contém dados de todas as empresas)
            dfp_data = self.download_and_extract_dataset('dfp', year)
            
            if not dfp_data:
                logger.warning(f"Nenhum dado DFP encontrado para {year}")
                return pd.DataFrame()
            
            # Procurar arquivo com dados das empresas
            company_files = [k for k in dfp_data.keys() if 'cia' in k.lower() or 'empresa' in k.lower()]
            
            if company_files:
                companies_df = dfp_data[company_files[0]]
                logger.info(f"Encontradas {len(companies_df)} empresas com dados DFP")
                return companies_df
            
            # Se não encontrar arquivo específico, usar qualquer um e extrair empresas únicas
            for dataset_name, df in dfp_data.items():
                if 'CD_CVM' in df.columns:
                    unique_companies = df[['CD_CVM', 'DENOM_CIA']].drop_duplicates()
                    logger.info(f"Extraídas {len(unique_companies)} empresas únicas de {dataset_name}")
                    return unique_companies
            
            logger.warning("Não foi possível extrair dados das empresas")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados das empresas {year}: {str(e)}")
            return pd.DataFrame()
    
    def extract_balance_sheet_data(self, cvm_code: str, year: int = 2024) -> Dict[str, Any]:
        """Extrai especificamente dados do balanço patrimonial"""
        try:
            logger.info(f"Extraindo balanço patrimonial - CVM {cvm_code} - {year}")
            
            dfp_data = self.download_and_extract_dataset('dfp', year)
            
            balance_data = {
                'cvm_code': cvm_code,
                'year': year,
                'assets': {},
                'liabilities': {},
                'equity': {},
                'extracted_at': datetime.now()
            }
            
            # Procurar dados do balanço patrimonial
            bpa_files = [k for k in dfp_data.keys() if 'bpa' in k.lower()]
            bpp_files = [k for k in dfp_data.keys() if 'bpp' in k.lower()]
            
            # Balanço Patrimonial Ativo
            if bpa_files:
                bpa_df = dfp_data[bpa_files[0]]
                company_bpa = bpa_df[bpa_df['CD_CVM'].astype(str) == str(cvm_code)]
                balance_data['assets'] = company_bpa.to_dict('records')
                logger.info(f"BPA extraído: {len(company_bpa)} contas")
            
            # Balanço Patrimonial Passivo
            if bpp_files:
                bpp_df = dfp_data[bpp_files[0]]
                company_bpp = bpp_df[bpp_df['CD_CVM'].astype(str) == str(cvm_code)]
                balance_data['liabilities'] = company_bpp.to_dict('records')
                logger.info(f"BPP extraído: {len(company_bpp)} contas")
            
            return balance_data
            
        except Exception as e:
            logger.error(f"Erro ao extrair balanço da empresa {cvm_code}: {str(e)}")
            return {}
    
    def extract_income_statement_data(self, cvm_code: str, year: int = 2024) -> Dict[str, Any]:
        """Extrai especificamente dados da DRE"""
        try:
            logger.info(f"Extraindo DRE - CVM {cvm_code} - {year}")
            
            dfp_data = self.download_and_extract_dataset('dfp', year)
            
            income_data = {
                'cvm_code': cvm_code,
                'year': year,
                'revenue': {},
                'expenses': {},
                'net_income': {},
                'extracted_at': datetime.now()
            }
            
            # Procurar dados da DRE
            dre_files = [k for k in dfp_data.keys() if 'dre' in k.lower()]
            
            if dre_files:
                dre_df = dfp_data[dre_files[0]]
                company_dre = dre_df[dre_df['CD_CVM'].astype(str) == str(cvm_code)]
                income_data['statements'] = company_dre.to_dict('records')
                logger.info(f"DRE extraída: {len(company_dre)} contas")
            
            return income_data
            
        except Exception as e:
            logger.error(f"Erro ao extrair DRE da empresa {cvm_code}: {str(e)}")
            return {}
    
    def batch_extract_companies(self, cvm_codes: List[str], year: int = 2024) -> Dict[str, Any]:
        """Extração em lote de múltiplas empresas"""
        try:
            logger.info(f"Extraindo dados de {len(cvm_codes)} empresas - {year}")
            
            # Download dos datasets uma vez só
            dfp_data = self.download_and_extract_dataset('dfp', year)
            itr_data = self.download_and_extract_dataset('itr', year)
            
            batch_results = {}
            
            for cvm_code in cvm_codes:
                try:
                    company_data = {
                        'cvm_code': cvm_code,
                        'year': year,
                        'dfp_data': self._filter_company_data(dfp_data, cvm_code),
                        'itr_data': self._filter_company_data(itr_data, cvm_code),
                        'extracted_at': datetime.now()
                    }
                    
                    batch_results[cvm_code] = company_data
                    logger.info(f"Extraído dados da empresa {cvm_code}")
                    
                except Exception as e:
                    logger.error(f"Erro ao extrair empresa {cvm_code}: {str(e)}")
                    continue
            
            logger.info(f"Extração em lote concluída: {len(batch_results)} empresas")
            return batch_results
            
        except Exception as e:
            logger.error(f"Erro na extração em lote: {str(e)}")
            return {}
    
    def get_dataset_summary(self) -> Dict[str, Any]:
        """Retorna resumo dos datasets disponíveis"""
        summary = {
            'total_datasets': len(self.datasets),
            'datasets': {},
            'last_updated': datetime.now()
        }
        
        for code, dataset in self.datasets.items():
            summary['datasets'][code] = {
                'name': dataset.name,
                'description': dataset.description,
                'years_available': dataset.years_available,
                'data_types': dataset.data_types,
                'estimated_files': len(dataset.data_types) * len(dataset.years_available)
            }
        
        return summary

# Função de uso prático
def extract_company_complete_data(cvm_code: str, year: int = 2024) -> Dict[str, Any]:
    """Função helper para extrair dados completos de uma empresa"""
    scraper = CVMAdvancedScraper()
    return scraper.extract_company_financial_data(cvm_code, year)

def get_all_companies_summary(year: int = 2024) -> pd.DataFrame:
    """Função helper para extrair resumo de todas as empresas"""
    scraper = CVMAdvancedScraper()
    return scraper.get_all_companies_basic_data(year)

if __name__ == "__main__":
    # Teste do scraper
    scraper = CVMAdvancedScraper()
    
    # Testar resumo dos datasets
    summary = scraper.get_dataset_summary()
    print(f"Datasets disponíveis: {summary['total_datasets']}")
    
    # Testar extração de uma empresa (exemplo)
    # company_data = scraper.extract_company_financial_data('25224', 2024)
    # print(f"Dados extraídos: {len(company_data)} seções")