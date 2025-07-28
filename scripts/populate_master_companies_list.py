# scripts/populate_master_companies_list.py
import os
import sys
import re
import pandas as pd
import requests
import zipfile
import io
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bs4 import BeautifulSoup

# Adiciona a pasta 'scraper' ao path para importar seus modelos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scraper')))
from models import Base, Company

def get_db_connection_string():
    """Lê as credenciais do .env na raiz."""
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    dbname = os.getenv("DB_NAME", "postgres")
    if not all([user, password, host, dbname]):
        raise ValueError("Credenciais do banco de dados não encontradas.")
    return f"postgresql+psycopg2://{user}:{password}@{host}/{dbname}?sslmode=require"

def normalize_company_name(name):
    """Limpa e padroniza o nome de uma empresa para facilitar o matching."""
    if not isinstance(name, str):
        return ""
    # Remove S.A, S/A, etc., converte para maiúsculas e remove espaços extras
    name = re.sub(r'\s+S\.A\.|\s+S/A', '', name, flags=re.IGNORECASE)
    return name.strip().upper()

def scrape_dados_mercado():
    """Faz scraping da lista de empresas do site dadosdemercado.com.br."""
    print("Iniciando scraping de dadosdemercado.com.br...")
    url = "https://www.dadosdemercado.com.br/acoes"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', {'id': 'stocks-list'})
    
    companies = []
    if table:
        for row in table.find('tbody').find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 2:
                ticker = cols[0].text.strip()
                name = cols[1].text.strip()
                companies.append({'ticker': ticker, 'name': name, 'normalized_name': normalize_company_name(name)})
    
    print(f"Encontradas {len(companies)} empresas no Dados de Mercado.")
    return pd.DataFrame(companies)

def get_cvm_master_data():
    """Baixa e processa o arquivo de cadastro da CVM."""
    print("Baixando dados cadastrais da CVM...")
    url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
    response = requests.get(url)
    response.raise_for_status()
    
    # Especifica a codificação correta e trata nomes de colunas
    cvm_data = pd.read_csv(io.StringIO(response.content.decode('latin-1')), sep=';', dtype=str)
    cvm_data['normalized_name'] = cvm_data['DENOM_SOCIAL'].apply(normalize_company_name)
    print("Dados da CVM processados.")
    return cvm_data

def run_etl():
    """Orquestra o processo de ETL para criar a lista mestra de empresas."""
    print("
--- INICIANDO ETL DA LISTA MESTRA DE EMPRESAS ---")
    
    engine = create_engine(get_db_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # FASE 1: EXTRAÇÃO
        df_mercado = scrape_dados_mercado()
        df_cvm = get_cvm_master_data()

        # FASE 2: TRANSFORMAÇÃO (ENRIQUECIMENTO)
        print("Enriquecendo dados com informações da CVM...")
        # Faz o merge (join) dos dois dataframes usando o nome normalizado
        df_merged = pd.merge(df_mercado, df_cvm, on='normalized_name', how='left')
        
        # Filtra apenas as que tiveram correspondência e remove duplicatas
        df_final = df_merged.dropna(subset=['CNPJ_CIA', 'CD_CVM']).drop_duplicates(subset=['ticker'])
        print(f"{len(df_final)} empresas tiveram correspondência e foram enriquecidas com sucesso.")

        # FASE 3: CARGA
        print("Limpando a tabela 'companies' e 'tickers' (CASCADE)...")
        session.execute(text("TRUNCATE TABLE public.companies RESTART IDENTITY CASCADE;"))
        
        print(f"Populando a tabela 'companies' com {len(df_final)} registros...")
        companies_to_load = []
        for _, row in df_final.iterrows():
            companies_to_load.append({
                'cvm_code': int(row['CD_CVM']),
                'company_name': row['name'], # Mantém o nome original do Dados de Mercado
                'trade_name': row['DENOM_COMERCIAL'],
                'cnpj': row['CNPJ_CIA'].replace('.', '').replace('/', '').replace('-', ''),
                'b3_listing_segment': row['SEGMENTO'],
                'is_b3_listed': True
            })
        
        if companies_to_load:
            session.bulk_insert_mappings(Company, companies_to_load)

        session.commit()
        print("🎉 Tabela 'companies' populada com sucesso!")

    except Exception as e:
        print(f"❌ ERRO durante o ETL: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    from sqlalchemy import text
    run_etl()
