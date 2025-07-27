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
    CORS(app) # Habilita o CORS

    app.config.from_object(Config)
    db.init_app(app)

    # Importa e registra os blueprints
    from backend.routes.companies_routes import companies_bp
    from backend.routes.documents_routes import documents_bp
    from backend.routes.tickers_routes import tickers_bp       # <-- ADICIONADO
    from backend.routes.financials_routes import financials_bp # <-- ADICIONADO

    app.register_blueprint(companies_bp, url_prefix='/api')
    app.register_blueprint(documents_bp, url_prefix='/api')
    app.register_blueprint(tickers_bp, url_prefix='/api')       # <-- ADICIONADO
    app.register_blueprint(financials_bp, url_prefix='/api') # <-- ADICIONADO

    @app.route('/')
    def index():
        return "Backend do Dashboard Financeiro está funcionando!"

    return app
