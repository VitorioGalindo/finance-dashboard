import pandas as pd
import psycopg2
import os
import requests
import zipfile
import io

# Configurações do banco de dados (ajuste conforme o seu ambiente)
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

# URL do arquivo ZIP da CVM
cvm_zip_url = 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_2025.zip'
csv_file_name = 'fca_cia_aberta_valor_mobiliario_2025.csv'

def download_and_extract_csv(url, csv_name):
    """Baixa o arquivo ZIP e extrai o CSV."""
    print(f"Baixando arquivo ZIP da CVM: {url}")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status() # Levanta exceção para status codes ruins

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            if csv_name in z.namelist():
                print(f"Extraindo {csv_name}")
                # Extract to a specific path if needed, e.g., os.path.join(os.getcwd(), csv_name)
                z.extract(csv_name)
                return csv_name
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
    conn = None
    cur = None
    try:
        # Conectar ao banco de dados
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()

        # Ler o arquivo CSV
        # Tentando múltiplos encodings comuns em arquivos brasileiros
        try:
            df = pd.read_csv(csv_file_path, sep=';', encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(csv_file_path, sep=';', encoding='ISO-8859-1')
            except UnicodeDecodeError:
                 df = pd.read_csv(csv_file_path, sep=';', encoding='latin1')
        except FileNotFoundError:
            print(f"Erro: Arquivo CSV não encontrado em {csv_file_path}")
            return
        except Exception as e:
            print(f"Erro ao ler arquivo CSV: {e}")
            return


        print(f"Lendo {len(df)} linhas do arquivo CSV.")

        # Iterar sobre as linhas do CSV
        for index, row in df.iterrows():
            cnpj = str(row['CNPJ_Companhia']).replace('.', '').replace('/', '').replace('-', '') # Limpar CNPJ
            nome_emp = row['Nome_Empresarial']
            codigo_neg = row['Codigo_Negociacao']

            if not cnpj:
                # print(f"Skipping row {index}: CNPJ vazio.")
                continue

            # Inserir/Atualizar na tabela companies
            try:
                cur.execute(
                    """
                    INSERT INTO companies (cnpj, name, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW())
                    ON CONFLICT (cnpj) DO NOTHING;
                    """,
                    (cnpj, nome_emp)
                )
                # Não commita aqui, para commitar tudo junto no final da linha
            except Exception as e:
                print(f"Erro ao inserir/atualizar empresa {cnpj}: {e}")
                conn.rollback() # Rollback em caso de erro na empresa, mas continua tentando tickers
                continue # Pula para a próxima linha do CSV se a empresa falhou

            # Inserir na tabela tickers
            if pd.notna(codigo_neg) and codigo_neg.strip(): # Garantir que Codigo_Negociacao não é nulo ou vazio
                 try:
                    cur.execute(
                        """
                        INSERT INTO tickers (ticker, company_cnpj, is_active, created_at, updated_at)
                        VALUES (%s, %s, TRUE, NOW(), NOW())
                        ON CONFLICT (ticker) DO NOTHING; -- Evita duplicados de ticker
                        """,
                        (codigo_neg.strip(), cnpj) # Usar strip() para remover espaços em branco
                    )
                    conn.commit() # Commita a inserção do ticker
                 except Exception as e:
                    print(f"Erro ao inserir ticker {codigo_neg} para empresa {cnpj}: {e}")
                    conn.rollback() # Rollback em caso de erro no ticker
            else:
                 # print(f"Skipping ticker insertion for company {cnpj}: Codigo_Negociacao is null or empty.")
                 pass # Ignora linhas sem código de negociação


        print(f"Carga inicial de dados de empresas e tickers concluída.")

    except psycopg2.OperationalError as e:
        print(f"Erro de conexão ao banco de dados: {e}")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

    finally:
        # Fechar conexão
        if cur:
            cur.close()
        if conn:
            conn.close()

# Executar o processo
if __name__ == "__main__": # Adicionado para permitir importação sem execução imediata
    downloaded_csv_path = download_and_extract_csv(cvm_zip_url, csv_file_name)
    if downloaded_csv_path:
        load_companies_and_tickers(downloaded_csv_path)
        # Opcional: Remover o arquivo CSV após a carga
        # try:
        #     os.remove(downloaded_csv_path)
        #     print(f\"Arquivo temporário {downloaded_csv_path} removido.\")
        # except OSError as e:
        #     print(f\"Erro ao remover arquivo temporário {downloaded_csv_path}: {e}\")
