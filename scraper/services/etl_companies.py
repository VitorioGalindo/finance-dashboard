"""
ETL para dados de empresas brasileiras
Integração com brapi.dev, CVM e B3
"""
import requests
import logging
from datetime import datetime
from app import db
from models import Company, Ticker, Quote
from services.external_apis import BrapiAPI, CVMIntegration

logger = logging.getLogger(__name__)

class CompaniesETL:
    def __init__(self):
        self.brapi = BrapiAPI()
        self.cvm = CVMIntegration()
        
    def extract_companies_from_brapi(self):
        """Extrai lista de empresas da brapi.dev"""
        try:
            url = "https://brapi.dev/api/available"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'stocks' in data:
                return data['stocks']
            return []
            
        except Exception as e:
            logger.error(f"Erro ao buscar empresas da brapi: {str(e)}")
            return []
    
    def extract_company_details(self, ticker):
        """Extrai detalhes específicos de uma empresa"""
        try:
            # Buscar dados da brapi
            url = f"https://brapi.dev/api/quote/{ticker}?fundamental=true"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'results' in data and len(data['results']) > 0:
                return data['results'][0]
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar detalhes da empresa {ticker}: {str(e)}")
            return None
    
    def transform_company_data(self, raw_data):
        """Transforma dados brutos em formato para o banco"""
        if not raw_data:
            return None
            
        try:
            fundamentals = raw_data.get('summaryProfile', {})
            
            return {
                'company_name': fundamentals.get('longName', ''),
                'trade_name': raw_data.get('shortName', ''),
                'website': fundamentals.get('website', ''),
                'main_activity': fundamentals.get('longBusinessSummary', ''),
                'employee_count': fundamentals.get('fullTimeEmployees'),
                'b3_sector': fundamentals.get('sector', ''),
                'b3_subsector': fundamentals.get('industry', ''),
                'market_cap': raw_data.get('marketCap'),
                'tickers': [raw_data.get('symbol', '')],
                'is_b3_listed': True
            }
            
        except Exception as e:
            logger.error(f"Erro ao transformar dados da empresa: {str(e)}")
            return None
    
    def load_company(self, company_data):
        """Carrega dados da empresa no banco"""
        if not company_data:
            return None
            
        try:
            # Verificar se empresa já existe
            existing = Company.query.filter_by(
                company_name=company_data['company_name']
            ).first()
            
            if existing:
                # Atualizar empresa existente
                for key, value in company_data.items():
                    if hasattr(existing, key) and value:
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                company = existing
            else:
                # Criar nova empresa
                company = Company(**company_data)
                db.session.add(company)
            
            db.session.commit()
            logger.info(f"Empresa carregada: {company.company_name}")
            return company
            
        except Exception as e:
            logger.error(f"Erro ao carregar empresa: {str(e)}")
            db.session.rollback()
            return None
    
    def extract_cvm_companies(self):
        """Extrai empresas da CVM"""
        try:
            # Endpoint da CVM para empresas registradas
            url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            # Parse CSV data
            import pandas as pd
            from io import StringIO
            
            df = pd.read_csv(StringIO(response.text), sep=';', encoding='latin1')
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Erro ao buscar empresas da CVM: {str(e)}")
            return []
    
    def transform_cvm_data(self, cvm_record):
        """Transforma dados da CVM"""
        try:
            return {
                'cvm_code': int(cvm_record.get('CD_CVM', 0)),
                'company_name': cvm_record.get('DENOM_SOCIAL', ''),
                'trade_name': cvm_record.get('DENOM_COMERC', ''),
                'cnpj': cvm_record.get('CNPJ_CIA', ''),
                'main_activity': cvm_record.get('SETOR_ATIV', ''),
                'is_state_owned': cvm_record.get('CATEG_REG', '') == 'Categoria A',
                'is_foreign': cvm_record.get('PAIS', '') != 'Brasil',
                'founded_date': self._parse_date(cvm_record.get('DT_CONST')),
                'is_b3_listed': cvm_record.get('SIT', '') == 'ATIVO'
            }
        except Exception as e:
            logger.error(f"Erro ao transformar dados CVM: {str(e)}")
            return None
    
    def _parse_date(self, date_str):
        """Parse date from CVM format"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            return None
    
    def run_full_etl(self):
        """Executa ETL completo de empresas"""
        logger.info("Iniciando ETL de empresas")
        
        companies_processed = 0
        
        # 1. Buscar empresas da brapi
        brapi_companies = self.extract_companies_from_brapi()
        logger.info(f"Encontradas {len(brapi_companies)} empresas na brapi")
        
        for ticker in brapi_companies[:50]:  # Limitar para evitar timeout
            company_details = self.extract_company_details(ticker)
            if company_details:
                transformed_data = self.transform_company_data(company_details)
                if transformed_data:
                    company = self.load_company(transformed_data)
                    if company:
                        companies_processed += 1
                        
                        # Criar ticker associado
                        ticker_obj = Ticker.query.filter_by(symbol=ticker).first()
                        if not ticker_obj:
                            ticker_obj = Ticker(
                                symbol=ticker,
                                company_id=company.id,
                                type='ON' if ticker.endswith('3') else 'PN'
                            )
                            db.session.add(ticker_obj)
                            db.session.commit()
        
        # 2. Buscar empresas da CVM
        cvm_companies = self.extract_cvm_companies()
        logger.info(f"Encontradas {len(cvm_companies)} empresas na CVM")
        
        for cvm_record in cvm_companies[:100]:  # Limitar para performance
            transformed_data = self.transform_cvm_data(cvm_record)
            if transformed_data and transformed_data.get('cvm_code'):
                # Verificar se já existe empresa com mesmo CVM
                existing = Company.query.filter_by(
                    cvm_code=transformed_data['cvm_code']
                ).first()
                
                if not existing:
                    company = self.load_company(transformed_data)
                    if company:
                        companies_processed += 1
        
        logger.info(f"ETL de empresas concluído. {companies_processed} empresas processadas")
        return companies_processed

if __name__ == '__main__':
    etl = CompaniesETL()
    etl.run_full_etl()