# scripts/etl_financial_statements.py (Versão Final - Filtra por Empresas Existentes)
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
        # Usa um set para uma verificação de existência (in) muito mais rápida
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
            for statement_type_raw in ['DRE_con', 'BPA_con', 'BPP_con', 'DFC_MD_con', 'DFC_MI_con']:
                file_name = f'{report_type_abbr.lower()}_cia_aberta_{statement_type_raw}_{year}.csv'
                if file_name in z.namelist():
                    print(f"  -> Processando arquivo: {file_name}")
                    with z.open(file_name) as f:
                        df = pd.read_csv(f, sep=';', encoding='latin-1', dtype=str)
                        
                        reports = df.groupby(['CNPJ_CIA', 'DT_FIM_EXERC'])
                        
                        with conn.cursor() as cur:
                            for (cnpj, dt_fim), group in reports:
                                cnpj_cleaned = ''.join(filter(str.isdigit, cnpj))
                                
                                # --- LÓGICA DE VERIFICAÇÃO ---
                                # Se o CNPJ da empresa não está na nossa lista mestra, PULA.
                                if cnpj_cleaned not in existing_companies:
                                    continue # Vai para a próxima empresa no arquivo
                                # --- FIM DA LÓGICA ---
                                
                                report_year = pd.to_datetime(dt_fim).year
                                
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
                                
                                for _, row in group.iterrows():
                                    if row['VL_CONTA'] is not None:
                                        cur.execute(
                                            """
                                            INSERT INTO financial_statements (report_id, statement_type, account_code, account_description, account_value)
                                            VALUES (%s, %s, %s, %s, %s)
                                            ON CONFLICT (report_id, statement_type, account_code) DO NOTHING;
                                            """,
                                            (report_id, statement_type_raw.split('_')[0], row['CD_CONTA'], row['DS_CONTA'], float(row['VL_CONTA'].replace(',', '.')))
                                        )
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
        # Busca a lista de empresas UMA VEZ no início
        empresas_de_interesse = get_existing_companies(main_conn)
        print(f"Encontradas {len(empresas_de_interesse)} empresas na lista mestra.")
        main_conn.close()

        start_year = int(input("Digite o ano inicial para a carga de dados (ex: 2022): "))
        end_year = datetime.now().year
        
        for year in range(start_year, end_year + 1):
            # Passa a lista de empresas para a função de processamento
            process_financial_data(year, "DFP", "ANUAL", empresas_de_interesse)
            process_financial_data(year, "ITR", "TRIMESTRAL", empresas_de_interesse)

    except Exception as e:
        print(f"Erro no script principal: {e}")
    finally:
        if main_conn:
             main_conn.close()

    print("--- CARGA DE DADOS FINANCEIROS CONCLUÍDA ---")
