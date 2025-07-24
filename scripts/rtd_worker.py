import os
import sys
import time
import pandas as pd
import MetaTrader5 as mt5
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# --- 1. CONFIGURAÇÃO E INICIALIZAÇÃO ---
print("--- Iniciando Worker RTD na VM ---")
load_dotenv()

# Define a região da AWS onde seus recursos estão
AWS_REGION = "sa-east-1"  # Região de São Paulo
PAUSE_INTERVAL_SECONDS = 15
RETRY_DELAY_SECONDS = 60

def initialize_services():
    """Conecta-se aos serviços e retorna a engine do banco."""
    print("--- Configurando Serviços ---")
    
    try:
        # --- Carregando credenciais do arquivo .env ---
        print("1. Lendo credenciais do arquivo .env...")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST")
        db_name = os.getenv("DB_NAME", "postgres") # Usa 'postgres' como padrão
        
        mt5_login = int(os.getenv("MT5_LOGIN"))
        mt5_password = os.getenv("MT5_PASSWORD")
        mt5_server = os.getenv("MT5_SERVER")
        
        if not all([db_user, db_password, db_host, mt5_login, mt5_password, mt5_server]):
            raise ValueError("Uma ou mais variáveis de ambiente não foram encontradas no arquivo .env.")
        print("   -> Credenciais carregadas.")

        # --- Conexão com o Banco de Dados (AWS RDS) ---
        print("2. Conectando ao banco de dados AWS RDS PostgreSQL...")
        db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}?sslmode=require"
        engine = create_engine(db_url)
        with engine.connect():
            pass
        print("   -> Conexão com o banco de dados estabelecida.")

        # --- Conexão com o MetaTrader 5 ---
        print("3. Conectando ao MetaTrader 5...")
        if not mt5.initialize(login=mt5_login, password=mt5_password, server=mt5_server):
            raise ConnectionError(f"Falha ao inicializar o MT5: {mt5.last_error()}")
        print("   -> Conexão com o MetaTrader 5 estabelecida.")

        print("--- Todos os serviços foram iniciados com sucesso! ---")
        return engine

    except Exception as e:
        print(f"\n[ERRO FATAL] Falha na inicialização: {e}")
        sys.exit(1)

def main_worker(engine):
    """Loop principal que busca e salva as cotações."""
    print(f"\n--- Worker iniciado. Buscando cotações a cada {PAUSE_INTERVAL_SECONDS} segundos. ---\n")
    while True:
        try:
            if not mt5.terminal_info():
                print(f"[{time.ctime()}] Conexão com MT5 perdida. Tentando reconectar...")
                mt5.shutdown()
                initialize_services()
                continue
            
            df_config = pd.read_sql("SELECT ticker FROM portfolio_config", engine)
            if df_config.empty:
                print(f"[{time.ctime()}] Nenhum ativo na 'portfolio_config'. Insira ativos pelo DBeaver para começar.")
                time.sleep(PAUSE_INTERVAL_SECONDS)
                continue

            quotes_to_upsert = []
            for ticker in df_config['ticker']:
                if not mt5.symbol_select(ticker, True): continue
                tick = mt5.symbol_info_tick(ticker)
                rates = mt5.copy_rates_from_pos(ticker, mt5.TIMEFRAME_D1, 0, 2)
                if tick and tick.last > 0 and rates is not None and len(rates) > 1:
                    quotes_to_upsert.append({
                        "ticker": ticker,
                        "last_price": tick.last,
                        "previous_close": rates[0]['close']
                    })
            
            if quotes_to_upsert:
                df_quotes = pd.DataFrame(quotes_to_upsert)
                with engine.connect() as conn:
                    df_quotes.to_sql('temp_quotes', conn, if_exists='replace', index=False)
                    upsert_sql = text("""
                        INSERT INTO realtime_quotes (ticker, last_price, previous_close)
                        SELECT ticker, last_price, previous_close FROM temp_quotes
                        ON CONFLICT (ticker) DO UPDATE
                        SET last_price = EXCLUDED.last_price, 
                            previous_close = EXCLUDED.previous_close,
                            updated_at = NOW();
                    """)
                    conn.execute(upsert_sql)
                    conn.commit()
                print(f"[{time.ctime()}] Preços atualizados para {len(quotes_to_upsert)} ativos.")
        except Exception as e:
            print(f"\n[ERRO NO LOOP] {e}. Aguardando {RETRY_DELAY_SECONDS}s...")
            time.sleep(RETRY_DELAY_SECONDS)
        
        time.sleep(PAUSE_INTERVAL_SECONDS)

if __name__ == "__main__":
    db_engine = initialize_services()
    main_worker(db_engine)