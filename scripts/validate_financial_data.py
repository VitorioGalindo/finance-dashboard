# scripts/validate_financial_data.py
import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine

def get_db_connection_string():
    """Lê as credenciais do .env e cria uma string de conexão SQLAlchemy."""
    load_dotenv()
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    dbname = os.getenv("DB_NAME", "postgres")
    if not all([user, password, host, dbname]):
        raise ValueError("Credenciais do banco de dados não encontradas.")
    return f"postgresql+psycopg2://{user}:{password}@{host}/{dbname}?sslmode=require"

def print_header(title):
    print("" + "=" * 60)
    print(f"📊 {title}")
    print("=" * 60)

def validate_financial_data():
    """Conecta ao DB e gera um relatório sobre a qualidade dos dados financeiros."""
    print_header("INICIANDO VALIDAÇÃO DOS DADOS FINANCEIROS ESTRUTURADOS")
    
    try:
        engine = create_engine(get_db_connection_string())
        with engine.connect() as connection:
            
            # --- Análise da Tabela `financial_reports` ---
            print_header("Análise da Tabela: financial_reports")
            
            total_reports = pd.read_sql("SELECT COUNT(*) FROM financial_reports;", connection).iloc[0,0]
            if total_reports == 0:
                print("❌ A tabela 'financial_reports' está vazia. O ETL pode não ter inserido dados.")
                return
            print(f"Total de Relatórios Registrados: {total_reports}")

            # Contagem por ano
            print("Contagem de Relatórios por Ano (Top 5):")
            reports_by_year_sql = """
            SELECT year, COUNT(*) as count
            FROM financial_reports
            GROUP BY year
            ORDER BY year DESC
            LIMIT 5;
            """
            df_year = pd.read_sql(reports_by_year_sql, connection)
            print(df_year.to_string(index=False))

            # Contagem por tipo de relatório
            print("Contagem de Relatórios por Tipo:")
            reports_by_type_sql = """
            SELECT report_type, period, COUNT(*) as count
            FROM financial_reports
            GROUP BY report_type, period
            ORDER BY count DESC;
            """
            df_type = pd.read_sql(reports_by_type_sql, connection)
            print(df_type.to_string(index=False))

            # --- Análise da Tabela `financial_statements` ---
            print_header("Análise da Tabela: financial_statements")
            total_statements = pd.read_sql("SELECT COUNT(*) FROM financial_statements;", connection).iloc[0,0]
            if total_statements == 0:
                print("❌ A tabela 'financial_statements' está vazia.")
                return
            print(f"Total de Linhas de Demonstrativos: {total_statements} (aprox. {total_statements / 1000000:.2f} milhões)")

            # Contagem por tipo de demonstrativo
            print("Contagem de Linhas por Tipo de Demonstrativo (Top 10):")
            statements_by_type_sql = """
            SELECT statement_type, COUNT(*) as count
            FROM financial_statements
            GROUP BY statement_type
            ORDER BY count DESC
            LIMIT 10;
            """
            df_stmt_type = pd.read_sql(statements_by_type_sql, connection)
            print(df_stmt_type.to_string(index=False))

            # --- Análise Cruzada: Empresas com Mais Relatórios ---
            print_header("Top 10 Empresas por Número de Relatórios")
            top_companies_sql = """
            SELECT c.name, COUNT(fr.id) as report_count
            FROM financial_reports fr
            JOIN companies c ON fr.company_cnpj = c.cnpj
            GROUP BY c.name
            ORDER BY report_count DESC
            LIMIT 10;
            """
            df_top_companies = pd.read_sql(top_companies_sql, connection)
            print(df_top_companies.to_string(index=False))

    except Exception as e:
        print(f"❌ Ocorreu um erro durante a validação: {e}")
    finally:
        print("" + "=" * 60)
        print("✅ VALIDAÇÃO CONCLUÍDA")
        print("=" * 60)

if __name__ == "__main__":
    validate_financial_data()
