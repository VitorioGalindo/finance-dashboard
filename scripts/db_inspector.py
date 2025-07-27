# scripts/db_inspector.py (Versão Corrigida)
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
import pandas as pd
import sys

def get_db_connection_string():
    """Lê as credenciais do .env e cria uma string de conexão SQLAlchemy."""
    load_dotenv()
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    dbname = os.getenv("DB_NAME", "postgres")
    if not all([user, password, host, dbname]):
        raise ValueError("Credenciais do banco (DB_USER, DB_PASSWORD, DB_HOST, DB_NAME) não encontradas.")
    
    return f"postgresql+psycopg2://{user}:{password}@{host}/{dbname}?sslmode=require"

def inspect_database():
    """Conecta ao banco de dados e imprime sua estrutura detalhada."""
    print("--- INICIANDO SCRIPT DE INSPEÇÃO DO BANCO DE DADOS (VERSÃO CORRIGIDA) ---")
    
    try:
        engine = create_engine(get_db_connection_string())
        inspector = inspect(engine)
        
        with engine.connect() as connection:
            print(f"Dialeto do Banco: {connection.dialect.name}")
            server_version = connection.execute(text("SELECT version();")).scalar()
            print(f"Versão do Servidor: {server_version}")

        schemas = inspector.get_schema_names()
        print(f"Esquemas encontrados: {schemas}")

        for schema in schemas:
            if schema.startswith('pg_') or schema == 'information_schema':
                continue

            print(f"{'='*30} ESQUEMA: {schema.upper()} {'='*30}")
            tables = sorted(inspector.get_table_names(schema=schema))
            print(f"Tabelas encontradas: {tables}")

            for table_name in tables:
                print(f"--- Tabela: {schema}.{table_name} ---")
                
                try:
                    pk_constraint = inspector.get_pk_constraint(table_name, schema=schema)
                    pk_columns = pk_constraint.get('constrained_columns', [])
                    print(f"  Chave Primária: {pk_columns if pk_columns else 'N/A'}")

                    print("  Estrutura das Colunas:")
                    columns = inspector.get_columns(table_name, schema=schema)
                    for column in columns:
                        # CORREÇÃO: Converte o tipo da coluna para string antes de formatar
                        column_type_str = str(column['type'])
                        col_info = (
                            f"    - Nome: {column['name']:<25} | "
                            f"Tipo: {column_type_str:<20} | "
                            f"Nulável: {column['nullable']:<5} | "
                            f"Default: {column['default']}"
                        )
                        print(col_info)
                    
                    foreign_keys = inspector.get_foreign_keys(table_name, schema=schema)
                    if foreign_keys:
                        print("  Chaves Estrangeiras:")
                        for fk in foreign_keys:
                            fk_info = (
                                f"    - Coluna(s) local: {fk['constrained_columns']} "
                                f"-> Refere-se a: {fk['referred_table']}.{fk['referred_columns'][0]}"
                            )
                            print(fk_info)
                    else:
                        print("  Chaves Estrangeiras: Nenhuma")

                except Exception as table_e:
                    print(f"  ERRO ao inspecionar a estrutura da tabela {table_name}: {table_e}")

    except Exception as e:
        print(f"Ocorreu um erro fatal durante a inspeção: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        print(f"{'='*70}--- SCRIPT DE INSPEÇÃO CONCLUÍDO ---{'='*70}")

if __name__ == "__main__":
    inspect_database()
