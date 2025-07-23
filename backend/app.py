# backend/app.py
from flask import Flask
from .config import Config
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy() # Inicializa a extensão SQLAlchemy

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app) # Inicializa o SQLAlchemy com a aplicação Flask

    # Importar e registrar blueprints (rotas) aqui depois
    # from .routes.<feature> import <feature>_bp
    # app.register_blueprint(<feature>_bp, url_prefix='/api')

    @app.route('/')
    def index():
        return "Backend do Dashboard Financeiro está funcionando!"

    return app

# Se este arquivo for executado diretamente
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) # Rode em modo debug durante o desenvolvimento
