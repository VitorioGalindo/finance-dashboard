import requests
import zipfile
import io
import chardet # Biblioteca para detectar a codificação

# URL do arquivo ZIP da CVM
cvm_zip_url = 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_2025.zip'
csv_file_name = 'fca_cia_aberta_valor_mobiliario_2025.csv'

def detect_csv_encoding(url, csv_name):
    """Baixa um ZIP, extrai o conteúdo de um CSV em memória e detecta sua codificação."""
    print(f"Baixando arquivo ZIP: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        print("Download concluído. Extraindo arquivo em memória...")
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            if csv_name in z.namelist():
                # Extrai o arquivo para a memória em vez de para o disco
                csv_content_bytes = z.read(csv_name)

                print("Arquivo extraído. Detectando a codificação...")
                # Usa chardet para analisar os bytes do arquivo
                detection_result = chardet.detect(csv_content_bytes)

                encoding = detection_result['encoding']
                confidence = detection_result['confidence']

                print("\n--- RESULTADO DA DETECÇÃO ---")
                print(f"Codificação detectada: {encoding}")
                print(f"Confiança: {confidence:.0%}")
                print("-----------------------------\n")

                if confidence < 0.9:
                    print("Aviso: A confiança da detecção é baixa. O resultado pode estar incorreto.")

                return encoding
            else:
                print(f"Erro: Arquivo '{csv_name}' não encontrado no ZIP.")
                return None

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        return None

if __name__ == "__main__":
    detected_encoding = detect_csv_encoding(cvm_zip_url, csv_file_name)
    if detected_encoding:
        print(f"Instrução: Use encoding='{detected_encoding}' no seu código pd.read_csv().")