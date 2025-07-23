# backend/config.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv() # Carrega variáveis do arquivo .env

class Config:
    # Configurações básicas do Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-padrao-muito-segura'

    # Configurações do SQLAlchemy
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_HOST = os.environ.get('DB_HOST')
    DB_NAME = os.environ.get('DB_NAME')
    
    SQLALCHEMY_DATABASE_URI = None
    
    # Verifica se todas as variáveis de ambiente para o DB estão presentes
    if all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
        # A URI de conexão com o banco de dados.
        SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?sslmode=require"
    else:
        print("ALERTA: Variáveis de ambiente do banco de dados não configuradas. Verifique seu arquivo .env. A aplicação pode não funcionar como esperado.")
        # Fallback para um DB em memória para evitar que a aplicação quebre ao iniciar
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

def get_db_engine():
    """
    Cria e retorna uma engine do SQLAlchemy baseada na URI de configuração.
    Esta função centraliza a criação da engine para ser usada por scripts
    e outras partes da aplicação que não estão diretamente no contexto do Flask.
    """
    uri = Config.SQLALCHEMY_DATABASE_URI
    if uri.startswith('sqlite'):
        print("AVISO: get_db_engine está usando o banco de dados em memória (SQLite) de fallback.")
    
    # pool_pre_ping=True verifica a validade das conexões antes de usá-las,
    # o que ajuda a lidar com conexões que foram encerradas pelo servidor de BD.
    return create_engine(uri, pool_pre_ping=True)

