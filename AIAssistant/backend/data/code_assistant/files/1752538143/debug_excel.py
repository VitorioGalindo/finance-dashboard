# --- SCRIPT DE DIAGNÓSTICO ---
import os
import pythoncom
import win32com.client

# Coloque aqui o caminho exato do seu ficheiro
EXCEL_PATH = r"C:\PYTHON\Dashboard da Carteira\Carteira Gerencial Diario.xlsx"

# Abas que queremos investigar
SHEETS_TO_DEBUG = ["CARTEIRA", "RTD", "FIA", "IBOV"]

def debug_excel_sheets():
    """
    Esta função abre o Excel, lê as primeiras 15 linhas de cada aba
    e imprime o conteúdo "cru" para análise.
    """
    # Validação inicial do caminho
    if not os.path.exists(EXCEL_PATH):
        print(f"ERRO: O ficheiro não foi encontrado em: {EXCEL_PATH}")
        return

    print("--- Iniciando Diagnóstico do Ficheiro Excel ---")
    print(f"A tentar abrir: {EXCEL_PATH}\n")

    excel, workbook = None, None
    try:
        # Inicializa o COM para esta thread
        pythoncom.CoInitialize()
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        workbook = excel.Workbooks.Open(EXCEL_PATH, ReadOnly=True)

        for sheet_name in SHEETS_TO_DEBUG:
            print(f"--- Lendo a Aba: '{sheet_name}' ---")
            try:
                sheet = workbook.Sheets(sheet_name)
                # Pega os dados do range utilizado da planilha
                data = sheet.UsedRange.Value
                
                if not data:
                    print("A aba está vazia ou não foi possível ler os dados.")
                    continue

                # Imprime as primeiras 15 linhas para análise
                for i, row in enumerate(data[:15]):
                    # Imprime o número da linha e o conteúdo
                    # O conteúdo da linha (row) é uma tupla de valores
                    print(f"Linha {i+1}: {row}")
                
                print(f"--- Fim da Aba: '{sheet_name}' ---\n")

            except Exception as e:
                print(f"ERRO ao tentar ler a aba '{sheet_name}': {e}\n")

    except Exception as e:
        print(f"ERRO CRÍTICO ao abrir o Excel ou o ficheiro: {e}")
    
    finally:
        # Garante que o Excel é sempre fechado
        if workbook:
            workbook.Close(SaveChanges=False)
        if excel:
            excel.Quit()
        # Finaliza o COM
        pythoncom.CoUninitialize()
        print("--- Diagnóstico Concluído ---")

if __name__ == '__main__':
    debug_excel_sheets()