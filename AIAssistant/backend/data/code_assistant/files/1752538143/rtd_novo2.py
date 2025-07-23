# RTD.py (Versão 6 - Leitura com Pandas para o Gráfico)

import os
import pythoncom
import win32com.client
import pandas as pd
from flask import Flask, jsonify
from flask_cors import CORS
import traceback

# --- Configuração ---
# ATENÇÃO: Verifique se os caminhos estão corretos.
EXCEL_PATH_MAIN = r"C:\PYTHON\Dashboard da Carteira\Carteira Gerencial Diario.xlsx"
EXCEL_PATH_CHART = r"C:\PYTHON\Dashboard da Carteira\grafico cota.xlsx"

SHEET_NAME_RTD = "RTD"
SHEET_NAME_COTA = "FIA"
SHEET_NAME_IBOV = "IBOV"
FLASK_PORT = 5000

app = Flask(__name__)
CORS(app)

# --- Função de Leitura com win32com (Apenas para RTD) ---
def read_rtd_data(workbook, sheet_name, expected_columns):
    try:
        sheet = workbook.Sheets(sheet_name)
        data = sheet.UsedRange.Value
        if not data or len(data) < 2:
            return pd.DataFrame(columns=expected_columns)
        headers = [str(h) for h in data[0]]
        rows = data[1:]
        df = pd.DataFrame(rows, columns=headers)
        return df[expected_columns]
    except Exception as e:
        print(f"ERRO ao ler a aba RTD '{sheet_name}': {e}")
        return pd.DataFrame(columns=expected_columns)

@app.route('/api/quotes', methods=['GET'])
def get_quotes():
    """Endpoint para dados em tempo real (RTD). Continua usando win32com."""
    pythoncom.CoInitialize()
    excel = None
    try:
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = False
        if not os.path.exists(EXCEL_PATH_MAIN):
            raise FileNotFoundError(f"Arquivo principal não encontrado: {EXCEL_PATH_MAIN}")
        workbook = excel.Workbooks.Open(EXCEL_PATH_MAIN, ReadOnly=True)

        df_rtd = read_rtd_data(workbook, SHEET_NAME_RTD, ['Asset', 'Data', 'Último', 'Fechamento Anterior'])
        if not df_rtd.empty:
            df_rtd['Último'] = pd.to_numeric(df_rtd['Último'], errors='coerce').fillna(0)
            df_rtd['Fechamento Anterior'] = pd.to_numeric(df_rtd['Fechamento Anterior'], errors='coerce').fillna(0)
        
        quotes = df_rtd.to_dict(orient='records')
        return jsonify(quotes)
    except Exception as e:
        print(f"Erro em /api/quotes: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        if 'workbook' in locals() and workbook:
            workbook.Close(SaveChanges=False)
        if excel:
            excel.Quit()
        pythoncom.CoUninitialize()

@app.route('/api/historical', methods=['GET'])
def get_historical_data():
    """Endpoint para dados históricos. Usa pandas.read_excel para mais robustez."""
    try:
        if not os.path.exists(EXCEL_PATH_CHART):
            raise FileNotFoundError(f"Arquivo de gráfico não encontrado: {EXCEL_PATH_CHART}")

        # --- NOVA ABORDAGEM: Lendo diretamente com Pandas ---
        df_cota = pd.read_excel(EXCEL_PATH_CHART, sheet_name=SHEET_NAME_COTA, engine='openpyxl')
        df_ibov = pd.read_excel(EXCEL_PATH_CHART, sheet_name=SHEET_NAME_IBOV, engine='openpyxl')
        
        print(f"DEBUG (Gráfico): Lidos {len(df_cota)} registros da aba Cota.")
        print(f"DEBUG (Gráfico): Lidos {len(df_ibov)} registros da aba IBOV.")

        # Limpeza e preparação dos dados
        df_cota.rename(columns={'Cota do Fundo': 'Cota'}, inplace=True)
        df_cota = df_cota[['Data', 'Cota']].copy()
        df_cota['Data'] = pd.to_datetime(df_cota['Data'], errors='coerce')
        df_cota['Cota'] = pd.to_numeric(df_cota['Cota'], errors='coerce')
        df_cota.dropna(inplace=True)

        df_ibov.rename(columns={'Fechamento': 'IBOV'}, inplace=True)
        df_ibov = df_ibov[['Data', 'IBOV']].copy()
        df_ibov['Data'] = pd.to_datetime(df_ibov['Data'], errors='coerce')
        df_ibov['IBOV'] = pd.to_numeric(df_ibov['IBOV'], errors='coerce')
        df_ibov.dropna(inplace=True)

        if df_cota.empty or df_ibov.empty:
            print("AVISO (Gráfico): Um ou ambos os dataframes (Cota, IBOV) estão vazios após a limpeza.")
            return jsonify([])

        # Merge dos dataframes
        df_merged = pd.merge(df_cota, df_ibov, on='Data', how='inner')
        print(f"DEBUG (Gráfico): Após o merge, resultaram {len(df_merged)} registros.")
        
        if df_merged.empty:
            print("AVISO (Gráfico): O merge resultou em um dataframe vazio. Verifique se as datas nas abas 'FIA' e 'IBOV' do arquivo 'grafico cota.xlsx' coincidem.")
            return jsonify([])

        df_merged.sort_values(by='Data', inplace=True)
        df_merged['Data'] = df_merged['Data'].dt.strftime('%Y-%m-%d')
        
        historical_data = df_merged.to_dict(orient='records')
        print(f"Historical: Servidor enviou {len(historical_data)} registros para o gráfico.")
        return jsonify(historical_data)

    except Exception as e:
        print(f"ERRO GERAL em /api/historical: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Iniciando servidor Flask...")
    print(f"Lendo dados da carteira de: {EXCEL_PATH_MAIN}")
    print(f"Lendo dados do gráfico de: {EXCEL_PATH_CHART}")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)
