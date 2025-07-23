import requests
import pandas as pd
import zipfile
import io

print("--- Iniciando verificação de colunas do arquivo CONSOLIDADO ---")
YEAR_TO_CHECK = 2024
url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/DADOS/vlmo_cia_aberta_{YEAR_TO_CHECK}.zip"
target_csv_file = f"vlmo_cia_aberta_con_{YEAR_TO_CHECK}.csv" # Foco no arquivo _con

try:
    print(f"Baixando dados de: {url}")
    response = requests.get(url, timeout=300)
    response.raise_for_status()
    print("Download concluído. Processando arquivo ZIP...")
    zip_buffer = io.BytesIO(response.content)

    with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
        if target_csv_file in zip_ref.namelist():
            with zip_ref.open(target_csv_file) as csv_file:
                df = pd.read_csv(csv_file, sep=';', encoding='ISO-8859-1', nrows=5)
                print("\n\n--- COLUNAS REAIS ENCONTRADAS (ARQUIVO CONSOLIDADO) ---")
                print(df.columns.tolist())
                print("----------------------------------------------------------\n")
        else:
            print(f"ERRO: Arquivo '{target_csv_file}' não encontrado no ZIP.")
except Exception as e:
    print(f"Ocorreu um erro: {e}")
print("--- Fim do script ---")