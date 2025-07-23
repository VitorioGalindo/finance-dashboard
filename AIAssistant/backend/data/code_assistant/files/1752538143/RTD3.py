# RTD3.py (Versão Final e Robusta)
# Este script conecta-se a uma instância aberta do Excel para dados em tempo real.

import os
import pythoncom
import win32com.client
import pandas as pd
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime

# --- Configuração ---
# Verifique se este caminho está 100% correto no novo computador.
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
    Conecta-se a uma instância aberta do Excel para obter dados em tempo real.
    """
    pythoncom.CoInitialize()
    excel = None
    workbook = None
    
    print("\n--- Nova Requisição Recebida ---")
    
    try:
        # Tenta se conectar a uma instância do Excel que já está rodando
        print("Tentando conectar com win32com.client.GetActiveObject...")
        excel = win32com.client.GetActiveObject("Excel.Application")
        print("Sucesso! Conectado a uma instância do Excel.")
    except Exception as e:
        print(f"ERRO CRÍTICO: Não foi possível encontrar uma instância do Excel aberta. {e}")
        print("Verifique se o Excel está rodando e se não há problemas de permissão (veja o guia).")
        return jsonify({"error": "Não foi possível conectar ao Excel. Verifique se o programa está aberto e se não há conflito de permissões."}), 503

    try:
        target_filename = os.path.basename(EXCEL_PATH).lower()
        print(f"Procurando pelo workbook: '{target_filename}'")

        found_wb = None
        open_workbooks = []
        if excel.Workbooks.Count > 0:
            for wb in excel.Workbooks:
                open_workbooks.append(wb.Name)
                if wb.Name.lower() == target_filename:
                    found_wb = wb
                    break
        
        if found_wb:
            workbook = found_wb
            print(f"Workbook '{workbook.Name}' encontrado e está aberto.")
        else:
            print(f"ERRO: O workbook '{target_filename}' não foi encontrado entre os arquivos abertos.")
            if open_workbooks:
                print("Os seguintes arquivos foram encontrados abertos no Excel:")
                for name in open_workbooks:
                    print(f"  - {name}")
                print("\nVERIFIQUE: O nome do arquivo aberto é EXATAMENTE igual ao esperado?")
            else:
                print("DIAGNÓSTICO: Nenhum arquivo foi encontrado aberto na instância do Excel conectada.")
            
            return jsonify({"error": f"O arquivo '{target_filename}' não está aberto no Excel. Abra-o e tente novamente."}), 503

        # Processamento dos dados da planilha
        sheet = workbook.Sheets(SHEET_NAME)
        data = sheet.UsedRange.Value
        headers = data[0]
        rows = data[1:]
        df = pd.DataFrame(rows, columns=headers)

        df = df[['Asset', 'Data', 'Último', 'Fechamento Anterior']]
        df['Último'] = pd.to_numeric(df['Último'], errors='coerce')
        df['Fechamento Anterior'] = pd.to_numeric(df['Fechamento Anterior'], errors='coerce')
        df.dropna(subset=['Último', 'Fechamento Anterior'], inplace=True)
        df = df[(df['Último'] > 0) & (df['Fechamento Anterior'] > 0)]
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
        df.dropna(subset=['Data'], inplace=True)

        quotes = df.to_dict(orient='records')
        print(f"Servidor enviou {len(quotes)} cotações às {datetime.now().strftime('%H:%M:%S')}")
        
        return jsonify(quotes)

    except Exception as e:
        error_message = f"Ocorreu um erro ao processar o arquivo Excel: {e}"
        print(error_message)
        return jsonify({"error": error_message}), 500
    finally:
        # Libera os objetos COM, mas não fecha o Excel
        workbook = None
        excel = None
        pythoncom.CoUninitialize()
        print("Recursos liberados.")

if __name__ == '__main__':
    print("Iniciando servidor Flask para conexão em tempo real com o Excel...")
    print("--------------------------------------------------------------------")
    print("IMPORTANTE: O Excel com a planilha de RTD deve estar aberto.")
    print("--------------------------------------------------------------------")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)
