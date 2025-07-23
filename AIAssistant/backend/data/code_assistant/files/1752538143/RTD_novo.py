# RTD.py (Versão Corrigida e Robusta)
# Este script abre o arquivo Excel em segundo plano para garantir a conexão.
# Não é mais necessário abrir o Excel manualmente.

import os
import pythoncom
import win32com.client
import pandas as pd
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime

# --- Configuração ---
EXCEL_PATH = r"C:\PYTHON\Dashboard da Carteira\Carteira Gerencial Diario.xlsx"
SHEET_NAME_RTD = "RTD"
SHEET_NAME_COTA = "FIA"  # Aba com histórico da cota (Data, Cota)
SHEET_NAME_IBOV = "IBOV" # Aba com histórico do IBOV (Data, Fechamento)
FLASK_PORT = 5000

# --- Aplicação Flask ---
app = Flask(__name__)
CORS(app)

def read_excel_data(workbook, sheet_name, columns):
    """Função auxiliar para ler e processar uma aba do Excel."""
    sheet = workbook.Sheets(sheet_name)
    data = sheet.UsedRange.Value
    headers = data[0]
    rows = data[1:]
    df = pd.DataFrame(rows, columns=headers)
    df = df[columns]
    
    # Converte a coluna 'Data', tratando erros ao transformar em NaT (Not a Time)
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    
    # >>> NOVA LINHA ADICIONADA AQUI <<<
    # Remove qualquer linha onde a data não pôde ser convertida (ficou como NaT)
    df.dropna(subset=['Data'], inplace=True)
    
    return df

@app.route('/api/quotes', methods=['GET'])
def get_quotes():
    """Endpoint para dados em tempo real (RTD)."""
    pythoncom.CoInitialize()
    excel = None
    workbook = None
    
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        workbook = excel.Workbooks.Open(EXCEL_PATH)
        # Garante que a coluna 'Fechamento Anterior' seja lida
        df_rtd = read_excel_data(workbook, SHEET_NAME_RTD, ['Asset', 'Data', 'Último', 'Fechamento Anterior'])
        quotes = df_rtd.to_dict(orient='records')
        print(f"RTD: Servidor enviou {len(quotes)} cotações.")
        return jsonify(quotes)
    except Exception as e:
        print(f"Erro em /api/quotes: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if workbook: workbook.Close(SaveChanges=False)
        if excel: excel.Quit()
        pythoncom.CoUninitialize()

@app.route('/api/historical', methods=['GET'])
def get_historical_data():
    """Endpoint para dados históricos (Cota e IBOV)."""
    pythoncom.CoInitialize()
    excel = None
    workbook = None

    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        workbook = excel.Workbooks.Open(EXCEL_PATH)

        df_cota = read_excel_data(workbook, SHEET_NAME_COTA, ['Data', 'Cota'])
        df_ibov = read_excel_data(workbook, SHEET_NAME_IBOV, ['Data', 'Fechamento'])
        df_ibov.rename(columns={'Fechamento': 'IBOV'}, inplace=True)

        df_merged = pd.merge(df_cota, df_ibov, on='Data', how='inner')
        df_merged.sort_values(by='Data', inplace=True)
        
        historical_data = df_merged.to_dict(orient='records')
        print(f"Historical: Servidor enviou {len(historical_data)} registros.")
        return jsonify(historical_data)

    except Exception as e:
        print(f"Erro em /api/historical: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if workbook: workbook.Close(SaveChanges=False)
        if excel: excel.Quit()
        pythoncom.CoUninitialize()

if __name__ == '__main__':
    print("Iniciando servidor Flask...")
    print("O script abrirá o Excel em segundo plano para ler os dados.")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)