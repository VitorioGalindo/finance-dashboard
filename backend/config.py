# backend/config.py
import os
from dotenv import load_dotenv

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
        # CORREÇÃO CRÍTICA:
        # A URI de conexão com o banco de dados DEVE ser uma única string.
        # A versão anterior com parênteses e quebra de linha criava uma tupla 
        # ('string1', 'string2'), que é uma URI inválida para o SQLAlchemy.
        # Agora, a f-string inteira está em uma linha para formar uma string única e válida.
        SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?sslmode=require"
    else:
        print("ALERTA: Variáveis de ambiente do banco de dados não configuradas. Verifique seu arquivo .env. A aplicação pode não funcionar como esperado.")
        # Fallback para um DB em memória para evitar que a aplicação quebre ao iniciar
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
