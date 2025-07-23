import os
import pandas as pd
import requests
import zipfile
import io
from dotenv import load_dotenv
from datetime import datetime
import psycopg2

def get_db_connection_string():
    """Lê as credenciais do .env e cria uma string de conexão para o RDS."""
    load_dotenv()
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    dbname = os.getenv("DB_NAME", "postgres")
    if not all([user, password, host, dbname]):
        raise ValueError("Credenciais do banco (DB_USER, DB_PASSWORD, DB_HOST, DB_NAME) não encontradas.")
    
    # Retorna a string de conexão base, sem forçar codificação.
    return f"postgresql://{user}:{password}@{host}/{dbname}?sslmode=require"

def run_company_list_pipeline():
    """
    Baixa, filtra e carrega os dados da CVM para as tabelas companies e tickers,
    lidando corretamente com a codificação.
    """
    print("--- INICIANDO PIPELINE DE CARGA DE EMPRESAS E TICKERS ---")
    
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
                # PASSO 1: Ler o CSV como latin-1 para obter strings Python corretas.
                df = pd.read_csv(f, sep=';', encoding='latin-1', dtype=str)

        print("Dados extraídos com sucesso. Aplicando filtros...")

        df_filtrado = df[
            (df['Codigo_Negociacao'].notna()) &
            (df['Codigo_Negociacao'] != 'N/A') &
            (df['Mercado'].str.contains("Bolsa", case=False, na=False)) &
            (df['Valor_Mobiliario'].str.contains("Ações|Units|BDRs", case=False, na=False))
        ].copy()

        print(f"Encontrados {len(df_filtrado)} valores mobiliários listados após filtro.")

        print("Carregando dados nas tabelas companies e tickers...")
        
        # PASSO 2: Conectar ao DB UTF-8 da maneira padrão.
        # O psycopg2 irá, por padrão, lidar com a conversão das strings Python para UTF-8.
        conn = psycopg2.connect(base_connection_str)
        cur = conn.cursor()

        for index, row in df_filtrado.iterrows():
            cnpj = str(row['CNPJ_Companhia']).replace('.', '').replace('/', '').replace('-', '')
            # A string nome_emp já está correta após a leitura do CSV com latin-1
            nome_emp = row['Nome_Empresarial'] 
            codigo_neg = row['Codigo_Negociacao'].strip()

            if not cnpj or not codigo_neg or not nome_emp:
                continue
            
            try:
                # PASSO 3: Inserir a string Python diretamente. Sem encode/decode aqui.
                cur.execute(
                    """
                    INSERT INTO companies (cnpj, name, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW())
                    ON CONFLICT (cnpj) DO NOTHING;
                    """,
                    (cnpj, nome_emp) # Usar a variável diretamente
                )

                cur.execute(
                    """
                    INSERT INTO tickers (ticker, company_cnpj, is_active, created_at, updated_at)
                    VALUES (%s, %s, TRUE, NOW(), NOW())
                    ON CONFLICT (ticker) DO NOTHING;
                    """,
                    (codigo_neg, cnpj)
                )
                
                conn.commit() 

            except Exception as e:
                print(f"Erro ao processar CNPJ {cnpj} e Ticker {codigo_neg}: {e}")
                conn.rollback()

        print("--- CARGA DE EMPRESAS E TICKERS CONCLUÍDA COM SUCESSO! ---")

    except Exception as e:
        print(f"Ocorreu um erro no pipeline: {e}")

    finally:
        if cur: cur.close()
        if conn: conn.close()

if __name__ == "__main__":
    run_company_list_pipeline()
