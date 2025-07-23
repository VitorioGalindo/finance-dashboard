# backend/app.py
from flask import Flask
from .config import Config
from . import db # <-- Importa a instância db de __init__.py

# Importar e registrar blueprints (rotas) aqui depois
from .routes.companies_routes import companies_bp # <-- Adicionar esta linha

# db = SQLAlchemy() # <-- REMOVER esta linha

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app) # Inicializa o SQLAlchemy com a aplicação Flask

    # Registrar blueprints
    app.register_blueprint(companies_bp, url_prefix='/api')

    @app.route('/')
    def index():
        return "Backend do Dashboard Financeiro está funcionando!"

    return app

# Se este arquivo for executado diretamente
if __name__ == '__main__':
    # Este bloco pode precisar ser ajustado para rodar com flask run
    # Flask run é a forma recomendada, então este bloco pode ser menos crucial
    app = create_app()
    app.run(debug=True)
