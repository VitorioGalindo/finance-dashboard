import pandas as pd
import psycopg2
import os
import requests
import zipfile
import io

# ... (as configurações de DB_HOST, URL, etc. continuam as mesmas) ...
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'your_db')
DB_USER = os.environ.get('DB_USER', 'your_user')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'your_password')

CVM_YEAR = 2025 
cvm_zip_url = f'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_{CVM_YEAR}.zip'
csv_file_name = f'fca_cia_aberta_valor_mobiliario_{CVM_YEAR}.csv'


def download_and_extract_csv(url, csv_name):
    # ... (esta função já está correta, não precisa de mudanças) ...
    print(f"Baixando arquivo ZIP da CVM: {url}")
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            if csv_name in z.namelist():
                print(f"Extraindo {csv_name}")
                extracted_path = z.extract(csv_name)
                return extracted_path
            else:
                print(f"Erro: Arquivo {csv_name} não encontrado dentro do ZIP.")
                return None
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar o arquivo: {e}")
        return None
    except zipfile.BadZipFile:
        print("Erro: Arquivo baixado não é um ZIP válido.")
        return None
    except Exception as e:
        print(f"Ocorreu um erro durante download/extração: {e}")
        return None


def load_companies_and_tickers(csv_file_path):
    """Carrega dados do CSV para as tabelas companies e tickers."""
    conn_params = {
        'host': DB_HOST,
        'database': DB_NAME,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'client_encoding': 'utf8' 
    }
    
    try:
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                print("Conexão com o banco de dados estabelecida.")

                try:
                    # ================== A CORREÇÃO ESTÁ AQUI ==================
                    # Trocamos 'latin-1' por 'cp1252', que é mais provável para
                    # arquivos gerados em sistemas Windows no Brasil.
                    df = pd.read_csv(csv_file_path, sep=';', encoding='cp1252', dtype=str)
                    # ==========================================================
                    
                    print(f"Arquivo CSV '{csv_file_path}' lido com sucesso usando codificação 'cp1252'.")
                
                except FileNotFoundError:
                    print(f"Erro: Arquivo CSV não encontrado em {csv_file_path}")
                    return
                except Exception as e:
                    print(f"Erro ao ler arquivo CSV: {e}")
                    return

                print(f"Processando {len(df)} linhas do arquivo CSV...")

                for index, row in df.iterrows():
                    cnpj = ''.join(filter(str.isdigit, str(row.get('CNPJ_Companhia', ''))))
                    nome_emp = row.get('Nome_Empresarial')
                    codigo_neg = row.get('Codigo_Negociacao')

                    if not cnpj or not nome_emp:
                        continue
                    
                    cur.execute(
                        """
                        INSERT INTO companies (cnpj, name, created_at, updated_at)
                        VALUES (%s, %s, NOW(), NOW())
                        ON CONFLICT (cnpj) DO UPDATE SET name = EXCLUDED.name, updated_at = NOW();
                        """,
                        (cnpj, nome_emp)
                    )
                    
                    if pd.notna(codigo_neg) and codigo_neg.strip():
                        cur.execute(
                            """
                            INSERT INTO tickers (ticker, company_cnpj, is_active, created_at, updated_at)
                            VALUES (%s, %s, TRUE, NOW(), NOW())
                            ON CONFLICT (ticker) DO NOTHING;
                            """,
                            (codigo_neg.strip(), cnpj)
                        )
                
                print(f"Carga de dados de empresas e tickers concluída com sucesso.")

    except psycopg2.Error as e:
        print(f"Erro de banco de dados: {e}")
    except Exception as e:
        # A mensagem de erro que você viu veio daqui
        print(f"Ocorreu um erro inesperado: {e}")


if __name__ == "__main__":
    downloaded_csv_path = download_and_extract_csv(cvm_zip_url, csv_file_name)
    if downloaded_csv_path:
        load_companies_and_tickers(downloaded_csv_path)
        try:
            os.remove(downloaded_csv_path)
            print(f"Arquivo temporário {downloaded_csv_path} removido.")
        except OSError as e:
            print(f"Erro ao remover arquivo temporário {downloaded_csv_path}: {e}")