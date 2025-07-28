# scraper/services/insider_transactions_service.py
import logging
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from scraper.database import get_db_session, engine
from scraper.models import Company, InsiderTransaction

# (A lógica de acquisition.py e parser.py será adaptada e inserida aqui)

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InsiderTransactionsCollector:
    """
    Serviço para coletar, processar e armazenar as transações de insiders
    do portal RAD da CVM.
    """
    def __init__(self):
        # Aqui podemos inicializar a sessão de requests e outras configurações
        pass

    def get_companies_from_db(self):
        """Busca as empresas do nosso banco de dados para iniciar o processo."""
        with get_db_session() as session:
            companies = session.query(Company.cvm_code, Company.cnpj).all()
            # Retorna um formato fácil de usar, por exemplo, um dicionário
            return {str(cvm_code): cnpj for cvm_code, cnpj in companies}

    def run_insider_transactions_load(self):
        """
        Orquestra o processo completo de coleta de transações de insiders.
        """
        logger.info("--- INICIANDO CARGA DE TRANSAÇÕES DE INSIDERS ---")
        
        # 1. Obter a lista de empresas do nosso banco de dados
        companies = self.get_companies_from_db()
        logger.info(f"Encontradas {len(companies)} empresas na base de dados para monitorar.")

        # 2. (A SER IMPLEMENTADO) Adaptar a lógica de 'acquisition.py'
        #    para buscar os PDFs/links para cada empresa.
        #    - A busca será feita pelo código CVM.
        
        # 3. (A SER IMPLEMENTADO) Adaptar a lógica de 'parser.py'
        #    para extrair as transações de cada documento.

        # 4. (A SER IMPLEMENTADO) Para cada transação encontrada:
        #    - Criar um objeto do nosso modelo `InsiderTransaction`.
        #    - Popular com os dados extraídos.
        #    - Salvar no banco de dados usando o `get_db_session`.

        logger.info("--- CARGA DE TRANSAÇÕES DE INSIDERS (EM DESENVOLVIMENTO) ---")

# Exemplo de como seria a execução
if __name__ == '__main__':
    collector = InsiderTransactionsCollector()
    collector.run_insider_transactions_load()
