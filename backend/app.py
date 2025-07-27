# backend/app.py
from flask import Flask
from flask_cors import CORS
from backend.config import Config
from backend import db

def create_app():
    """
    Função de fábrica para criar e configurar a aplicação Flask.
    """
    app = Flask(__name__)
    CORS(app) # Habilita o CORS para permitir requisições do frontend

    # Carrega a configuração a partir do objeto Config
    app.config.from_object(Config)
    
    # Associa a instância do SQLAlchemy com a aplicação Flask
    db.init_app(app)

    # Importa e registra os blueprints DENTRO da função de fábrica
    # para evitar importações circulares.
    from backend.routes.companies_routes import companies_bp
    from backend.routes.documents_routes import documents_bp # <-- ADICIONAR ESTA LINHA

    app.register_blueprint(companies_bp, url_prefix='/api')
    app.register_blueprint(documents_bp, url_prefix='/api') # <-- ADICIONAR ESTA LINHA

    @app.route('/')
    def index():
        return "Backend do Dashboard Financeiro está funcionando!"

    return app
