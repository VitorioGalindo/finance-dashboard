# backend/routes/companies_routes.py
from flask import Blueprint, jsonify
from backend.models import Company
from backend import db
import unicodedata

companies_bp = Blueprint('companies_bp', __name__)

@companies_bp.route('/companies', methods=['GET'])
def get_companies():
    """Retorna uma lista de todas as empresas."""
    try:
        companies = Company.query.all()

        companies_list = []
        for company in companies:
            company_name = company.name
            if company_name:
                try:
                    # Tenta decodificar usando latin1, cp1252 e utf-8, substituindo erros
                    company_name = company_name.encode('latin1').decode('utf-8', errors='replace')
                except UnicodeEncodeError:
                    try:
                        company_name = company_name.encode('cp1252').decode('utf-8', errors='replace')
                    except:
                        company_name = company_name.encode('utf-8').decode('utf-8', errors='replace')


                # Remove caracteres de controle e normaliza a string
                company_name = ''.join(c for c in company_name if unicodedata.category(c) != 'Cc')
                company_name = unicodedata.normalize('NFKD', company_name).encode('ascii', 'ignore').decode('utf-8') # Transliterate


            companies_list.append({
                'cnpj': company.cnpj,
                'name': company_name if company_name else None,
                'created_at': company.created_at.isoformat() if company.created_at else None,
                'updated_at': company.updated_at.isoformat() if company.updated_at else None
            })

        return jsonify(companies_list)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
