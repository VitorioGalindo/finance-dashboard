# scripts/refactor_schema.py
import os
import sys
from sqlalchemy import create_engine, text, inspect
import logging

# Adiciona o diretório raiz ao path para permitir a importação de módulos do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importa a string de conexão e os modelos
from scraper.config import DATABASE_URL
from scraper.models import Base  # Importa a Base para garantir que os modelos sejam conhecidos

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_company_id_to_financial_statements():
    """
    Verifica se a coluna 'company_id' existe na tabela 'financial_statements'
    e, se não existir, a adiciona com a devida chave estrangeira.
    """
    logger.info("Iniciando a verificação e refatoração do esquema do banco de dados...")
    
    # Cria a engine de conexão com o banco
    engine = create_engine(DATABASE_URL)
    
    # Cria um 'Inspector' para examinar o esquema do banco de dados
    inspector = inspect(engine)
    
    table_name = 'financial_statements'
    column_name = 'company_id'
    
    # Busca a lista de colunas da tabela
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    
    # 1. VERIFICA E ADICIONA A COLUNA
    if column_name not in columns:
        logger.info(f"A coluna '{column_name}' não foi encontrada na tabela '{table_name}'.")
        logger.info(f"Adicionando a coluna '{column_name}' do tipo INTEGER...")
        
        try:
            with engine.connect() as connection:
                # O ideal é usar uma ferramenta de migração como Alembic, mas para uma
                # alteração simples, um SQL direto é aceitável.
                # A coluna é adicionada como NULLABLE primeiro para não falhar em tabelas com dados.
                connection.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" INTEGER;'))
                connection.commit()
            logger.info("Coluna adicionada com sucesso.")
        except Exception as e:
            logger.error(f"Falha ao adicionar a coluna: {e}")
            return # Aborta se a coluna não puder ser adicionada

    else:
        logger.info(f"A coluna '{column_name}' já existe na tabela '{table_name}'. Nenhuma ação necessária para a coluna.")

    # 2. VERIFICA E ADICIONA A CHAVE ESTRANGEIRA (FOREIGN KEY)
    foreign_keys = inspector.get_foreign_keys(table_name)
    fk_exists = any(fk['constrained_columns'] == [column_name] for fk in foreign_keys)
    
    if not fk_exists:
        logger.info(f"A chave estrangeira para '{column_name}' não foi encontrada.")
        logger.info("Adicionando a constraint de chave estrangeira...")
        
        fk_name = f"fk_{table_name}_{column_name}" # Nome padrão para a constraint
        try:
            with engine.connect() as connection:
                # Adiciona a constraint de chave estrangeira referenciando a tabela 'companies'
                sql_command = text(f'ALTER TABLE "{table_name}" ADD CONSTRAINT "{fk_name}" FOREIGN KEY ("{column_name}") REFERENCES companies(id);')
                connection.execute(sql_command)
                connection.commit()
            logger.info("Chave estrangeira adicionada com sucesso.")
        except Exception as e:
            logger.error(f"Falha ao adicionar a chave estrangeira: {e}")
            logger.warning("A coluna 'company_id' foi adicionada, mas a constraint de FK não pôde ser criada. Isso pode indicar um problema de integridade ou tipo de dados.")
            
    else:
        logger.info(f"A chave estrangeira para '{column_name}' já existe. Nenhuma ação necessária para a constraint.")
        
    # 3. (OPCIONAL) Preencher a nova coluna company_id com base nos cvm_codes existentes
    # Esta etapa seria necessária se já existissem dados na tabela financial_statements
    # antes da adição da coluna.
    logger.info("Verificando se há necessidade de popular a coluna 'company_id'...")
    with engine.connect() as connection:
        # Verifica se há linhas onde company_id é NULL
        result = connection.execute(text(f'SELECT COUNT(*) FROM "{table_name}" WHERE "{column_name}" IS NULL;'))
        rows_to_update = result.scalar()
        
        if rows_to_update > 0:
            logger.info(f"Encontradas {rows_to_update} linhas com 'company_id' nulo. Tentando popular...")
            try:
                # Este comando atualiza a tabela financial_statements, pegando o 'id' correspondente
                # da tabela 'companies' onde os 'cvm_code' são iguais.
                update_sql = text(f"""
                UPDATE "{table_name}" AS fs
                SET "{column_name}" = c.id
                FROM companies AS c
                WHERE fs.cvm_code = c.cvm_code AND fs."{column_name}" IS NULL;
                """)
                update_result = connection.execute(update_sql)
                connection.commit()
                logger.info(f"{update_result.rowcount} linhas foram atualizadas com o 'company_id' correspondente.")
            except Exception as e:
                logger.error(f"Falha ao tentar popular a coluna 'company_id': {e}")
        else:
            logger.info("Nenhuma linha precisa ser atualizada. A coluna 'company_id' está populada.")

    # 4. ALTERAR A COLUNA PARA NOT NULL (se desejado, após o preenchimento)
    # Esta é a última etapa para garantir a integridade dos dados.
    logger.info("Verificando se a coluna 'company_id' permite valores nulos...")
    columns_after_update = [col for col in inspector.get_columns(table_name) if col['name'] == column_name]
    if columns_after_update and columns_after_update[0]['nullable']:
        logger.info("A coluna 'company_id' ainda permite nulos. Alterando para NOT NULL...")
        try:
            with engine.connect() as connection:
                connection.execute(text(f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" SET NOT NULL;'))
                connection.commit()
                logger.info("Coluna alterada para NOT NULL com sucesso.")
        except Exception as e:
            logger.error(f"Falha ao alterar a coluna para NOT NULL: {e}. Verifique se todas as linhas foram populadas.")
    else:
        logger.info("A coluna 'company_id' já está definida como NOT NULL.")

    logger.info("Refatoração do esquema concluída com sucesso!")

if __name__ == "__main__":
    add_company_id_to_financial_statements()
