import requests
import pandas as pd
import zipfile
import io

def find_unique_values(year: int):
    """
    Baixa o arquivo ZIP da CVM e imprime os valores únicos das colunas 'Categoria' e 'Tipo'.
    """
    url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/DADOS/vlmo_cia_aberta_{year}.zip"
    target_csv = f"vlmo_cia_aberta_{year}.csv"
    
    print(f"Baixando e analisando o arquivo de: {url}")
    
    try:
        response = requests.get(url, timeout=300)
        response.raise_for_status()

        zip_buffer = io.BytesIO(response.content)
        
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            with zip_ref.open(target_csv) as csv_file:
                # Lê o arquivo inteiro para encontrar todos os valores únicos
                df = pd.read_csv(csv_file, sep=';', encoding='ISO-8859-1', low_memory=False)
                
                print("\n\n--- VALORES ÚNICOS ENCONTRADOS ---")
                
                if 'Categoria' in df.columns:
                    print("\nValores únicos para a coluna 'Categoria':")
                    print(df['Categoria'].unique())
                else:
                    print("\nA coluna 'Categoria' não foi encontrada.")

                if 'Tipo' in df.columns:
                    print("\nValores únicos para a coluna 'Tipo':")
                    print(df['Tipo'].unique())
                else:
                    print("\nA coluna 'Tipo' não foi encontrada.")

                print("\n----------------------------------\n")

    except Exception as e:
        print(f"Ocorreu um erro durante a execução: {e}")

if __name__ == "__main__":
    find_unique_values(2024)