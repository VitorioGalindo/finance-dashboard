"""
Filtro para manter apenas empresas com ticker e negociação ativa na B3
"""
import requests
import logging
from typing import List, Dict, Optional
from app import db
from models import Company

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class B3CompanyFilter:
    """Filtra empresas mantendo apenas as com ticker e negociação ativa na B3"""
    
    def __init__(self):
        self.brapi_base_url = "https://brapi.dev/api/quote"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; B3CompanyFilter/1.0)'
        })
    
    def get_active_b3_tickers(self) -> List[str]:
        """Busca tickers ativos na B3 via brapi.dev"""
        try:
            # Busca lista de todas as ações disponíveis
            response = self.session.get(f"{self.brapi_base_url}/list")
            if response.status_code == 200:
                data = response.json()
                if 'stocks' in data:
                    return [stock for stock in data['stocks'] if self._is_valid_ticker(stock)]
            
            # Fallback: lista manual de tickers mais negociados
            return self._get_manual_ticker_list()
            
        except Exception as e:
            logger.error(f"Erro ao buscar tickers da B3: {str(e)}")
            return self._get_manual_ticker_list()
    
    def _is_valid_ticker(self, ticker: str) -> bool:
        """Valida se o ticker segue padrão brasileiro"""
        if not ticker or len(ticker) < 5:
            return False
        
        # Padrão: 4 letras + número (ex: PRIO3, VALE3, PETR4)
        return (len(ticker) >= 5 and 
                ticker[:4].isalpha() and 
                ticker[4:].isdigit() and
                ticker.endswith(('3', '4', '11')))
    
    def _get_manual_ticker_list(self) -> List[str]:
        """Lista manual dos principais tickers B3 para fallback"""
        return [
            'PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'ABEV3', 'MGLU3', 'WEGE3',
            'PRIO3', 'RENT3', 'LREN3', 'JBSS3', 'RAIL3', 'UGPA3', 'USIM5',
            'CCRO3', 'CSAN3', 'ELET3', 'CMIG4', 'GOAU4', 'CSNA3', 'SUZB3',
            'KLBN11', 'EMBR3', 'CVCB3', 'NTCO3', 'RADL3', 'BRFS3', 'MRFG3',
            'QUAL3', 'AZUL4', 'GOLL4', 'BEEF3', 'LWSA3', 'TOTS3', 'PETZ3',
            'IFCM3', 'MEAL3', 'SOMA3', 'YDUQ3', 'VVAR3', 'MULT3', 'MDIA3'
        ]
    
    def get_company_ticker_mapping(self) -> Dict[str, str]:
        """Cria mapeamento entre código CVM e ticker B3"""
        # Mapeamento manual para principais empresas
        # Em implementação real, seria extraído dos formulários CVM
        return {
            '22187': 'PRIO3',  # PRIO S.A.
            '16292': 'PETR4',  # Petrobras
            '4170': 'VALE3',   # Vale
            '7617': 'ITUB4',   # Itaú
            '19348': 'BBDC4',  # Bradesco
            '3271': 'ABEV3',   # Ambev
            '16616': 'MGLU3',  # Magazine Luiza
            '5410': 'WEGE3',   # WEG
            '17973': 'RENT3',  # Localiza
            '4963': 'LREN3',   # Lojas Renner
            '20672': 'JBSS3',  # JBS
            '2151': 'RAIL3',   # Rumo
            '1856': 'UGPA3',   # Ultrapar
            '7140': 'USIM5',   # Usiminas
            '19429': 'CCRO3',  # CCR
            '20532': 'CSAN3',  # Cosan
            '1539': 'ELET3',   # Eletrobras
            '1164': 'CMIG4',   # Cemig
            '20362': 'GOAU4',  # Metalúrgica Gerdau
            '2211': 'CSNA3',   # Companhia Siderúrgica Nacional
            '1066': 'SUZB3',   # Suzano
            '15300': 'KLBN11', # Klabin
            '6610': 'EMBR3',   # Embraer
            '19736': 'CVCB3',  # CVC Brasil
            '23264': 'NTCO3',  # Natura
            '4677': 'RADL3',   # Raia Drogasil
            '4820': 'BRFS3',   # BRF
            '7207': 'MRFG3',   # Marfrig
            '18503': 'QUAL3',  # Qualicorp
            '20435': 'AZUL4',  # Azul
            '7491': 'GOLL4',   # Gol
            '21610': 'BEEF3',  # Minerva
            '24468': 'LWSA3',  # Locaweb
            '15543': 'TOTS3',  # Totvs
            '26609': 'PETZ3',  # Petz
            '18660': 'IFCM3',  # Infracommerce
            '20540': 'MEAL3',  # Meal
            '21261': 'SOMA3',  # Soma
            '2020': 'YDUQ3',   # Yduqs
            '21423': 'VVAR3',  # Vamos
            '17434': 'MULT3',  # Multiplan
            '21016': 'MDIA3'   # M.Dias Branco
        }
    
    def filter_companies_with_tickers(self) -> List[Dict]:
        """Filtra empresas mantendo apenas as com ticker ativo na B3"""
        logger.info("Iniciando filtro de empresas com ticker B3...")
        
        # Buscar todas as empresas do database
        companies = Company.query.all()
        logger.info(f"Total de empresas no database: {len(companies)}")
        
        # Buscar tickers ativos
        active_tickers = self.get_active_b3_tickers()
        ticker_mapping = self.get_company_ticker_mapping()
        
        filtered_companies = []
        
        for company in companies:
            cvm_code = str(company.cvm_code)
            
            # Verificar se empresa tem ticker mapeado
            if cvm_code in ticker_mapping:
                ticker = ticker_mapping[cvm_code]
                
                # Verificar se ticker está ativo na B3
                if ticker in active_tickers:
                    company_data = {
                        'id': company.id,
                        'cvm_code': company.cvm_code,
                        'company_name': company.company_name,
                        'trading_name': company.trade_name,
                        'ticker': ticker,
                        'cnpj': company.cnpj,
                        'industry_classification': company.industry_classification,
                        'is_active_b3': True
                    }
                    filtered_companies.append(company_data)
        
        logger.info(f"Empresas filtradas com ticker B3: {len(filtered_companies)}")
        return filtered_companies
    
    def update_companies_with_tickers(self):
        """Atualiza database mantendo apenas empresas com ticker B3"""
        filtered_companies = self.filter_companies_with_tickers()
        ticker_mapping = self.get_company_ticker_mapping()
        
        # Marcar empresas sem ticker como inativas
        inactive_count = 0
        for company in Company.query.all():
            cvm_code = str(company.cvm_code)
            if cvm_code not in ticker_mapping:
                # Opcionalmente marcar como inativa ao invés de deletar
                company.is_active = False
                inactive_count += 1
        
        # Adicionar campo ticker às empresas ativas
        for company_data in filtered_companies:
            company = Company.query.filter_by(cvm_code=company_data['cvm_code']).first()
            if company:
                company.ticker = company_data['ticker']
                company.is_active = True
        
        try:
            db.session.commit()
            logger.info(f"Database atualizado: {len(filtered_companies)} empresas ativas, {inactive_count} inativas")
            return filtered_companies
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao atualizar database: {str(e)}")
            return []

if __name__ == "__main__":
    filter_service = B3CompanyFilter()
    
    # Testar filtro
    filtered = filter_service.filter_companies_with_tickers()
    
    print(f"\n🎯 EMPRESAS FILTRADAS COM TICKER B3")
    print("=" * 60)
    
    for i, company in enumerate(filtered[:20], 1):  # Mostrar primeiras 20
        print(f"{i:2d}. {company['ticker']:6s} | {company['company_name'][:40]:40s} | CVM: {company['cvm_code']}")
    
    print(f"\nTotal: {len(filtered)} empresas com ticker ativo na B3")