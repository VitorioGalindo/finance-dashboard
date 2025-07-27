# backend/database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from pathlib import Path

def get_database_url():
    """
    Carrega as credenciais do arquivo .env na raiz do projeto
    e retorna a string de conexão SQLAlchemy.
    """
    # Garante que estamos procurando o .env a partir da raiz do projeto
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / '.env'
    
    if not env_path.exists():
        raise FileNotFoundError(f"Arquivo .env não encontrado em {env_path}. Certifique-se de que ele está na raiz do projeto.")
        
    load_dotenv(dotenv_path=env_path)

    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    dbname = os.getenv("DB_NAME", "postgres")
    
    if not all([user, password, host, dbname]):
        raise ValueError("Uma ou mais variáveis de banco de dados (DB_USER, DB_PASSWORD, DB_HOST, DB_NAME) não estão definidas no arquivo .env.")
    
    # Retorna a string de conexão padrão para SQLAlchemy com psycopg2
    return f"postgresql+psycopg2://{user}:{password}@{host}/{dbname}?sslmode=require"

# Cria uma única instância da engine para ser importada por outros módulos
# Isso é mais eficiente do que criar uma nova engine toda vez.
db_url = get_database_url()
engine = create_engine(db_url)
