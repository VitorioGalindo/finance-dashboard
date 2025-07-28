# scraper/config.py
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env na raiz do projeto
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Configurações do Banco de Dados ---
DB_USER = os.getenv("DB_USER", "default_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "default_password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "default_db")
DB_PORT = os.getenv("DB_PORT", "5432")

# String de conexão do SQLAlchemy
# Garante que o modo SSL seja 'require' para compatibilidade com serviços em nuvem
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"

# --- Configurações Gerais do Scraper ---
LOG_LEVEL = "INFO"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# --- Configurações da CVM ---
# URL base para o portal de dados abertos
CVM_DADOS_ABERTOS_URL = "https://dados.cvm.gov.br/dados"

# User-Agent para simular um navegador e evitar bloqueios
REQUESTS_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Ano inicial para a carga histórica de dados
START_YEAR_HISTORICAL_LOAD = 2012
