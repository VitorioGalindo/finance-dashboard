# core/parser.py

import pdfplumber
import re
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional

class PDFParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = str(pdf_path)

    def _clean_text(self, text: Optional[str]) -> str:
        if not text: return ""
        return ' '.join(str(text).strip().split())

    def _parse_number(self, value: Optional[str]) -> Optional[float]:
        if not value: return None
        try:
            return float(self._clean_text(value).replace('.', '').replace(',', '.'))
        except (ValueError, TypeError):
            return None

    def extract_transactions(self) -> List[Dict[str, Any]]:
        all_transactions = []
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text(x_tolerance=1)
                    if not page_text or "Movimentações no Mês" not in page_text or "(X) não foram realizadas operações" in page_text:
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
                        
                        # Lógica para juntar linhas de operação quebradas
                        processed_rows, temp_row = [], {}
                        for i, row in df_body.iterrows():
                            if pd.notna(row.get('Dia')) and self._clean_text(row.get('Dia')):
                                if temp_row: processed_rows.append(temp_row)
                                temp_row = row.to_dict()
                            else:
                                if temp_row:
                                    op_text = self._clean_text(row.get('Operação', ''))
                                    asset_text = self._clean_text(df.columns[0]) # Nome da primeira coluna
                                    if op_text:
                                        temp_row['Operação'] = f"{temp_row.get('Operação', '')} {op_text}".strip()
                                    if asset_text and asset_text not in temp_row.get('Valor Mobiliário/Derivativo',''):
                                        temp_row['Valor Mobiliário/Derivativo'] = f"{temp_row.get('Valor Mobiliário/Derivativo', '')} {asset_text}".strip()

                        if temp_row: processed_rows.append(temp_row)

                        for row_dict in processed_rows:
                            day = self._parse_number(row_dict.get('Dia'))
                            quantity = self._parse_number(row_dict.get('Quantidade'))
                            if day and quantity and quantity != 0:
                                all_transactions.append({
                                    "transaction_date": datetime(year, month, 1).replace(day=int(day)).date(),
                                    "operation_type": self._clean_text(row_dict.get('Operação')),
                                    "asset_type": self._clean_text(row_dict.get('Valor Mobiliário/Derivativo')),
                                    "quantity": int(quantity),
                                    "price": self._parse_number(row_dict.get('Preço')),
                                    "volume": self._parse_number(row_dict.get('Volume (R$)'))
                                })
        except Exception as e:
            print(f"ERRO no Parser ao processar {self.pdf_path}: {e}")
        return all_transactions