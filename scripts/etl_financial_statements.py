# scripts/etl_financial_statements.py (VERSÃO FINAL E CORRIGIDA PÓS-REATORAÇÃO)
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import requests
import zipfile
import io
from datetime import datetime

def get_db_connection_string():
    """Lê as credenciais do .env."""
    load_dotenv()
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    dbname = os.getenv("DB_NAME", "postgres")
    if not all([user, password, host, dbname]):
        raise ValueError("Credenciais do banco de dados não encontradas.")
    return f"postgresql://{user}:{password}@{host}/{dbname}?sslmode=require"

def get_existing_companies(conn):
    """Busca o conjunto de todos os CNPJs existentes na tabela 'companies'."""
    with conn.cursor() as cur:
        cur.execute("SELECT cnpj FROM companies;")
        return {row[0] for row in cur.fetchall()}

def process_financial_data(year, report_type_abbr, period_name, existing_companies):
    """Busca e processa um ano de dados DFP ou ITR, apenas para empresas existentes."""
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
            statements_to_process = ['DRE_con', 'BPA_con', 'BPP_con', 'DFC_MD_con', 'DFC_MI_con']
            
            for statement_file_suffix in statements_to_process:
                file_name = f'{report_type_abbr.lower()}_cia_aberta_{statement_file_suffix}_{year}.csv'
                if file_name in z.namelist():
                    print(f"  -> Processando arquivo: {file_name}...", end='', flush=True)
                    total_rows = 0
                    
                    with z.open(file_name) as f:
                        for chunk in pd.read_csv(f, sep=';', encoding='latin-1', dtype=str, chunksize=10000):
                            total_rows += len(chunk)
                            
                            chunk['CNPJ_CIA_cleaned'] = chunk['CNPJ_CIA'].str.replace(r'\D', '', regex=True)
                            chunk_filtered = chunk[chunk['CNPJ_CIA_cleaned'].isin(existing_companies)].copy()
                            
                            if chunk_filtered.empty:
                                continue

                            with conn.cursor() as cur:
                                reports_data = set()
                                for _, row in chunk_filtered.iterrows():
                                    report_year = pd.to_datetime(row['DT_FIM_EXERC']).year
                                    reports_data.add((
                                        row['CNPJ_CIA_cleaned'], report_year, period_name, report_type_abbr.upper()
                                    ))
                                
                                if reports_data:
                                    execute_values(cur,
                                        """
                                        INSERT INTO financial_reports (company_cnpj, year, period, report_type)
                                        VALUES %s ON CONFLICT (company_cnpj, year, period, report_type) DO NOTHING;
                                        """, list(reports_data))

                                cur.execute(
                                    "SELECT id, company_cnpj, year, period, report_type FROM financial_reports WHERE company_cnpj = ANY(%s)",
                                    (list(chunk_filtered['CNPJ_CIA_cleaned'].unique()),)
                                )
                                report_map = { (r[1], r[2], r[3], r[4]): r[0] for r in cur.fetchall() }

                                statements_to_insert = []
                                for _, row in chunk_filtered.iterrows():
                                    report_year = pd.to_datetime(row['DT_FIM_EXERC']).year
                                    key = (row['CNPJ_CIA_cleaned'], report_year, period_name, report_type_abbr.upper())
                                    report_id = report_map.get(key)
                                    
                                    if report_id and row['VL_CONTA'] is not None:
                                        statements_to_insert.append((
                                            report_id, statement_file_suffix.split('_')[0], row['CD_CONTA'], 
                                            row['DS_CONTA'], float(row['VL_CONTA'].replace(',', '.'))
                                        ))
                                
                                if statements_to_insert:
                                    execute_values(cur,
                                        """
                                        INSERT INTO financial_statements (report_id, statement_type, account_code, account_description, account_value)
                                        VALUES %s ON CONFLICT (report_id, statement_type, account_code) DO NOTHING;
                                        """, statements_to_insert)

                    print(f" Concluído. Total de {total_rows} linhas lidas.")
                    conn.commit()
    except Exception as e:
        print(f"  -> ERRO ao processar o ano {year}: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    main_conn = None
    try:
        print("Buscando lista de empresas de interesse no banco de dados...")
        main_conn = psycopg2.connect(get_db_connection_string())
        empresas_de_interesse = get_existing_companies(main_conn)
        print(f"Encontradas {len(empresas_de_interesse)} empresas na lista mestra.")
        main_conn.close()

        start_year = int(input("Digite o ano inicial para a carga de dados (ex: 2022): "))
        end_year = datetime.now().year
        
        for year in range(start_year, end_year + 1):
            process_financial_data(year, "DFP", "ANUAL", empresas_de_interesse)
            process_financial_data(year, "ITR", "TRIMESTRAL", empresas_de_interesse)

    except Exception as e:
        print(f"Erro no script principal: {e}")
    finally:
        if main_conn: main_conn.close()

    print("--- CARGA DE DADOS FINANCEIROS CONCLUÍDA ---")
