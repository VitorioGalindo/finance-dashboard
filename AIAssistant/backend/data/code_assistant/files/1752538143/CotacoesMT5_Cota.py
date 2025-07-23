# rtd_mt5.py (Versão com Fechamento Anterior Corrigido)

import os
import MetaTrader5 as mt5
import pandas as pd
from flask import Flask, jsonify
from flask_cors import CORS
import traceback
from datetime import datetime
import time # Importado para adicionar pausas

# --- Configuração ---
# A lista de ativos a serem monitorizados.
ASSETS_TO_MONITOR = [
    "PRIO3", "RAPT4", "MDNE3", "ANIM3", "SIMH3", "DEXP3", "BRSR6", "BRAV3", 
    "LPSB3", "MLAS3", "HAPV3", "GUAR3", "SBFG3", "MYPK3", "ALOS3", "INBR32", 
    "LJQQ3", "LOGG3", "CSAN3", "LWSA3", "BOVA11"
]

# O único arquivo Excel necessário agora é para os dados do gráfico.
EXCEL_PATH_CHART = r"C:\PYTHON\Dashboard da Carteira\grafico cota.xlsx"

# Nomes das abas no arquivo de gráfico
SHEET_NAME_COTA = "FIA"
SHEET_NAME_IBOV = "IBOV"
FLASK_PORT = 5000

app = Flask(__name__)
CORS(app)

@app.route('/api/quotes', methods=['GET'])
def get_quotes():
    """Endpoint que busca as cotações em tempo real via MetaTrader 5."""
    if not mt5.initialize():
        error_message = f"initialize() falhou, erro = {mt5.last_error()}"
        print(error_message)
        return jsonify({"error": "Falha ao conectar com o MetaTrader 5. Verifique se o terminal está aberto."}), 500

    print("Conectado ao MetaTrader 5 com sucesso.")
    
    quotes = []
    today_date = datetime.now().strftime('%Y-%m-%d')

    for asset in ASSETS_TO_MONITOR:
        try:
            if not mt5.symbol_select(asset, True):
                print(f"Aviso: Falha ao selecionar o ativo '{asset}' no MT5. Pode não estar disponível na sua corretora. Erro: {mt5.last_error()}")
                continue

            time.sleep(0.05)

            tick = mt5.symbol_info_tick(asset)
            
            # --- CORREÇÃO: Obter o fechamento do dia anterior a partir dos dados de barras diárias ---
            rates = mt5.copy_rates_from_pos(asset, mt5.TIMEFRAME_D1, 0, 2)
            
            previous_close = None
            if rates is not None and len(rates) > 1:
                # O fechamento anterior é o preço de fechamento da penúltima barra (índice 0)
                previous_close = rates[0]['close']

            if tick and previous_close is not None and tick.last > 0:
                quotes.append({
                    "Asset": asset,
                    "Data": today_date,
                    "Último": tick.last,
                    "Fechamento Anterior": previous_close
                })
            else:
                print(f"Aviso: Não foi possível obter dados completos para o ativo '{asset}'. Verifique se o nome está correto e se há liquidez. Erro MT5: {mt5.last_error()}")
        except Exception as e:
            print(f"Erro ao processar o ativo {asset}: {e}")
    
    mt5.shutdown()
    
    print(f"MT5: Servidor enviou {len(quotes)} cotações.")
    return jsonify(quotes)

@app.route('/api/historical', methods=['GET'])
def get_historical_data():
    """Endpoint para dados históricos. Continua lendo do arquivo de gráfico."""
    try:
        if not os.path.exists(EXCEL_PATH_CHART):
            raise FileNotFoundError(f"Arquivo de gráfico não encontrado: {EXCEL_PATH_CHART}")

        df_cota = pd.read_excel(EXCEL_PATH_CHART, sheet_name=SHEET_NAME_COTA, engine='openpyxl')
        df_ibov = pd.read_excel(EXCEL_PATH_CHART, sheet_name=SHEET_NAME_IBOV, engine='openpyxl')
        
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
            return jsonify([])

        df_merged = pd.merge(df_cota, df_ibov, on='Data', how='inner')
        df_merged.sort_values(by='Data', inplace=True)
        
        if df_merged.empty:
            return jsonify([])

        base_cota = df_merged['Cota'].iloc[0]
        base_ibov = df_merged['IBOV'].iloc[0]
        df_merged['cota_return'] = (df_merged['Cota'] / base_cota) - 1
        df_merged['ibov_return'] = (df_merged['IBOV'] / base_ibov) - 1
        df_merged['Data'] = df_merged['Data'].dt.strftime('%Y-%m-%d')
        
        df_merged_final = df_merged[['Data', 'cota_return', 'ibov_return', 'Cota', 'IBOV']].copy()
        
        historical_data = df_merged_final.to_dict(orient='records')
        return jsonify(historical_data)

    except Exception as e:
        print(f"ERRO GERAL em /api/historical: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Iniciando servidor Flask...")
    print("Buscando cotações via MetaTrader 5.")
    print(f"Lendo dados do gráfico de: {EXCEL_PATH_CHART}")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)
