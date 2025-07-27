# backend/routes/financials_routes.py (VERSÃO FINAL PÓS-REATORAÇÃO)
from flask import Blueprint, jsonify, request
from backend.models import FinancialReport, FinancialStatement, Company
from sqlalchemy.orm import joinedload

financials_bp = Blueprint('financials_bp', __name__)

@financials_bp.route('/companies/<string:cnpj>/financials', methods=['GET'])
def get_financials(cnpj):
    """
    Retorna os dados financeiros anuais (DFP) de uma empresa,
    estruturados por ano para fácil consumo do frontend.
    """
    company = Company.query.get(cnpj)
    if not company:
        return jsonify({"error": f"Empresa com CNPJ {cnpj} não encontrada"}), 404
        
    try:
        # Busca todos os relatórios anuais da empresa e suas respectivas linhas (statements)
        # O 'joinedload' otimiza a busca, fazendo um JOIN em vez de múltiplas queries.
        reports = FinancialReport.query.options(
            joinedload(FinancialReport.statements)
        ).filter_by(
            company_cnpj=cnpj,
            period='ANUAL',
            report_type='DFP'
        ).order_by(FinancialReport.year).all()
        
        # Estrutura a resposta como um dicionário onde a chave é o ano
        response_data = {}
        for report in reports:
            # Para cada ano, cria um dicionário para os tipos de demonstrativos (DRE, BPA, etc.)
            response_data[report.year] = {
                'DRE': [],
                'BPA': [],

                'BPP': [],
                'DFC_MD': [],
                'DFC_MI': []
            }
            # Agrupa as linhas do relatório em seus respectivos demonstrativos
            for statement in report.statements:
                if statement.statement_type in response_data[report.year]:
                    response_data[report.year][statement.statement_type].append(statement.to_dict())

        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
