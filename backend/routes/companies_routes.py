# backend/routes/companies_routes.py
from flask import Blueprint, jsonify
from ..models import Company # Importa o modelo Company
from ..app import db # Importa a instância do SQLAlchemy

# Cria um Blueprint para agrupar as rotas de empresas
companies_bp = Blueprint('companies', __name__)

@companies_bp.route('/companies', methods=['GET'])
def get_companies():
    """Retorna uma lista de todas as empresas."""
    try:
        # Consulta todas as empresas no banco de dados
        companies = Company.query.all()

        # Converte a lista de objetos Company para uma lista de dicionários
        companies_list = []
        for company in companies:
            companies_list.append({
                'cnpj': company.cnpj,
                'name': company.name,
                'created_at': company.created_at.isoformat() if company.created_at else None,
                'updated_at': company.updated_at.isoformat() if company.updated_at else None
            })

        # Retorna a lista de empresas em formato JSON
        return jsonify(companies_list)

    except Exception as e:
        # Em caso de erro, retorna uma mensagem de erro com status 500
        return jsonify({"error": str(e)}), 500

# Adicionar outras rotas relacionadas a empresas aqui (ex: buscar empresa por CNPJ)
# @companies_bp.route('/companies/<string:cnpj>', methods=['GET'])
# def get_company_by_cnpj(cnpj):
#     # ... lógica para buscar empresa por CNPJ ...
#     pass
