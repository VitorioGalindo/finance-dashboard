# backend/routes/financials_routes.py
from flask import Blueprint, jsonify
from backend.models import FinancialStatement, Company

financials_bp = Blueprint('financials_bp', __name__)

@financials_bp.route('/companies/<string:cnpj>/financials', methods=['GET'])
def get_financials(cnpj):
    """
    Retorna todos os dados financeiros (financial_statements) para uma empresa específica.
    """
    # Verifica se a empresa existe
    company = Company.query.get(cnpj)
    if not company:
        return jsonify({"error": f"Empresa com CNPJ {cnpj} não encontrada"}), 404
        
    try:
        # Busca todos os registros financeiros para o CNPJ fornecido
        statements = FinancialStatement.query.filter_by(company_cnpj=cnpj).all()
        
        # Converte a lista de objetos para dicionários usando o método to_dict()
        statements_list = [stmt.to_dict() for stmt in statements]

        return jsonify(statements_list)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
