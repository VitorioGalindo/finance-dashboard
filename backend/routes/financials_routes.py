# backend/routes/financials_routes.py

from flask import Blueprint, jsonify
from sqlalchemy import func, desc
from backend.models import Company, Ticker, FinancialStatement, RealtimeQuote, CvmDocument
from backend import db
import traceback

financials_bp = Blueprint('financials_bp', __name__, url_prefix='/api/financials')

@financials_bp.route('/overview/<string:ticker_symbol>')
def get_company_overview(ticker_symbol):
    """
    Retorna um resumo completo (cadastral, financeiro, cotação e documentos)
    para um determinado ticker.
    """
    try:
        ticker_symbol = ticker_symbol.upper()

        # 1. Encontrar o CNPJ a partir do Ticker
        ticker_info = Ticker.query.filter_by(ticker=ticker_symbol).first()
        if not ticker_info:
            return jsonify({"error": f"Ticker '{ticker_symbol}' não encontrado."}), 404
        
        cnpj = ticker_info.company_cnpj

        # 2. Buscar dados da empresa e cotação
        company_info = Company.query.get(cnpj)
        realtime_quote = RealtimeQuote.query.get(ticker_symbol)

        # 3. Buscar os últimos Fatos Relevantes (ex: 5 mais recentes)
        relevant_facts = CvmDocument.query.filter(
            CvmDocument.company_cnpj == cnpj,
            CvmDocument.category == 'Fato Relevante'
        ).order_by(desc(CvmDocument.reference_date)).limit(5).all()

        # 4. Buscar um conjunto expandido de dados financeiros
        # Mapeamento de nomes amigáveis para códigos de conta
        account_map = {
            "receita_liquida": "3.01",
            "lucro_bruto": "3.03",
            "ebit": "3.05",
            "lucro_liquido": "3.11",
            "patrimonio_liquido": "2.03",
            "divida_bruta": "2.01.04", # Passivo Circulante - Empréstimos
            "divida_liquida": "2.02.01", # Passivo Não-Circulante - Empréstimos
            "disponibilidades": "1.01.01" # Caixa e Equivalentes
        }
        
        financials = {}
        # Buscando o último valor ANUAL para cada conta
        for key, code in account_map.items():
            statement = FinancialStatement.query.filter(
                FinancialStatement.company_cnpj == cnpj,
                FinancialStatement.account_code == code,
                FinancialStatement.period == 'ANUAL'
            ).order_by(desc(FinancialStatement.reference_date)).first()
            
            if statement:
                financials[key] = statement.to_dict()

        # 5. Montar a resposta final
        overview_data = {
            "company": company_info.to_dict() if company_info else None,
            "quote": realtime_quote.to_dict() if realtime_quote else None,
            "relevant_facts": [doc.to_dict() for doc in relevant_facts],
            "financials": financials
        }

        return jsonify(overview_data)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Erro interno ao buscar dados da empresa.", "details": str(e)}), 500