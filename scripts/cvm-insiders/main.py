# scripts/cvm-insiders/main.py
import sys
import os

# Adiciona o diretório raiz ao path para que os imports de 'core' funcionem
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.fetch_filings import fetch_and_save_filings
from core.parser import run_parser

def main():
    """
    Ponto de entrada principal para o pipeline de dados de insiders.
    Executa a busca por novos documentos (filings) e, em seguida,
    o processamento (parsing) desses documentos para extrair transações.
    """
    print("--- INICIANDO O PIPELINE COMPLETO DE DADOS DE INSIDERS ---")
    
    # Etapa 1: Buscar e salvar os registros de documentos (filings) da CVM.
    # Esta etapa garante que a tabela 'filings' esteja atualizada.
    fetch_and_save_filings()
    
    print("" + "="*50 + "")
    
    # Etapa 2: Processar os filings que ainda não foram analisados.
    # Esta etapa lê a tabela 'filings', baixa os PDFs e extrai as transações.
    run_parser()
    
    print("--- PIPELINE COMPLETO DE DADOS DE INSIDERS CONCLUÍDO ---")

if __name__ == "__main__":
    main()
