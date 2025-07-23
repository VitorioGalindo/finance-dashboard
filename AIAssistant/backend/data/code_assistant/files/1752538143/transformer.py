import pandas as pd
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

class DataTransformer:
    """
    Transforma dados brutos do PDF em um formato estruturado e limpo,
    reconstruindo linhas de transação e enriquecendo com metadados.
    """
    def __init__(self, parsed_data: Dict[str, Any]):
        self.parsed_data = parsed_data
        print("Transformer inicializado com os dados extraídos.")

    def _clean_currency(self, text_value: str) -> float:
        if not isinstance(text_value, str) or not text_value: return 0.0
        is_negative = text_value.startswith('(') and text_value.endswith(')')
        cleaned_value = re.sub(r'[^\d,]', '', text_value).replace(',', '.')
        try:
            numeric_value = float(cleaned_value)
            return -numeric_value if is_negative else numeric_value
        except (ValueError, TypeError): return 0.0

    def _find_transactions_table(self) -> Optional[pd.DataFrame]:
        extracted_tables = self.parsed_data.get("extracted_tables")
        if not extracted_tables: return None
        expected_keywords = ["operação", "dia", "quantidade", "preço", "volume"]
        for df in extracted_tables:
            header_str = ""
            for i in range(min(4, len(df))):
                header_str += ' '.join(map(str, df.iloc[i])).lower()
            if sum(keyword in header_str for keyword in expected_keywords) >= 3:
                print("Tabela de movimentações principal identificada.")
                return df
        print("AVISO: Nenhuma tabela de movimentações principal foi identificada.")
        return None

    def _reconstruct_transaction_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        print("Iniciando reconstrução das linhas de transação...")
        header_row_index = -1
        for i, row in df.iterrows():
            row_str = ' '.join(map(str, row)).lower()
            if 'operação' in row_str and 'preço' in row_str:
                header_row_index = i
                break
        if header_row_index == -1: return pd.DataFrame()
        data_rows = df.iloc[header_row_index + 1:].copy()
        data_rows.replace('', pd.NA, inplace=True)
        reconstructed_data = []
        current_transaction = {}
        for _, row in data_rows.iterrows():
            is_data_row = pd.notna(row.iloc[-1]) or pd.notna(row.iloc[-3])
            if is_data_row:
                if current_transaction: reconstructed_data.append(current_transaction)
                current_transaction = row.to_dict()
            else:
                if current_transaction:
                    for i, value in row.items():
                        if pd.notna(value):
                            current_transaction[i] = f"{current_transaction.get(i, '')} {value}".strip()
        if current_transaction: reconstructed_data.append(current_transaction)
        if not reconstructed_data: return pd.DataFrame()
        df_reconstructed = pd.DataFrame(reconstructed_data)
        print(f"Reconstrução concluída. {len(df_reconstructed)} transações montadas.")
        return df_reconstructed

    def transform_to_transactions_schema(self) -> pd.DataFrame:
        print("Iniciando processo de transformação de dados...")
        df_raw_transactions = self._find_transactions_table()
        if df_raw_transactions is None: return pd.DataFrame()
        df_reconstructed = self._reconstruct_transaction_rows(df_raw_transactions)
        if df_reconstructed.empty: return pd.DataFrame()
        df_reconstructed.dropna(axis=1, how='all', inplace=True)
        try:
            df_reconstructed.columns = [
                "valor_mobiliario", "caracteristicas", "intermediario", "operacao", 
                "dia", "quantidade", "preco", "volume_rs"
            ]
        except Exception as e:
            print(f"ERRO DE MAPEAMENTO DE COLUNAS: {e}.")
            return pd.DataFrame()

        metadata = self.parsed_data.get("metadata", {})
        df_final = pd.DataFrame()
        df_final['descricao'] = df_reconstructed["operacao"] + " - " + df_reconstructed["valor_mobiliario"]
        df_final['categoria'] = metadata.get('form_type', 'N/A')
        df_final['valor'] = df_reconstructed["volume_rs"].apply(self._clean_currency)
        df_final['moeda'] = 'BRL'
        df_final['cnpj_companhia'] = metadata.get('cnpj_companhia', None)
        df_final['nome_companhia'] = metadata.get('nome_companhia', None)
        df_final['data_referencia'] = pd.to_datetime(metadata.get('data_referencia', None), errors='coerce')
        
        # Constrói a data completa da transação
        df_reconstructed['dia'] = pd.to_numeric(df_reconstructed['dia'], errors='coerce')
        # Garante que a data de referência seja um datetime antes de usar
        report_date = pd.to_datetime(df_final['data_referencia'].iloc[0]) if not df_final.empty else datetime.now()
        df_final['data'] = df_reconstructed['dia'].apply(
            lambda d: report_date.replace(day=int(d)) if pd.notna(d) and d > 0 else report_date
        )

        final_columns = ['data', 'descricao', 'categoria', 'valor', 'moeda', 'cnpj_companhia', 'nome_companhia', 'data_referencia']
        df_final = df_final[final_columns]
        print(f"Transformação final concluída. {len(df_final)} linhas enriquecidas prontas para carregar.")
        return df_final
