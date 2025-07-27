# backend/routes/documents_routes.py
from flask import Blueprint, jsonify
from backend.models import CvmDocument, Company

# Cria um Blueprint para agrupar as rotas de documentos
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
        # Busca todos os documentos associados ao CNPJ, ordenados
        documents = CvmDocument.query.filter_by(cnpj_companhia=cnpj).order_by(CvmDocument.data_entrega.desc()).all()
        
        # Converte a lista de objetos CvmDocument para uma lista de dicionários
        documents_list = [doc.to_dict() for doc in documents]
        
        return jsonify(documents_list)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
