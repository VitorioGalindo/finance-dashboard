#!/usr/bin/env python3
"""
RAD CVM Superscraper - Versão Corrigida
Extrai documentos de empresas da B3 do portal RAD CVM em tempo real
"""

import time
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import pandas as pd

class RADCVMScraper:
    """Scraper para o portal RAD CVM"""
    
    def __init__(self, headless: bool = True):
        self.base_url = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx"
        self.headless = headless
        self.driver = None
        self.session = requests.Session()
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Configura o logger"""
        logger = logging.getLogger('RADCVMScraper')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Configura o driver do Selenium"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        
        # Usa o chromedriver do sistema
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    
    def start_driver(self):
        """Inicia o driver do Selenium"""
        if self.driver is None:
            self.driver = self._setup_driver()
            self.logger.info("Driver do Selenium iniciado")
    
    def stop_driver(self):
        """Para o driver do Selenium"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.logger.info("Driver do Selenium parado")
    
    def test_connection(self) -> bool:
        """Testa conexão com o portal"""
        try:
            self.start_driver()
            self.logger.info("Testando conexão com o portal RAD CVM")
            self.driver.get(self.base_url)
            
            # Aguarda carregamento da página
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            title = self.driver.title
            self.logger.info(f"Título da página: {title}")
            
            if "Consulta de Documentos" in title:
                self.logger.info("✓ Conexão com portal estabelecida")
                return True
            else:
                self.logger.error("✗ Título da página não confere")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao testar conexão: {e}")
            return False
    
    def search_recent_documents(self, days_back: int = 1) -> List[Dict]:
        """Busca documentos recentes (últimos X dias)"""
        try:
            self.start_driver()
            self.logger.info(f"Buscando documentos dos últimos {days_back} dias")
            self.driver.get(self.base_url)
            
            # Aguarda carregamento
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Configura filtro de data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Procura e marca checkbox "No período"
            try:
                periodo_elements = self.driver.find_elements(By.XPATH, "//input[@type='checkbox']")
                for elem in periodo_elements:
                    parent = elem.find_element(By.XPATH, "..")
                    if "período" in parent.text.lower():
                        if not elem.is_selected():
                            elem.click()
                        break
            except Exception as e:
                self.logger.warning(f"Não foi possível configurar filtro de período: {e}")
            
            # Tenta preencher datas se os campos existirem
            try:
                date_inputs = self.driver.find_elements(By.XPATH, "//input[contains(@placeholder, '__/__/____')]")
                if len(date_inputs) >= 2:
                    # Data inicial
                    date_inputs[0].clear()
                    date_inputs[0].send_keys(start_date.strftime("%d/%m/%Y"))
                    
                    # Data final
                    date_inputs[1].clear()
                    date_inputs[1].send_keys(end_date.strftime("%d/%m/%Y"))
            except Exception as e:
                self.logger.warning(f"Não foi possível configurar datas: {e}")
            
            # Clica em consultar
            try:
                consultar_btn = self.driver.find_element(By.XPATH, "//input[@value='Consultar']")
                consultar_btn.click()
                
                # Aguarda resultados
                time.sleep(3)
                
            except Exception as e:
                self.logger.error(f"Erro ao executar consulta: {e}")
                return []
            
            # Extrai documentos
            documents = self._extract_documents_from_page()
            
            self.logger.info(f"Encontrados {len(documents)} documentos")
            return documents
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar documentos recentes: {e}")
            return []
    
    def _extract_documents_from_page(self) -> List[Dict]:
        """Extrai documentos da página atual"""
        documents = []
        
        try:
            # Aguarda a tabela carregar
            time.sleep(2)
            
            # Procura por tabelas na página
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            
            for table in tables:
                try:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    
                    # Verifica se é a tabela de resultados (deve ter cabeçalhos específicos)
                    if len(rows) > 1:
                        header_row = rows[0]
                        header_text = header_row.text.lower()
                        
                        if "empresa" in header_text and "categoria" in header_text:
                            # Esta é a tabela de resultados
                            for row in rows[1:]:
                                cells = row.find_elements(By.TAG_NAME, "td")
                                if len(cells) >= 8:  # Mínimo de colunas esperadas
                                    document = {
                                        'codigo_cvm': cells[0].text.strip() if len(cells) > 0 else '',
                                        'empresa': cells[1].text.strip() if len(cells) > 1 else '',
                                        'categoria': cells[2].text.strip() if len(cells) > 2 else '',
                                        'tipo': cells[3].text.strip() if len(cells) > 3 else '',
                                        'especie': cells[4].text.strip() if len(cells) > 4 else '',
                                        'data_referencia': cells[5].text.strip() if len(cells) > 5 else '',
                                        'data_entrega': cells[6].text.strip() if len(cells) > 6 else '',
                                        'status': cells[7].text.strip() if len(cells) > 7 else '',
                                        'versao': cells[8].text.strip() if len(cells) > 8 else '',
                                        'modalidade': cells[9].text.strip() if len(cells) > 9 else '',
                                        'scraped_at': datetime.now().isoformat()
                                    }
                                    
                                    # Só adiciona se tiver dados válidos
                                    if document['empresa'] and document['categoria']:
                                        documents.append(document)
                            break
                            
                except Exception as e:
                    self.logger.debug(f"Erro ao processar tabela: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Erro ao extrair documentos: {e}")
            
        return documents
    
    def get_page_info(self) -> Dict:
        """Obtém informações da página atual"""
        try:
            info = {
                'title': self.driver.title,
                'url': self.driver.current_url,
                'page_source_length': len(self.driver.page_source),
                'timestamp': datetime.now().isoformat()
            }
            
            # Procura por mensagens de resultado
            try:
                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                if "registros" in body_text.lower():
                    lines = body_text.split('\n')
                    for line in lines:
                        if "registros" in line.lower():
                            info['result_message'] = line.strip()
                            break
            except:
                pass
                
            return info
            
        except Exception as e:
            self.logger.error(f"Erro ao obter informações da página: {e}")
            return {}

# Script de teste
if __name__ == "__main__":
    print("=== Teste do RAD CVM Scraper (Versão Corrigida) ===")
    
    # Configura logging
    logging.basicConfig(level=logging.INFO)
    
    scraper = RADCVMScraper(headless=True)
    
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
        page_info = scraper.get_page_info()
        for key, value in page_info.items():
            print(f"   {key}: {value}")
        
        # Teste 3: Busca de documentos
        print("\n3. Buscando documentos recentes...")
        documents = scraper.search_recent_documents(days_back=7)
        
        print(f"   Encontrados {len(documents)} documentos")
        
        if documents:
            print("\n   Primeiros documentos:")
            for i, doc in enumerate(documents[:3]):
                print(f"   {i+1}. {doc['empresa']} - {doc['categoria']} ({doc['data_entrega']})")
        
        print("\n✓ Teste concluído com sucesso!")
        
    except Exception as e:
        print(f"\n✗ Erro durante o teste: {e}")
        
    finally:
        scraper.stop_driver()

