#!/usr/bin/env python3
"""
RAD CVM Superscraper
Extrai documentos de empresas da B3 do portal RAD CVM em tempo real
Foco especial em documentos CVM 44 (insider trading)
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
from webdriver_manager.chrome import ChromeDriverManager
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
        
        service = Service(ChromeDriverManager().install())
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
    
    def get_brazilian_companies(self) -> List[Dict]:
        """Obtém lista de empresas brasileiras do portal"""
        self.start_driver()
        
        try:
            self.logger.info("Acessando portal RAD CVM")
            self.driver.get(self.base_url)
            
            # Aguarda carregamento da página
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Lista para armazenar empresas brasileiras
            companies = []
            
            # Busca por empresas com códigos brasileiros (menores que 05000)
            # Implementar lógica para extrair lista de empresas
            
            self.logger.info(f"Encontradas {len(companies)} empresas brasileiras")
            return companies
            
        except Exception as e:
            self.logger.error(f"Erro ao obter empresas: {e}")
            return []
    
    def search_company_documents(self, company_code: str, company_name: str, 
                                days_back: int = 7) -> List[Dict]:
        """Busca documentos de uma empresa específica"""
        self.start_driver()
        
        try:
            self.logger.info(f"Buscando documentos para {company_name} ({company_code})")
            self.driver.get(self.base_url)
            
            # Aguarda carregamento
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Preenche campo empresa
            empresa_field = self.driver.find_element(By.XPATH, "//input[contains(@id, 'txtEmpresa')]")
            empresa_field.clear()
            empresa_field.send_keys(company_name)
            
            # Aguarda autocomplete e seleciona empresa
            time.sleep(2)
            
            # Configura filtro de data (últimos X dias)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Marca checkbox "No período"
            periodo_checkbox = self.driver.find_element(By.XPATH, "//input[@type='checkbox' and contains(@id, 'chkPeriodo')]")
            if not periodo_checkbox.is_selected():
                periodo_checkbox.click()
            
            # Preenche datas
            data_de = self.driver.find_element(By.XPATH, "//input[contains(@id, 'txtDataDe')]")
            data_de.clear()
            data_de.send_keys(start_date.strftime("%d/%m/%Y"))
            
            data_ate = self.driver.find_element(By.XPATH, "//input[contains(@id, 'txtDataAte')]")
            data_ate.clear()
            data_ate.send_keys(end_date.strftime("%d/%m/%Y"))
            
            # Clica em consultar
            consultar_btn = self.driver.find_element(By.XPATH, "//input[@value='Consultar']")
            consultar_btn.click()
            
            # Aguarda resultados
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Extrai documentos da tabela
            documents = self._extract_documents_from_table()
            
            self.logger.info(f"Encontrados {len(documents)} documentos para {company_name}")
            return documents
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar documentos para {company_name}: {e}")
            return []
    
    def _extract_documents_from_table(self) -> List[Dict]:
        """Extrai documentos da tabela de resultados"""
        documents = []
        
        try:
            # Encontra a tabela de resultados
            table = self.driver.find_element(By.XPATH, "//table[contains(@class, 'grid')]")
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            for row in rows[1:]:  # Pula cabeçalho
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 10:
                    document = {
                        'codigo_cvm': cells[0].text.strip(),
                        'empresa': cells[1].text.strip(),
                        'categoria': cells[2].text.strip(),
                        'tipo': cells[3].text.strip(),
                        'especie': cells[4].text.strip(),
                        'data_referencia': cells[5].text.strip(),
                        'data_entrega': cells[6].text.strip(),
                        'status': cells[7].text.strip(),
                        'versao': cells[8].text.strip(),
                        'modalidade': cells[9].text.strip(),
                        'download_url': self._extract_download_url(cells[10]),
                        'scraped_at': datetime.now().isoformat()
                    }
                    documents.append(document)
                    
        except Exception as e:
            self.logger.error(f"Erro ao extrair documentos da tabela: {e}")
            
        return documents
    
    def _extract_download_url(self, actions_cell) -> Optional[str]:
        """Extrai URL de download da célula de ações"""
        try:
            download_link = actions_cell.find_element(By.XPATH, ".//a[contains(@title, 'Download')]")
            onclick = download_link.get_attribute('onclick')
            # Extrair URL do onclick JavaScript
            # Implementar lógica para extrair URL real
            return onclick
        except:
            return None
    
    def download_document(self, download_url: str, filename: str) -> bool:
        """Baixa um documento específico"""
        try:
            response = self.session.get(download_url)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                self.logger.info(f"Documento baixado: {filename}")
                return True
            else:
                self.logger.error(f"Erro ao baixar documento: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Erro ao baixar documento: {e}")
            return False
    
    def search_cvm44_documents(self, days_back: int = 1) -> List[Dict]:
        """Busca especificamente documentos CVM 44 (insider trading)"""
        self.start_driver()
        
        try:
            self.logger.info("Buscando documentos CVM 44 (insider trading)")
            self.driver.get(self.base_url)
            
            # Aguarda carregamento
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Busca por palavra-chave "Valores Mobiliários"
            palavra_chave = self.driver.find_element(By.XPATH, "//input[contains(@id, 'txtPalavraChave')]")
            palavra_chave.clear()
            palavra_chave.send_keys("Valores Mobiliários")
            
            # Configura filtro de data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Marca checkbox "No período"
            periodo_checkbox = self.driver.find_element(By.XPATH, "//input[@type='checkbox' and contains(@id, 'chkPeriodo')]")
            if not periodo_checkbox.is_selected():
                periodo_checkbox.click()
            
            # Preenche datas
            data_de = self.driver.find_element(By.XPATH, "//input[contains(@id, 'txtDataDe')]")
            data_de.clear()
            data_de.send_keys(start_date.strftime("%d/%m/%Y"))
            
            data_ate = self.driver.find_element(By.XPATH, "//input[contains(@id, 'txtDataAte')]")
            data_ate.clear()
            data_ate.send_keys(end_date.strftime("%d/%m/%Y"))
            
            # Clica em consultar
            consultar_btn = self.driver.find_element(By.XPATH, "//input[@value='Consultar']")
            consultar_btn.click()
            
            # Aguarda resultados
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Extrai documentos CVM 44
            documents = self._extract_documents_from_table()
            
            # Filtra apenas documentos brasileiros (códigos < 05000)
            brazilian_docs = [
                doc for doc in documents 
                if doc['codigo_cvm'] and int(doc['codigo_cvm'].split('-')[0]) < 5000
            ]
            
            self.logger.info(f"Encontrados {len(brazilian_docs)} documentos CVM 44 brasileiros")
            return brazilian_docs
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar documentos CVM 44: {e}")
            return []
    
    def run_continuous_monitoring(self, interval_minutes: int = 1):
        """Executa monitoramento contínuo de novos documentos"""
        self.logger.info(f"Iniciando monitoramento contínuo (intervalo: {interval_minutes} minutos)")
        
        while True:
            try:
                # Busca documentos CVM 44 do último minuto
                new_documents = self.search_cvm44_documents(days_back=1)
                
                if new_documents:
                    self.logger.info(f"Encontrados {len(new_documents)} novos documentos")
                    # Processar e salvar documentos
                    self._process_new_documents(new_documents)
                
                # Aguarda próximo ciclo
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                self.logger.info("Monitoramento interrompido pelo usuário")
                break
            except Exception as e:
                self.logger.error(f"Erro no monitoramento: {e}")
                time.sleep(60)  # Aguarda 1 minuto antes de tentar novamente
    
    def _process_new_documents(self, documents: List[Dict]):
        """Processa novos documentos encontrados"""
        for doc in documents:
            try:
                # Salvar metadados no banco de dados
                # Baixar PDF se for CVM 44
                # Processar PDF para extrair dados de insider trading
                self.logger.info(f"Processando documento: {doc['empresa']} - {doc['tipo']}")
                
            except Exception as e:
                self.logger.error(f"Erro ao processar documento: {e}")

if __name__ == "__main__":
    scraper = RADCVMScraper(headless=False)
    
    try:
        # Teste básico
        documents = scraper.search_cvm44_documents(days_back=7)
        print(f"Encontrados {len(documents)} documentos CVM 44")
        
        for doc in documents[:5]:  # Mostra primeiros 5
            print(f"- {doc['empresa']}: {doc['tipo']} ({doc['data_entrega']})")
            
    finally:
        scraper.stop_driver()

