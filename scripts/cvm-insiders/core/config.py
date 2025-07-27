# core/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Constrói o caminho para a raiz do projeto (dois níveis acima de core/)
# core -> cvm-insiders -> raiz do projeto
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Carrega as variáveis do arquivo .env localizado na raiz do projeto
env_path = PROJECT_ROOT / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    # URLs da CVM
    CVM_PORTAL_URL = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx"
    CVM_DOWNLOAD_URL = "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx"

    # Configurações do Banco de Dados (lidas do .env da raiz)
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")
    
    # Adiciona sslmode=require à URL para compatibilidade com a AWS RDS
    if DB_USER and DB_PASSWORD and DB_HOST and DB_NAME:
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
    else:
        DATABASE_URL = None # Ou levanta um erro se as credenciais são obrigatórias

    # Diretórios (baseados na raiz do projeto para consistência)
    DOWNLOAD_DIR = PROJECT_ROOT / "scripts" / "cvm-insiders" / "data" / "downloads"

settings = Settings()

# Cria o diretório de downloads se não existir
if settings.DOWNLOAD_DIR:
    settings.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
