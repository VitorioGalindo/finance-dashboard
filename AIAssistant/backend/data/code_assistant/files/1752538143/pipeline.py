import pandas as pd
from pathlib import Path
from supabase import create_client, Client
import os

# --- Configurações ---
# Substitua com suas credenciais reais do Supabase API
SUPABASE_URL = "https://jcvwnitmrjdjeocxgmiy.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpjdnduaXRtcmpkamVvY3hnbWl5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjA5MjQ3NywiZXhwIjoyMDY3NjY4NDc3fQ.oF6enp5M3WrJxOGa4lLkKUMgc8zT8fA_GzRtigCa--8"
TABLE_NAME = "transacoes"

# --- Funções do Pipeline ---
def extract(file_path: Path) -> pd.DataFrame:
    """Extrai dados de um arquivo CSV, usando codificação 'latin-1'."""
    print(f"Iniciando extração de: {file_path.name} (usando codificação latin-1)")
    return pd.read_csv(file_path, encoding='latin-1')

def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Transforma os dados e os prepara para o formato JSON."""
    print("Iniciando a fase de transformação...")
    df_transformed = df.copy()
    # ... (as transformações anteriores como ffill, fillna, etc.) ...
    df_transformed['data'] = df_transformed['data'].ffill()
    df_transformed['descricao'] = df_transformed['descricao'].fillna('N/A')
    df_transformed['moeda'] = df_transformed['moeda'].fillna('BRL')
    df_transformed['categoria'] = df_transformed['categoria'].str.upper().str.strip()
    # A sanitização explícita não é mais necessária, a biblioteca JSON lida com isso.
    df_transformed['data'] = pd.to_datetime(df_transformed['data']).astype(str) # Converte data para string
    df_transformed['valor'] = pd.to_numeric(df_transformed['valor'])
    print("Transformação concluída.")
    # Converte o DataFrame para uma lista de dicionários (formato JSON)
    return df_transformed.to_dict(orient='records')

def load(data: list, supabase: Client, table_name: str):
    """Carrega os dados para o Supabase, limpando a tabela antes."""
    print(f"Iniciando carregamento para a tabela '{table_name}' no Supabase...")
    try:
        # 1. Limpa a tabela para garantir idempotência
        supabase.table(table_name).delete().neq('valor', -9999999).execute() # Deleta todos os registros
        print(f"Tabela '{table_name}' limpa com sucesso.")

        # 2. Insere os novos dados
        response = supabase.table(table_name).insert(data).execute()
        print(f"Dados carregados com sucesso!")
        # print("Resposta da API:", response)

    except Exception as e:
        print(f"ERRO ao carregar dados para o Supabase: {e}")
        raise

# --- Bloco de Execução Principal ---
if __name__ == "__main__":
    print("Iniciando o pipeline de dados completo com a API Supabase...")
    
    # Inicializa o cliente Supabase
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    csv_path = Path(__file__).parent.parent / 'data' / 'raw' / 'transacoes.csv'
    
    try:
        raw_df = extract(csv_path)
        transformed_data = transform(raw_df)
        load(transformed_data, supabase, TABLE_NAME)
        print(f"\nPipeline executado com sucesso! Base de dados na nuvem foi atualizada via API.")
    except Exception as e:
        print(f"\nPipeline falhou. Erro: {e}")