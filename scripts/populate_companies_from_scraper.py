# scripts/populate_companies_from_scraper.py
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Adiciona a pasta 'scraper' ao path para importar seus módulos de serviço
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scraper')))

from services.company_list_scraper import B3CompanyListScraper # Importa a lógica do scraper
from models import Company # Importa a definição do modelo

def get_db_connection_string():
    # ... (lógica para obter a string de conexão do .env da raiz)
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    dbname = os.getenv("DB_NAME", "postgres")
    if not all([user, password, host, dbname]):
        raise ValueError("Credenciais do banco não encontradas.")
    return f"postgresql+psycopg2://{user}:{password}@{host}/{dbname}?sslmode=require"

def run_etl():
    print("--- INICIANDO ETL DE COMPANHIAS USANDO A LÓGICA DO SCRAPER ---")
    
    engine = create_engine(get_db_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Extração (usando a classe do scraper)
        print("Buscando dados da B3...")
        scraper = B3CompanyListScraper()
        companies_data = scraper.get_all_companies() # Supondo que este método exista
        print(f"Encontradas {len(companies_data)} empresas.")

        # 2. Transformação e Carga
        print("Populando a tabela 'companies'...")
        for index, data in companies_data.iterrows():
            # Mapeia os dados do DataFrame para o nosso objeto Company
            company = Company(
                cvm_code=data.get('cd_cvm'),
                company_name=data.get('razao_social'),
                # ... (mapear outros campos)
            )
            
            # Adiciona ao banco de dados
            session.merge(company) # Usa merge para inserir ou atualizar
        
        session.commit()
        print("🎉 Tabela 'companies' populada com sucesso!")

    except Exception as e:
        print(f"❌ ERRO durante o ETL: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    # Precisamos analisar 'company_list_scraper.py' para ver o método real
    # Por enquanto, este é um esqueleto funcional
    print("Este script é um esqueleto. A lógica de extração precisa ser confirmada.")
    # run_etl()
