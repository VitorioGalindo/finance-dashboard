# backend/app.py
import os
from flask import Flask
from flask_cors import CORS
from .config import Config

# Importação Centralizada: Importa o 'db' do nosso __init__.py
from . import db

def create_app(test_config=None):
    """
    Função de fábrica para criar e configurar a aplicação Flask.
    """
    app = Flask(__name__)
    CORS(app) # Habilita o CORS para permitir requisições do frontend

    if test_config is None:
        # Carrega a configuração a partir do objeto Config se não estiver em modo de teste
        app.config.from_object(Config)
    else:
        # Carrega a configuração de teste se for fornecida
        app.config.from_mapping(test_config)
    
    # Associa a instância do SQLAlchemy com a aplicação Flask
    db.init_app(app)

    # --- Registro dos Blueprints (Rotas) ---
    from backend.routes.companies_routes import companies_bp
    app.register_blueprint(companies_bp)
    
    from backend.routes.ai_routes import ai_bp
    app.register_blueprint(ai_bp)
    
    # Registra o novo blueprint de Portfólio
    from backend.routes.portfolio_routes import portfolio_bp
    app.register_blueprint(portfolio_bp)

    from backend.routes.financials_routes import financials_bp
    app.register_blueprint(financials_bp)
    
    with app.app_context():
        # Importa os modelos aqui para que o SQLAlchemy os reconheça
        from . import models
        
        # O comando a seguir cria as tabelas no banco de dados se elas não existirem.
        # Em um ambiente de produção mais maduro, usaríamos migrações (Flask-Migrate).
        # Por enquanto, para nosso desenvolvimento inicial, isso é suficiente.
        db.create_all()

    return app
