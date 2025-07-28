# scraper/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from scraper.config import DATABASE_URL
import logging

# Configura o logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Cria a engine do SQLAlchemy. 
    # O pool_pre_ping verifica as conexões antes de usá-las, o que ajuda a lidar com conexões que podem ter sido fechadas pelo banco de dados.
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    # Cria uma classe de Session configurada. Esta é a "fábrica" de sessões.
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    logger.info("Conexão com o banco de dados e SessionLocal configurados com sucesso.")

except Exception as e:
    logger.error(f"❌ Falha ao configurar a conexão com o banco de dados: {e}")
    # Se a configuração falhar, definimos as variáveis como None para que as tentativas de uso falhem de forma clara.
    engine = None
    SessionLocal = None

@contextmanager
def get_db_session():
    """
    Fornece uma sessão de banco de dados transacional usando um gerenciador de contexto.
    Garante que a sessão seja sempre fechada corretamente, mesmo em caso de erros.
    
    Uso:
    with get_db_session() as session:
        session.query(...)
    """
    if SessionLocal is None:
        raise ConnectionError("A fábrica de sessões (SessionLocal) não foi inicializada. Verifique a conexão com o banco.")
        
    session = SessionLocal()
    try:
        # Entrega a sessão para ser usada no bloco 'with'
        yield session
        # Se tudo no bloco 'with' ocorrer sem erros, commita a transação.
        session.commit()
        logger.debug("Sessão commitada com sucesso.")
    except Exception as e:
        # Se ocorrer qualquer exceção, faz o rollback para não deixar dados inconsistentes.
        logger.error(f"Erro na sessão do banco de dados, fazendo rollback. Erro: {e}")
        session.rollback()
        # Propaga a exceção para que o código que chamou saiba do erro.
        raise
    finally:
        # Garante que a sessão seja fechada, liberando a conexão de volta para o pool.
        session.close()
        logger.debug("Sessão fechada.")

def check_db_connection():
    """Tenta conectar ao banco de dados para verificar o status."""
    if engine is None:
        logger.error("Engine do SQLAlchemy não está disponível.")
        return False
    try:
        with engine.connect() as connection:
            logger.info("✅ Conexão com o banco de dados verificada com sucesso!")
            return True
    except Exception as e:
        logger.error(f"❌ Falha ao conectar com o banco de dados: {e}")
        return False

# Exemplo de como usar (para teste)
if __name__ == '__main__':
    check_db_connection()
