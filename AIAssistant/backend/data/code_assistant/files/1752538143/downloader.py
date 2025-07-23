import requests
from pathlib import Path
import time

class PDFDownloader:
    """
    Responsável por baixar um arquivo PDF de uma URL de forma robusta,
    com gestão de retentativas.
    """
    def __init__(self, save_directory: Path):
        self.save_dir = save_directory
        self.save_dir.mkdir(parents=True, exist_ok=True)
        print(f"Downloader inicializado. Os PDFs serão salvos em: {self.save_dir}")

    def download(self, url: str, filename: str, retries: int = 3, delay: int = 5) -> Path | None:
        """
        Baixa um PDF. Tenta novamente em caso de falha.
        Retorna o caminho do arquivo baixado ou None em caso de falha.
        """
        save_path = self.save_dir / filename
        
        for attempt in range(retries):
            print(f"  Tentativa {attempt + 1}/{retries} para baixar: {filename}")
            try:
                response = requests.get(url, timeout=30, headers={'User-Agent': 'My-Cool-Scraper/1.0'})
                response.raise_for_status()
                
                save_path.write_bytes(response.content)
                print(f"  SUCESSO no download. Salvo em: {save_path}")
                return save_path
            
            except requests.exceptions.RequestException as e:
                print(f"  FALHA na tentativa {attempt + 1}: {e}")
                if attempt < retries - 1:
                    print(f"  Aguardando {delay} segundos antes de tentar novamente...")
                    time.sleep(delay)
                else:
                    print(f"  Máximo de tentativas atingido. Desistindo do arquivo: {filename}")
                    return None
        return None
