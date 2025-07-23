# backend/routes/companies_routes.py (VERSÃO FINAL E LIMPA)
from flask import Blueprint, jsonify
from backend.models import Company

companies_bp = Blueprint('companies_bp', __name__)

@companies_bp.route('/companies', methods=['GET'])
def get_companies():
    """Retorna uma lista de todas as empresas."""
    try:
        companies = Company.query.all()
        
        companies_list = [
            {
                'cnpj': company.cnpj,
                'name': company.name,
                'created_at': company.created_at.isoformat() if company.created_at else None,
                'updated_at': company.updated_at.isoformat() if company.updated_at else None
            } 
            for company in companies
        ]
        
        return jsonify(companies_list)
    except Exception as e:
        # Retorna o erro real para depuração, caso ocorra
        return jsonify({"error": str(e)}), 500
