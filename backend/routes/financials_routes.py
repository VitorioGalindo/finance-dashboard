# backend/routes/financials_routes.py (VERSÃO APRIMORADA COM FILTROS)
from flask import Blueprint, jsonify, request
from backend.models import FinancialStatement, Company

financials_bp = Blueprint('financials_bp', __name__)

@financials_bp.route('/companies/<string:cnpj>/financials', methods=['GET'])
def get_financials(cnpj):
    """
    Retorna dados financeiros para uma empresa, com filtros opcionais.
    Uso: /api/companies/<cnpj>/financials?report_type=DRE&period=ANUAL
    """
    # Verifica se a empresa existe
    company = Company.query.get(cnpj)
    if not company:
        return jsonify({"error": f"Empresa com CNPJ {cnpj} não encontrada"}), 404
        
    try:
        # Pega os parâmetros da URL. Se não forem fornecidos, não são usados no filtro.
        report_type = request.args.get('report_type', type=str)
        period = request.args.get('period', type=str)

        # Começa a construir a query
        query = FinancialStatement.query.filter_by(company_cnpj=cnpj)

        # Adiciona filtros à query se os parâmetros foram fornecidos
        if report_type:
            # O frontend pode pedir 'BPA' ou 'BPP' para o balanço.
            # Se pedir 'BP' (Balanço Patrimonial), podemos retornar ambos.
            if report_type.upper() == 'BP':
                query = query.filter(FinancialStatement.report_type.in_(['BPA', 'BPP']))
            else:
                query = query.filter(FinancialStatement.report_type == report_type.upper())
        
        if period:
            query = query.filter(FinancialStatement.periodo == period.upper())

        # Executa a query final
        statements = query.all()
        
        statements_list = [stmt.to_dict() for stmt in statements]

        return jsonify(statements_list)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
