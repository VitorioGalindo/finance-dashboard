# scripts/migrate_schema.py
import os
from dotenv import load_dotenv
import psycopg2

def get_db_connection_string():
    """Lê as credenciais do .env e cria uma string de conexão."""
    load_dotenv()
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    dbname = os.getenv("DB_NAME", "postgres")
    if not all([user, password, host, dbname]):
        raise ValueError("Credenciais do banco não encontradas.")
    
    return f"postgresql://{user}:{password}@{host}/{dbname}?sslmode=require"

def run_migration():
    """Executa os comandos SQL para padronizar o esquema do banco de dados."""
    print("--- INICIANDO SCRIPT DE MIGRAÇÃO DE ESQUEMA ---")
    
    # Lista de comandos SQL a serem executados em ordem
    # Cada tupla contém: (descrição_da_tarefa, comando_sql)
    migration_commands = [
        # --- Padronização da Tabela 'cvm_dados_financeiros' ---
        ("Renomeando tabela 'cvm_dados_financeiros' para 'financial_statements'",
         "ALTER TABLE IF EXISTS public.cvm_dados_financeiros RENAME TO financial_statements;"),
        
        ("Renomeando coluna 'cnpj_cia' para 'company_cnpj' em 'financial_statements'",
         "ALTER TABLE IF EXISTS public.financial_statements RENAME COLUMN cnpj_cia TO company_cnpj;"),
        
        ("Renomeando outras colunas em 'financial_statements'",
         """
         DO $$
         BEGIN
            ALTER TABLE public.financial_statements RENAME COLUMN denom_cia TO company_name;
            ALTER TABLE public.financial_statements RENAME COLUMN cd_cvm TO cvm_code;
            ALTER TABLE public.financial_statements RENAME COLUMN versao TO report_version;
            ALTER TABLE public.financial_statements RENAME COLUMN dt_refer TO reference_date;
            ALTER TABLE public.financial_statements RENAME COLUMN dt_ini_exerc TO fiscal_year_start;
            ALTER TABLE public.financial_statements RENAME COLUMN dt_fim_exerc TO fiscal_year_end;
            ALTER TABLE public.financial_statements RENAME COLUMN cd_conta TO account_code;
            ALTER TABLE public.financial_statements RENAME COLUMN ds_conta TO account_description;
            ALTER TABLE public.financial_statements RENAME COLUMN vl_conta TO account_value;
            ALTER TABLE public.financial_statements RENAME COLUMN escala_moeda TO currency_scale;
            ALTER TABLE public.financial_statements RENAME COLUMN ordem_exerc TO fiscal_year_order;
            ALTER TABLE public.financial_statements RENAME COLUMN tipo_demonstracao TO report_type;
         END $$;
         """),

        # --- Padronização da Tabela 'transacoes' ---
        ("Renomeando tabela 'transacoes' para 'generic_transactions'",
         "ALTER TABLE IF EXISTS public.transacoes RENAME TO generic_transactions;"),
        
        ("Renomeando coluna 'cnpj_companhia' para 'company_cnpj' em 'generic_transactions'",
         "ALTER TABLE IF EXISTS public.generic_transactions RENAME COLUMN cnpj_companhia TO company_cnpj;"),

        # --- Padronização da Tabela 'transactions' (de insiders) ---
        ("Renomeando tabela 'transactions' para 'insider_transactions'",
         "ALTER TABLE IF EXISTS public.transactions RENAME TO insider_transactions;"),
         
        # --- Adicionar outras padronizações aqui, se necessário ---
        # Ex: ("Renomeando coluna 'data' para 'date' em 'portfolio_history'",
        #      "ALTER TABLE IF EXISTS public.portfolio_history RENAME COLUMN data TO date;")
    ]
    
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(get_db_connection_string())
        cur = conn.cursor()
        
        print("Executando migrações...")
        for description, command in migration_commands:
            try:
                print(f"  - {description}...", end='')
                cur.execute(command)
                print(" OK")
            except Exception as e:
                print(f" FALHOU: {e}")
                # Decide se quer parar ou continuar em caso de erro
                # raise e # Descomente para parar no primeiro erro
        
        conn.commit()
        print("Migrações executadas com sucesso!")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Ocorreu um erro durante a migração: {e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()
        print("--- SCRIPT DE MIGRAÇÃO CONCLUÍDO ---")

if __name__ == "__main__":
    run_migration()
