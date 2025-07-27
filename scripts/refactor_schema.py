# scripts/refactor_schema.py (Versão 2 - Corrigida para usar a tabela original 'cvm_dados_financeiros')
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
    """Executa os comandos SQL para refatorar o esquema do banco de dados."""
    print("--- INICIANDO SCRIPT DE MIGRAÇÃO PARA O ESQUEMA ESTRUTURADO ---")
    
    conn_str = get_db_connection_string()
    conn = None
    
    commands = {
        "1_prepare_environment": [
            ("Desabilitando triggers", "SET session_replication_role = 'replica';"),
        ],
        "2_create_new_tables": [
            ("Criando nova tabela 'financial_reports'",
             """
             CREATE TABLE IF NOT EXISTS public.financial_reports (
                 id BIGSERIAL PRIMARY KEY,
                 company_cnpj VARCHAR(20) NOT NULL REFERENCES public.companies(cnpj),
                 year INTEGER NOT NULL,
                 period VARCHAR(20) NOT NULL,
                 report_type VARCHAR(50) NOT NULL,
                 UNIQUE (company_cnpj, year, period, report_type)
             );
             """),
            # ... (outras criações de tabela, que já funcionaram)
        ],
        "3_refactor_financial_statements": [
            ("Renomeando tabela 'cvm_dados_financeiros' para 'old_financial_statements'",
             "ALTER TABLE IF EXISTS public.cvm_dados_financeiros RENAME TO old_financial_statements;"), # CORREÇÃO AQUI
            
            ("Criando a nova tabela 'financial_statements' estruturada",
             """
             CREATE TABLE IF NOT EXISTS public.financial_statements (
                 id BIGSERIAL PRIMARY KEY,
                 report_id BIGINT NOT NULL REFERENCES public.financial_reports(id) ON DELETE CASCADE,
                 statement_type VARCHAR(50) NOT NULL,
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
                 cnpj_cia, -- CORREÇÃO: Usando nome da coluna original
                 EXTRACT(YEAR FROM dt_fim_exerc)::INTEGER, -- CORREÇÃO: Usando nome da coluna original
                 periodo, -- CORREÇÃO: Usando nome da coluna original
                 tipo_demonstracao -- CORREÇÃO: Usando nome da coluna original
             FROM public.old_financial_statements
             WHERE cnpj_cia IS NOT NULL AND dt_fim_exerc IS NOT NULL AND periodo IS NOT NULL AND tipo_demonstracao IS NOT NULL
             ON CONFLICT (company_cnpj, year, period, report_type) DO NOTHING;
             """),
            
            ("Migrando dados para a nova 'financial_statements'",
             """
             INSERT INTO public.financial_statements (report_id, statement_type, account_code, account_description, account_value)
             SELECT
                 fr.id,
                 ofs.tipo_demonstracao, -- CORREÇÃO: Usando nome da coluna original
                 ofs.cd_conta, -- CORREÇÃO: Usando nome da coluna original
                 ofs.ds_conta, -- CORREÇÃO: Usando nome da coluna original
                 ofs.vl_conta -- CORREÇÃO: Usando nome da coluna original
             FROM public.old_financial_statements AS ofs
             JOIN public.financial_reports AS fr
                 ON ofs.cnpj_cia = fr.company_cnpj
                 AND EXTRACT(YEAR FROM ofs.dt_fim_exerc)::INTEGER = fr.year
                 AND ofs.periodo = fr.period
                 AND ofs.tipo_demonstracao = fr.report_type;
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
                        conn.rollback()
                        raise e

        conn.commit()
        print("🎉 Migração de esquema concluída com sucesso!")

    except Exception as e:
        print("❌ ERRO FATAL DURANTE A MIGRAÇÃO. O processo foi interrompido.")
    finally:
        if conn:
            conn.close()
        print("--- SCRIPT DE MIGRAÇÃO CONCLUÍDO ---")

if __name__ == "__main__":
    run_migration()
