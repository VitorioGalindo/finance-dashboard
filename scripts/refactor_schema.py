# scripts/refactor_schema.py (VERSÃO FINAL - Baseada na inspeção do DB)
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
        raise ValueError("Credenciais do banco de dados não encontradas.")
    return f"postgresql://{user}:{password}@{host}/{dbname}?sslmode=require"

def run_migration():
    """Executa os comandos SQL para criar a arquitetura final e padronizada do banco de dados."""
    print("--- INICIANDO SCRIPT FINAL DE REATORAÇÃO DE ESQUEMA ---")
    
    conn_str = get_db_connection_string()
    conn = None
    
    commands = {
        "1_cleanup_obsolete_tables": [
            ("Limpando tabelas antigas ou não padronizadas (se existirem)",
             """
             DROP TABLE IF EXISTS public.old_financial_statements CASCADE;
             DROP TABLE IF EXISTS public.generic_transactions CASCADE;
             DROP TABLE IF EXISTS public.cvm_dados_financeiros CASCADE;
             """),
        ],
        "2_standardize_existing_tables": [
            ("Padronizando colunas da tabela 'portfolio_config'",
             """
             DO $$
             BEGIN
                IF EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='portfolio_config' AND column_name='quantidade') THEN
                    ALTER TABLE public.portfolio_config RENAME COLUMN quantidade TO quantity;
                END IF;
                IF EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='portfolio_config' AND column_name='posicao_alvo') THEN
                    ALTER TABLE public.portfolio_config RENAME COLUMN posicao_alvo TO target_weight;
                END IF;
             END $$;
             """),
            ("Padronizando colunas da tabela 'portfolio_history'",
             """
             DO $$
             BEGIN
                IF EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='portfolio_history' AND column_name='data') THEN
                    ALTER TABLE public.portfolio_history RENAME COLUMN data TO event_date;
                END IF;
             END $$;
             """),
        ],
        "3_create_structured_financial_tables": [
            ("Recriando a tabela 'financial_reports' (garantindo limpeza)",
             """
             DROP TABLE IF EXISTS public.financial_reports CASCADE;
             CREATE TABLE public.financial_reports (
                 id BIGSERIAL PRIMARY KEY,
                 company_cnpj VARCHAR(20) NOT NULL REFERENCES public.companies(cnpj),
                 year INTEGER NOT NULL,
                 period VARCHAR(20) NOT NULL, -- Ex: 'ANUAL' ou 'TRIMESTRAL'
                 report_type VARCHAR(50) NOT NULL, -- Ex: 'DFP' ou 'ITR'
                 UNIQUE (company_cnpj, year, period, report_type)
             );
             """),
            ("Recriando a tabela 'financial_statements' (garantindo limpeza)",
             """
             DROP TABLE IF EXISTS public.financial_statements CASCADE;
             CREATE TABLE public.financial_statements (
                 id BIGSERIAL PRIMARY KEY,
                 report_id BIGINT NOT NULL REFERENCES public.financial_reports(id) ON DELETE CASCADE,
                 statement_type VARCHAR(50) NOT NULL, -- Ex: 'DRE', 'BPA', 'BPP', 'DFC'
                 account_code VARCHAR(30) NOT NULL,
                 account_description TEXT,
                 account_value NUMERIC(20, 2) NOT NULL,
                 UNIQUE(report_id, statement_type, account_code)
             );
             """),
            ("Recriando a tabela 'company_financial_ratios' (garantindo limpeza)",
             """
             DROP TABLE IF EXISTS public.company_financial_ratios CASCADE;
             CREATE TABLE public.company_financial_ratios (
                 id BIGSERIAL PRIMARY KEY,
                 report_id BIGINT NOT NULL REFERENCES public.financial_reports(id),
                 ratio_name VARCHAR(50) NOT NULL,
                 ratio_value NUMERIC(20, 4) NOT NULL,
                 UNIQUE (report_id, ratio_name)
             );
             """),
        ]
    }
    
    try:
        conn = psycopg2.connect(conn_str)
        
        for stage, commands_list in commands.items():
            print(f"--- EXECUTANDO ESTÁGIO: {stage} ---")
            with conn.cursor() as cur:
                for description, command in commands_list:
                    try:
                        print(f"  - {description}...", end='', flush=True)
                        cur.execute(command)
                        print(" OK")
                    except Exception as e:
                        print(f" FALHOU: {e.pgcode if hasattr(e, 'pgcode') else ''} {e.pgerror if hasattr(e, 'pgerror') else str(e).strip()}")
                        conn.rollback()
                        raise e
        conn.commit()
        print("🎉 Refatoração de esquema concluída com sucesso!")

    except Exception as e:
        print("❌ ERRO FATAL DURANTE A REATORAÇÃO. O processo foi interrompido.")
    finally:
        if conn:
            conn.close()
        print("--- SCRIPT DE REATORAÇÃO CONCLUÍDO ---")

if __name__ == "__main__":
    run_migration()
