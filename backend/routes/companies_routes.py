# backend/routes/companies_routes.py
from flask import Blueprint, jsonify
from backend.models import Company

companies_bp = Blueprint('companies_bp', __name__, url_prefix='/api/companies')

@companies_bp.route('/', methods=['GET'])
def get_companies():
    """
    Retorna uma lista de todas as empresas cadastradas.
    """
    try:
        companies = Company.query.all()
        return jsonify([company.to_dict() for company in companies])
    except Exception as e:
        # Log do erro para depuração
        print(f"Erro ao buscar empresas: {e}")
        return jsonify({"error": "Erro interno ao processar a solicitação"}), 500

@companies_bp.route('/<string:cnpj>', methods=['GET'])
def get_company_by_cnpj(cnpj):
    """
    Retorna os dados de uma empresa específica com base no CNPJ.
    """
    try:
        # Busca a empresa pelo CNPJ no banco de dados.
        # O método first_or_404 é conveniente: ele retorna a empresa
        # ou dispara um erro 404 (Not Found) automaticamente se não encontrar.
        company = Company.query.filter_by(cnpj=cnpj).first_or_404()
        return jsonify(company.to_dict())
    except Exception as e:
        # Captura outras exceções que possam ocorrer
        print(f"Erro ao buscar empresa por CNPJ ({cnpj}): {e}")
        return jsonify({"error": "Erro interno ao buscar dados da empresa"}), 500
