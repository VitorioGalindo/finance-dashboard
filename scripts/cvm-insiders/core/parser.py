# scripts/cvm-insiders/core/parser.py
import pdfplumber
import re
import pandas as pd
import requests
import tempfile
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Adiciona o diretório raiz para permitir a importação do 'backend'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importações centralizadas do nosso backend e database
from backend.models import Filing, Insider, Transaction, Company
from .database import get_db

class PDFParser:
    """
    Classe responsável por extrair informações de um único arquivo PDF.
    A lógica interna de parsing de PDF permanece a mesma.
    """
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def _clean_text(self, text: Optional[str]) -> str:
        if not text: return ""
        return ' '.join(str(text).strip().split())

    def _parse_number(self, value: Optional[str]) -> Optional[float]:
        if not value: return None
        try:
            cleaned_value = self._clean_text(value).replace('.', '').replace(',', '.')
            # Retorna None se o valor for apenas um traço ou vazio após a limpeza
            return float(cleaned_value) if cleaned_value and cleaned_value != '-' else None
        except (ValueError, TypeError):
            return None

    def extract_insider_info(self, page_text: str) -> Optional[Dict[str, str]]:
        """Extrai o nome e documento do insider do texto da página."""
        name_match = re.search(r"Nome da Pessoa Física ou Jurídica\s*
(.*?)
", page_text)
        doc_match = re.search(r"CPF/CNPJ\s*
(.*?)
", page_text)
        
        if name_match:
            return {
                "name": self._clean_text(name_match.group(1)),
                "document": self._clean_text(doc_match.group(1)) if doc_match else None
            }
        return None

    def extract_transactions(self) -> Dict[str, Any]:
        """Extrai as informações do insider e a lista de transações do PDF."""
        all_transactions = []
        insider_info = None
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text(x_tolerance=1)
                    if not page_text: continue

                    # Tenta extrair informações do insider em cada página, mas armazena apenas a primeira encontrada
                    if not insider_info:
                        insider_info = self.extract_insider_info(page_text)

                    # Procura por tabelas de transação
                    if "Movimentações no Mês" not in page_text or "(X) não foram realizadas operações" in page_text:
                        continue
                    
                    ref_date_match = re.search(r"Em\s*(\d{2}/\d{4})", page_text)
                    if not ref_date_match: continue
                    month, year = map(int, ref_date_match.group(1).split('/'))
                    
                    tables = page.extract_tables(table_settings={"vertical_strategy": "lines", "horizontal_strategy": "text"})
                    for table_data in tables:
                        df = pd.DataFrame(table_data)
                        if df.empty or "Dia" not in df.to_string() or "Operação" not in df.to_string(): continue
                        
                        header_row_index = next((i for i, row in df.iterrows() if 'Dia' in str(row.values) and 'Operação' in str(row.values)), -1)
                        if header_row_index == -1: continue

                        df.columns = [self._clean_text(col) for col in df.iloc[header_row_index]]
                        df_body = df.iloc[header_row_index + 1:].reset_index(drop=True)
                        
                        processed_rows = []
                        for _, row in df_body.iterrows():
                            # Ignora linhas que são completamente vazias
                            if row.isnull().all(): continue
                            processed_rows.append(row.to_dict())

                        for row_dict in processed_rows:
                            day_str = self._clean_text(row_dict.get('Dia'))
                            day = int(float(day_str)) if day_str else None
                            quantity = self._parse_number(row_dict.get('Quantidade'))

                            if day and quantity and quantity != 0:
                                all_transactions.append({
                                    "transaction_date": datetime(year, month, day).date(),
                                    "operation_type": self._clean_text(row_dict.get('Operação')),
                                    "asset_type": self._clean_text(row_dict.get('Valor Mobiliário/Derivativo')),
                                    "quantity": int(quantity),
                                    "price": self._parse_number(row_dict.get('Preço')),
                                    "volume": self._parse_number(row_dict.get('Volume (R$)'))
                                })
        except Exception as e:
            print(f"    -> ERRO no Parser ao processar {os.path.basename(self.pdf_path)}: {e}")
        
        return {"insider": insider_info, "transactions": all_transactions}

def get_or_create_insider(db: Session, company_cnpj: str, insider_info: Dict[str, str]) -> Insider:
    """Busca um insider pelo nome e CNPJ da empresa, ou cria um novo se não existir."""
    insider = db.query(Insider).filter_by(company_cnpj=company_cnpj, name=insider_info['name']).first()
    if not insider:
        print(f"    -> Novo insider encontrado: {insider_info['name']}. Criando registro...")
        insider = Insider(
            company_cnpj=company_cnpj,
            name=insider_info['name'],
            document=insider_info.get('document'),
            insider_type='Individual' # Placeholder, pode ser melhorado
        )
        db.add(insider)
        db.commit() # Comita para que o ID seja gerado e possa ser usado
        db.refresh(insider)
    return insider

def run_parser():
    """
    Função principal que orquestra o processo de parsing.
    Busca filings não processados, baixa os PDFs e salva as transações.
    """
    print("-- Iniciando o parser de PDFs de insiders --")
    with get_db() as db:
        # Busca filings que ainda não foram processados
        unprocessed_filings = db.query(Filing).filter(Filing.processed_at == None).all()
        
        if not unprocessed_filings:
            print("Nenhum novo filing para processar.")
            return
            
        print(f"Encontrados {len(unprocessed_filings)} filings para processar.")

        for filing in unprocessed_filings:
            print(f"  -> Processando Filing ID: {filing.id}, Protocolo: {filing.cvm_protocol}")
            
            # Baixa o PDF para um arquivo temporário
            try:
                response = requests.get(filing.pdf_url)
                response.raise_for_status()
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    tmp.write(response.content)
                    pdf_path = tmp.name
            except requests.RequestException as e:
                print(f"    -> ERRO: Falha ao baixar o PDF {filing.pdf_url}. {e}")
                filing.processed_at = datetime.utcnow() # Marca como processado para não tentar de novo
                db.commit()
                continue
            
            # Extrai as informações do PDF
            parser = PDFParser(pdf_path)
            extracted_data = parser.extract_transactions()
            os.remove(pdf_path) # Remove o arquivo temporário

            insider_info = extracted_data.get('insider')
            transactions = extracted_data.get('transactions', [])

            if not insider_info:
                print("    -> AVISO: Não foi possível extrair informações do insider. Pulando filing.")
                filing.processed_at = datetime.utcnow()
                db.commit()
                continue

            # Pega ou cria o registro do insider
            try:
                insider = get_or_create_insider(db, filing.company_cnpj, insider_info)
                
                if transactions:
                    print(f"    -> Extraídas {len(transactions)} transações para o insider {insider.name}.")
                    new_transactions = []
                    for t_data in transactions:
                        new_t = Transaction(
                            filing_id=filing.id,
                            insider_id=insider.id,
                            **t_data
                        )
                        new_transactions.append(new_t)
                    
                    db.bulk_save_objects(new_transactions)
                else:
                    print("    -> Nenhuma transação encontrada no documento.")

                # Marca o filing como processado
                filing.processed_at = datetime.utcnow()
                db.commit()
                
            except SQLAlchemyError as e:
                print(f"    -> ERRO DE BANCO DE DADOS: {e}. Revertendo alterações para este filing.")
                db.rollback()

    print("-- Parser de PDFs de insiders concluído --")

if __name__ == '__main__':
    run_parser()
