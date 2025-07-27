# core/config.py
from pathlib import Path

class Settings:
    # URLs da CVM
    CVM_PORTAL_URL = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx"
    CVM_DOWNLOAD_URL = "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx"

    # Diretórios (baseados na localização do script)
    # Isso mantém os downloads dentro da pasta do projeto de insiders
    BASE_DIR = Path(__file__).resolve().parent.parent
    DOWNLOAD_DIR = BASE_DIR / "data" / "downloads"

settings = Settings()

# Cria o diretório de downloads se não existir
settings.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
