# backend/routes/documents_routes.py (VERSÃO FINAL CORRIGIDA)
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
        return jsonify({"error": f"Empresa com CNPJ {cnpj} não encontrada"}), 404

    try:
        # A consulta agora funciona porque o modelo CvmDocument reflete a tabela real
        # Filtramos por 'company_cnpj' que é o nome da propriedade no modelo.
        documents = CvmDocument.query.filter_by(company_cnpj=cnpj).order_by(CvmDocument.delivery_date.desc()).all()
        
        # Converte a lista de objetos para dicionários
        documents_list = [{
            'id': doc.id,
            'company_cnpj': doc.company_cnpj,
            'company_name': doc.company_name,
            'category': doc.category,
            'doc_type': doc.doc_type,
            'subject': doc.subject,
            'delivery_date': doc.delivery_date.isoformat() if doc.delivery_date else None,
            'download_link': doc.download_link
        } for doc in documents]
        
        return jsonify(documents_list)
        
    except Exception as e:
        return jsonify({
            "error": "Ocorreu um erro interno no servidor.",
            "details": str(e)
        }), 500
