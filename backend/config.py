# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv() # Carrega variáveis do arquivo .env

class Config:
    # Configurações básicas do Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-padrao-muito-segura' # Altere em produção!

    # Configurações do SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"postgresql+psycopg2://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}/{os.environ.get('DB_NAME')}?sslmode=require"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configurações específicas da aplicação (se houver)
    # CVM_API_URL = "..."
