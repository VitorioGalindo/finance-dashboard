# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv() # Carrega variáveis do arquivo .env

class Config:
    # Configurações básicas do Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-padrao-muito-segura'

    # Configurações do SQLAlchemy
    # ADICIONANDO 'client_encoding=latin1' de volta à string de conexão do SQLAlchemy.
    # Agora que sabemos que os dados no DB estão limpos, isso deve instruir o SQLAlchemy
    # a interpretar corretamente os dados que o PostgreSQL envia.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"postgresql+psycopg2://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}/{os.environ.get('DB_NAME')}?sslmode=require&client_encoding=latin1"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
