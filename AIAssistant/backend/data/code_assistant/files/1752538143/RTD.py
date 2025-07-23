import os
import pythoncom
import win32com.client
import pandas as pd
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime

# --- Configuração ---
EXCEL_PATH = r"C:\PYTHON\Dashboard da Carteira\Carteira Gerencial Diario.xlsx"
SHEET_NAME = "RTD"
FLASK_PORT = 5000

# --- Aplicação Flask ---
app = Flask(__name__)
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
        print("Procurando por workbook:", target_filename)
        for wb in excel.Workbooks:
            print("Workbook aberto:", wb.Name)
            if wb.Name.lower() == target_filename:
                workbook = wb
                break
        
        if not workbook:
            print(f"Workbook '{target_filename}' não encontrado, tentando abrir de '{EXCEL_PATH}'...")
            workbook = excel.Workbooks.Open(EXCEL_PATH)

        print(f"Workbook '{workbook.Name}' acessado com sucesso.")
        
        # Acessa a planilha
        sheet = workbook.Sheets(SHEET_NAME)
        
        # Lê os dados da planilha para um DataFrame do Pandas
        data = sheet.UsedRange.Value
        headers = data[0]
        rows = data[1:]
        df = pd.DataFrame(rows, columns=headers)
        
        # --- Limpeza e Processamento dos Dados ---
        # Seleciona apenas as colunas necessárias
        df = df[['Asset', 'Data', 'Último', 'Fechamento Anterior']]
        
        # Converte 'Último' e 'Fechamento Anterior' para numérico
        df['Último'] = pd.to_numeric(df['Último'], errors='coerce')
        df['Fechamento Anterior'] = pd.to_numeric(df['Fechamento Anterior'], errors='coerce')
        
        # Remove linhas onde preços são inválidos
        df.dropna(subset=['Último', 'Fechamento Anterior'], inplace=True)
        df = df[(df['Último'] > 0) & (df['Fechamento Anterior'] > 0)]

        # Converte 'Data' para formato de data
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.strftime('%d/%m/%Y')
        df.dropna(subset=['Data'], inplace=True)
        
        # Converte o DataFrame para JSON
        quotes = df.to_dict(orient='records')
        print(f"Servidor enviou {len(quotes)} cotações às {datetime.now().strftime('%H:%M:%S')}")
        
        return jsonify(quotes)

    except Exception as e:
        error_message = f"Ocorreu um erro ao ler o arquivo Excel: {e}"
        print(error_message)
        return jsonify({"error": error_message}), 500
    finally:
        pythoncom.CoUninitialize()

if __name__ == '__main__':
    print("Iniciando servidor Flask...")
    print(f"Acesse o painel no seu navegador. As cotações serão servidas de '{EXCEL_PATH}'")
    print(f"O servidor estará disponível em http://localhost:{FLASK_PORT}")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)