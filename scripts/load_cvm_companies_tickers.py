import os
import pandas as pd
from sqlalchemy import create_engine, text
import requests
import zipfile
import io
from dotenv import load_dotenv
from datetime import datetime
import psycopg2 # Importar psycopg2 para o caso de usar cursor diretamente

def get_db_engine_vm():
    """Lê as credenciais do .env e cria uma engine de conexão para o RDS."""
    load_dotenv()
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    dbname = os.getenv("DB_NAME", "postgres")
    if not all([user, password, host]):
        raise ValueError("Credenciais do banco não encontradas no arquivo .env")
    # Usando psycopg2 diretamente para a connection string para melhor compatibilidade
    conn_str = f"postgresql://{user}:{password}@{host}/{dbname}?sslmode=require"
    # Podemos usar create_engine para outras operações se necessário, mas para inserts em loop, psycopg2 é comum.
    # Vamos retornar a connection string e usar psycopg2.connect diretamente na função de carga.
    return conn_str

def run_company_list_pipeline():
    """
    Baixa os dados cadastrais (FCA) da CVM, filtra as empresas listadas
    com ações na bolsa e salva uma lista mestra nas tabelas companies e tickers.
    """
    print("--- INICIANDO PIPELINE DE CARGA DE EMPRESAS E TICKERS ---")
    
    # Obtém a connection string do banco
    db_connection_str = get_db_engine_vm()
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

        conn = psycopg2.connect(db_connection_str)
        cur = conn.cursor()

        # Iterar sobre as linhas do DataFrame filtrado
        for index, row in df_filtrado.iterrows():
            cnpj = str(row['CNPJ_Companhia']).replace('.', '').replace('/', '').replace('-', '')
            nome_emp = row['Nome_Empresarial']
            codigo_neg = row['Codigo_Negociacao'].strip()

            if not cnpj or not codigo_neg:
                # print(f"Skipping row {index}: CNPJ or Ticker is empty.")
                continue

            try:
                # Inserir/Atualizar na tabela companies
                cur.execute(
                    """
                    INSERT INTO companies (cnpj, name, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW())
                    ON CONFLICT (cnpj) DO NOTHING;
                    """,
                    (cnpj, nome_emp)
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
