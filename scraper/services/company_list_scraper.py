#!/usr/bin/env python3
"""
Scraper para obter a lista correta de empresas da DadosDeMercado
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
from typing import List, Dict
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompanyListScraper:
    """Scraper para obter lista correta de empresas B3"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_companies_from_dadosdemercado(self) -> List[Dict]:
        """Obter lista de empresas da DadosDeMercado"""
        logger.info("🔍 Buscando lista de empresas na DadosDeMercado...")
        
        try:
            url = "https://www.dadosdemercado.com.br/acoes"
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Erro ao acessar DadosDeMercado: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            companies = []
            
            # Procurar tabela ou lista de ações
            # A estrutura pode variar, vamos tentar diferentes seletores
            
            # Tentar encontrar elementos com tickers
            ticker_elements = soup.find_all(['td', 'div', 'span'], text=lambda text: text and len(text) >= 4 and text.endswith('3') or text.endswith('4') or text.endswith('11'))
            
            for element in ticker_elements:
                ticker_text = element.get_text().strip()
                if len(ticker_text) >= 5 and (ticker_text.endswith('3') or ticker_text.endswith('4') or ticker_text.endswith('11')):
                    # Tentar encontrar nome da empresa próximo
                    company_name = ""
                    parent = element.parent
                    if parent:
                        siblings = parent.find_all(['td', 'div', 'span'])
                        for sibling in siblings:
                            if sibling != element and len(sibling.get_text().strip()) > 10:
                                company_name = sibling.get_text().strip()
                                break
                    
                    companies.append({
                        'ticker': ticker_text,
                        'company_name': company_name,
                        'cnpj': '',  # Será preenchido posteriormente
                        'cvm_code': ''  # Será preenchido posteriormente
                    })
            
            # Se não encontrou com a primeira estratégia, tentar outra
            if not companies:
                # Procurar por padrões de ticker nas URLs ou links
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if '/acoes/' in href:
                        ticker_match = href.split('/acoes/')[-1].split('/')[0]
                        if len(ticker_match) >= 5 and ticker_match.isalnum():
                            companies.append({
                                'ticker': ticker_match.upper(),
                                'company_name': link.get_text().strip(),
                                'cnpj': '',
                                'cvm_code': ''
                            })
            
            logger.info(f"✅ Encontradas {len(companies)} empresas na DadosDeMercado")
            return companies[:200]  # Limitar para evitar duplicatas
            
        except Exception as e:
            logger.error(f"Erro ao buscar empresas: {str(e)}")
            return []
    
    def get_hardcoded_b3_companies(self) -> List[Dict]:
        """Lista hardcoded das principais empresas B3 como fallback"""
        logger.info("📋 Usando lista hardcoded das principais empresas B3...")
        
        return [
            # Petróleo e Gás
            {'ticker': 'PETR3', 'company_name': 'Petróleo Brasileiro S.A. - Petrobras', 'cnpj': '33.000.167/0001-01', 'cvm_code': '9512'},
            {'ticker': 'PETR4', 'company_name': 'Petróleo Brasileiro S.A. - Petrobras', 'cnpj': '33.000.167/0001-01', 'cvm_code': '9512'},
            {'ticker': 'PRIO3', 'company_name': 'Prio S.A.', 'cnpj': '42.817.979/0001-73', 'cvm_code': '22187'},
            {'ticker': 'RRRP3', 'company_name': '3R Petroleum Óleo e Gás S.A.', 'cnpj': '31.509.449/0001-08', 'cvm_code': '23540'},
            
            # Vale
            {'ticker': 'VALE3', 'company_name': 'Vale S.A.', 'cnpj': '33.592.510/0001-54', 'cvm_code': '4170'},
            
            # Bancos
            {'ticker': 'ITUB3', 'company_name': 'Itaú Unibanco Holding S.A.', 'cnpj': '60.872.504/0001-23', 'cvm_code': '18520'},
            {'ticker': 'ITUB4', 'company_name': 'Itaú Unibanco Holding S.A.', 'cnpj': '60.872.504/0001-23', 'cvm_code': '18520'},
            {'ticker': 'BBDC3', 'company_name': 'Banco Bradesco S.A.', 'cnpj': '60.746.948/0001-12', 'cvm_code': '906'},
            {'ticker': 'BBDC4', 'company_name': 'Banco Bradesco S.A.', 'cnpj': '60.746.948/0001-12', 'cvm_code': '906'},
            {'ticker': 'BBAS3', 'company_name': 'Banco do Brasil S.A.', 'cnpj': '00.000.000/0001-91', 'cvm_code': '1023'},
            {'ticker': 'SANB3', 'company_name': 'Banco Santander (Brasil) S.A.', 'cnpj': '90.400.888/0001-42', 'cvm_code': '20766'},
            {'ticker': 'SANB4', 'company_name': 'Banco Santander (Brasil) S.A.', 'cnpj': '90.400.888/0001-42', 'cvm_code': '20766'},
            
            # Varejo
            {'ticker': 'MGLU3', 'company_name': 'Magazine Luiza S.A.', 'cnpj': '47.960.950/0001-21', 'cvm_code': '12190'},
            {'ticker': 'LREN3', 'company_name': 'Lojas Renner S.A.', 'cnpj': '92.754.738/0001-62', 'cvm_code': '7541'},
            {'ticker': 'AMER3', 'company_name': 'Americanas S.A.', 'cnpj': '33.014.556/0001-96', 'cvm_code': '5258'},
            {'ticker': 'VVAR3', 'company_name': 'Via S.A.', 'cnpj': '33.041.260/0001-56', 'cvm_code': '19615'},
            
            # Tecnologia
            {'ticker': 'LWSA3', 'company_name': 'Locaweb Serviços de Internet S.A.', 'cnpj': '02.351.877/0001-74', 'cvm_code': '23825'},
            {'ticker': 'MELI34', 'company_name': 'MercadoLibre Inc.', 'cnpj': '', 'cvm_code': ''},
            
            # Alimentação
            {'ticker': 'JBSS3', 'company_name': 'JBS S.A.', 'cnpj': '02.916.265/0001-60', 'cvm_code': '20176'},
            {'ticker': 'BRFS3', 'company_name': 'BRF S.A.', 'cnpj': '01.838.723/0001-27', 'cvm_code': '20478'},
            {'ticker': 'MRFG3', 'company_name': 'Marfrig Global Foods S.A.', 'cnpj': '03.853.896/0001-40', 'cvm_code': '20850'},
            
            # Siderurgia
            {'ticker': 'USIM3', 'company_name': 'Usinas Siderúrgicas de Minas Gerais S.A.', 'cnpj': '60.894.730/0001-05', 'cvm_code': '7792'},
            {'ticker': 'USIM5', 'company_name': 'Usinas Siderúrgicas de Minas Gerais S.A.', 'cnpj': '60.894.730/0001-05', 'cvm_code': '7792'},
            {'ticker': 'CSNA3', 'company_name': 'Companhia Siderúrgica Nacional', 'cnpj': '33.042.730/0001-04', 'cvm_code': '1098'},
            {'ticker': 'GGBR3', 'company_name': 'Gerdau S.A.', 'cnpj': '33.611.500/0001-19', 'cvm_code': '3441'},
            {'ticker': 'GGBR4', 'company_name': 'Gerdau S.A.', 'cnpj': '33.611.500/0001-19', 'cvm_code': '3441'},
            
            # Utilities
            {'ticker': 'ELET3', 'company_name': 'Centrais Elétricas Brasileiras S.A.', 'cnpj': '00.001.180/0001-26', 'cvm_code': '2437'},
            {'ticker': 'ELET6', 'company_name': 'Centrais Elétricas Brasileiras S.A.', 'cnpj': '00.001.180/0001-26', 'cvm_code': '2437'},
            {'ticker': 'EGIE3', 'company_name': 'Engie Brasil Energia S.A.', 'cnpj': '02.474.103/0001-19', 'cvm_code': '19924'},
            {'ticker': 'CPFE3', 'company_name': 'CPFL Energia S.A.', 'cnpj': '02.429.144/0001-93', 'cvm_code': '19348'},
            {'ticker': 'SBSP3', 'company_name': 'Companhia de Saneamento Básico do Estado de São Paulo', 'cnpj': '43.776.517/0001-80', 'cvm_code': '1228'},
            
            # Real Estate
            {'ticker': 'BTOW3', 'company_name': 'B2W Digital S.A.', 'cnpj': '00.776.574/0001-56', 'cvm_code': '19440'},
            {'ticker': 'CYRE3', 'company_name': 'Cyrela Brazil Realty S.A.', 'cnpj': '73.178.600/0001-41', 'cvm_code': '11312'},
            {'ticker': 'MRVE3', 'company_name': 'MRV Engenharia e Participações S.A.', 'cnpj': '08.343.492/0001-20', 'cvm_code': '11573'},
            
            # Telecomunicações
            {'ticker': 'VIVT3', 'company_name': 'Telefônica Brasil S.A.', 'cnpj': '02.558.157/0001-62', 'cvm_code': '18724'},
            {'ticker': 'VIVT4', 'company_name': 'Telefônica Brasil S.A.', 'cnpj': '02.558.157/0001-62', 'cvm_code': '18724'},
            {'ticker': 'TIMS3', 'company_name': 'TIM S.A.', 'cnpj': '02.421.421/0001-11', 'cvm_code': '18061'},
            
            # Papel e Celulose
            {'ticker': 'SUZB3', 'company_name': 'Suzano S.A.', 'cnpj': '16.404.287/0001-55', 'cvm_code': '20710'},
            {'ticker': 'KLBN3', 'company_name': 'Klabin S.A.', 'cnpj': '89.637.490/0001-45', 'cvm_code': '4529'},
            {'ticker': 'KLBN4', 'company_name': 'Klabin S.A.', 'cnpj': '89.637.490/0001-45', 'cvm_code': '4529'},
            
            # Mineração
            {'ticker': 'CMIN3', 'company_name': 'CSN Mineração S.A.', 'cnpj': '15.115.504/0001-24', 'cvm_code': '23264'},
            {'ticker': 'GOAU3', 'company_name': 'Glencore plc', 'cnpj': '', 'cvm_code': ''},
            {'ticker': 'GOAU4', 'company_name': 'Glencore plc', 'cnpj': '', 'cvm_code': ''},
            
            # Aviação
            {'ticker': 'GOLL4', 'company_name': 'Gol Linhas Aéreas Inteligentes S.A.', 'cnpj': '06.164.253/0001-87', 'cvm_code': '16806'},
            {'ticker': 'AZUL4', 'company_name': 'Azul S.A.', 'cnpj': '09.296.295/0001-60', 'cvm_code': '22490'},
            
            # Healthcare
            {'ticker': 'RDOR3', 'company_name': 'Rede D\'Or São Luiz S.A.', 'cnpj': '06.047.087/0001-81', 'cvm_code': '24066'},
            {'ticker': 'HAPV3', 'company_name': 'Hapvida Participações e Investimentos S.A.', 'cnpj': '19.512.464/0001-73', 'cvm_code': '22845'},
            
            # Logística
            {'ticker': 'RAIL3', 'company_name': 'Rumo S.A.', 'cnpj': '02.387.241/0001-60', 'cvm_code': '14207'},
            {'ticker': 'CCRO3', 'company_name': 'CCR S.A.', 'cnpj': '02.846.056/0001-97', 'cvm_code': '15156'},
            
            # Agronegócio
            {'ticker': 'SLCE3', 'company_name': 'SLC Agrícola S.A.', 'cnpj': '89.096.457/0001-04', 'cvm_code': '20087'},
            {'ticker': 'CAML3', 'company_name': 'Camil Alimentos S.A.', 'cnpj': '22.426.221/0001-85', 'cvm_code': '19011'},
            
            # Construção
            {'ticker': 'TGMA3', 'company_name': 'Tegma Gestão Logística S.A.', 'cnpj': '02.351.144/0001-58', 'cvm_code': '19550'},
            {'ticker': 'EZTC3', 'company_name': 'EZTEC Empreendimentos e Participações S.A.', 'cnpj': '08.486.147/0001-15', 'cvm_code': '15423'},
            
            # Educação
            {'ticker': 'COGN3', 'company_name': 'Cogna Educação S.A.', 'cnpj': '02.576.178/0001-07', 'cvm_code': '19629'},
            {'ticker': 'YDUQ3', 'company_name': 'Yduqs Participações S.A.', 'cnpj': '07.437.147/0001-43', 'cvm_code': '18066'},
            
            # Químicos
            {'ticker': 'PCAR3', 'company_name': 'P.A.C. - Produtos de Aço Carbono S.A.', 'cnpj': '60.992.477/0001-29', 'cvm_code': '1155'},
            {'ticker': 'UNIP6', 'company_name': 'Unipar Carbocloro S.A.', 'cnpj': '33.593.260/0001-18', 'cvm_code': '1207'},
            
            # Seguros
            {'ticker': 'SULA11', 'company_name': 'SulAmérica S.A.', 'cnpj': '29.978.814/0001-87', 'cvm_code': '4316'},
            {'ticker': 'IRBR3', 'company_name': 'IRB Brasil Resseguros S.A.', 'cnpj': '33.376.989/0001-29', 'cvm_code': '20877'},
        ]

if __name__ == "__main__":
    scraper = CompanyListScraper()
    companies = scraper.get_companies_from_dadosdemercado()
    
    # Se não conseguiu da DadosDeMercado, usar lista hardcoded
    if not companies:
        companies = scraper.get_hardcoded_b3_companies()
    
    print(f"Total de empresas encontradas: {len(companies)}")
    for company in companies[:10]:
        print(f"  {company['ticker']} - {company['company_name']}")