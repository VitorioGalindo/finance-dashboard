# scripts/create_scraper_schema.py
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Adiciona a pasta 'scraper' ao path para que possamos importar seus modelos
# Isso garante que a linha 'from models import Base' funcione
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scraper')))

def get_db_connection_string():
    """Lê as credenciais do .env na raiz."""
    # ... (código para carregar .env e construir a string de conexão)
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    dbname = os.getenv("DB_NAME", "postgres")
    if not all([user, password, host, dbname]):
        raise ValueError("Credenciais do banco não encontradas.")
    return f"postgresql+psycopg2://{user}:{password}@{host}/{dbname}?sslmode=require"

def create_schema():
    """Cria todas as tabelas definidas nos modelos do scraper."""
    print("--- INICIANDO CRIAÇÃO DO ESQUEMA DO BANCO DE DADOS ---")
    try:
        engine = create_engine(get_db_connection_string())
        
        # Importa a Base dos modelos corrigidos
        from models import Base
        
        print("Conectado ao banco de dados. Criando tabelas...")
        Base.metadata.create_all(bind=engine)
        
        print("🎉 Esquema criado com sucesso com base em scraper/models.py!")
    except Exception as e:
        print(f"❌ ERRO ao criar o esquema: {e}")

if __name__ == "__main__":
    create_schema()
