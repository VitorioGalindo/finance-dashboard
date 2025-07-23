# backend/__init__.py

# Este arquivo inicializa o pacote 'backend' e centraliza extensões do Flask.

from flask_sqlalchemy import SQLAlchemy

# 1. Cria a instância do SQLAlchemy aqui, de forma desacoplada da aplicação.
#    Este objeto 'db' será importado por outras partes do nosso código (modelos, app).
db = SQLAlchemy()
