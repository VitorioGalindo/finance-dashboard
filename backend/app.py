# backend/app.py
from flask import Flask
from .config import Config
from flask_sqlalchemy import SQLAlchemy

# Importar e registrar blueprints (rotas) aqui depois
from .routes.companies_routes import companies_bp # <-- Adicionar esta linha

db = SQLAlchemy() # Inicializa a extensão SQLAlchemy

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app) # Inicializa o SQLAlchemy com a aplicação Flask

    # Registrar blueprints
    app.register_blueprint(companies_bp, url_prefix='/api') # <-- Adicionar esta linha para registrar o blueprint

    @app.route('/')
    def index():
        return "Backend do Dashboard Financeiro está funcionando!"

    return app

# Se este arquivo for executado diretamente
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) # Rode em modo debug durante o desenvolvimento
