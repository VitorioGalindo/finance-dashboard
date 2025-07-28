"""
Scraper para o sistema RAD da CVM - Portal de Consultas Externas
https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time
import re
from urllib.parse import urljoin, parse_qs, urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RADCVMScraper:
    """Scraper para o sistema RAD (Relatórios e Atos de Documentos) da CVM"""
    
    def __init__(self):
        self.base_url = "https://www.rad.cvm.gov.br/ENET/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Estado da sessão ASP.NET
        self.viewstate = None
        self.viewstate_generator = None
        self.event_validation = None
    
    def _get_initial_page(self) -> bool:
        """Carrega a página inicial e extrai os parâmetros de estado ASP.NET"""
        try:
            url = f"{self.base_url}frmConsultaExternaCVM.aspx"
            logger.info("Carregando página inicial do RAD CVM...")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrair parâmetros ASP.NET
            viewstate_input = soup.find('input', {'name': '__VIEWSTATE'})
            if viewstate_input:
                self.viewstate = viewstate_input.get('value')
            
            viewstate_gen_input = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
            if viewstate_gen_input:
                self.viewstate_generator = viewstate_gen_input.get('value')
            
            event_val_input = soup.find('input', {'name': '__EVENTVALIDATION'})
            if event_val_input:
                self.event_validation = event_val_input.get('value')
            
            logger.info("Página inicial carregada com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar página inicial: {str(e)}")
            return False
    
    def search_companies(self, 
                        company_name: str = "", 
                        participant_type: str = "TODOS",
                        sector: str = "TODOS",
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Busca empresas no sistema RAD"""
        try:
            if not self._get_initial_page():
                return []
            
            logger.info(f"Buscando empresas: '{company_name}' - Tipo: {participant_type} - Setor: {sector}")
            
            # Dados do formulário de busca
            search_data = {
                '__VIEWSTATE': self.viewstate,
                '__VIEWSTATEGENERATOR': self.viewstate_generator,
                '__EVENTVALIDATION': self.event_validation,
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                'ctl00$cphPage$txtEmpresa': company_name,
                'ctl00$cphPage$ddlTipoParticipante': participant_type,
                'ctl00$cphPage$ddlSetorAtividade': sector,
                'ctl00$cphPage$btnConsultar': 'Consultar'
            }
            
            # Realizar busca
            search_url = f"{self.base_url}frmConsultaExternaCVM.aspx"
            response = self.session.post(search_url, data=search_data, timeout=60)
            response.raise_for_status()
            
            # Parsear resultados
            companies = self._parse_company_search_results(response.content)
            
            logger.info(f"Encontradas {len(companies)} empresas")
            return companies[:limit]
            
        except Exception as e:
            logger.error(f"Erro na busca de empresas: {str(e)}")
            return []
    
    def _parse_company_search_results(self, html_content: bytes) -> List[Dict[str, Any]]:
        """Parseia os resultados da busca de empresas"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            companies = []
            
            # Procurar tabela de resultados
            results_table = soup.find('table', {'id': re.compile(r'.*gvEmpresa.*')})
            if not results_table:
                logger.warning("Tabela de resultados não encontrada")
                return companies
            
            # Processar linhas da tabela
            rows = results_table.find_all('tr')[1:]  # Pular cabeçalho
            
            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        company = {
                            'company_name': cells[0].get_text(strip=True),
                            'cvm_code': cells[1].get_text(strip=True),
                            'cnpj': cells[2].get_text(strip=True),
                            'sector': cells[3].get_text(strip=True),
                            'participant_type': cells[4].get_text(strip=True) if len(cells) > 4 else '',
                            'status': cells[5].get_text(strip=True) if len(cells) > 5 else '',
                            'extracted_at': datetime.now()
                        }
                        
                        # Link para documentos da empresa
                        link = cells[0].find('a')
                        if link and link.get('href'):
                            company['documents_url'] = urljoin(self.base_url, link.get('href'))
                        
                        companies.append(company)
                        
                except Exception as e:
                    logger.warning(f"Erro ao processar linha da tabela: {str(e)}")
                    continue
            
            return companies
            
        except Exception as e:
            logger.error(f"Erro ao parsear resultados: {str(e)}")
            return []
    
    def get_company_documents(self, cvm_code: str, 
                            document_category: str = "TODOS",
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Busca documentos de uma empresa específica"""
        try:
            logger.info(f"Buscando documentos da empresa CVM {cvm_code}")
            
            if not start_date:
                start_date = datetime.now() - timedelta(days=365)
            if not end_date:
                end_date = datetime.now()
            
            # Buscar a empresa primeiro
            companies = self.search_companies(company_name=cvm_code)
            target_company = None
            
            for company in companies:
                if company['cvm_code'] == cvm_code:
                    target_company = company
                    break
            
            if not target_company:
                logger.warning(f"Empresa CVM {cvm_code} não encontrada")
                return []
            
            # Se há URL específica para documentos, usar ela
            if 'documents_url' in target_company:
                return self._get_documents_from_url(target_company['documents_url'])
            
            # Caso contrário, fazer busca por documentos
            return self._search_company_documents(cvm_code, document_category, start_date, end_date)
            
        except Exception as e:
            logger.error(f"Erro ao buscar documentos da empresa {cvm_code}: {str(e)}")
            return []
    
    def _search_company_documents(self, cvm_code: str, 
                                 category: str,
                                 start_date: datetime,
                                 end_date: datetime) -> List[Dict[str, Any]]:
        """Busca documentos usando os filtros de data e categoria"""
        try:
            if not self._get_initial_page():
                return []
            
            # Configurar filtros de busca
            search_data = {
                '__VIEWSTATE': self.viewstate,
                '__VIEWSTATEGENERATOR': self.viewstate_generator,
                '__EVENTVALIDATION': self.event_validation,
                'ctl00$cphPage$txtEmpresa': cvm_code,
                'ctl00$cphPage$ddlCategoria': category,
                'ctl00$cphPage$txtDataInicio': start_date.strftime('%d/%m/%Y'),
                'ctl00$cphPage$txtDataFim': end_date.strftime('%d/%m/%Y'),
                'ctl00$cphPage$btnConsultar': 'Consultar'
            }
            
            search_url = f"{self.base_url}frmConsultaExternaCVM.aspx"
            response = self.session.post(search_url, data=search_data, timeout=60)
            response.raise_for_status()
            
            return self._parse_documents_results(response.content)
            
        except Exception as e:
            logger.error(f"Erro na busca de documentos: {str(e)}")
            return []
    
    def _parse_documents_results(self, html_content: bytes) -> List[Dict[str, Any]]:
        """Parseia resultados de documentos"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            documents = []
            
            # Procurar tabela de documentos
            docs_table = soup.find('table', {'id': re.compile(r'.*gvDocumento.*')})
            if not docs_table:
                return documents
            
            rows = docs_table.find_all('tr')[1:]  # Pular cabeçalho
            
            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) >= 6:
                        document = {
                            'company_name': cells[0].get_text(strip=True),
                            'document_type': cells[1].get_text(strip=True),
                            'document_category': cells[2].get_text(strip=True),
                            'delivery_date': cells[3].get_text(strip=True),
                            'reference_date': cells[4].get_text(strip=True),
                            'status': cells[5].get_text(strip=True),
                            'extracted_at': datetime.now()
                        }
                        
                        # Link para download/visualização
                        link = cells[1].find('a')
                        if link and link.get('href'):
                            document['download_url'] = urljoin(self.base_url, link.get('href'))
                        
                        documents.append(document)
                        
                except Exception as e:
                    logger.warning(f"Erro ao processar documento: {str(e)}")
                    continue
            
            return documents
            
        except Exception as e:
            logger.error(f"Erro ao parsear documentos: {str(e)}")
            return []
    
    def get_document_types_available(self) -> List[str]:
        """Lista tipos de documentos disponíveis no sistema"""
        try:
            if not self._get_initial_page():
                return []
            
            url = f"{self.base_url}frmConsultaExternaCVM.aspx"
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Procurar dropdown de categorias
            category_select = soup.find('select', {'name': re.compile(r'.*ddlCategoria.*')})
            if not category_select:
                return []
            
            options = category_select.find_all('option')
            document_types = [opt.get_text(strip=True) for opt in options if opt.get('value')]
            
            logger.info(f"Encontrados {len(document_types)} tipos de documentos")
            return document_types
            
        except Exception as e:
            logger.error(f"Erro ao listar tipos de documentos: {str(e)}")
            return []
    
    def get_sectors_available(self) -> List[str]:
        """Lista setores de atividade disponíveis"""
        try:
            if not self._get_initial_page():
                return []
            
            url = f"{self.base_url}frmConsultaExternaCVM.aspx"
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Procurar dropdown de setores
            sector_select = soup.find('select', {'name': re.compile(r'.*ddlSetorAtividade.*')})
            if not sector_select:
                return []
            
            options = sector_select.find_all('option')
            sectors = [opt.get_text(strip=True) for opt in options if opt.get('value')]
            
            logger.info(f"Encontrados {len(sectors)} setores")
            return sectors
            
        except Exception as e:
            logger.error(f"Erro ao listar setores: {str(e)}")
            return []
    
    def download_document(self, download_url: str, save_path: str = None) -> Optional[bytes]:
        """Download de um documento específico"""
        try:
            logger.info(f"Baixando documento: {download_url}")
            
            response = self.session.get(download_url, timeout=120)
            response.raise_for_status()
            
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Documento salvo em: {save_path}")
            
            return response.content
            
        except Exception as e:
            logger.error(f"Erro ao baixar documento: {str(e)}")
            return None
    
    def batch_extract_companies_data(self, sectors: List[str] = None, 
                                   limit_per_sector: int = 50) -> Dict[str, List[Dict]]:
        """Extração em lote de empresas por setor"""
        try:
            if not sectors:
                sectors = ["Bancos", "Energia Elétrica", "Petróleo e Gás", "Metalurgia e Siderurgia"]
            
            logger.info(f"Extraindo dados de {len(sectors)} setores")
            
            results = {}
            
            for sector in sectors:
                try:
                    logger.info(f"Processando setor: {sector}")
                    companies = self.search_companies(
                        company_name="",
                        sector=sector,
                        limit=limit_per_sector
                    )
                    
                    results[sector] = companies
                    logger.info(f"Setor {sector}: {len(companies)} empresas")
                    
                    # Delay entre setores
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Erro ao processar setor {sector}: {str(e)}")
                    continue
            
            total_companies = sum(len(companies) for companies in results.values())
            logger.info(f"Extração concluída: {total_companies} empresas em {len(results)} setores")
            
            return results
            
        except Exception as e:
            logger.error(f"Erro na extração em lote: {str(e)}")
            return {}

# Função utilitária
def get_companies_by_sector(sector: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Função helper para buscar empresas por setor"""
    scraper = RADCVMScraper()
    return scraper.search_companies(sector=sector, limit=limit)

def get_company_info(cvm_code: str) -> Dict[str, Any]:
    """Função helper para obter informações completas de uma empresa"""
    scraper = RADCVMScraper()
    
    # Buscar dados básicos da empresa
    companies = scraper.search_companies(company_name=cvm_code)
    company_info = None
    
    for company in companies:
        if company['cvm_code'] == cvm_code:
            company_info = company
            break
    
    if not company_info:
        return {}
    
    # Buscar documentos da empresa
    documents = scraper.get_company_documents(cvm_code)
    company_info['documents'] = documents
    company_info['total_documents'] = len(documents)
    
    return company_info

if __name__ == "__main__":
    # Teste do scraper
    scraper = RADCVMScraper()
    
    # Testar busca de empresas
    companies = scraper.search_companies(company_name="PETROBRAS", limit=5)
    print(f"Empresas encontradas: {len(companies)}")
    
    for company in companies:
        print(f"- {company['company_name']} (CVM: {company['cvm_code']})")