import pandas as pd
import requests
import zipfile
import io
from datetime import datetime
from typing import List

class CVMDataIngestor:
    """
    Responsável por buscar o índice de documentos da CVM e extrair os
    metadados necessários, como os links para os relatórios em PDF.
    """
    def __init__(self, year: int = None):
        self.year = year if year else datetime.now().year
        self.target_csv_filename = f"vlmo_cia_aberta_{self.year}.csv"
        print(f"Ingestor CVM inicializado para o ano de {self.year}. Alvo: {self.target_csv_filename}")

    def get_document_metadata(self) -> pd.DataFrame:
        """
        Busca o arquivo ZIP de metadados da CVM para um determinado ano,
        extrai o CSV principal e retorna um DataFrame com os metadados.
        """
        zip_url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/DADOS/vlmo_cia_aberta_{self.year}.zip"
        print(f"Buscando índice de metadados de: {zip_url}")

        try:
            response = requests.get(zip_url, timeout=60)
            response.raise_for_status()
            
            zip_buffer = io.BytesIO(response.content)
            
            with zipfile.ZipFile(zip_buffer) as z:
                if self.target_csv_filename not in z.namelist():
                    raise FileNotFoundError(f"O arquivo '{self.target_csv_filename}' não foi encontrado no ZIP.")
                
                print(f"Arquivo de metadados encontrado: {self.target_csv_filename}")

                with z.open(self.target_csv_filename) as csv_file:
                    df_index = pd.read_csv(
                        csv_file,
                        sep=';',
                        encoding='latin-1',
                        dtype=str,
                        on_bad_lines='warn' 
                    )
                    
                    # --- LINHA DE DEPURAÇÃO ADICIONADA ---
                    print(f"\n[DEBUG] Colunas encontradas no CSV de {self.year}:")
                    print(df_index.columns.tolist())
                    print("[DEBUG] Fim da lista de colunas.\n")
                    
                    print(f"Índice carregado com sucesso. Total de {len(df_index)} registros de metadados encontrados.")
                    return df_index
        except Exception as e:
            print(f"ERRO inesperado durante a ingestão de metadados: {e}")
            raise
