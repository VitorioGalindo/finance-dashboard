# backend/routes/tickers_routes.py
from flask import Blueprint, jsonify, request
from backend.models import Ticker, Company
from sqlalchemy import or_

tickers_bp = Blueprint('tickers_bp', __name__)

@tickers_bp.route('/tickers/search', methods=['GET'])
def search_tickers():
    """
    Busca tickers e nomes de empresas com base em um termo de pesquisa.
    Ex: /api/tickers/search?q=PRIO
    """
    # Pega o termo de pesquisa dos argumentos da URL (?q=...)
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify([]) # Retorna lista vazia se a busca for vazia

    try:
        search_term = f"%{query.upper()}%" # Adiciona '%' para busca parcial (LIKE)

        # Busca tickers que correspondem ao termo ou cuja empresa associada corresponde
        results = Ticker.query.join(Company).filter(
            or_(
                Ticker.ticker.ilike(search_term),
                Company.name.ilike(search_term)
            )
        ).limit(10).all() # Limita a 10 resultados para performance

        # Formata os resultados para o frontend
        search_results = [
            {
                'ticker': ticker.ticker,
                'company_name': ticker.company.name,
                'company_cnpj': ticker.company_cnpj
            }
            for ticker in results
        ]

        return jsonify(search_results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
