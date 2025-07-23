# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv() # Carrega variáveis do arquivo .env

class Config:
    # Configurações básicas do Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-padrao-muito-segura'

    # Configurações do SQLAlchemy
    # CORREÇÃO: A f-string foi movida para a mesma linha da atribuição da variável.
    # Adicionamos client_encoding='utf8' para garantir que o Python e o PostgreSQL
    # conversem usando a mesma codificação (UTF-8), que é o padrão moderno.
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_HOST = os.environ.get('DB_HOST')
    DB_NAME = os.environ.get('DB_NAME')
    
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
        "?sslmode=require"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
