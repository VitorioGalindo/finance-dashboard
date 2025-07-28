# scripts/populate_companies.py
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Adiciona a pasta 'scraper' e a raiz ao path para importações
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scraper')))

from scraper.services.company_list_scraper import CompanyListScraper
from scraper.models import Company # Importa o modelo do esquema que criamos

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

def run_etl():
    """Executa o ETL para popular a tabela 'companies'."""
    print("--- INICIANDO ETL DE COMPANHIAS (BASEADO NO SCRAPER) ---")
    
    engine = create_engine(get_db_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Extração
        print("Buscando lista de empresas da B3...")
        scraper = CompanyListScraper()
        companies_data = scraper.get_hardcoded_b3_companies() # Usando a lista hardcoded que é mais confiável
        
        # Opcional: tentar o scraper online e fazer merge
        # online_companies = scraper.get_companies_from_dadosdemercado()
        # (lógica de merge aqui se necessário)
        
        print(f"Encontradas {len(companies_data)} empresas na lista de referência.")

        # 2. Transformação e Carga
        print("Populando a tabela 'companies'...")
        new_companies = 0
        updated_companies = 0
        
        for company_data in companies_data:
            # Pula entradas sem CVM code, pois é nosso identificador principal no modelo
            if not company_data.get('cvm_code'):
                continue

            # Verifica se a empresa já existe pelo código CVM
            instance = session.query(Company).filter_by(cvm_code=company_data['cvm_code']).first()
            
            if instance:
                # Atualiza (se necessário)
                instance.company_name = company_data['company_name']
                instance.cnpj = company_data.get('cnpj')
                # (adicionar outros campos para atualizar)
                updated_companies += 1
            else:
                # Insere nova
                instance = Company(
                    cvm_code=company_data['cvm_code'],
                    company_name=company_data['company_name'],
                    trade_name=company_data.get('company_name'), # Pode ser melhorado
                    cnpj=company_data.get('cnpj'),
                    is_b3_listed=True
                    # (mapear outros campos do scraper para o modelo)
                )
                session.add(instance)
                new_companies += 1
        
        session.commit()
        print(f"🎉 Tabela 'companies' populada com sucesso!")
        print(f"  - {new_companies} novas empresas inseridas.")
        print(f"  - {updated_companies} empresas atualizadas.")

    except Exception as e:
        print(f"❌ ERRO durante o ETL: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    run_etl()
