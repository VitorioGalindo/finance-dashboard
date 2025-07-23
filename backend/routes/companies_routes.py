# backend/routes/companies_routes.py
from flask import Blueprint, jsonify
from backend.models import Company
import traceback # Importar o traceback para logs detalhados

companies_bp = Blueprint('companies_bp', __name__, url_prefix='/api/companies')

@companies_bp.route('/', methods=['GET'])
def get_companies():
    """
    Retorna uma lista de todas as empresas cadastradas.
    """
    try:
        companies = Company.query.all()
        # A serialização acontece aqui, este é um ponto de falha comum.
        return jsonify([company.to_dict() for company in companies])
    except Exception as e:
        # CORREÇÃO: Melhora no log de erro.
        # Imprime o stack trace completo do erro no console do Flask.
        # Isso nos dará a causa exata do erro 500.
        print("="*80)
        print(f"ERRO DETALHADO em get_companies: {e}")
        traceback.print_exc()
        print("="*80)
        # Retorna uma mensagem de erro mais informativa para o frontend.
        return jsonify({
            "error": "Ocorreu um erro interno no servidor ao processar os dados das empresas.",
            "details": str(e)
        }), 500

@companies_bp.route('/<string:cnpj>', methods=['GET'])
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
        # CORREÇÃO: Melhora no log de erro.
        print("="*80)
        print(f"ERRO DETALHADO em get_company_by_cnpj para CNPJ {cnpj}: {e}")
        traceback.print_exc()
        print("="*80)
        return jsonify({
            "error": f"Ocorreu um erro interno no servidor ao buscar a empresa de CNPJ {cnpj}.",
            "details": str(e)
        }), 500
