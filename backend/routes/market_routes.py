#!/usr/bin/env python3
"""
Rotas para dados de mercado
"""

from flask import Blueprint, jsonify, request
from backend.models import Company, Ticker, Shareholders
from backend import db
import psycopg2
from psycopg2.extras import RealDictCursor

market_bp = Blueprint('market_bp', __name__)

# Configurações de conexão direta (para queries complexas)
DB_CONFIG = {
    'host': 'cvm-insiders-db.cb2uq8cqs3dn.us-east-2.rds.amazonaws.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'pandora',
    'password': 'Pandora337303$'
}

def get_db_connection():
    """Cria conexão direta com PostgreSQL"""
    return psycopg2.connect(**DB_CONFIG)

@market_bp.route('/market/quotes/<string:ticker>', methods=['GET'])
def get_ticker_quotes(ticker):
    """Retorna cotações de um ticker específico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Busca cotações do ticker
        cursor.execute("""
            SELECT ticker, date, open_price, high_price, low_price, close_price, 
                   volume, price, change, change_percent, market_status, created_at
            FROM quotes 
            WHERE ticker = %s 
            ORDER BY date DESC 
            LIMIT 30
        """, (ticker.upper(),))
        
        quotes = cursor.fetchall()
        
        conn.close()
        
        if not quotes:
            return jsonify({"message": f"Nenhuma cotação encontrada para {ticker}"}), 404
        
        return jsonify({
            "ticker": ticker.upper(),
            "quotes": [dict(quote) for quote in quotes]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@market_bp.route('/market/overview', methods=['GET'])
def get_market_overview():
    """Retorna visão geral do mercado"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Estatísticas gerais
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT ticker) as total_tickers,
                COUNT(*) as total_quotes,
                AVG(close_price) as avg_price,
                SUM(volume) as total_volume
            FROM quotes 
            WHERE date >= CURRENT_DATE - INTERVAL '7 days'
        """)
        
        stats = cursor.fetchone()
        
        # Top gainers (últimos 7 dias)
        cursor.execute("""
            SELECT ticker, close_price, change_percent
            FROM quotes 
            WHERE date >= CURRENT_DATE - INTERVAL '7 days'
            AND change_percent IS NOT NULL
            ORDER BY change_percent DESC 
            LIMIT 5
        """)
        
        top_gainers = cursor.fetchall()
        
        # Top losers (últimos 7 dias)
        cursor.execute("""
            SELECT ticker, close_price, change_percent
            FROM quotes 
            WHERE date >= CURRENT_DATE - INTERVAL '7 days'
            AND change_percent IS NOT NULL
            ORDER BY change_percent ASC 
            LIMIT 5
        """)
        
        top_losers = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            "statistics": dict(stats) if stats else {},
            "top_gainers": [dict(row) for row in top_gainers],
            "top_losers": [dict(row) for row in top_losers]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@market_bp.route('/market/sectors', methods=['GET'])
def get_market_sectors():
    """Retorna empresas agrupadas por setor"""
    try:
        companies = Company.query.filter(
            Company.b3_sector.isnot(None),
            Company.is_active == True
        ).all()
        
        # Agrupa por setor
        sectors = {}
        for company in companies:
            sector = company.b3_sector or "Outros"
            if sector not in sectors:
                sectors[sector] = []
            
            sectors[sector].append({
                "id": company.id,
                "company_name": company.company_name,
                "ticker": company.ticker,
                "cvm_code": company.cvm_code
            })
        
        # Ordena setores por número de empresas
        sorted_sectors = dict(sorted(sectors.items(), key=lambda x: len(x[1]), reverse=True))
        
        return jsonify({
            "sectors": sorted_sectors,
            "total_sectors": len(sorted_sectors),
            "total_companies": len(companies)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@market_bp.route('/market/tickers', methods=['GET'])
def get_all_tickers():
    """Retorna todos os tickers disponíveis"""
    try:
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '', type=str)
        
        # Query base
        query = Ticker.query.join(Company).filter(Company.is_active == True)
        
        # Filtro de busca
        if search:
            query = query.filter(
                db.or_(
                    Ticker.symbol.ilike(f'%{search}%'),
                    Company.company_name.ilike(f'%{search}%')
                )
            )
        
        # Paginação
        tickers = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        result = []
        for ticker in tickers.items:
            company = Company.query.get(ticker.company_id)
            result.append({
                "symbol": ticker.symbol,
                "type": ticker.type,
                "company_id": ticker.company_id,
                "company_name": company.company_name if company else None,
                "sector": company.b3_sector if company else None
            })
        
        return jsonify({
            "tickers": result,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": tickers.total,
                "pages": tickers.pages,
                "has_next": tickers.has_next,
                "has_prev": tickers.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@market_bp.route('/market/insider-transactions', methods=['GET'])
def get_insider_transactions():
    """Retorna transações de insider recentes"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Parâmetros
        limit = request.args.get('limit', 20, type=int)
        cvm_code = request.args.get('cvm_code', type=int)
        
        # Query base
        query = """
            SELECT cvm_code, company_name, insider_name, position, transaction_type,
                   quantity, unit_price, total_value, transaction_date, created_at
            FROM insider_transactions 
        """
        params = []
        
        # Filtro por empresa
        if cvm_code:
            query += " WHERE cvm_code = %s"
            params.append(cvm_code)
        
        query += " ORDER BY transaction_date DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        transactions = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            "transactions": [dict(transaction) for transaction in transactions],
            "total": len(transactions)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@market_bp.route('/market/news', methods=['GET'])
def get_market_news():
    """Retorna notícias do mercado"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Parâmetros
        limit = request.args.get('limit', 10, type=int)
        ticker = request.args.get('ticker', type=str)
        
        # Query base
        if ticker:
            cursor.execute("""
                SELECT news_id, title, summary, content, author, published_at, 
                       url, category, impact_score, related_tickers
                FROM news 
                WHERE related_tickers::text ILIKE %s
                ORDER BY published_at DESC 
                LIMIT %s
            """, (f'%{ticker}%', limit))
        else:
            cursor.execute("""
                SELECT news_id, title, summary, content, author, published_at, 
                       url, category, impact_score, related_tickers
                FROM news 
                ORDER BY published_at DESC 
                LIMIT %s
            """, (limit,))
        
        news = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            "news": [dict(article) for article in news],
            "total": len(news)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

