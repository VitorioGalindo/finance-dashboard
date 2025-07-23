# update_script.py
# Este script é responsável por atualizar o arquivo Excel com os dados de fechamento do dia.
# Ele deve ser executado em segundo plano ou através de uma tarefa agendada.

import MetaTrader5 as mt5
import pandas as pd
import os
from datetime import datetime
import time
import schedule
import pytz

# --- CONFIGURAÇÃO DA CARTEIRA ---
# AJUSTE AQUI: Mantenha esta lista de ativos e suas quantidades atualizada.
# Esta é a composição da sua carteira para o cálculo da cota.
ASSETS_AND_QUANTITIES = {
    "PRIO3": 39080, "RAPT4": 150000, "MDNE3": 47400, "ANIM3": 210100, 
    "SIMH3": 137500, "DEXP3": 62500, "BRSR6": 48716, "BRAV3": 31500, 
    "LPSB3": 346900, "MLAS3": 507900, "HAPV3": 14800, "GUAR3": 52800, 
    "SBFG3": 34000, "MYPK3": 31000, "ALOS3": 17800, "INBR32": 9500, 
    "LJQQ3": 156000, "LOGG3": 19000, "CSAN3": 56000, "LWSA3": 95000, 
    "BOVA11": -13311
}

# AJUSTE AQUI: Mantenha estas métricas financeiras atualizadas.
# Elas são usadas para calcular o valor total do patrimônio.
METRICS = {
    "caixa_bruto": 607589,
    "outros": -244111,
    "outras_despesas": -299430,
    "quantidade_cotas": 88073 
}

# Ativo para representar o IBOV no MT5
IBOV_SYMBOL = "IBOV" 

# Caminho para o arquivo Excel que armazena os dados históricos
EXCEL_PATH_CHART = r"C:\PYTHON\Dashboard da Carteira\grafico cota.xlsx"
SHEET_NAME_COTA = "FIA"
SHEET_NAME_IBOV = "IBOV"

def update_excel_data():
    """
    Conecta ao MT5, calcula a cota do dia, busca o fechamento do IBOV
    e atualiza o arquivo Excel.
    """
    print(f"[{datetime.now()}] Iniciando a tarefa de atualização diária...")

    # 1. Conectar ao MetaTrader 5
    if not mt5.initialize():
        print(f"initialize() falhou, erro = {mt5.last_error()}")
        return

    print("Conectado ao MT5 para atualização.")

    try:
        # 2. Calcular o valor total dos ativos da carteira
        total_assets_value = 0
        for asset, quantity in ASSETS_AND_QUANTITIES.items():
            # Pega a última barra diária para obter o preço de fechamento
            rates = mt5.copy_rates_from_pos(asset, mt5.TIMEFRAME_D1, 0, 1)
            if rates is None or len(rates) == 0:
                print(f"Aviso: Não foi possível obter o preço de fechamento para {asset}.")
                continue
            
            close_price = rates[0]['close']
            total_assets_value += close_price * quantity
            print(f"  - Ativo: {asset}, Fechamento: {close_price}, Quantidade: {quantity}")

        # 3. Calcular o valor da cota
        patrimonio_liquido = total_assets_value + METRICS["caixa_bruto"] + METRICS["outros"] + METRICS["outras_despesas"]
        cota_do_dia = patrimonio_liquido / METRICS["quantidade_cotas"]
        print(f"Patrimônio Líquido Calculado: R$ {patrimonio_liquido:,.2f}")
        print(f"Cota do Dia Calculada: R$ {cota_do_dia:,.4f}")

        # 4. Obter o valor de fechamento do IBOV
        rates_ibov = mt5.copy_rates_from_pos(IBOV_SYMBOL, mt5.TIMEFRAME_D1, 0, 1)
        if rates_ibov is None or len(rates_ibov) == 0:
            print(f"Aviso: Não foi possível obter o preço de fechamento para {IBOV_SYMBOL}.")
            ibov_close = None
        else:
            ibov_close = rates_ibov[0]['close']
            print(f"Fechamento do IBOV: {ibov_close:,.2f}")

        # 5. Atualizar o arquivo Excel
        if ibov_close is not None:
            today = datetime.now().date()
            
            # Carrega as planilhas existentes
            df_cota = pd.read_excel(EXCEL_PATH_CHART, sheet_name=SHEET_NAME_COTA)
            df_ibov = pd.read_excel(EXCEL_PATH_CHART, sheet_name=SHEET_NAME_IBOV)

            # Converte a coluna 'Data' para o formato correto para evitar conflitos
            df_cota['Data'] = pd.to_datetime(df_cota['Data']).dt.date
            df_ibov['Data'] = pd.to_datetime(df_ibov['Data']).dt.date

            # Verifica se a data de hoje já existe para não duplicar
            if today in df_cota['Data'].values or today in df_ibov['Data'].values:
                print("Os dados de hoje já existem no arquivo. Nenhuma atualização foi feita.")
            else:
                # Adiciona a nova linha de dados
                nova_linha_cota = pd.DataFrame([{'Data': pd.to_datetime(today), 'Cota': cota_do_dia}])
                nova_linha_ibov = pd.DataFrame([{'Data': pd.to_datetime(today), 'Fechamento': ibov_close}])
                
                df_cota = pd.concat([df_cota, nova_linha_cota], ignore_index=True)
                df_ibov = pd.concat([df_ibov, nova_linha_ibov], ignore_index=True)

                # Salva as planilhas atualizadas no mesmo arquivo
                with pd.ExcelWriter(EXCEL_PATH_CHART, engine='openpyxl') as writer:
                    df_cota.to_excel(writer, sheet_name=SHEET_NAME_COTA, index=False)
                    df_ibov.to_excel(writer, sheet_name=SHEET_NAME_IBOV, index=False)
                
                print(f"Arquivo '{EXCEL_PATH_CHART}' atualizado com sucesso com os dados de {today.strftime('%d/%m/%Y')}.")

    except Exception as e:
        print(f"Ocorreu um erro durante a atualização: {e}")
        traceback.print_exc()
    finally:
        # 6. Encerrar a conexão
        mt5.shutdown()
        print("Conexão com o MT5 encerrada.")

# --- AGENDAMENTO DA TAREFA ---
# Define o fuso horário de Brasília
brasilia_tz = pytz.timezone('America/Sao_Paulo')

# Agenda a tarefa para ser executada todos os dias às 18:30, no fuso horário de Brasília.
schedule.every().day.at("18:30", "America/Sao_Paulo").do(update_excel_data)

print("Script de automação iniciado. Aguardando o horário agendado (18:30)...")
print("Para testar imediatamente, descomente a linha 'update_excel_data()' abaixo e execute o script.")
# update_excel_data() # Descomente esta linha para executar a atualização uma vez, imediatamente.

while True:
    schedule.run_pending()
    time.sleep(1)
