import os
import pythoncom
import win32com.client
import pandas as pd
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime

# --- Configuração ---
# Garanta que este caminho está correto para o seu computador.
EXCEL_PATH = r"C:\PYTHON\Dashboard da Carteira\Carteira Gerencial Diario.xlsx"
SHEET_NAME = "RTD"
FLASK_PORT = 5000

# --- Aplicação Flask ---
app = Flask(__name__)
# Habilita CORS para permitir que a página HTML acesse a API
CORS(app)

@app.route('/api/quotes', methods=['GET'])
def get_quotes():
    """
    Endpoint da API para buscar as cotações do arquivo Excel.
    Conecta-se a uma instância aberta do Excel, lê a planilha e retorna os dados em JSON.
    """
    pythoncom.CoInitialize()  # Inicializa o COM para esta thread
    
    excel = None
    workbook = None

    try:
        # Tenta se conectar a uma instância do Excel que já está rodando
        excel = win32com.client.GetActiveObject("Excel.Application")
        print("Conectado a uma instância do Excel existente.")
    except Exception as e:
        print(f"Não foi possível encontrar uma instância do Excel aberta: {e}")
        return jsonify({"error": "Por favor, abra o arquivo Excel antes de iniciar o servidor."}), 503

    try:
        # Procura o workbook pelo nome do arquivo
        target_filename = os.path.basename(EXCEL_PATH).lower()
        for wb in excel.Workbooks:
            if wb.Name.lower() == target_filename:
                workbook = wb
                break
        
        if not workbook:
            # Se não encontrou, tenta abrir o arquivo
            print(f"Workbook '{target_filename}' não encontrado, tentando abrir de '{EXCEL_PATH}'...")
            workbook = excel.Workbooks.Open(EXCEL_PATH)

        print(f"Workbook '{workbook.Name}' acessado com sucesso.")
        
        # Acessa a planilha
        sheet = workbook.Sheets(SHEET_NAME)
        
        # Lê os dados da planilha para um DataFrame do Pandas
        # Usamos `UsedRange` para pegar apenas a área com dados
        data = sheet.UsedRange.Value
        headers = data[0]
        rows = data[1:]
        df = pd.DataFrame(rows, columns=headers)
        
        # --- Limpeza e Processamento dos Dados ---
        
        # 1. Seleciona apenas as colunas necessárias
        df = df[['Asset', 'Data', 'Último']]
        
        # 2. Converte 'Último' para numérico, tratando erros
        df['Último'] = pd.to_numeric(df['Último'], errors='coerce')
        
        # 3. Remove linhas onde o preço é inválido (nulo, zero ou negativo)
        df.dropna(subset=['Último'], inplace=True)
        df = df[df['Último'] > 0]

        # 4. Converte 'Data' para o formato de data, tratando erros
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.strftime('%d/%m/%Y')

        # 5. Remove linhas com data inválida
        df.dropna(subset=['Data'], inplace=True)
        
        # Converte o DataFrame limpo para um dicionário (formato JSON)
        quotes = df.to_dict(orient='records')
        
        print(f"Servidor enviou {len(quotes)} cotações às {datetime.now().strftime('%H:%M:%S')}")
        
        return jsonify(quotes)

    except Exception as e:
        error_message = f"Ocorreu um erro ao ler o arquivo Excel: {e}"
        print(error_message)
        return jsonify({"error": error_message}), 500
    finally:
        # Libera os recursos COM. Não fechamos o Excel ou o workbook
        # pois a intenção é que eles permaneçam abertos.
        pythoncom.CoUninitialize()

if __name__ == '__main__':
    print("Iniciando servidor Flask...")
    print(f"Acesse o painel no seu navegador. As cotações serão servidas de '{EXCEL_PATH}'")
    print(f"O servidor estará disponível em http://localhost:{FLASK_PORT}")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)
