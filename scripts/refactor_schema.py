# scripts/refactor_schema.py
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

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
    """Executa os comandos SQL para refatorar o esquema do banco de dados."""
    print("--- INICIANDO SCRIPT DE MIGRAÇÃO PARA O ESQUEMA ESTRUTURADO ---")
    
    conn_str = get_db_connection_string()
    conn = None
    
    # Comandos são separados em blocos lógicos
    commands = {
        "1_prepare_environment": [
            ("Desabilitando triggers (se houver) para performance", "SET session_replication_role = 'replica';"),
        ],
        "2_create_new_tables": [
            ("Criando nova tabela 'financial_reports'",
             """
             CREATE TABLE IF NOT EXISTS public.financial_reports (
                 id BIGSERIAL PRIMARY KEY,
                 company_cnpj VARCHAR(14) NOT NULL REFERENCES public.companies(cnpj),
                 year INTEGER NOT NULL,
                 period VARCHAR(20) NOT NULL,
                 report_type VARCHAR(10) NOT NULL,
                 UNIQUE (company_cnpj, year, period, report_type)
             );
             """),
            ("Criando nova tabela 'company_financial_ratios'",
             """
             CREATE TABLE IF NOT EXISTS public.company_financial_ratios (
                 id BIGSERIAL PRIMARY KEY,
                 report_id BIGINT NOT NULL REFERENCES public.financial_reports(id),
                 ratio_name VARCHAR(50) NOT NULL,
                 ratio_value NUMERIC(20, 4) NOT NULL,
                 UNIQUE (report_id, ratio_name)
             );
             """),
            ("Criando nova tabela 'news_articles'",
             """
             CREATE TABLE IF NOT EXISTS public.news_articles (
                 id BIGSERIAL PRIMARY KEY,
                 source VARCHAR(100),
                 published_at TIMESTAMP WITH TIME ZONE,
                 url VARCHAR(512) UNIQUE,
                 title TEXT,
                 summary TEXT
             );
             """),
            ("Criando nova tabela de ligação 'news_company_link'",
             """
             CREATE TABLE IF NOT EXISTS public.news_company_link (
                 news_id BIGINT NOT NULL REFERENCES public.news_articles(id) ON DELETE CASCADE,
                 company_cnpj VARCHAR(14) NOT NULL REFERENCES public.companies(cnpj) ON DELETE CASCADE,
                 PRIMARY KEY (news_id, company_cnpj)
             );
             """),
        ],
        "3_refactor_financial_statements": [
            ("Renomeando tabela 'financial_statements' para 'old_financial_statements'",
             "ALTER TABLE IF EXISTS public.financial_statements RENAME TO old_financial_statements;"),
            
            ("Criando a nova tabela 'financial_statements' estruturada",
             """
             CREATE TABLE public.financial_statements (
                 id BIGSERIAL PRIMARY KEY,
                 report_id BIGINT NOT NULL REFERENCES public.financial_reports(id) ON DELETE CASCADE,
                 statement_type VARCHAR(10) NOT NULL, -- DRE, BPA, BPP, DFC
                 account_code VARCHAR(30) NOT NULL,
                 account_description TEXT,
                 account_value NUMERIC(20, 2) NOT NULL
             );
             """),
        ],
        "4_migrate_data": [
            ("Migrando dados para 'financial_reports'",
             """
             INSERT INTO public.financial_reports (company_cnpj, year, period, report_type)
             SELECT DISTINCT
                 company_cnpj,
                 EXTRACT(YEAR FROM fiscal_year_end)::INTEGER,
                 periodo,
                 CASE 
                     WHEN report_type IN ('BPA', 'BPP', 'DFC', 'DRE') THEN 'DFP' -- Simplificação, pode ser ajustado
                     ELSE report_type
                 END
             FROM public.old_financial_statements
             WHERE company_cnpj IS NOT NULL AND fiscal_year_end IS NOT NULL AND periodo IS NOT NULL
             ON CONFLICT (company_cnpj, year, period, report_type) DO NOTHING;
             """),
            
            ("Migrando dados para a nova 'financial_statements'",
             """
             INSERT INTO public.financial_statements (report_id, statement_type, account_code, account_description, account_value)
             SELECT
                 fr.id,
                 ofs.report_type,
                 ofs.account_code,
                 ofs.account_description,
                 ofs.account_value
             FROM public.old_financial_statements AS ofs
             JOIN public.financial_reports AS fr
                 ON ofs.company_cnpj = fr.company_cnpj
                 AND EXTRACT(YEAR FROM ofs.fiscal_year_end)::INTEGER = fr.year
                 AND ofs.periodo = fr.period;
             """),
        ],
        "5_cleanup": [
            ("Removendo a tabela antiga 'old_financial_statements'",
             "DROP TABLE IF EXISTS public.old_financial_statements;"),
            ("Reabilitando triggers", "SET session_replication_role = 'origin';"),
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
                        conn.rollback() # Desfaz a transação atual
                        raise e # Para a execução no primeiro erro

        conn.commit()
        print("🎉 Migração de esquema concluída com sucesso!")

    except Exception as e:
        print(f"❌ ERRO FATAL DURANTE A MIGRAÇÃO. O processo foi interrompido.")
    finally:
        if conn:
            conn.close()
        print("--- SCRIPT DE MIGRAÇÃO CONCLUÍDO ---")

if __name__ == "__main__":
    run_migration()
