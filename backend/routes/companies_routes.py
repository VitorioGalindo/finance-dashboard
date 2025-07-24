# backend/routes/companies_routes.py
from flask import Blueprint, jsonify
from backend.models import Company, FinancialStatement, CvmDocument # Importar CvmDocument
import traceback

companies_bp = Blueprint('companies_bp', __name__, url_prefix='/api')

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
        print("="*80)
        print(f"ERRO DETALHADO em get_company_by_cnpj para CNPJ {cnpj}: {e}")
        traceback.print_exc()
        print("="*80)
        return jsonify({
            "error": f"Ocorreu um erro interno no servidor ao buscar a empresa de CNPJ {cnpj}.",
            "details": str(e)
        }), 500

@companies_bp.route('/companies/<string:cnpj>/financials', methods=['GET'])
def get_financial_statements(cnpj):
    """
    Retorna os demonstrativos financeiros de uma empresa específica.
    """
    try:
        company = Company.query.filter_by(cnpj=cnpj).first_or_404(
            description=f"Nenhuma empresa encontrada com o CNPJ: {cnpj}"
        )
        statements = FinancialStatement.query.filter_by(company_cnpj=cnpj).all()
        if not statements:
            return jsonify([])
        return jsonify([statement.to_dict() for statement in statements])
    except Exception as e:
        print("="*80)
        print(f"ERRO DETALHADO em get_financial_statements para CNPJ {cnpj}: {e}")
        traceback.print_exc()
        print("="*80)
        return jsonify({
            "error": f"Ocorreu um erro interno no servidor ao buscar os dados financeiros para o CNPJ {cnpj}.",
            "details": str(e)
        }), 500

# ROTA CORRIGIDA: Aponta para o modelo CvmDocument e a tabela cvm_documents
@companies_bp.route('/companies/<string:cnpj>/documents', methods=['GET'])
def get_cvm_documents(cnpj):
    """
    Retorna os documentos IPE (agora da tabela cvm_documents) de uma empresa.
    """
    try:
        company = Company.query.filter_by(cnpj=cnpj).first_or_404(
            description=f"Nenhuma empresa encontrada com o CNPJ: {cnpj}"
        )
        
        documents = CvmDocument.query.filter_by(company_cnpj=cnpj).order_by(CvmDocument.reference_date.desc()).all()
        
        if not documents:
            return jsonify([])
            
        return jsonify([doc.to_dict() for doc in documents])

    except Exception as e:
        print("="*80)
        print(f"ERRO DETALHADO em get_cvm_documents para CNPJ {cnpj}: {e}")
        traceback.print_exc()
        print("="*80)
        return jsonify({
            "error": f"Ocorreu um erro interno no servidor ao buscar os documentos CVM para o CNPJ {cnpj}.",
            "details": str(e)
        }), 500
