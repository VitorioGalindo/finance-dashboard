#!/usr/bin/env python3
"""
RAD CVM Superscraper - Versão com Requests
Extrai documentos de empresas da B3 do portal RAD CVM usando requests + BeautifulSoup
"""

import time
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import pandas as pd
import re
from urllib.parse import urljoin, parse_qs, urlparse

class RADCVMScraperRequests:
    """Scraper para o portal RAD CVM usando requests"""
    
    def __init__(self):
        self.base_url = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx"
        self.session = requests.Session()
        self.logger = self._setup_logger()
        
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
        logger = logging.getLogger('RADCVMScraperRequests')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def test_connection(self) -> bool:
        """Testa conexão com o portal"""
        try:
            self.logger.info("Testando conexão com o portal RAD CVM")
            response = self.session.get(self.base_url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.title.string if soup.title else ""
                
                self.logger.info(f"Status: {response.status_code}")
                self.logger.info(f"Título: {title}")
                
                if "Consulta de Documentos" in title:
                    self.logger.info("✓ Conexão estabelecida com sucesso")
                    return True
                else:
                    self.logger.warning("⚠ Página carregada mas título não confere")
                    return True  # Ainda assim consideramos sucesso
            else:
                self.logger.error(f"✗ Erro HTTP: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao testar conexão: {e}")
            return False
    
    def get_page_form_data(self) -> Dict:
        """Obtém dados do formulário ASP.NET (ViewState, etc.)"""
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
            
            self.logger.info(f"Extraídos {len(form_data)} campos do formulário")
            return form_data
            
        except Exception as e:
            self.logger.error(f"Erro ao obter dados do formulário: {e}")
            return {}
    
    def search_documents_simple(self) -> List[Dict]:
        """Busca documentos sem filtros específicos"""
        try:
            self.logger.info("Buscando documentos sem filtros")
            
            # Primeira requisição para obter o formulário
            response = self.session.get(self.base_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrai dados do formulário
            form_data = {}
            form = soup.find('form')
            if form:
                inputs = form.find_all('input')
                for input_field in inputs:
                    name = input_field.get('name')
                    value = input_field.get('value', '')
                    if name:
                        form_data[name] = value
            
            # Adiciona dados para consulta
            form_data.update({
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                'ctl00$ContentPlaceHolder1$btnConsultar': 'Consultar'
            })
            
            # Faz a requisição de consulta
            self.logger.info("Enviando requisição de consulta")
            response = self.session.post(self.base_url, data=form_data)
            
            if response.status_code == 200:
                documents = self._extract_documents_from_html(response.content)
                self.logger.info(f"Encontrados {len(documents)} documentos")
                return documents
            else:
                self.logger.error(f"Erro na consulta: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar documentos: {e}")
            return []
    
    def _extract_documents_from_html(self, html_content: bytes) -> List[Dict]:
        """Extrai documentos do HTML da resposta"""
        documents = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Procura por tabelas
            tables = soup.find_all('table')
            
            for table in tables:
                # Verifica se é a tabela de resultados
                headers = table.find_all('th') or table.find_all('td')
                if not headers:
                    continue
                
                header_text = ' '.join([h.get_text().strip().lower() for h in headers[:10]])
                
                if 'empresa' in header_text and 'categoria' in header_text:
                    self.logger.info("Encontrada tabela de resultados")
                    
                    rows = table.find_all('tr')
                    for i, row in enumerate(rows[1:]):  # Pula cabeçalho
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 6:
                            document = {
                                'codigo_cvm': cells[0].get_text().strip() if len(cells) > 0 else '',
                                'empresa': cells[1].get_text().strip() if len(cells) > 1 else '',
                                'categoria': cells[2].get_text().strip() if len(cells) > 2 else '',
                                'tipo': cells[3].get_text().strip() if len(cells) > 3 else '',
                                'especie': cells[4].get_text().strip() if len(cells) > 4 else '',
                                'data_referencia': cells[5].get_text().strip() if len(cells) > 5 else '',
                                'data_entrega': cells[6].get_text().strip() if len(cells) > 6 else '',
                                'status': cells[7].get_text().strip() if len(cells) > 7 else '',
                                'versao': cells[8].get_text().strip() if len(cells) > 8 else '',
                                'modalidade': cells[9].get_text().strip() if len(cells) > 9 else '',
                                'scraped_at': datetime.now().isoformat()
                            }
                            
                            # Só adiciona se tiver dados válidos
                            if document['empresa'] and document['categoria']:
                                documents.append(document)
                    break
            
            # Se não encontrou na tabela, procura por outras estruturas
            if not documents:
                self.logger.info("Procurando documentos em outras estruturas")
                
                # Procura por divs ou outras estruturas que possam conter dados
                content_divs = soup.find_all('div', class_=re.compile(r'.*content.*|.*result.*|.*grid.*', re.I))
                for div in content_divs:
                    text = div.get_text()
                    if 'empresa' in text.lower() and len(text) > 100:
                        self.logger.info(f"Encontrado conteúdo em div: {text[:200]}...")
                        break
                        
        except Exception as e:
            self.logger.error(f"Erro ao extrair documentos do HTML: {e}")
            
        return documents
    
    def get_page_content_info(self) -> Dict:
        """Obtém informações sobre o conteúdo da página"""
        try:
            response = self.session.get(self.base_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            info = {
                'status_code': response.status_code,
                'title': soup.title.string if soup.title else '',
                'content_length': len(response.content),
                'forms_count': len(soup.find_all('form')),
                'tables_count': len(soup.find_all('table')),
                'inputs_count': len(soup.find_all('input')),
                'timestamp': datetime.now().isoformat()
            }
            
            # Procura por mensagens específicas
            body_text = soup.get_text()
            if 'registros' in body_text.lower():
                lines = body_text.split('\n')
                for line in lines:
                    if 'registros' in line.lower() and 'mostrando' in line.lower():
                        info['result_message'] = line.strip()
                        break
            
            # Lista alguns elementos importantes
            form = soup.find('form')
            if form:
                info['form_action'] = form.get('action', '')
                info['form_method'] = form.get('method', '')
            
            return info
            
        except Exception as e:
            self.logger.error(f"Erro ao obter informações da página: {e}")
            return {}
    
    def search_by_keyword(self, keyword: str) -> List[Dict]:
        """Busca documentos por palavra-chave"""
        try:
            self.logger.info(f"Buscando documentos com palavra-chave: {keyword}")
            
            # Obtém formulário inicial
            response = self.session.get(self.base_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrai dados do formulário
            form_data = {}
            inputs = soup.find_all('input')
            for input_field in inputs:
                name = input_field.get('name')
                value = input_field.get('value', '')
                if name:
                    form_data[name] = value
            
            # Procura campo de palavra-chave
            keyword_field = None
            for input_field in inputs:
                if 'palavra' in input_field.get('name', '').lower() or 'keyword' in input_field.get('name', '').lower():
                    keyword_field = input_field.get('name')
                    break
            
            if keyword_field:
                form_data[keyword_field] = keyword
                self.logger.info(f"Campo palavra-chave encontrado: {keyword_field}")
            else:
                self.logger.warning("Campo palavra-chave não encontrado")
            
            # Adiciona dados para consulta
            form_data.update({
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                'ctl00$ContentPlaceHolder1$btnConsultar': 'Consultar'
            })
            
            # Faz a requisição
            response = self.session.post(self.base_url, data=form_data)
            
            if response.status_code == 200:
                documents = self._extract_documents_from_html(response.content)
                self.logger.info(f"Encontrados {len(documents)} documentos com palavra-chave '{keyword}'")
                return documents
            else:
                self.logger.error(f"Erro na consulta: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar por palavra-chave: {e}")
            return []

# Script de teste
if __name__ == "__main__":
    print("=== Teste do RAD CVM Scraper (Versão Requests) ===")
    
    # Configura logging
    logging.basicConfig(level=logging.INFO)
    
    scraper = RADCVMScraperRequests()
    
    try:
        # Teste 1: Conexão
        print("\n1. Testando conexão...")
        if scraper.test_connection():
            print("   ✓ Conexão estabelecida")
        else:
            print("   ✗ Falha na conexão")
            exit(1)
        
        # Teste 2: Informações da página
        print("\n2. Obtendo informações da página...")
        page_info = scraper.get_page_content_info()
        for key, value in page_info.items():
            print(f"   {key}: {value}")
        
        # Teste 3: Busca simples
        print("\n3. Buscando documentos (consulta simples)...")
        documents = scraper.search_documents_simple()
        
        print(f"   Encontrados {len(documents)} documentos")
        
        if documents:
            print("\n   Primeiros documentos:")
            for i, doc in enumerate(documents[:3]):
                print(f"   {i+1}. {doc['empresa']} - {doc['categoria']}")
                if doc['data_entrega']:
                    print(f"      Data: {doc['data_entrega']}")
        
        # Teste 4: Busca por palavra-chave
        print("\n4. Buscando por palavra-chave 'Valores Mobiliários'...")
        cvm44_docs = scraper.search_by_keyword("Valores Mobiliários")
        
        print(f"   Encontrados {len(cvm44_docs)} documentos CVM 44")
        
        if cvm44_docs:
            print("\n   Documentos CVM 44:")
            for i, doc in enumerate(cvm44_docs[:3]):
                print(f"   {i+1}. {doc['empresa']} - {doc['tipo']}")
        
        print("\n✓ Teste concluído com sucesso!")
        
    except Exception as e:
        print(f"\n✗ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

