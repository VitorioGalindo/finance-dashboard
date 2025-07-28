# scripts/create_fre_tables.py
import os
import sys
from sqlalchemy import create_engine, inspect, text
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scraper.config import DATABASE_URL
from scraper.models import Base

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_database_schema():
    """
    Verifica e cria/altera todas as tabelas e colunas necessárias para os dados do FRE.
    - Cria as tabelas: 'capital_structure', 'shareholders', 'company_administrators', 'company_risk_factors'.
    - Adiciona colunas à tabela 'companies'.
    """
    logger.info("Iniciando a verificação e atualização completa do esquema do banco de dados para o FRE...")
    
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    # --- 1. Verificação e Criação de Novas Tabelas ---
    
    all_model_tables = set(Base.metadata.tables.keys())
    existing_tables = set(inspector.get_table_names())
    
    tables_to_create = [
        Base.metadata.tables[name] 
        for name in all_model_tables 
        if name not in existing_tables
    ]
    
    if tables_to_create:
        logger.info(f"As seguintes tabelas serão criadas: {[t.name for t in tables_to_create]}")
        try:
            Base.metadata.create_all(bind=engine, tables=tables_to_create)
            logger.info("Novas tabelas criadas com sucesso!")
        except Exception as e:
            logger.error(f"Ocorreu um erro durante a criação de novas tabelas: {e}")
            return
    else:
        logger.info("Nenhuma nova tabela precisa ser criada. Todas já existem.")

    # --- 2. Verificação e Adição de Novas Colunas à Tabela 'companies' ---

    company_columns_to_add = {
        'activity_description': 'TEXT',
        'capital_structure_summary': 'JSON'
    }
    
    logger.info("Verificando colunas na tabela 'companies'...")
    companies_table_columns = [col['name'] for col in inspector.get_columns('companies')]
    
    with engine.connect() as connection:
        for col_name, col_type in company_columns_to_add.items():
            if col_name not in companies_table_columns:
                logger.info(f"Adicionando coluna '{col_name}' do tipo {col_type} à tabela 'companies'...")
                try:
                    # Usamos `text` para executar o SQL de forma segura
                    connection.execute(text(f'ALTER TABLE companies ADD COLUMN "{col_name}" {col_type};'))
                    connection.commit()
                    logger.info(f"Coluna '{col_name}' adicionada com sucesso.")
                except Exception as e:
                    logger.error(f"Falha ao adicionar a coluna '{col_name}': {e}")
                    connection.rollback()
            else:
                logger.info(f"Coluna '{col_name}' já existe na tabela 'companies'.")

    logger.info("Atualização do esquema do banco de dados concluída com sucesso!")

if __name__ == "__main__":
    update_database_schema()
