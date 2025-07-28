# scripts/refactor_schema.py
import os
import sys
from sqlalchemy import create_engine, inspect, text, BigInteger, Text, JSON, String
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scraper.config import DATABASE_URL
from scraper.models import Base

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_database_schema():
    """
    Verifica e cria/altera todas as tabelas e colunas necessárias para o projeto.
    """
    logger.info("Iniciando a verificação e atualização completa do esquema do banco de dados...")
    
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    # 1. Criação de Novas Tabelas
    all_model_tables = set(Base.metadata.tables.keys())
    existing_tables = set(inspector.get_table_names())
    
    tables_to_create = [Base.metadata.tables[name] for name in all_model_tables if name not in existing_tables]
    
    if tables_to_create:
        logger.info(f"As seguintes tabelas serão criadas: {[t.name for t in tables_to_create]}")
        Base.metadata.create_all(bind=engine, tables=tables_to_create)
        logger.info("Novas tabelas criadas com sucesso!")
    else:
        logger.info("Nenhuma nova tabela precisa ser criada.")

    # 2. Alteração de Tipos de Coluna (Generalizado)
    tables_to_check = {
        'capital_structure': {
            'qty_ordinary_shares': BigInteger,
            'qty_preferred_shares': BigInteger,
            'qty_total_shares': BigInteger,
        },
        'company_administrators': {
            'term_of_office': String(100)
        }
    }

    with engine.connect() as connection:
        for table_name, columns_to_alter in tables_to_check.items():
            if table_name in existing_tables:
                logger.info(f"Verificando colunas na tabela '{table_name}'...")
                db_columns = {col['name']: col['type'] for col in inspector.get_columns(table_name)}
                
                for col_name, col_type in columns_to_alter.items():
                    target_type = col_type.compile(dialect=engine.dialect)
                    db_type = db_columns.get(col_name).compile(dialect=engine.dialect)

                    # Compara o tipo genérico e o comprimento para VARCHAR
                    is_different = type(db_columns.get(col_name)) != type(col_type) or \
                                   (isinstance(col_type, String) and db_columns.get(col_name).length < col_type.length)

                    if col_name in db_columns and is_different:
                        logger.info(f"Alterando tipo da coluna '{col_name}' em '{table_name}' para {target_type}...")
                        sql = text(f'ALTER TABLE {table_name} ALTER COLUMN "{col_name}" TYPE {target_type};')
                        connection.execute(sql)
                        connection.commit()
                    else:
                        logger.info(f"Coluna '{col_name}' em '{table_name}' já está com o tipo correto.")
            
    # 3. Adição de Colunas à Tabela 'companies'
    company_columns_to_add = {
        'activity_description': Text,
        'capital_structure_summary': JSON,
    }
    
    if 'companies' in existing_tables:
        logger.info("Verificando colunas na tabela 'companies'...")
        companies_table_columns = [col['name'] for col in inspector.get_columns('companies')]
        with engine.connect() as connection:
            for col_name, col_type in company_columns_to_add.items():
                if col_name not in companies_table_columns:
                    sql = text(f'ALTER TABLE companies ADD COLUMN "{col_name}" {col_type().compile(dialect=engine.dialect)};')
                    connection.execute(sql)
                    connection.commit()

    logger.info("Atualização do esquema do banco de dados concluída!")

if __name__ == "__main__":
    update_database_schema()
