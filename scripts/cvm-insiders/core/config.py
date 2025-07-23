# core/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    # URLs da CVM
    CVM_PORTAL_URL = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx"
    CVM_DOWNLOAD_URL = "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx"

    # Configurações do Banco de Dados (lidas do .env)
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # Diretórios
    DOWNLOAD_DIR = Path("data/downloads")

settings = Settings()

# Cria o diretório de downloads se não existir
settings.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)