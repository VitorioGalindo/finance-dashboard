# scripts/find_bad_encoding.py
import os
from dotenv import load_dotenv
import psycopg2
import sys

def get_db_connection_string():
    """Lê as credenciais do .env e cria uma string de conexão para o RDS."""
    load_dotenv()
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    dbname = os.getenv("DB_NAME", "postgres")
    if not all([user, password, host, dbname]):
        raise ValueError("Credenciais do banco de dados não encontradas.")
    
    return f"postgresql://{user}:{password}@{host}/{dbname}?sslmode=require"

def find_bad_encoding_company():
    """Conecta ao DB e itera sobre a tabela 'companies' para encontrar erros de codificação."""
    print("--- INICIANDO SCRIPT DE DIAGNÓSTICO DE CODIFICAÇÃO ---")
    
    conn = None
    cur = None
    
    try:
        # Conecta ao DB com a codificação padrão (UTF-8)
        conn = psycopg2.connect(get_db_connection_string())
        cur = conn.cursor()
        
        print("Executando query: SELECT cnpj, name FROM companies;")
        cur.execute("SELECT cnpj, name FROM companies;")
        
        row_count = 0
        while True:
            row = cur.fetchone()
            if row is None:
                break
            
            row_count += 1
            cnpj, name = row
            
            try:
                # A exceção de codificação acontece quando o Python tenta
                # processar a string recebida do banco.
                print(f"OK [{row_count}]: CNPJ={cnpj}, Name='{name}'")
            except UnicodeDecodeError as e:
                # CORREÇÃO: Usando aspas triplas para strings multi-linha
                print("""
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!""")
                print("!!! ERRO DE CODIFICAÇÃO ENCONTRADO!")
                print(f"!!! CNPJ Problemático: {cnpj}")
                print(f"!!! Detalhe do Erro: {e}")
                # CORREÇÃO: Usando aspas triplas para strings multi-linha
                print("""!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
""")
                # Tenta mostrar os bytes brutos para análise
                try:
                    print(f"Bytes brutos do nome: {name.encode('latin1')}")
                except:
                    pass
                break # Para no primeiro erro

    except Exception as e:
        # CORREÇÃO: Usando aspas triplas para strings multi-linha
        print(f"""
Ocorreu um erro durante o processo: {e}""")
    finally:
        if cur: cur.close()
        if conn: conn.close()
        print("--- SCRIPT DE DIAGNÓSTICO CONCLUÍDO ---")

if __name__ == "__main__":
    find_bad_encoding_company()