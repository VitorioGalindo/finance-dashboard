# scripts/cvm-insiders/core/database.py
import sys
import os
from contextlib import contextmanager

# Adiciona o diretório raiz do projeto ao path do Python
# Isso permite que o script encontre o pacote 'backend'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend import db
from backend.app import create_app

# O scraper roda fora do contexto de uma requisição Flask,
# então precisamos criar um contexto de aplicação para acessar as extensões do Flask.
app = create_app()

@contextmanager
def get_db():
    """
    Fornece uma sessão do banco de dados dentro de um contexto de aplicação Flask.
    Isso substitui a antiga função get_db que criava sua própria sessão.
    """
    with app.app_context():
        # A sessão é gerenciada pelo Flask-SQLAlchemy, então apenas a retornamos.
        # O commit e o fechamento são tratados pelo bloco da transação no código que a utiliza.
        yield db.session
