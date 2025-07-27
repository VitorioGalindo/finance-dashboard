# scripts/etl_financial_statements.py
import os
from dotenv import load_dotenv
import psycopg2
import pandas as pd
import requests
import zipfile
import io
from datetime import datetime

def get_db_connection_string():
    """Lê as credenciais do .env."""
    load_dotenv()
    # ... (código igual aos outros scripts)
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    dbname = os.getenv("DB_NAME", "postgres")
    if not all([user, password, host, dbname]):
        raise ValueError("Credenciais do banco não encontradas.")
    return f"postgresql://{user}:{password}@{host}/{dbname}?sslmode=require"

def process_financial_data(year, report_type_abbr, period_name):
    """Busca e processa um ano de dados DFP ou ITR."""
    print(f"Buscando dados {period_name} para o ano: {year}...")
    
    conn_str = get_db_connection_string()
    conn = None

    try:
        url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/{report_type_abbr.upper()}/DADOS/{report_type_abbr.lower()}_cia_aberta_{year}.zip"
        response = requests.get(url, timeout=180)
        if response.status_code != 200:
            print(f"  -> Arquivo para o ano {year} não encontrado. Pulando.")
            return

        conn = psycopg2.connect(f"{conn_str}&client_encoding=latin1")
        print("  -> Conectado ao banco de dados.")

        zip_buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buffer) as z:
            for statement_type in ['DRE', 'BPA', 'BPP', 'DFC_MD', 'DFC_MI']:
                file_name = f'{report_type_abbr.lower()}_cia_aberta_{statement_type}_con_{year}.csv'
                if file_name in z.namelist():
                    print(f"  -> Processando arquivo: {file_name}")
                    with z.open(file_name) as f:
                        df = pd.read_csv(f, sep=';', encoding='latin-1', dtype=str)
                        
                        # Processa em lotes (chunks) para não sobrecarregar a memória
                        for chunk in [df[i:i+5000] for i in range(0, df.shape[0], 5000)]:
                            with conn.cursor() as cur:
                                # Agrupa por empresa/relatório
                                reports = chunk.groupby(['CNPJ_CIA', 'DT_FIM_EXERC'])
                                
                                for (cnpj, dt_fim), group in reports:
                                    cnpj_cleaned = ''.join(filter(str.isdigit, cnpj))
                                    report_year = pd.to_datetime(dt_fim).year
                                    
                                    # Insere o relatório e obtém o ID
                                    cur.execute(
                                        """
                                        INSERT INTO financial_reports (company_cnpj, year, period, report_type)
                                        VALUES (%s, %s, %s, %s)
                                        ON CONFLICT (company_cnpj, year, period, report_type) DO UPDATE SET company_cnpj = EXCLUDED.company_cnpj
                                        RETURNING id;
                                        """,
                                        (cnpj_cleaned, report_year, period_name, report_type_abbr.upper())
                                    )
                                    report_id = cur.fetchone()[0]
                                    
                                    # Insere as linhas do relatório
                                    for _, row in group.iterrows():
                                        cur.execute(
                                            """
                                            INSERT INTO financial_statements (report_id, statement_type, account_code, account_description, account_value)
                                            VALUES (%s, %s, %s, %s, %s)
                                            ON CONFLICT (report_id, statement_type, account_code) DO NOTHING;
                                            """,
                                            (report_id, statement_type, row['CD_CONTA'], row['DS_CONTA'], float(row['VL_CONTA'].replace(',', '.')))
                                        )
                                conn.commit()
    except Exception as e:
        print(f"  -> ERRO ao processar o ano {year}: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    start_year = int(input("Digite o ano inicial para a carga de dados (ex: 2020): "))
    end_year = datetime.now().year
    
    for year in range(start_year, end_year + 1):
        process_financial_data(year, "DFP", "ANUAL")
        process_financial_data(year, "ITR", "TRIMESTRAL")

    print("--- CARGA DE DADOS FINANCEIROS CONCLUÍDA ---")
