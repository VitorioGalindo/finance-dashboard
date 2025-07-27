# scripts/db_inspector.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
import pandas as pd

def get_db_connection_string():
    """Lê as credenciais do .env e cria uma string de conexão SQLAlchemy."""
    load_dotenv()
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    dbname = os.getenv("DB_NAME", "postgres")
    if not all([user, password, host, dbname]):
        raise ValueError("Credenciais do banco (DB_USER, DB_PASSWORD, DB_HOST, DB_NAME) não encontradas.")
    
    # Retorna a string de conexão para SQLAlchemy
    return f"postgresql+psycopg2://{user}:{password}@{host}/{dbname}?sslmode=require"

def inspect_database():
    """Conecta ao banco de dados e imprime sua estrutura e amostras de dados."""
    print("--- INICIANDO SCRIPT DE INSPEÇÃO DO BANCO DE DADOS ---")
    
    try:
        engine = create_engine(get_db_connection_string())
        inspector = inspect(engine)
        schemas = inspector.get_schema_names()

        print(f"Esquemas encontrados: {schemas}")

        for schema in schemas:
            if schema in ['information_schema', 'pg_catalog', 'pg_toast']:
                continue # Pula esquemas internos do PostgreSQL

            print(f"{'='*20} ESQUEMA: {schema.upper()} {'='*20}")
            tables = inspector.get_table_names(schema=schema)
            print(f"Tabelas encontradas: {tables}")

            for table_name in tables:
                print(f"--- Tabela: {schema}.{table_name} ---")
                
                # Imprime informações das colunas
                print("Estrutura das Colunas:")
                columns = inspector.get_columns(table_name, schema=schema)
                for column in columns:
                    col_info = (
                        f"  - Nome: {column['name']}, "
                        f"Tipo: {column['type']}, "
                        f"Nulável: {column['nullable']}, "
                        f"Chave Primária: {column['primary_key']}"
                    )
                    print(col_info)
                
                # Imprime informações de chaves estrangeiras
                foreign_keys = inspector.get_foreign_keys(table_name, schema=schema)
                if foreign_keys:
                    print("Chaves Estrangeiras:")
                    for fk in foreign_keys:
                        fk_info = (
                            f"  - Coluna(s) local: {fk['constrained_columns']} "
                            f"-> Refere-se a: {fk['referred_table']}.{fk['referred_columns'][0]}"
                        )
                        print(fk_info)

                # Busca e imprime as 5 primeiras linhas da tabela
                print("Amostra de Dados (5 primeiras linhas):")
                try:
                    with engine.connect() as connection:
                        # Usamos text() para garantir que o nome da tabela seja tratado corretamente
                        query = text(f'SELECT * FROM "{schema}"."{table_name}" LIMIT 5;')
                        df_sample = pd.read_sql(query, connection)
                        
                        if df_sample.empty:
                            print("  (A tabela está vazia)")
                        else:
                            # Imprime o DataFrame como uma string formatada
                            print(df_sample.to_string())
                except Exception as e:
                    print(f"  ERRO ao buscar amostra de dados para a tabela {table_name}: {e}")

    except Exception as e:
        print(f"
Ocorreu um erro durante a inspeção: {e}")
    finally:
        print(f"{'='*50}--- SCRIPT DE INSPEÇÃO CONCLUÍDO ---{'='*50}")

if __name__ == "__main__":
    inspect_database()
