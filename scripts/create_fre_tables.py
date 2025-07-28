# scripts/create_fre_tables.py
import os
import sys
from sqlalchemy import create_engine, inspect
import logging

# Adiciona o diretório raiz ao path para permitir a importação de módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper.config import DATABASE_URL
from scraper.models import Base  # Importar a Base é crucial, pois ela contém os metadados das tabelas

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_fre_related_tables():
    """
    Cria as tabelas 'capital_structure' and 'shareholders' se elas ainda não existirem.
    """
    logger.info("Iniciando a verificação e criação das tabelas relacionadas ao FRE...")
    
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    # Lista das novas tabelas que queremos criar
    tables_to_create = ['capital_structure', 'shareholders']
    
    # Pega os nomes das tabelas que já existem no banco de dados
    existing_tables = inspector.get_table_names()
    
    # Filtra a lista de tabelas para criar apenas as que não existem
    tables_needing_creation = [
        table_name for table_name in tables_to_create if table_name not in existing_tables
    ]
    
    if not tables_needing_creation:
        logger.info("Todas as tabelas relacionadas ao FRE ('capital_structure', 'shareholders') já existem.")
        return

    logger.info(f"As seguintes tabelas serão criadas: {', '.join(tables_needing_creation)}")
    
    try:
        # A mágica do SQLAlchemy: `Base.metadata.create_all` é idempotente.
        # Ele verifica a existência de cada tabela antes de tentar criá-la.
        # Passamos a lista de tabelas para garantir que só estamos criando o que queremos.
        tables_to_create_objects = [
            Base.metadata.tables[name] for name in tables_needing_creation
        ]
        Base.metadata.create_all(bind=engine, tables=tables_to_create_objects)
        
        logger.info("Tabelas criadas com sucesso!")
        
    except Exception as e:
        logger.error(f"Ocorreu um erro durante a criação das tabelas: {e}")
        # Em um cenário de produção, um tratamento de erro mais robusto seria necessário.

if __name__ == "__main__":
    create_fre_related_tables()
