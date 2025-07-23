# backend/routes/companies_routes.py
from flask import Blueprint, jsonify
from backend.models import Company
from backend import db

companies_bp = Blueprint('companies_bp', __name__)

@companies_bp.route('/companies', methods=['GET']) # <-- ROTA IMPORTANTE
def get_companies():
    # ... resto do código ...

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
        return jsonify({"error": str(e)}), 500
