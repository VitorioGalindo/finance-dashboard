# backend/routes/documents_routes.py (CORRIGIDO)
from flask import Blueprint, jsonify
from backend.models import CvmDocument, Company

documents_bp = Blueprint('documents_bp', __name__)

@documents_bp.route('/companies/<string:cnpj>/documents', methods=['GET'])
def get_documents_by_company(cnpj):
    """
    Retorna uma lista de documentos CVM para uma empresa específica,
    ordenados por data de entrega (mais recentes primeiro).
    """
    # Verifica se a empresa existe
    company = Company.query.get(cnpj)
    if not company:
        return jsonify({"error": "Empresa não encontrada"}), 404

    try:
        # CORREÇÃO: Usa 'company_cnpj' que é o nome da propriedade no modelo CvmDocument
        documents = CvmDocument.query.filter_by(company_cnpj=cnpj).order_by(CvmDocument.delivery_date.desc()).all()
        
        documents_list = [doc.to_dict() for doc in documents]
        
        return jsonify(documents_list)
        
    except Exception as e:
        # Adiciona o erro original na resposta para melhor depuração
        return jsonify({
            "error": f"Ocorreu um erro interno no servidor ao buscar os documentos CVM para o CNPJ {cnpj}.",
            "details": str(e)
        }), 500
