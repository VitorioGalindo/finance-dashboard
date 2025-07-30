#!/usr/bin/env python3
"""
Rotas para dados financeiros - VERSÃO CORRIGIDA
"""

from flask import Blueprint, jsonify, request
from backend.models import Company, CVMFinancialData
from backend import db
import psycopg2
from psycopg2.extras import RealDictCursor

financials_bp = Blueprint('financials_bp', __name__)

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

@financials_bp.route('/companies/<int:company_id>/financials', methods=['GET'])
def get_company_financials(company_id):
    """Retorna dados financeiros de uma empresa específica"""
    try:
        # Busca a empresa
        company = Company.query.get(company_id)
        if not company:
            return jsonify({"error": "Empresa não encontrada"}), 404
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Busca dados financeiros da empresa
        cursor.execute("""
            SELECT year, quarter, statement_type, revenue, net_income, 
                   total_assets, total_liabilities, shareholders_equity,
                   operating_cash_flow, investing_cash_flow, financing_cash_flow,
                   created_at
            FROM cvm_financial_data 
            WHERE company_id = %s 
            ORDER BY year DESC, quarter DESC
            LIMIT 20
        """, (company_id,))
        
        financial_data = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            "company": {
                "id": company.id,
                "company_name": company.company_name,
                "cvm_code": company.cvm_code,
                "ticker": company.ticker,
                "b3_sector": company.b3_sector
            },
            "financial_data": [dict(record) for record in financial_data]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@financials_bp.route('/financials/summary', methods=['GET'])
def get_financials_summary():
    """Retorna resumo dos dados financeiros disponíveis"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Estatísticas gerais
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT company_id) as companies_with_data,
                COUNT(*) as total_records,
                MIN(year) as earliest_year,
                MAX(year) as latest_year,
                COUNT(DISTINCT CONCAT(year, quarter)) as periods_covered
            FROM cvm_financial_data
        """)
        
        summary = cursor.fetchone()
        
        # Dados por ano
        cursor.execute("""
            SELECT year, COUNT(*) as records, COUNT(DISTINCT company_id) as companies
            FROM cvm_financial_data 
            GROUP BY year 
            ORDER BY year DESC
        """)
        
        by_year = cursor.fetchall()
        
        # Dados por tipo de demonstração
        cursor.execute("""
            SELECT statement_type, COUNT(*) as records, COUNT(DISTINCT company_id) as companies
            FROM cvm_financial_data 
            GROUP BY statement_type
        """)
        
        by_statement = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            "summary": dict(summary) if summary else {},
            "by_year": [dict(record) for record in by_year],
            "by_statement_type": [dict(record) for record in by_statement]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@financials_bp.route('/financials/companies', methods=['GET'])
def get_companies_with_financials():
    """Retorna empresas que possuem dados financeiros"""
    try:
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        year = request.args.get('year', type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query base
        query = """
            SELECT DISTINCT 
                c.id, c.company_name, c.cvm_code, c.ticker, c.b3_sector,
                COUNT(f.id) as financial_records,
                MAX(f.year) as latest_year,
                MIN(f.year) as earliest_year
            FROM companies c
            INNER JOIN cvm_financial_data f ON c.id = f.company_id
        """
        
        params = []
        
        # Filtro por ano
        if year:
            query += " WHERE f.year = %s"
            params.append(year)
        
        query += """
            GROUP BY c.id, c.company_name, c.cvm_code, c.ticker, c.b3_sector
            ORDER BY financial_records DESC, c.company_name
        """
        
        # Paginação manual
        offset = (page - 1) * per_page
        query += f" LIMIT {per_page} OFFSET {offset}"
        
        cursor.execute(query, params)
        companies = cursor.fetchall()
        
        # Conta total para paginação
        count_query = """
            SELECT COUNT(DISTINCT c.id)
            FROM companies c
            INNER JOIN cvm_financial_data f ON c.id = f.company_id
        """
        
        if year:
            count_query += " WHERE f.year = %s"
            cursor.execute(count_query, [year])
        else:
            cursor.execute(count_query)
        
        total = cursor.fetchone()['count']
        
        conn.close()
        
        return jsonify({
            "companies": [dict(company) for company in companies],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page,
                "has_next": offset + per_page < total,
                "has_prev": page > 1
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@financials_bp.route('/financials/metrics/<int:company_id>', methods=['GET'])
def get_company_metrics(company_id):
    """Calcula métricas financeiras básicas para uma empresa"""
    try:
        company = Company.query.get(company_id)
        if not company:
            return jsonify({"error": "Empresa não encontrada"}), 404
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Busca dados financeiros mais recentes
        cursor.execute("""
            SELECT year, quarter, revenue, net_income, total_assets, 
                   total_liabilities, shareholders_equity
            FROM cvm_financial_data 
            WHERE company_id = %s 
            AND revenue IS NOT NULL 
            AND total_assets IS NOT NULL
            ORDER BY year DESC, quarter DESC
            LIMIT 8
        """, (company_id,))
        
        financial_data = cursor.fetchall()
        
        if not financial_data:
            return jsonify({
                "company": {
                    "id": company.id,
                    "company_name": company.company_name,
                    "cvm_code": company.cvm_code
                },
                "metrics": {},
                "message": "Dados financeiros insuficientes para cálculo de métricas"
            })
        
        # Calcula métricas básicas
        latest = financial_data[0]
        metrics = {}
        
        # ROA (Return on Assets)
        if latest['total_assets'] and latest['net_income']:
            metrics['roa'] = round((latest['net_income'] / latest['total_assets']) * 100, 2)
        
        # ROE (Return on Equity)
        if latest['shareholders_equity'] and latest['net_income']:
            metrics['roe'] = round((latest['net_income'] / latest['shareholders_equity']) * 100, 2)
        
        # Margem Líquida
        if latest['revenue'] and latest['net_income']:
            metrics['net_margin'] = round((latest['net_income'] / latest['revenue']) * 100, 2)
        
        # Debt to Equity
        if latest['total_liabilities'] and latest['shareholders_equity']:
            metrics['debt_to_equity'] = round(latest['total_liabilities'] / latest['shareholders_equity'], 2)
        
        # Crescimento de receita (se tiver dados de períodos anteriores)
        if len(financial_data) >= 2:
            current_revenue = latest['revenue']
            previous_revenue = financial_data[1]['revenue']
            if previous_revenue and current_revenue:
                revenue_growth = ((current_revenue - previous_revenue) / previous_revenue) * 100
                metrics['revenue_growth'] = round(revenue_growth, 2)
        
        conn.close()
        
        return jsonify({
            "company": {
                "id": company.id,
                "company_name": company.company_name,
                "cvm_code": company.cvm_code,
                "ticker": company.ticker
            },
            "latest_period": {
                "year": latest['year'],
                "quarter": latest['quarter']
            },
            "metrics": metrics,
            "raw_data": dict(latest)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500