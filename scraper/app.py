# scraper/app.py (CORRIGIDO)
import os
import logging
from flask import Flask
from flask_cors import CORS

# CORREÇÃO: Importa as extensões do arquivo central
from extensions import db

def create_app():
    app = Flask(__name__)
    
    # Carrega a configuração do .env
    # (Você já tem a lógica para isso, que usa os.environ.get)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///mercado_brasil.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # CORREÇÃO: Inicializa o db a partir de extensions.py
    db.init_app(app)
    CORS(app)
    
    # O contexto da aplicação agora é criado aqui
    with app.app_context():
        # Importa os modelos aqui, depois que o 'db' está inicializado
        import models
        # Cria as tabelas
        db.create_all()

        # Importa e registra os blueprints aqui
        from api.companies import companies_bp
        # ... (importar outros blueprints)
        
        app.register_blueprint(companies_bp, url_prefix='/api/v1')
        # ... (registrar outros blueprints)

    @app.route('/')
    def index():
        return "API do Scraper está funcionando!"

    return app

app = create_app()

if __name__ == '__main__':
    # Para rodar, use 'flask run' ou, se executar diretamente,
    # considere que o contexto de importação pode ser um problema.
    # A melhor prática é usar um entrypoint como 'wsgi.py' e rodar com gunicorn.
    # Por agora, o objetivo é criar as tabelas.
    
    # Para garantir que as tabelas sejam criadas ao executar diretamente:
    with app.app_context():
        db.create_all()
    print("Tabelas criadas (se não existiam). Inicie com 'flask run' ou um servidor WSGI.")
