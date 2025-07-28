# scraper/run_complete_system.py
import argparse
import logging
import sys
import os

# Adiciona o diretório raiz ao path para importações corretas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper.services.cvm_service import CVMDataCollector
from scraper.database import check_db_connection

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Ponto de entrada principal para o sistema de coleta de dados.
    Utiliza argumentos de linha de comando para determinar qual tarefa executar.
    """
    logger.info("Verificando a conexão com o banco de dados antes de iniciar...")
    if not check_db_connection():
        logger.error("❌ Abortando a execução. Não foi possível conectar ao banco de dados.")
        return
    
    parser = argparse.ArgumentParser(description="Orquestrador do Sistema de Coleta de Dados Financeiros.")
    parser.add_argument(
        "task",
        choices=["historical-financials", "historical-fre", "daily-update", "company-deep-dive"],
        help=(
            "A tarefa a ser executada. "
            "'historical-financials': Carrega todo o histórico de DFP/ITR. "
            "'historical-fre': Carrega o histórico de dados do Formulário de Referência (FRE). "
            "'daily-update': (Não implementado) Busca atualizações diárias. "
            "'company-deep-dive': (Não implementado) Busca todos os dados de uma empresa."
        )
    )
    parser.add_argument("--year", type=int, help="Ano específico para rodar uma tarefa (opcional).")
    parser.add_argument("--cvm_code", type=str, help="Código CVM para a tarefa 'company-deep-dive'.")

    args = parser.parse_args()
    
    collector = CVMDataCollector()
    
    logger.info(f"Iniciando a tarefa: '{args.task}'")

    if args.task == "historical-financials":
        if args.year:
            logger.info(f"Executando carga histórica de DADOS FINANCEIROS para um ano específico: {args.year}")
            collector.process_financial_statements('DFP', args.year)
            collector.process_financial_statements('ITR', args.year)
        else:
            collector.run_historical_financial_load()

    elif args.task == "historical-fre":
        if args.year:
            logger.info(f"Executando carga histórica de DADOS DO FRE para um ano específico: {args.year}")
            collector.process_fre_data(args.year)
        else:
            collector.run_historical_fre_load()
            
    elif args.task == "daily-update":
        logger.warning("A tarefa 'daily-update' ainda não foi implementada.")
        pass
        
    elif args.task == "company-deep-dive":
        if not args.cvm_code:
            logger.error("O argumento --cvm_code é obrigatório para a tarefa 'company-deep-dive'.")
        else:
            logger.warning("A tarefa 'company-deep-dive' ainda não foi implementada.")
            pass

    logger.info(f"Tarefa '{args.task}' concluída com sucesso!")

if __name__ == "__main__":
    main()
