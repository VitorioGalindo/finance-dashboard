import os
import pandas as pd
from sqlalchemy import create_engine, text
import requests
import zipfile
import io
from dotenv import load_dotenv
from datetime import datetime
import psycopg2 # Importar psycopg2 para a conexão direta

def get_db_connection_string():
    """Lê as credenciais do .env e cria uma string de conexão para o RDS."""
    load_dotenv()
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    dbname = os.getenv("DB_NAME", "postgres")
    if not all([user, password, host, dbname]):
        raise ValueError("Credenciais do banco de dados (DB_USER, DB_PASSWORD, DB_HOST, DB_NAME) não encontradas nas variáveis de ambiente ou arquivo .env")
    
    # Retorna a string de conexão base
    return f"postgresql://{user}:{password}@{host}/{dbname}?sslmode=require"

def run_company_list_pipeline():
    """
    Baixa os dados cadastrais (FCA) da CVM, filtra as empresas listadas
    com ações na bolsa e salva uma lista mestra nas tabelas companies e tickers.
    """
    print("--- INICIANDO PIPELINE DE CARGA DE EMPRESAS E TICKERS ---")
    
    # Obtém a string de conexão base
    base_connection_str = get_db_connection_string()
    
    conn = None
    cur = None

    ano_atual = datetime.now().year
    url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_{ano_atual}.zip"
    arquivo_csv = f"fca_cia_aberta_valor_mobiliario_{ano_atual}.csv"

    print(f"Baixando dados cadastrais de: {url}")
    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()

        zip_buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buffer) as z:
            if arquivo_csv not in z.namelist():
                raise FileNotFoundError(f"Arquivo '{arquivo_csv}' não encontrado no ZIP.")

            with z.open(arquivo_csv) as f:
                # Lendo CSV com encoding='latin-1' e dtype=str, que já sabemos que funciona
                df = pd.read_csv(f, sep=';', encoding='latin-1', dtype=str)

        print("Dados extraídos com sucesso. Aplicando filtros...")

        # --- Aplicação dos seus filtros ---
        df_filtrado = df[
            (df['Codigo_Negociacao'].notna()) &
            (df['Codigo_Negociacao'] != 'N/A') &
            (df['Mercado'].str.contains("Bolsa", case=False, na=False)) &
            (df['Valor_Mobiliario'].str.contains("Ações|Units|BDRs", case=False, na=False))
        ].copy()

        print(f"Encontrados {len(df_filtrado)} valores mobiliários listados após filtro.")

        # --- Carga para o banco de dados (tabelas companies e tickers) ---
        print("Carregando dados nas tabelas companies e tickers...")
        
        # Conecta ao banco de dados, especificando client_encoding=latin1 na conexão psycopg2
        # Isso informa ao PostgreSQL que os dados que estamos ENVIANDO são latin1
        # para que ele possa convertê-los corretamente para UTF8 (seu DB default)
        conn = psycopg2.connect(f"{base_connection_str}&client_encoding=latin1")
        cur = conn.cursor()

        # Iterar sobre as linhas do DataFrame filtrado
        for index, row in df_filtrado.iterrows():
            cnpj = str(row['CNPJ_Companhia']).replace('.', '').replace('/', '').replace('-', '')
            nome_emp_original = row['Nome_Empresarial']
            codigo_neg = row['Codigo_Negociacao'].strip()

            if not cnpj or not codigo_neg:
                continue

            # Tentar converter o nome da empresa para UTF-8, substituindo caracteres problemáticos
            nome_emp_cleaned = nome_emp_original
            if nome_emp_original:
                try:
                    nome_emp_cleaned = nome_emp_original.encode('latin1').decode('utf-8', errors='replace')
                except Exception as e:
                    print(f"Erro ao forçar UTF-8 para '{nome_emp_original}': {e}. Usando original com cuidado.")
                    # Fallback para o original se a conversão falhar, mas isso pode levar ao erro de DB
                    # Idealmente, você investigaria esses casos específicos ou limparia ainda mais.
                    nome_emp_cleaned = nome_emp_original
            
            try:
                # Inserir/Atualizar na tabela companies
                cur.execute(
                    """
                    INSERT INTO companies (cnpj, name, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW())
                    ON CONFLICT (cnpj) DO NOTHING;
                    """,
                    (cnpj, nome_emp_cleaned) # <-- Usar a versão limpa aqui
                )

                # Inserir na tabela tickers
                cur.execute(
                    """
                    INSERT INTO tickers (ticker, company_cnpj, is_active, created_at, updated_at)
                    VALUES (%s, %s, TRUE, NOW(), NOW())
                    ON CONFLICT (ticker) DO NOTHING;
                    """,
                    (codigo_neg, cnpj)
                )
                
                # Commitar cada linha para ver o progresso, ou commitar em lotes para performance
                conn.commit() 

            except Exception as e:
                print(f"Erro ao processar CNPJ {cnpj} e Ticker {codigo_neg}: {e}")
                conn.rollback() # Rollback da transação atual em caso de erro

        print("--- CARGA DE EMPRESAS E TICKERS CONCLUÍDA COM SUCESSO! ---")

    except FileNotFoundError as e:
         print(f"Erro de arquivo: {e}")
    except requests.exceptions.RequestException as e:
         print(f"Erro ao baixar dados: {e}")
    except zipfile.BadZipFile:
         print("Erro: Arquivo baixado não é um ZIP válido.")
    except Exception as e:
        print(f"Ocorreu um erro no pipeline: {e}")

    finally:
        # Fechar cursor e conexão
        if cur:
            cur.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    run_company_list_pipeline()
