#!/usr/bin/env python3
"""
Scraper Histórico RAD CVM
Busca todos os documentos desde 2010 de empresas brasileiras
"""

import time
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import pandas as pd
import re
from urllib.parse import urljoin, parse_qs, urlparse
import json
from database import DatabaseManager

class HistoricalRADCVMScraper:
    """Scraper histórico para o portal RAD CVM"""
    
    def __init__(self):
        self.base_url = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx"
        self.session = requests.Session()
        self.logger = self._setup_logger()
        self.db = DatabaseManager()
        
        # Headers para simular navegador
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def _setup_logger(self) -> logging.Logger:
        """Configura o logger"""
        logger = logging.getLogger('HistoricalRADCVMScraper')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def get_form_data(self) -> Dict:
        """Obtém dados do formulário ASP.NET"""
        try:
            response = self.session.get(self.base_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            form_data = {}
            
            # Extrai campos hidden do ASP.NET
            hidden_inputs = soup.find_all('input', {'type': 'hidden'})
            for input_field in hidden_inputs:
                name = input_field.get('name')
                value = input_field.get('value', '')
                if name:
                    form_data[name] = value
            
            # Adiciona campos padrão
            form_data.update({
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                'ctl00$ContentPlaceHolder1$btnConsultar': 'Consultar'
            })
            
            self.logger.info(f"Extraídos {len(form_data)} campos do formulário")
            return form_data
            
        except Exception as e:
            self.logger.error(f"Erro ao obter dados do formulário: {e}")
            return {}
    
    def search_documents_by_period(self, start_date: str, end_date: str, 
                                  max_pages: int = 10) -> List[Dict]:
        """Busca documentos por período específico"""
        try:
            self.logger.info(f"Buscando documentos de {start_date} a {end_date}")
            
            # Obtém dados do formulário
            form_data = self.get_form_data()
            if not form_data:
                return []
            
            # Configura filtros de data
            form_data.update({
                'ctl00$ContentPlaceHolder1$chkPeriodo': 'on',  # Marca checkbox "No período"
                'ctl00$ContentPlaceHolder1$txtDataDe': start_date,
                'ctl00$ContentPlaceHolder1$txtDataAte': end_date,
                'ctl00$ContentPlaceHolder1$ddlRegistrosPorPagina': '100'  # Máximo por página
            })
            
            all_documents = []
            page = 1
            
            while page <= max_pages:
                self.logger.info(f"Processando página {page}")
                
                # Faz a requisição
                response = self.session.post(self.base_url, data=form_data)
                
                if response.status_code != 200:
                    self.logger.error(f"Erro HTTP {response.status_code} na página {page}")
                    break
                
                # Extrai documentos da página
                documents = self._extract_documents_from_html(response.content)
                
                if not documents:
                    self.logger.info(f"Nenhum documento encontrado na página {page}")
                    break
                
                # Filtra apenas empresas brasileiras (código CVM < 05000)
                brazilian_docs = []
                for doc in documents:
                    try:
                        codigo_parts = doc['codigo_cvm'].split('-')
                        if codigo_parts and int(codigo_parts[0]) < 5000:
                            brazilian_docs.append(doc)
                    except:
                        continue
                
                all_documents.extend(brazilian_docs)
                self.logger.info(f"Página {page}: {len(brazilian_docs)} documentos brasileiros")
                
                # Verifica se há próxima página
                if not self._has_next_page(response.content):
                    break
                
                # Prepara para próxima página
                form_data = self._get_next_page_form_data(response.content, form_data)
                page += 1
                
                # Delay entre requisições
                time.sleep(2)
            
            self.logger.info(f"Total de documentos coletados: {len(all_documents)}")
            return all_documents
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar documentos por período: {e}")
            return []
    
    def _extract_documents_from_html(self, html_content: bytes) -> List[Dict]:
        """Extrai documentos do HTML da resposta"""
        documents = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Procura pela tabela de resultados
            table = soup.find('table', {'id': re.compile(r'.*gvDocumentos.*')})
            if not table:
                # Tenta encontrar qualquer tabela com dados
                tables = soup.find_all('table')
                for t in tables:
                    if len(t.find_all('tr')) > 5:  # Tabela com pelo menos 5 linhas
                        table = t
                        break
            
            if not table:
                return documents
            
            rows = table.find_all('tr')
            
            # Identifica cabeçalho
            header_row = None
            for i, row in enumerate(rows):
                cells = row.find_all(['th', 'td'])
                if cells and any('código' in cell.get_text().lower() for cell in cells):
                    header_row = i
                    break
            
            if header_row is None:
                header_row = 0
            
            # Processa linhas de dados
            for row in rows[header_row + 1:]:
                cells = row.find_all('td')
                if len(cells) >= 8:
                    try:
                        document = {
                            'codigo_cvm': cells[0].get_text().strip(),
                            'empresa': cells[1].get_text().strip(),
                            'categoria': cells[2].get_text().strip(),
                            'tipo': cells[3].get_text().strip(),
                            'especie': cells[4].get_text().strip(),
                            'data_referencia': cells[5].get_text().strip(),
                            'data_entrega': cells[6].get_text().strip(),
                            'status': cells[7].get_text().strip(),
                            'versao': cells[8].get_text().strip() if len(cells) > 8 else '',
                            'modalidade': cells[9].get_text().strip() if len(cells) > 9 else '',
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        # Extrai URL de download se disponível
                        download_link = cells[-1].find('a', title=re.compile(r'.*download.*', re.I))
                        if download_link:
                            document['download_url'] = download_link.get('href', '')
                        
                        # Só adiciona se tiver dados válidos
                        if document['empresa'] and document['categoria']:
                            documents.append(document)
                            
                    except Exception as e:
                        self.logger.debug(f"Erro ao processar linha: {e}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"Erro ao extrair documentos do HTML: {e}")
            
        return documents
    
    def _has_next_page(self, html_content: bytes) -> bool:
        """Verifica se há próxima página"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Procura por links de paginação
            next_links = soup.find_all('a', string=re.compile(r'próxima|next|>'))
            return len(next_links) > 0
            
        except:
            return False
    
    def _get_next_page_form_data(self, html_content: bytes, current_form_data: Dict) -> Dict:
        """Obtém dados do formulário para próxima página"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Atualiza campos hidden
            hidden_inputs = soup.find_all('input', {'type': 'hidden'})
            for input_field in hidden_inputs:
                name = input_field.get('name')
                value = input_field.get('value', '')
                if name:
                    current_form_data[name] = value
            
            # Procura por link da próxima página
            next_link = soup.find('a', string=re.compile(r'próxima|next|>'))
            if next_link:
                href = next_link.get('href', '')
                if 'doPostBack' in href:
                    # Extrai parâmetros do postback
                    match = re.search(r"doPostBack\('([^']+)','([^']*)'\)", href)
                    if match:
                        current_form_data['__EVENTTARGET'] = match.group(1)
                        current_form_data['__EVENTARGUMENT'] = match.group(2)
            
            return current_form_data
            
        except Exception as e:
            self.logger.error(f"Erro ao obter dados da próxima página: {e}")
            return current_form_data
    
    def search_cvm44_documents_historical(self, start_year: int = 2010) -> List[Dict]:
        """Busca documentos CVM 44 históricos"""
        try:
            self.logger.info(f"Buscando documentos CVM 44 desde {start_year}")
            
            all_documents = []
            current_year = datetime.now().year
            
            for year in range(start_year, current_year + 1):
                self.logger.info(f"Processando ano {year}")
                
                # Busca por trimestres para evitar timeout
                for quarter in range(1, 5):
                    start_month = (quarter - 1) * 3 + 1
                    end_month = quarter * 3
                    
                    start_date = f"01/{start_month:02d}/{year}"
                    if end_month == 12:
                        end_date = f"31/12/{year}"
                    else:
                        end_date = f"30/{end_month:02d}/{year}"
                    
                    self.logger.info(f"Buscando Q{quarter}/{year}: {start_date} a {end_date}")
                    
                    # Busca documentos do período
                    documents = self.search_documents_by_period(start_date, end_date)
                    
                    # Filtra apenas CVM 44
                    cvm44_docs = [
                        doc for doc in documents 
                        if 'valores mobiliários' in doc['categoria'].lower() or
                           'cvm 44' in doc['tipo'].lower() or
                           'insider' in doc['categoria'].lower()
                    ]
                    
                    all_documents.extend(cvm44_docs)
                    self.logger.info(f"Q{quarter}/{year}: {len(cvm44_docs)} documentos CVM 44")
                    
                    # Delay entre trimestres
                    time.sleep(3)
                
                # Delay entre anos
                time.sleep(5)
            
            self.logger.info(f"Total de documentos CVM 44 históricos: {len(all_documents)}")
            return all_documents
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar documentos CVM 44 históricos: {e}")
            return []
    
    def save_documents_to_database(self, documents: List[Dict]) -> int:
        """Salva documentos no banco de dados"""
        try:
            if not self.db.connect():
                self.logger.error("Erro ao conectar ao banco de dados")
                return 0
            
            saved_count = 0
            
            for doc in documents:
                try:
                    # Converte datas
                    doc_data = doc.copy()
                    
                    # Processa data de entrega
                    if doc_data.get('data_entrega'):
                        try:
                            # Formato: "28/07/2025 16:01"
                            date_str = doc_data['data_entrega'].strip()
                            if ' ' in date_str:
                                date_part, time_part = date_str.split(' ', 1)
                                doc_data['data_entrega'] = datetime.strptime(
                                    f"{date_part} {time_part}", "%d/%m/%Y %H:%M"
                                ).isoformat()
                            else:
                                doc_data['data_entrega'] = datetime.strptime(
                                    date_part, "%d/%m/%Y"
                                ).isoformat()
                        except:
                            doc_data['data_entrega'] = None
                    
                    # Processa data de referência
                    if doc_data.get('data_referencia'):
                        try:
                            date_str = doc_data['data_referencia'].strip()
                            if '/' in date_str and len(date_str) >= 8:
                                doc_data['data_referencia'] = datetime.strptime(
                                    date_str, "%d/%m/%Y"
                                ).date().isoformat()
                        except:
                            doc_data['data_referencia'] = None
                    
                    # Processa versão
                    try:
                        doc_data['versao'] = int(doc_data.get('versao', 1))
                    except:
                        doc_data['versao'] = 1
                    
                    # Salva empresa primeiro
                    empresa_data = {
                        'codigo_cvm': doc_data['codigo_cvm'],
                        'nome': doc_data['empresa'],
                        'setor': '',
                        'situacao': 'Ativo'
                    }
                    self.db.insert_empresa(empresa_data)
                    
                    # Salva documento
                    documento_id = self.db.insert_documento(doc_data)
                    if documento_id:
                        saved_count += 1
                        
                except Exception as e:
                    self.logger.error(f"Erro ao salvar documento: {e}")
                    continue
            
            self.db.disconnect()
            self.logger.info(f"Salvos {saved_count} documentos no banco de dados")
            return saved_count
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar documentos no banco: {e}")
            return 0
    
    def run_historical_collection(self, start_year: int = 2010):
        """Executa coleta histórica completa"""
        try:
            self.logger.info(f"Iniciando coleta histórica desde {start_year}")
            
            # Busca documentos CVM 44 históricos
            documents = self.search_cvm44_documents_historical(start_year)
            
            if documents:
                # Salva no banco de dados
                saved_count = self.save_documents_to_database(documents)
                
                # Salva backup em JSON
                backup_file = f"/home/ubuntu/rad_cvm_superscraper/historical_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(documents, f, ensure_ascii=False, indent=2)
                
                self.logger.info(f"Coleta histórica concluída: {len(documents)} documentos coletados, {saved_count} salvos")
                return {
                    'success': True,
                    'total_documents': len(documents),
                    'saved_documents': saved_count,
                    'backup_file': backup_file
                }
            else:
                self.logger.warning("Nenhum documento histórico encontrado")
                return {
                    'success': False,
                    'message': 'Nenhum documento encontrado'
                }
                
        except Exception as e:
            self.logger.error(f"Erro na coleta histórica: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Script de teste
if __name__ == "__main__":
    print("=== Scraper Histórico RAD CVM ===")
    
    # Configura logging
    logging.basicConfig(level=logging.INFO)
    
    scraper = HistoricalRADCVMScraper()
    
    try:
        # Teste com período pequeno primeiro
        print("\n1. Testando busca por período (últimos 30 dias)...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        documents = scraper.search_documents_by_period(
            start_date.strftime("%d/%m/%Y"),
            end_date.strftime("%d/%m/%Y"),
            max_pages=2
        )
        
        print(f"   Encontrados {len(documents)} documentos")
        
        if documents:
            print("\n   Primeiros 3 documentos:")
            for i, doc in enumerate(documents[:3]):
                print(f"   {i+1}. {doc['empresa']} - {doc['categoria']} ({doc['data_entrega']})")
        
        # Teste de salvamento no banco
        if documents:
            print("\n2. Testando salvamento no banco...")
            saved = scraper.save_documents_to_database(documents[:5])  # Salva apenas 5 para teste
            print(f"   Salvos {saved} documentos no banco")
        
        print("\n✓ Teste concluído!")
        
    except Exception as e:
        print(f"\n✗ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

