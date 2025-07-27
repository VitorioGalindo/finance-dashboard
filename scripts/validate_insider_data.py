# scripts/validate_insider_data.py
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

def validate_insider_data():
    """Conecta ao DB e gera um relatório sobre a qualidade dos dados de insiders."""
    print_header("INICIANDO VALIDAÇÃO DOS DADOS DE INSIDERS")
    
    try:
        engine = create_engine(get_db_connection_string())
        with engine.connect() as connection:
            
            # --- Análise da Tabela `insider_transactions` ---
            print_header("Análise da Tabela: insider_transactions")
            
            # Contagem total de registros
            total_transactions = pd.read_sql("SELECT COUNT(*) FROM insider_transactions;", connection).iloc[0,0]
            if total_transactions == 0:
                print("❌ A tabela 'insider_transactions' está vazia. O ETL pode não ter inserido dados.")
                return # Encerra se não houver dados
            print(f"Total de Transações Registradas: {total_transactions}")
            
            # Análise de Nulos
            print("Análise de Valores Nulos (colunas importantes):")
            null_checks_sql = """
            SELECT
                COUNT(CASE WHEN price IS NULL THEN 1 END) AS null_price,
                COUNT(CASE WHEN volume IS NULL THEN 1 END) AS null_volume,
                COUNT(CASE WHEN asset_type IS NULL THEN 1 END) AS null_asset_type,
                COUNT(CASE WHEN operation_type IS NULL THEN 1 END) AS null_operation_type
            FROM insider_transactions;
            """
            df_nulls = pd.read_sql(null_checks_sql, connection)
            for col, count in df_nulls.iloc[0].items():
                percentage = (count / total_transactions) * 100
                print(f"  - {col:<20}: {count} nulos ({percentage:.2f}%)")

            # Distribuição por Tipo de Operação
            print("Distribuição por Tipo de Operação (Top 10):")
            operation_type_sql = """
            SELECT operation_type, COUNT(*) as count
            FROM insider_transactions
            GROUP BY operation_type
            ORDER BY count DESC
            LIMIT 10;
            """
            df_ops = pd.read_sql(operation_type_sql, connection)
            print(df_ops.to_string(index=False))

            # --- Análise da Tabela `insiders` ---
            print_header("Análise da Tabela: insiders")
            total_insiders = pd.read_sql("SELECT COUNT(*) FROM insiders;", connection).iloc[0,0]
            print(f"Total de Insiders Únicos Registrados: {total_insiders}")
            
            # --- Análise da Tabela `filings` ---
            print_header("Análise da Tabela: filings")
            total_filings = pd.read_sql("SELECT COUNT(*) FROM filings;", connection).iloc[0,0]
            print(f"Total de Documentos (Filings) Processados: {total_filings}")
            
            # --- Análise Cruzada: Empresas com Mais Transações ---
            print_header("Top 10 Empresas por Número de Transações de Insiders")
            top_companies_sql = """
            SELECT c.name, COUNT(it.id) as transaction_count
            FROM insider_transactions it
            JOIN filings f ON it.filing_id = f.id
            JOIN companies c ON f.company_cnpj = c.cnpj
            GROUP BY c.name
            ORDER BY transaction_count DESC
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
    validate_insider_data()
