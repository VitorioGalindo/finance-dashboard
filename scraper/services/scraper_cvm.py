"""
Scraper para dados da CVM (Comissão de Valores Mobiliários)
Busca dados diretamente dos sistemas públicos da CVM
"""
import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
from io import StringIO, BytesIO
import zipfile
from app import db
from models import Company, FinancialStatement
import trafilatura

logger = logging.getLogger(__name__)

class CVMScraper:
    def __init__(self):
        self.base_url = "https://dados.cvm.gov.br/dados"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_companies_registry(self):
        """Scraper do cadastro de empresas da CVM"""
        try:
            # URL do arquivo CSV de empresas cadastradas
            url = f"{self.base_url}/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
            
            logger.info("Buscando cadastro de empresas da CVM...")
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            
            # Parse CSV com encoding correto
            df = pd.read_csv(StringIO(response.text), sep=';', encoding='latin1')
            
            companies_data = []
            for _, row in df.iterrows():
                company_data = {
                    'cvm_code': int(row.get('CD_CVM', 0)) if pd.notna(row.get('CD_CVM')) else None,
                    'company_name': str(row.get('DENOM_SOCIAL', '')).strip(),
                    'trade_name': str(row.get('DENOM_COMERC', '')).strip(),
                    'cnpj': str(row.get('CNPJ_CIA', '')).strip(),
                    'main_activity': str(row.get('SETOR_ATIV', '')).strip(),
                    'is_state_owned': str(row.get('CATEG_REG', '')) == 'Categoria A',
                    'is_foreign': str(row.get('PAIS', '')) != 'Brasil',
                    'founded_date': self._parse_date(row.get('DT_CONST')),
                    'is_b3_listed': str(row.get('SIT', '')) == 'ATIVO',
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                
                if company_data['cvm_code']:
                    companies_data.append(company_data)
            
            logger.info(f"Encontradas {len(companies_data)} empresas no cadastro CVM")
            return companies_data
            
        except Exception as e:
            logger.error(f"Erro ao buscar cadastro CVM: {str(e)}")
            return []
    
    def scrape_financial_statements(self, year=None):
        """Scraper de demonstrações financeiras"""
        if not year:
            year = datetime.now().year
            
        try:
            # URLs dos diferentes tipos de demonstrações
            statement_types = {
                'BPA': 'Balanço Patrimonial Ativo',
                'BPP': 'Balanço Patrimonial Passivo', 
                'DRE': 'Demonstração do Resultado',
                'DFC_MI': 'Demonstração dos Fluxos de Caixa',
                'DVA': 'Demonstração do Valor Adicionado',
                'DRA': 'Demonstração do Resultado Abrangente'
            }
            
            all_statements = []
            
            for statement_type, description in statement_types.items():
                logger.info(f"Extraindo {description} do ano {year}")
                
                url = f"{self.base_url}/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{statement_type}_{year}.zip"
                
                try:
                    response = self.session.get(url, timeout=120)
                    if response.status_code == 200:
                        # Extrair arquivo ZIP
                        with zipfile.ZipFile(BytesIO(response.content)) as zip_file:
                            # Encontrar arquivo CSV dentro do ZIP
                            csv_files = [f for f in zip_file.namelist() if f.endswith('.csv')]
                            if csv_files:
                                csv_content = zip_file.read(csv_files[0])
                                df = pd.read_csv(StringIO(csv_content.decode('latin1')), sep=';')
                                
                                # Processar dados financeiros
                                for _, row in df.iterrows():
                                    statement_data = {
                                        'cvm_code': int(row.get('CD_CVM', 0)) if pd.notna(row.get('CD_CVM')) else None,
                                        'report_type': statement_type,
                                        'aggregation': str(row.get('ORDEM_EXERC', 'INDIVIDUAL')),
                                        'reference_date': self._parse_date(row.get('DT_REFER')),
                                        'publish_date': self._parse_date(row.get('DT_RECEB')),
                                        'version': int(row.get('VERSAO', 1)) if pd.notna(row.get('VERSAO')) else 1,
                                        'data': self._extract_financial_data(row),
                                        'created_at': datetime.utcnow()
                                    }
                                    
                                    if statement_data['cvm_code'] and statement_data['reference_date']:
                                        all_statements.append(statement_data)
                                        
                except Exception as e:
                    logger.warning(f"Erro ao processar {statement_type}: {str(e)}")
                    continue
            
            logger.info(f"Extraídas {len(all_statements)} demonstrações financeiras")
            return all_statements
            
        except Exception as e:
            logger.error(f"Erro ao extrair demonstrações financeiras: {str(e)}")
            return []
    
    def scrape_stock_offerings(self):
        """Scraper de ofertas públicas de ações"""
        try:
            url = f"{self.base_url}/CIA_ABERTA/DOC/IPO/DADOS/"
            
            # Buscar página de listagem de arquivos
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                # Parse HTML para encontrar arquivos CSV
                import re
                csv_files = re.findall(r'href="([^"]*\.csv)"', response.text)
                
                offerings_data = []
                for csv_file in csv_files[-5:]:  # Últimos 5 arquivos
                    try:
                        file_url = url + csv_file
                        csv_response = self.session.get(file_url, timeout=30)
                        if csv_response.status_code == 200:
                            df = pd.read_csv(StringIO(csv_response.text), sep=';', encoding='latin1')
                            
                            for _, row in df.iterrows():
                                offering_data = {
                                    'cvm_code': int(row.get('CD_CVM', 0)) if pd.notna(row.get('CD_CVM')) else None,
                                    'offering_type': str(row.get('TP_OFERTA', '')),
                                    'offering_date': self._parse_date(row.get('DT_OFERTA')),
                                    'volume': float(row.get('VL_OFERTA', 0)) if pd.notna(row.get('VL_OFERTA')) else 0,
                                    'shares_offered': int(row.get('QT_ACOES', 0)) if pd.notna(row.get('QT_ACOES')) else 0,
                                    'price_per_share': float(row.get('VL_UNITARIO', 0)) if pd.notna(row.get('VL_UNITARIO')) else 0
                                }
                                
                                if offering_data['cvm_code']:
                                    offerings_data.append(offering_data)
                    except:
                        continue
                
                return offerings_data
                
        except Exception as e:
            logger.error(f"Erro ao extrair ofertas públicas: {str(e)}")
            return []
    
    def scrape_executive_compensation(self):
        """Scraper de remuneração de executivos"""
        try:
            current_year = datetime.now().year
            url = f"{self.base_url}/CIA_ABERTA/DOC/FRE/DADOS/fre_cia_aberta_remuneracao_{current_year}.csv"
            
            response = self.session.get(url, timeout=60)
            if response.status_code == 200:
                df = pd.read_csv(StringIO(response.text), sep=';', encoding='latin1')
                
                compensation_data = []
                for _, row in df.iterrows():
                    comp_data = {
                        'cvm_code': int(row.get('CD_CVM', 0)) if pd.notna(row.get('CD_CVM')) else None,
                        'executive_type': str(row.get('TP_ORGAO', '')),
                        'total_compensation': float(row.get('VL_TOTAL', 0)) if pd.notna(row.get('VL_TOTAL')) else 0,
                        'fixed_compensation': float(row.get('VL_FIXO', 0)) if pd.notna(row.get('VL_FIXO')) else 0,
                        'variable_compensation': float(row.get('VL_VARIAVEL', 0)) if pd.notna(row.get('VL_VARIAVEL')) else 0,
                        'stock_compensation': float(row.get('VL_ACOES', 0)) if pd.notna(row.get('VL_ACOES')) else 0,
                        'reference_year': current_year
                    }
                    
                    if comp_data['cvm_code']:
                        compensation_data.append(comp_data)
                
                return compensation_data
                
        except Exception as e:
            logger.error(f"Erro ao extrair remuneração executivos: {str(e)}")
            return []
    
    def _parse_date(self, date_str):
        """Parse date from CVM format"""
        if not date_str or pd.isna(date_str):
            return None
        try:
            return datetime.strptime(str(date_str).split()[0], '%Y-%m-%d')
        except:
            return None
    
    def _extract_financial_data(self, row):
        """Extrai dados financeiros estruturados da linha"""
        return {
            'account_code': str(row.get('CD_CONTA', '')),
            'account_description': str(row.get('DS_CONTA', '')),
            'value': float(row.get('VL_CONTA', 0)) if pd.notna(row.get('VL_CONTA')) else 0,
            'scale': str(row.get('ESCALA_MOEDA', 'UNIDADE'))
        }
    
    def load_companies_to_db(self, companies_data):
        """Carrega empresas no banco de dados"""
        loaded_count = 0
        
        try:
            for company_data in companies_data:
                if not company_data.get('cvm_code'):
                    continue
                    
                # Verificar se empresa já existe
                existing = Company.query.filter_by(cvm_code=company_data['cvm_code']).first()
                
                if existing:
                    # Atualizar dados existentes
                    for key, value in company_data.items():
                        if hasattr(existing, key) and value:
                            setattr(existing, key, value)
                    existing.updated_at = datetime.utcnow()
                else:
                    # Criar nova empresa
                    company = Company(**company_data)
                    db.session.add(company)
                
                loaded_count += 1
                
                # Commit a cada 100 registros
                if loaded_count % 100 == 0:
                    db.session.commit()
                    logger.info(f"Carregadas {loaded_count} empresas...")
            
            db.session.commit()
            logger.info(f"Total de {loaded_count} empresas carregadas no banco")
            return loaded_count
            
        except Exception as e:
            logger.error(f"Erro ao carregar empresas: {str(e)}")
            db.session.rollback()
            return 0
    
    def load_financial_statements_to_db(self, statements_data):
        """Carrega demonstrações financeiras no banco"""
        loaded_count = 0
        
        try:
            for statement_data in statements_data:
                if not statement_data.get('cvm_code'):
                    continue
                
                # Verificar se demonstração já existe
                existing = FinancialStatement.query.filter_by(
                    cvm_code=statement_data['cvm_code'],
                    report_type=statement_data['report_type'],
                    reference_date=statement_data['reference_date']
                ).first()
                
                if not existing:
                    statement = FinancialStatement(**statement_data)
                    db.session.add(statement)
                    loaded_count += 1
                    
                    # Commit a cada 50 registros
                    if loaded_count % 50 == 0:
                        db.session.commit()
                        logger.info(f"Carregadas {loaded_count} demonstrações...")
            
            db.session.commit()
            logger.info(f"Total de {loaded_count} demonstrações carregadas")
            return loaded_count
            
        except Exception as e:
            logger.error(f"Erro ao carregar demonstrações: {str(e)}")
            db.session.rollback()
            return 0
    
    def run_full_scraping(self):
        """Executa scraping completo da CVM"""
        logger.info("Iniciando scraping completo da CVM")
        
        # 1. Scraping do cadastro de empresas
        companies_data = self.scrape_companies_registry()
        companies_loaded = self.load_companies_to_db(companies_data)
        
        # 2. Scraping de demonstrações financeiras
        statements_data = self.scrape_financial_statements()
        statements_loaded = self.load_financial_statements_to_db(statements_data)
        
        # 3. Scraping de ofertas públicas
        offerings_data = self.scrape_stock_offerings()
        
        # 4. Scraping de remuneração de executivos
        compensation_data = self.scrape_executive_compensation()
        
        results = {
            'companies_loaded': companies_loaded,
            'statements_loaded': statements_loaded,
            'offerings_found': len(offerings_data),
            'compensation_records': len(compensation_data)
        }
        
        logger.info(f"Scraping CVM concluído: {results}")
        return results

if __name__ == '__main__':
    scraper = CVMScraper()
    scraper.run_full_scraping()