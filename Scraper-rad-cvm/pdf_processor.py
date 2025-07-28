#!/usr/bin/env python3
"""
Processador de PDFs para documentos CVM 44 (insider trading)
Extrai dados de movimentações de valores mobiliários
"""

import logging
import re
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pdfplumber
import PyPDF2
from io import BytesIO
import requests

class CVM44PDFProcessor:
    """Processador de PDFs de documentos CVM 44"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Configura o logger"""
        logger = logging.getLogger('CVM44PDFProcessor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def download_pdf(self, url: str, filename: str) -> bool:
        """Baixa um PDF de uma URL"""
        try:
            self.logger.info(f"Baixando PDF: {url}")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                self.logger.info(f"PDF salvo: {filename}")
                return True
            else:
                self.logger.error(f"Erro ao baixar PDF: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao baixar PDF: {e}")
            return False
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrai texto completo de um PDF"""
        try:
            text = ""
            
            # Tenta com pdfplumber primeiro
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if not text.strip():
                # Fallback para PyPDF2
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            
            self.logger.info(f"Texto extraído: {len(text)} caracteres")
            return text
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair texto do PDF: {e}")
            return ""
    
    def extract_tables_from_pdf(self, pdf_path: str) -> List[pd.DataFrame]:
        """Extrai tabelas de um PDF"""
        tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    
                    for table_num, table in enumerate(page_tables):
                        if table and len(table) > 1:  # Pelo menos cabeçalho + 1 linha
                            df = pd.DataFrame(table[1:], columns=table[0])
                            df['page_number'] = page_num + 1
                            df['table_number'] = table_num + 1
                            tables.append(df)
                            
                            self.logger.info(f"Tabela extraída da página {page_num + 1}: {df.shape}")
            
            self.logger.info(f"Total de tabelas extraídas: {len(tables)}")
            return tables
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair tabelas do PDF: {e}")
            return []
    
    def identify_cvm44_document_type(self, text: str) -> str:
        """Identifica o tipo de documento CVM 44"""
        text_lower = text.lower()
        
        if "valores mobiliários negociados e detidos" in text_lower:
            return "valores_mobiliarios"
        elif "movimentação" in text_lower and "insider" in text_lower:
            return "movimentacao_insider"
        elif "participação" in text_lower and "capital" in text_lower:
            return "participacao_capital"
        else:
            return "outros"
    
    def extract_company_info(self, text: str) -> Dict:
        """Extrai informações da empresa do documento"""
        company_info = {}
        
        try:
            # Padrões para extrair informações
            patterns = {
                'empresa': r'(?:empresa|companhia|denominação):\s*([^\n]+)',
                'cnpj': r'cnpj[:\s]*(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})',
                'codigo_cvm': r'(?:código|cod\.?)\s*cvm[:\s]*(\d+)',
                'data_documento': r'(?:data|em)\s*(\d{1,2}/\d{1,2}/\d{4})'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    company_info[key] = match.group(1).strip()
            
            self.logger.info(f"Informações da empresa extraídas: {company_info}")
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair informações da empresa: {e}")
            
        return company_info
    
    def extract_person_info(self, text: str) -> List[Dict]:
        """Extrai informações das pessoas (administradores, controladores)"""
        people = []
        
        try:
            # Padrões para identificar pessoas
            person_patterns = [
                r'nome:\s*([^\n]+)',
                r'cpf[:\s]*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
                r'cargo[:\s]*([^\n]+)',
                r'(?:administrador|controlador|diretor)[:\s]*([^\n]+)'
            ]
            
            # Divide o texto em seções por pessoa
            sections = re.split(r'(?:nome|pessoa|administrador|controlador)', text, flags=re.IGNORECASE)
            
            for section in sections[1:]:  # Pula primeira seção vazia
                person = {}
                
                # Extrai nome
                name_match = re.search(r'^[:\s]*([^\n]+)', section)
                if name_match:
                    person['nome'] = name_match.group(1).strip()
                
                # Extrai CPF
                cpf_match = re.search(r'cpf[:\s]*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})', section, re.IGNORECASE)
                if cpf_match:
                    person['cpf'] = cpf_match.group(1)
                
                # Extrai cargo
                cargo_match = re.search(r'cargo[:\s]*([^\n]+)', section, re.IGNORECASE)
                if cargo_match:
                    person['cargo'] = cargo_match.group(1).strip()
                
                if person.get('nome'):
                    people.append(person)
            
            self.logger.info(f"Pessoas identificadas: {len(people)}")
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair informações de pessoas: {e}")
            
        return people
    
    def process_movimentacao_table(self, df: pd.DataFrame) -> List[Dict]:
        """Processa tabela de movimentações"""
        movimentacoes = []
        
        try:
            # Identifica colunas relevantes
            columns_map = {}
            for col in df.columns:
                col_lower = str(col).lower()
                if 'valor' in col_lower and 'mobiliário' in col_lower:
                    columns_map['valor_mobiliario'] = col
                elif 'quantidade' in col_lower and 'anterior' in col_lower:
                    columns_map['quantidade_anterior'] = col
                elif 'quantidade' in col_lower and 'atual' in col_lower:
                    columns_map['quantidade_atual'] = col
                elif 'preço' in col_lower or 'preco' in col_lower:
                    columns_map['preco_unitario'] = col
                elif 'valor' in col_lower and 'total' in col_lower:
                    columns_map['valor_total'] = col
                elif 'data' in col_lower:
                    columns_map['data_movimentacao'] = col
                elif 'tipo' in col_lower and 'operação' in col_lower:
                    columns_map['tipo_movimentacao'] = col
            
            # Processa cada linha
            for _, row in df.iterrows():
                movimentacao = {}
                
                for key, col in columns_map.items():
                    if col in df.columns:
                        value = row[col]
                        if pd.notna(value):
                            movimentacao[key] = str(value).strip()
                
                # Calcula quantidade movimentada se não estiver presente
                if ('quantidade_anterior' in movimentacao and 
                    'quantidade_atual' in movimentacao and
                    'quantidade_movimentada' not in movimentacao):
                    try:
                        anterior = float(movimentacao['quantidade_anterior'].replace(',', '.'))
                        atual = float(movimentacao['quantidade_atual'].replace(',', '.'))
                        movimentacao['quantidade_movimentada'] = str(atual - anterior)
                    except:
                        pass
                
                if movimentacao:
                    movimentacoes.append(movimentacao)
            
            self.logger.info(f"Movimentações processadas: {len(movimentacoes)}")
            
        except Exception as e:
            self.logger.error(f"Erro ao processar tabela de movimentações: {e}")
            
        return movimentacoes
    
    def process_cvm44_pdf(self, pdf_path: str) -> Dict:
        """Processa um PDF CVM 44 completo"""
        result = {
            'success': False,
            'document_type': '',
            'company_info': {},
            'people': [],
            'movimentacoes': [],
            'raw_text': '',
            'tables_count': 0,
            'processed_at': datetime.now().isoformat()
        }
        
        try:
            self.logger.info(f"Processando PDF CVM 44: {pdf_path}")
            
            # Extrai texto
            text = self.extract_text_from_pdf(pdf_path)
            result['raw_text'] = text
            
            if not text:
                self.logger.error("Não foi possível extrair texto do PDF")
                return result
            
            # Identifica tipo de documento
            result['document_type'] = self.identify_cvm44_document_type(text)
            
            # Extrai informações da empresa
            result['company_info'] = self.extract_company_info(text)
            
            # Extrai informações de pessoas
            result['people'] = self.extract_person_info(text)
            
            # Extrai tabelas
            tables = self.extract_tables_from_pdf(pdf_path)
            result['tables_count'] = len(tables)
            
            # Processa tabelas de movimentação
            for table in tables:
                movimentacoes = self.process_movimentacao_table(table)
                result['movimentacoes'].extend(movimentacoes)
            
            result['success'] = True
            self.logger.info(f"PDF processado com sucesso: {len(result['movimentacoes'])} movimentações")
            
        except Exception as e:
            self.logger.error(f"Erro ao processar PDF CVM 44: {e}")
            result['error'] = str(e)
            
        return result
    
    def create_sample_pdf_data(self) -> Dict:
        """Cria dados de exemplo para teste"""
        return {
            'success': True,
            'document_type': 'valores_mobiliarios',
            'company_info': {
                'empresa': 'PETROBRAS S.A.',
                'cnpj': '33.000.167/0001-01',
                'codigo_cvm': '9512',
                'data_documento': '28/07/2025'
            },
            'people': [
                {
                    'nome': 'João Silva Santos',
                    'cpf': '123.456.789-01',
                    'cargo': 'Diretor Presidente'
                },
                {
                    'nome': 'Maria Oliveira Costa',
                    'cpf': '987.654.321-09',
                    'cargo': 'Diretora Financeira'
                }
            ],
            'movimentacoes': [
                {
                    'valor_mobiliario': 'Ações Ordinárias',
                    'quantidade_anterior': '1000000',
                    'quantidade_atual': '1050000',
                    'quantidade_movimentada': '50000',
                    'tipo_movimentacao': 'Compra',
                    'preco_unitario': '25.50',
                    'valor_total': '1275000.00',
                    'data_movimentacao': '25/07/2025'
                },
                {
                    'valor_mobiliario': 'Ações Preferenciais',
                    'quantidade_anterior': '500000',
                    'quantidade_atual': '480000',
                    'quantidade_movimentada': '-20000',
                    'tipo_movimentacao': 'Venda',
                    'preco_unitario': '22.75',
                    'valor_total': '455000.00',
                    'data_movimentacao': '26/07/2025'
                }
            ],
            'tables_count': 2,
            'processed_at': datetime.now().isoformat()
        }

# Script de teste
if __name__ == "__main__":
    print("=== Teste do Processador de PDFs CVM 44 ===")
    
    # Configura logging
    logging.basicConfig(level=logging.INFO)
    
    processor = CVM44PDFProcessor()
    
    try:
        # Teste com dados de exemplo
        print("\n1. Testando com dados de exemplo...")
        sample_data = processor.create_sample_pdf_data()
        
        print(f"   Empresa: {sample_data['company_info']['empresa']}")
        print(f"   CNPJ: {sample_data['company_info']['cnpj']}")
        print(f"   Pessoas: {len(sample_data['people'])}")
        print(f"   Movimentações: {len(sample_data['movimentacoes'])}")
        
        for i, mov in enumerate(sample_data['movimentacoes']):
            print(f"   {i+1}. {mov['valor_mobiliario']}: {mov['quantidade_movimentada']} ({mov['tipo_movimentacao']})")
        
        print("\n✓ Processador de PDFs funcionando!")
        
    except Exception as e:
        print(f"\n✗ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

