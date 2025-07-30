# backend/app.py - VERSÃO CORRIGIDA
from flask import Flask, jsonify
from flask_cors import CORS
from backend.config import Config
from backend import db

def create_app():
    """
    Função de fábrica para criar e configurar a aplicação Flask.
    """
    app = Flask(__name__)
    CORS(app) # Habilita o CORS para permitir requisições do frontend

    app.config.from_object(Config)
    db.init_app(app)

    # Importa e registra os blueprints DENTRO da função de fábrica
    try:
        from backend.routes.companies_routes import companies_bp
        app.register_blueprint(companies_bp, url_prefix='/api')
    except ImportError as e:
        print(f"Aviso: Não foi possível importar companies_routes: {e}")

    try:
        from backend.routes.documents_routes import documents_bp
        app.register_blueprint(documents_bp, url_prefix='/api')
    except ImportError as e:
        print(f"Aviso: Não foi possível importar documents_routes: {e}")

    try:
        from backend.routes.tickers_routes import tickers_bp
        app.register_blueprint(tickers_bp, url_prefix='/api')
    except ImportError as e:
        print(f"Aviso: Não foi possível importar tickers_routes: {e}")

    try:
        from backend.routes.financials_routes import financials_bp
        app.register_blueprint(financials_bp, url_prefix='/api')
    except ImportError as e:
        print(f"Aviso: Não foi possível importar financials_routes: {e}")

    try:
        from backend.routes.market_routes import market_bp
        app.register_blueprint(market_bp, url_prefix='/api')
    except ImportError as e:
        print(f"Aviso: Não foi possível importar market_routes: {e}")

    @app.route('/')
    def index():
        return "Backend do Dashboard Financeiro está funcionando!"

    @app.route('/health')
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "Finance Dashboard Backend",
            "version": "1.0.0"
        })

    return app