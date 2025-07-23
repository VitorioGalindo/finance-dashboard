import pandas as pd
from supabase import create_client, Client

class SupabaseLoader:
    """
    Responsável por carregar um DataFrame limpo no banco de dados Supabase.
    """
    def __init__(self, supabase_url: str, supabase_key: str):
        print("Inicializando o Supabase Loader...")
        try:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            print("Cliente Supabase criado com sucesso.")
        except Exception as e:
            print(f"Falha ao criar o cliente Supabase: {e}")
            raise

    def load_transactions(self, df: pd.DataFrame, table_name: str = "transacoes", mode: str = 'replace'):
        """
        Carrega os dados no Supabase, sanitizando os tipos de dados.
        Suporta os modos 'replace' (limpa e insere) e 'append' (apenas insere).
        """
        if df.empty:
            print("Nenhum dado para carregar. Processo de carregamento ignorado.")
            return
            
        print(f"Iniciando carregamento de {len(df)} linhas para a tabela '{table_name}' (modo: {mode})...")
        
        df_sanitized = df.copy().replace({pd.NaT: None})
        for col in df_sanitized.select_dtypes(include=['datetime64[ns]']).columns:
            df_sanitized[col] = df_sanitized[col].apply(lambda x: x.isoformat() if pd.notna(x) else None)
        
        data_to_insert = df_sanitized.to_dict(orient='records')
        
        try:
            if mode == 'replace':
                self.supabase.table(table_name).delete().neq('id', -1).execute() 
                print(f"Tabela '{table_name}' limpa com sucesso.")
            
            response = self.supabase.table(table_name).insert(data_to_insert).execute()
            print(f"Dados carregados com sucesso no Supabase!")

        except Exception as e:
            print(f"ERRO ao carregar dados para o Supabase: {e}")
            raise
