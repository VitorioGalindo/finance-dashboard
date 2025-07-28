#!/usr/bin/env python3
"""
Scraper Real RAD CVM
Versão corrigida que funciona com dados reais do portal
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

class RealRADCVMScraper:
    """Scraper real para o portal RAD CVM"""
    
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
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx'
        })
        
    def _setup_logger(self) -> logging.Logger:
        """Configura o logger"""
        logger = logging.getLogger('RealRADCVMScraper')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def get_initial_page(self) -> Dict:
        """Obtém página inicial e extrai dados do formulário"""
        try:
            self.logger.info("Carregando página inicial do RAD CVM")
            response = self.session.get(self.base_url)
            
            if response.status_code != 200:
                self.logger.error(f"Erro ao carregar página: {response.status_code}")
                return {}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrai campos hidden do ASP.NET
            form_data = {}
            hidden_inputs = soup.find_all('input', {'type': 'hidden'})
            
            for input_field in hidden_inputs:
                name = input_field.get('name')
                value = input_field.get('value', '')
                if name:
                    form_data[name] = value
            
            self.logger.info(f"Extraídos {len(form_data)} campos hidden")
            return form_data
            
        except Exception as e:
            self.logger.error(f"Erro ao obter página inicial: {e}")
            return {}
    
    def search_documents_by_period(self, start_date: str, end_date: str) -> List[Dict]:
        """Busca documentos por período específico"""
        try:
            self.logger.info(f"Buscando documentos de {start_date} a {end_date}")
            
            # Obtém dados iniciais do formulário
            form_data = self.get_initial_page()
            if not form_data:
                return []
            
            # Configura parâmetros da busca
            search_params = {
                # Campos hidden obrigatórios do ASP.NET
                '__VIEWSTATE': form_data.get('__VIEWSTATE', ''),
                '__VIEWSTATEGENERATOR': form_data.get('__VIEWSTATEGENERATOR', ''),
                '__EVENTVALIDATION': form_data.get('__EVENTVALIDATION', ''),
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                
                # Filtros de busca
                'ctl00$ContentPlaceHolder1$txtEmpresa': '',  # Todas as empresas
                'ctl00$ContentPlaceHolder1$ddlTipoParticipante': '-1',  # Todos
                'ctl00$ContentPlaceHolder1$ddlSetorAtividade': '-1',  # Todos
                'ctl00$ContentPlaceHolder1$ddlSituacaoRegistroCVM': '-1',  # Todas
                'ctl00$ContentPlaceHolder1$ddlCategoriaRegistroCVM': '-1',  # Todas
                'ctl00$ContentPlaceHolder1$ddlSituacaoOperacional': '-1',  # Todas
                
                # Filtros de data - marcar "No período"
                'ctl00$ContentPlaceHolder1$rblDataEntrega': '3',  # 3 = "No período"
                'ctl00$ContentPlaceHolder1$txtDataDe': start_date,
                'ctl00$ContentPlaceHolder1$txtDataAte': end_date,
                'ctl00$ContentPlaceHolder1$txtHoraDe': '',
                'ctl00$ContentPlaceHolder1$txtHoraAte': '',
                
                # Outros filtros
                'ctl00$ContentPlaceHolder1$txtDataReferencia': '',
                'ctl00$ContentPlaceHolder1$ddlStatus': '-1',  # Todos
                'ctl00$ContentPlaceHolder1$ddlTipoEntrega': '-1',  # Todos
                'ctl00$ContentPlaceHolder1$ddlCategoria': '-1',  # Todas
                'ctl00$ContentPlaceHolder1$ddlTipo': '-1',  # Todos
                'ctl00$ContentPlaceHolder1$ddlEspecie': '-1',  # Todos
                'ctl00$ContentPlaceHolder1$txtPalavraChave': '',
                
                # Configurações de exibição
                'ctl00$ContentPlaceHolder1$ddlRegistrosPorPagina': '100',  # Máximo por página
                
                # Botão de consulta
                'ctl00$ContentPlaceHolder1$btnConsultar': 'Consultar'
            }
            
            # Adiciona outros campos hidden que possam existir
            for key, value in form_data.items():
                if key not in search_params and key.startswith('ctl00'):
                    search_params[key] = value
            
            self.logger.info("Executando busca...")
            
            # Faz a requisição POST
            response = self.session.post(
                self.base_url,
                data=search_params,
                timeout=60
            )
            
            if response.status_code != 200:
                self.logger.error(f"Erro na busca: HTTP {response.status_code}")
                return []
            
            # Extrai documentos da resposta
            documents = self._extract_documents_from_response(response.content)
            
            # Filtra apenas empresas brasileiras (código CVM < 05000)
            brazilian_docs = []
            for doc in documents:
                try:
                    codigo_parts = doc['codigo_cvm'].replace('-', '').split()
                    if codigo_parts:
                        codigo_num = int(codigo_parts[0])
                        if codigo_num < 5000:  # Empresas brasileiras
                            brazilian_docs.append(doc)
                except:
                    continue
            
            self.logger.info(f"Encontrados {len(documents)} documentos, {len(brazilian_docs)} brasileiros")
            return brazilian_docs
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar documentos: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_documents_from_response(self, html_content: bytes) -> List[Dict]:
        """Extrai documentos do HTML da resposta"""
        documents = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Procura pela tabela de resultados
            table = soup.find('table', {'id': re.compile(r'.*gvDocumentos.*')})
            if not table:
                # Procura por qualquer tabela com dados
                tables = soup.find_all('table')
                for t in tables:
                    rows = t.find_all('tr')
                    if len(rows) > 3:  # Tabela com dados
                        # Verifica se tem colunas típicas de documentos
                        header_text = ' '.join([cell.get_text() for cell in rows[0].find_all(['th', 'td'])])
                        if any(word in header_text.lower() for word in ['código', 'empresa', 'categoria', 'data']):
                            table = t
                            break
            
            if not table:
                self.logger.warning("Tabela de documentos não encontrada")
                return documents
            
            rows = table.find_all('tr')
            
            # Processa linhas de dados (pula cabeçalho)
            for i, row in enumerate(rows[1:], 1):
                cells = row.find_all('td')
                if len(cells) >= 7:  # Mínimo de colunas esperadas
                    try:
                        # Extrai dados das células
                        codigo_cvm = cells[0].get_text().strip()
                        empresa = cells[1].get_text().strip()
                        categoria = cells[2].get_text().strip()
                        tipo = cells[3].get_text().strip() if len(cells) > 3 else ''
                        especie = cells[4].get_text().strip() if len(cells) > 4 else ''
                        data_referencia = cells[5].get_text().strip() if len(cells) > 5 else ''
                        data_entrega = cells[6].get_text().strip() if len(cells) > 6 else ''
                        status = cells[7].get_text().strip() if len(cells) > 7 else ''
                        versao = cells[8].get_text().strip() if len(cells) > 8 else '1'
                        modalidade = cells[9].get_text().strip() if len(cells) > 9 else ''
                        
                        # Procura por links de download
                        download_url = ''
                        download_links = row.find_all('a', title=re.compile(r'download', re.I))
                        if download_links:
                            download_url = download_links[0].get('href', '')
                        
                        # Extrai assunto se disponível
                        assunto = ''
                        assunto_cell = row.find('td', string=re.compile(r'Assunto\\(s\\):'))
                        if assunto_cell:
                            assunto = assunto_cell.get_text().replace('Assunto(s):', '').strip()
                        
                        document = {
                            'codigo_cvm': codigo_cvm,
                            'empresa': empresa,
                            'categoria': categoria,
                            'tipo': tipo,
                            'especie': especie,
                            'data_referencia': data_referencia,
                            'data_entrega': data_entrega,
                            'status': status,
                            'versao': versao,
                            'modalidade': modalidade,
                            'download_url': download_url,
                            'assunto': assunto,
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        # Só adiciona se tiver dados válidos
                        if empresa and categoria:
                            documents.append(document)
                            
                    except Exception as e:
                        self.logger.debug(f"Erro ao processar linha {i}: {e}")
                        continue
            
            self.logger.info(f"Extraídos {len(documents)} documentos da resposta")
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair documentos: {e}")
            
        return documents
    
    def search_cvm44_historical(self, start_year: int = 2020) -> List[Dict]:
        """Busca documentos CVM 44 históricos"""
        try:
            self.logger.info(f"Buscando documentos CVM 44 desde {start_year}")
            
            all_documents = []
            current_year = datetime.now().year
            
            # Busca ano por ano para evitar timeout
            for year in range(start_year, current_year + 1):
                self.logger.info(f"Processando ano {year}")
                
                # Busca por semestres
                for semester in [1, 2]:
                    if semester == 1:
                        start_date = f"01/01/{year}"
                        end_date = f"30/06/{year}"
                    else:
                        start_date = f"01/07/{year}"
                        end_date = f"31/12/{year}"
                    
                    self.logger.info(f"Buscando S{semester}/{year}: {start_date} a {end_date}")
                    
                    # Busca documentos do período
                    documents = self.search_documents_by_period(start_date, end_date)
                    
                    # Filtra documentos CVM 44 e relacionados
                    cvm44_docs = []
                    for doc in documents:
                        categoria_lower = doc['categoria'].lower()
                        tipo_lower = doc['tipo'].lower()
                        
                        if any(keyword in categoria_lower for keyword in [
                            'valores mobiliários', 'insider', 'cvm 44', 'participação acionária'
                        ]) or any(keyword in tipo_lower for keyword in [
                            'cvm 44', 'insider', 'valores mobiliários'
                        ]):
                            cvm44_docs.append(doc)
                    
                    all_documents.extend(cvm44_docs)
                    self.logger.info(f"S{semester}/{year}: {len(cvm44_docs)} documentos CVM 44")
                    
                    # Delay entre semestres
                    time.sleep(5)
                
                # Delay entre anos
                time.sleep(10)
            
            self.logger.info(f"Total de documentos CVM 44 históricos: {len(all_documents)}")
            return all_documents
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar documentos CVM 44 históricos: {e}")
            return []
    
    def save_to_database(self, documents: List[Dict]) -> int:
        """Salva documentos no banco de dados"""
        try:
            if not self.db.connect():
                self.logger.error("Erro ao conectar ao banco de dados")
                return 0
            
            saved_count = 0
            
            for doc in documents:
                try:
                    # Processa dados do documento
                    doc_data = doc.copy()
                    
                    # Converte datas
                    if doc_data.get('data_entrega'):
                        try:
                            date_str = doc_data['data_entrega'].strip()
                            if ' ' in date_str:
                                date_part, time_part = date_str.split(' ', 1)
                                doc_data['data_entrega'] = datetime.strptime(
                                    f"{date_part} {time_part}", "%d/%m/%Y %H:%M"
                                ).isoformat()
                            else:
                                doc_data['data_entrega'] = datetime.strptime(
                                    date_str, "%d/%m/%Y"
                                ).isoformat()
                        except:
                            doc_data['data_entrega'] = None
                    
                    if doc_data.get('data_referencia'):
                        try:
                            date_str = doc_data['data_referencia'].strip()
                            if date_str and '/' in date_str:
                                doc_data['data_referencia'] = datetime.strptime(
                                    date_str, "%d/%m/%Y"
                                ).date().isoformat()
                        except:
                            doc_data['data_referencia'] = None
                    
                    # Converte versão
                    try:
                        doc_data['versao'] = int(doc_data.get('versao', 1))
                    except:
                        doc_data['versao'] = 1
                    
                    # Salva empresa
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
            self.logger.info(f"Salvos {saved_count} documentos no banco")
            return saved_count
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar no banco: {e}")
            return 0
    
    def run_full_historical_collection(self, start_year: int = 2010):
        """Executa coleta histórica completa"""
        try:
            self.logger.info(f"Iniciando coleta histórica completa desde {start_year}")
            
            # Busca documentos históricos
            documents = self.search_cvm44_historical(start_year)
            
            if documents:
                # Salva no banco
                saved_count = self.save_to_database(documents)
                
                # Salva backup
                backup_file = f"/home/ubuntu/rad_cvm_superscraper/historical_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(documents, f, ensure_ascii=False, indent=2)
                
                result = {
                    'success': True,
                    'total_documents': len(documents),
                    'saved_documents': saved_count,
                    'backup_file': backup_file,
                    'message': f'Coleta concluída: {len(documents)} documentos coletados, {saved_count} salvos'
                }
                
                self.logger.info(result['message'])
                return result
            else:
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
    print("=== Scraper Real RAD CVM ===")
    
    logging.basicConfig(level=logging.INFO)
    
    scraper = RealRADCVMScraper()
    
    try:
        # Teste com período recente
        print("\n1. Testando busca por período (janeiro 2024)...")
        documents = scraper.search_documents_by_period("01/01/2024", "31/01/2024")
        
        print(f"   Encontrados {len(documents)} documentos")
        
        if documents:
            print("\n   Primeiros 5 documentos:")
            for i, doc in enumerate(documents[:5]):
                print(f"   {i+1}. {doc['codigo_cvm']} - {doc['empresa']} - {doc['categoria']}")
        
        # Salva no banco se encontrou documentos
        if documents:
            print("\n2. Salvando no banco de dados...")
            saved = scraper.save_to_database(documents[:10])  # Salva apenas 10 para teste
            print(f"   Salvos {saved} documentos")
        
        print("\n✓ Teste concluído com sucesso!")
        
    except Exception as e:
        print(f"\n✗ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

