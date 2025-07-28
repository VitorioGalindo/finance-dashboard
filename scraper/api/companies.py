from flask import Blueprint, request, jsonify
from utils.auth import require_api_key
from utils.rate_limiter import apply_rate_limit
from utils.validators import validate_cvm_code, validate_pagination, validate_report_type, validate_aggregation
from services.data_fetcher import data_fetcher
from services.calculations import financial_calc
from models import Company, FinancialStatement, db
from datetime import datetime

companies_bp = Blueprint('companies', __name__)

@companies_bp.route('/companies', methods=['GET'])
@require_api_key
@apply_rate_limit
def list_companies():
    """Lista paginada de empresas com filtros"""
    # Validate pagination
    valid, error, page, limit = validate_pagination()
    if not valid:
        return jsonify({'error': error}), 400
    
    # Get filter parameters
    sector = request.args.get('sector')
    segment = request.args.get('segment')
    is_b3_listed = request.args.get('is_b3_listed')
    
    # Build query
    query = Company.query
    
    if sector:
        query = query.filter(Company.b3_sector.ilike(f'%{sector}%'))
    if segment:
        query = query.filter(Company.b3_listing_segment.ilike(f'%{segment}%'))
    if is_b3_listed is not None:
        query = query.filter(Company.is_b3_listed == (is_b3_listed.lower() == 'true'))
    
    # Apply pagination
    total = query.count()
    companies = query.offset((page - 1) * limit).limit(limit).all()
    
    # Format response
    companies_data = []
    for company in companies:
        companies_data.append({
            'cvm_code': company.cvm_code,
            'company_name': company.company_name,
            'trade_name': company.trade_name,
            'cnpj': company.cnpj,
            'founded_date': company.founded_date.isoformat() if company.founded_date else None,
            'main_activity': company.main_activity,
            'website': company.website,
            'controlling_interest': company.controlling_interest,
            'is_state_owned': company.is_state_owned,
            'is_foreign': company.is_foreign,
            'is_b3_listed': company.is_b3_listed,
            'b3_issuer_code': company.b3_issuer_code,
            'b3_listing_segment': company.b3_listing_segment,
            'b3_sector': company.b3_sector,
            'b3_subsector': company.b3_subsector,
            'b3_segment': company.b3_segment,
            'tickers': company.tickers,
            'market_cap': company.market_cap,
            'employee_count': company.employee_count,
            'about': company.about
        })
    
    return jsonify({
        'companies': companies_data,
        'pagination': {
            'current_page': page,
            'total_pages': (total + limit - 1) // limit,
            'total_items': total,
            'per_page': limit
        }
    })

@companies_bp.route('/companies/<int:cvm_code>', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_company_details(cvm_code):
    """Detalhes completos da empresa"""
    valid, error = validate_cvm_code(cvm_code)
    if not valid:
        return jsonify({'error': error}), 400
    
    # Try to fetch from database first
    company = Company.query.filter_by(cvm_code=cvm_code).first()
    
    if not company:
        # Fetch from external API
        company_data = data_fetcher.fetch_company_data(cvm_code)
        if company_data.get('error'):
            return jsonify({'error': 'Company not found'}), 404
        
        return jsonify(company_data)
    
    # Return database data
    return jsonify({
        'cvm_code': company.cvm_code,
        'company_name': company.company_name,
        'trade_name': company.trade_name,
        'cnpj': company.cnpj,
        'founded_date': company.founded_date.isoformat() if company.founded_date else None,
        'main_activity': company.main_activity,
        'website': company.website,
        'controlling_interest': company.controlling_interest,
        'is_state_owned': company.is_state_owned,
        'is_foreign': company.is_foreign,
        'is_b3_listed': company.is_b3_listed,
        'b3_issuer_code': company.b3_issuer_code,
        'b3_listing_segment': company.b3_listing_segment,
        'b3_sector': company.b3_sector,
        'b3_subsector': company.b3_subsector,
        'b3_segment': company.b3_segment,
        'tickers': company.tickers,
        'market_cap': company.market_cap,
        'employee_count': company.employee_count,
        'about': company.about
    })

@companies_bp.route('/companies/<int:cvm_code>/raw-reports', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_raw_reports(cvm_code):
    """Relatórios brutos (DFP/ITR)"""
    valid, error = validate_cvm_code(cvm_code)
    if not valid:
        return jsonify({'error': error}), 400
    
    # Validate optional parameters
    report_type = request.args.get('report_type')
    aggregation = request.args.get('aggregation')
    
    if report_type:
        valid, error = validate_report_type(report_type)
        if not valid:
            return jsonify({'error': error}), 400
    
    if aggregation:
        valid, error = validate_aggregation(aggregation)
        if not valid:
            return jsonify({'error': error}), 400
    
    # Fetch financial statements
    statements = data_fetcher.fetch_financial_statements(cvm_code, report_type, aggregation)
    
    if not statements:
        return jsonify({'error': 'No financial statements found'}), 404
    
    return jsonify(statements)

@companies_bp.route('/companies/<int:cvm_code>/financial-ratios', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_financial_ratios(cvm_code):
    """Indicadores financeiros calculados"""
    valid, error = validate_cvm_code(cvm_code)
    if not valid:
        return jsonify({'error': error}), 400
    
    # Fetch latest financial statements
    statements = data_fetcher.fetch_financial_statements(cvm_code, aggregation='CONSOLIDATED')
    
    if not statements:
        return jsonify({'error': 'Financial data not available'}), 404
    
    # Mock calculation with sample data structure
    sample_ratios = {
        'liquidity_ratios': {
            'current_ratio': 2.15,
            'quick_ratio': 1.87,
            'cash_ratio': 0.54
        },
        'profitability_ratios': {
            'gross_margin': 0.45,
            'operating_margin': 0.32,
            'net_margin': 0.28,
            'roe': 0.18,
            'roa': 0.12,
            'roic': 0.15
        },
        'leverage_ratios': {
            'debt_to_equity': 0.65,
            'debt_to_assets': 0.38,
            'interest_coverage': 8.5
        },
        'efficiency_ratios': {
            'asset_turnover': 0.85,
            'inventory_turnover': 12.3,
            'receivables_turnover': 6.7
        },
        'reference_date': datetime.now().isoformat(),
        'cvm_code': cvm_code
    }
    
    return jsonify(sample_ratios)

@companies_bp.route('/companies/<int:cvm_code>/market-ratios', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_market_ratios(cvm_code):
    """Indicadores de mercado (Valuation)"""
    valid, error = validate_cvm_code(cvm_code)
    if not valid:
        return jsonify({'error': error}), 400
    
    # Mock market ratios data
    market_ratios = {
        'valuation_ratios': {
            'pe_ratio': 12.5,
            'pb_ratio': 1.8,
            'ev_ebitda': 8.9,
            'peg_ratio': 1.2,
            'price_to_sales': 2.1,
            'price_to_book': 1.8,
            'price_to_cash_flow': 9.8
        },
        'per_share_data': {
            'earnings_per_share': 8.45,
            'book_value_per_share': 47.32,
            'dividend_per_share': 2.15,
            'cash_flow_per_share': 12.67
        },
        'market_data': {
            'market_cap': 389450000000,
            'enterprise_value': 445230000000,
            'shares_outstanding': 13007000000,
            'float_shares': 7804200000
        },
        'reference_date': datetime.now().isoformat(),
        'cvm_code': cvm_code
    }
    
    return jsonify(market_ratios)

@companies_bp.route('/companies/<int:cvm_code>/dividends', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_company_dividends(cvm_code):
    """Histórico de dividendos"""
    valid, error = validate_cvm_code(cvm_code)
    if not valid:
        return jsonify({'error': error}), 400
    
    # Mock dividends data
    dividends_data = {
        'dividends': [
            {
                'type': 'dividend',
                'ex_date': '2023-08-15',
                'payment_date': '2023-09-01',
                'amount_per_share': 1.25,
                'currency': 'BRL',
                'ticker': f'TICKER{cvm_code % 1000}4',
                'total_amount': 16258750000,
                'yield_percentage': 3.2
            },
            {
                'type': 'jcp',
                'ex_date': '2023-05-15',
                'payment_date': '2023-06-01',
                'amount_per_share': 0.85,
                'currency': 'BRL',
                'ticker': f'TICKER{cvm_code % 1000}4',
                'total_amount': 11059450000,
                'yield_percentage': 2.1
            }
        ],
        'cvm_code': cvm_code,
        'total_dividends_12m': 2.10,
        'dividend_yield_12m': 5.3
    }
    
    return jsonify(dividends_data)

@companies_bp.route('/companies/<int:cvm_code>/insider-transactions', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_insider_transactions(cvm_code):
    """Transações de insiders"""
    valid, error = validate_cvm_code(cvm_code)
    if not valid:
        return jsonify({'error': error}), 400
    
    # Mock insider transactions data
    transactions_data = {
        'transactions': [
            {
                'transaction_date': '2023-11-15',
                'transaction_type': 'purchase',
                'insider_name': 'João Silva Santos',
                'insider_position': 'CEO',
                'shares_transacted': 50000,
                'average_price': 28.45,
                'total_value': 1422500,
                'shares_held_after': 1250000,
                'ownership_percentage': 0.96
            },
            {
                'transaction_date': '2023-10-20',
                'transaction_type': 'sale',
                'insider_name': 'Maria Oliveira Costa',
                'insider_position': 'CFO',
                'shares_transacted': 25000,
                'average_price': 29.80,
                'total_value': 745000,
                'shares_held_after': 185000,
                'ownership_percentage': 0.14
            }
        ],
        'cvm_code': cvm_code,
        'summary': {
            'total_transactions_3m': 5,
            'net_insider_activity': 'buying',
            'total_value_3m': 3500000
        }
    }
    
    return jsonify(transactions_data)

@companies_bp.route('/companies/<int:cvm_code>/documents', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_company_documents(cvm_code):
    """Documentos CVM"""
    valid, error = validate_cvm_code(cvm_code)
    if not valid:
        return jsonify({'error': error}), 400
    
    document_type = request.args.get('document_type')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Mock documents data
    documents_data = {
        'documents': [
            {
                'document_id': 'doc_123456',
                'document_type': 'DFP',
                'title': 'Demonstrações Financeiras Padronizadas - 2022',
                'reference_date': '2022-12-31',
                'publish_date': '2023-03-30',
                'url': f'https://cvm.gov.br/documents/{cvm_code}/dfp_2022.pdf',
                'version': 1,
                'status': 'active'
            },
            {
                'document_id': 'doc_123457',
                'document_type': 'ITR',
                'title': 'Informações Trimestrais - 3T2023',
                'reference_date': '2023-09-30',
                'publish_date': '2023-11-14',
                'url': f'https://cvm.gov.br/documents/{cvm_code}/itr_3t2023.pdf',
                'version': 1,
                'status': 'active'
            }
        ],
        'cvm_code': cvm_code,
        'total_documents': 2
    }
    
    return jsonify(documents_data)
