# backend/routes/companies_routes.py
from flask import Blueprint, jsonify
from backend.models import Company
import traceback

# CORREÇÃO: O prefixo da URL foi simplificado para /api.
# O nome do recurso ('companies') foi movido para cada rota individualmente.
# Isso elimina a ambiguidade que causava o roteamento incorreto.
companies_bp = Blueprint('companies_bp', __name__, url_prefix='/api')

# ROTA CORRIGIDA: Agora explicitamente /companies
@companies_bp.route('/companies', methods=['GET'])
def get_companies():
    """
    Retorna uma lista de todas as empresas cadastradas.
    """
    try:
        companies = Company.query.all()
        return jsonify([company.to_dict() for company in companies])
    except Exception as e:
        print("="*80)
        print(f"ERRO DETALHADO em get_companies: {e}")
        traceback.print_exc()
        print("="*80)
        return jsonify({
            "error": "Ocorreu um erro interno no servidor ao processar os dados das empresas.",
            "details": str(e)
        }), 500

# ROTA CORRIGIDA: Agora explicitamente /companies/<cnpj>
@companies_bp.route('/companies/<string:cnpj>', methods=['GET'])
def get_company_by_cnpj(cnpj):
    """
    Retorna os dados de uma empresa específica com base no CNPJ.
    """
    try:
        company = Company.query.filter_by(cnpj=cnpj).first_or_404(
            description=f"Nenhuma empresa encontrada com o CNPJ: {cnpj}"
        )
        return jsonify(company.to_dict())
    except Exception as e:
        # Este bloco agora só será acionado por erros genuínos, não por falhas de roteamento.
        print("="*80)
        print(f"ERRO DETALHADO em get_company_by_cnpj para CNPJ {cnpj}: {e}")
        traceback.print_exc()
        print("="*80)
        return jsonify({
            "error": f"Ocorreu um erro interno no servidor ao buscar a empresa de CNPJ {cnpj}.",
            "details": str(e)
        }), 500
