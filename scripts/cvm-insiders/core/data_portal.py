# core/data_portal.py

import requests
import pandas as pd
import zipfile
import io
from typing import Tuple

def download_and_extract_dataframes(year: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/DADOS/vlmo_cia_aberta_{year}.zip"
    main_csv_name = f"vlmo_cia_aberta_{year}.csv"
    con_csv_name = f"vlmo_cia_aberta_con_{year}.csv"
    
    print(f"Baixando arquivo de metadados de: {url}")
    try:
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        zip_buffer = io.BytesIO(response.content)
        df_main, df_con = pd.DataFrame(), pd.DataFrame()
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            with zip_ref.open(main_csv_name) as csv_file:
                df_main = pd.read_csv(csv_file, sep=';', encoding='ISO-8859-1', low_memory=False)
                print(f"Lido com sucesso: {main_csv_name}")
            with zip_ref.open(con_csv_name) as csv_file:
                df_con = pd.read_csv(csv_file, sep=';', encoding='ISO-8859-1', low_memory=False)
                print(f"Lido com sucesso: {con_csv_name}")
        return df_main, df_con
    except Exception as e:
        print(f"ERRO: Falha ao processar o arquivo ZIP. Erro: {e}")
    return pd.DataFrame(), pd.DataFrame()