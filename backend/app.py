# backend/app.py
from flask import Flask
from backend.config import Config
from backend import db
from backend.routes.companies_routes import companies_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializa o db com a aplicação
    db.init_app(app)

    # Registra o blueprint
    app.register_blueprint(companies_bp, url_prefix='/api') # <-- LINHA IMPORTANTE

    @app.route('/')
    def index():
        return "Backend do Dashboard Financeiro está funcionando!"

    return app

# Se este arquivo for executado diretamente
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
