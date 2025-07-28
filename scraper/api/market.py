from flask import Blueprint, request, jsonify
from utils.auth import require_api_key
from utils.rate_limiter import apply_rate_limit
from utils.validators import validate_ticker, validate_period, validate_interval, validate_pagination
from services.data_fetcher import data_fetcher
from services.calculations import financial_calc
from models import Quote, db
from datetime import datetime, timedelta

market_bp = Blueprint('market', __name__)

@market_bp.route('/assets', methods=['GET'])
@require_api_key
@apply_rate_limit
def list_assets():
    """Lista de ativos com filtros"""
    # Validate pagination
    valid, error, page, limit = validate_pagination()
    if not valid:
        return jsonify({'error': error}), 400
    
    asset_type = request.args.get('asset_type')
    sector = request.args.get('sector')
    index = request.args.get('index')
    
    # Mock assets data
    assets_data = {
        'assets': [
            {
                'ticker': 'PETR4',
                'company_name': 'Petróleo Brasileiro S.A.',
                'asset_type': 'stock',
                'sector': 'Petróleo, Gás e Biocombustíveis',
                'subsector': 'Exploração e Refino',
                'market_cap': 503100000000,
                'free_float': 0.72,
                'listing_segment': 'Novo Mercado',
                'is_ibovespa': True,
                'is_ibrx100': True,
                'trading_status': 'active'
            },
            {
                'ticker': 'VALE3',
                'company_name': 'Vale S.A.',
                'asset_type': 'stock',
                'sector': 'Materiais Básicos',
                'subsector': 'Mineração',
                'market_cap': 287450000000,
                'free_float': 0.68,
                'listing_segment': 'Novo Mercado',
                'is_ibovespa': True,
                'is_ibrx100': True,
                'trading_status': 'active'
            },
            {
                'ticker': 'HGLG11',
                'company_name': 'CSHG Logística FII',
                'asset_type': 'reit',
                'sector': 'Fundos Imobiliários',
                'subsector': 'Logística',
                'market_cap': 2450000000,
                'free_float': 0.95,
                'listing_segment': 'FII',
                'is_ibovespa': False,
                'is_ibrx100': False,
                'trading_status': 'active'
            }
        ],
        'pagination': {
            'current_page': page,
            'total_pages': 25,
            'total_items': 1234,
            'per_page': limit
        },
        'filters_applied': {
            'asset_type': asset_type,
            'sector': sector,
            'index': index
        }
    }
    
    return jsonify(assets_data)

@market_bp.route('/quotes', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_quotes():
    """Cotações em tempo real"""
    tickers_param = request.args.get('tickers')
    if not tickers_param:
        return jsonify({'error': 'tickers parameter is required'}), 400
    
    tickers = [ticker.strip().upper() for ticker in tickers_param.split(',')]
    
    # Validate each ticker
    for ticker in tickers:
        valid, error = validate_ticker(ticker)
        if not valid:
            return jsonify({'error': f'Invalid ticker {ticker}: {error}'}), 400
    
    quotes_data = []
    
    for ticker in tickers:
        # Try to fetch real data first
        quote_data = data_fetcher.fetch_quote(ticker)
        
        if quote_data:
            quotes_data.append(quote_data)
        else:
            # Mock quote data if external API fails
            mock_quote = {
                'ticker': ticker,
                'price': 28.45,
                'change': 0.87,
                'change_percent': 3.15,
                'volume': 45230000,
                'volume_financial': 1287000000,
                'open': 27.58,
                'high': 28.67,
                'low': 27.45,
                'previous_close': 27.58,
                'bid': 28.43,
                'ask': 28.47,
                'bid_size': 1000,
                'ask_size': 500,
                'timestamp': datetime.now().isoformat(),
                'market_status': 'closed',
                'error': 'Real-time data unavailable - showing sample structure'
            }
            quotes_data.append(mock_quote)
    
    return jsonify({'quotes': quotes_data})

@market_bp.route('/quotes/<ticker>/history', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_quote_history(ticker):
    """Histórico de preços"""
    valid, error = validate_ticker(ticker)
    if not valid:
        return jsonify({'error': error}), 400
    
    period = request.args.get('period', '1y')
    interval = request.args.get('interval', '1d')
    adjusted = request.args.get('adjusted', 'true').lower() == 'true'
    
    # Validate parameters
    valid, error = validate_period(period)
    if not valid:
        return jsonify({'error': error}), 400
    
    valid, error = validate_interval(interval)
    if not valid:
        return jsonify({'error': error}), 400
    
    # Fetch historical data
    historical_data = data_fetcher.fetch_historical_data(ticker, period, interval)
    
    if not historical_data:
        # Mock historical data structure
        historical_data = [
            {
                'date': int((datetime.now() - timedelta(days=i)).timestamp()),
                'open': 28.50 + (i * 0.1),
                'high': 29.00 + (i * 0.1),
                'low': 28.00 + (i * 0.1),
                'close': 28.75 + (i * 0.1),
                'volume': 45000000 + (i * 1000000),
                'adjusted_close': (28.75 + (i * 0.1)) if adjusted else None
            }
            for i in range(min(30, 365 if 'y' in period else 30))
        ]
    
    return jsonify({
        'ticker': ticker,
        'period': period,
        'interval': interval,
        'adjusted': adjusted,
        'historical_data': historical_data,
        'metadata': {
            'data_points': len(historical_data),
            'first_date': historical_data[0]['date'] if historical_data else None,
            'last_date': historical_data[-1]['date'] if historical_data else None
        }
    })

@market_bp.route('/indices', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_indices():
    """Índices de mercado"""
    # Mock indices data
    indices_data = {
        'indices': [
            {
                'index_code': 'IBOV',
                'name': 'Índice Bovespa',
                'value': 126543.78,
                'change': 1245.67,
                'change_percent': 0.99,
                'volume': 12450000000,
                'timestamp': datetime.now().isoformat(),
                'components_count': 85,
                'market_cap': 4567000000000
            },
            {
                'index_code': 'IBRX100',
                'name': 'Índice Brasil 100',
                'value': 54321.45,
                'change': -234.56,
                'change_percent': -0.43,
                'volume': 8900000000,
                'timestamp': datetime.now().isoformat(),
                'components_count': 100,
                'market_cap': 3890000000000
            },
            {
                'index_code': 'SMLL',
                'name': 'Índice Small Cap',
                'value': 3456.78,
                'change': 23.45,
                'change_percent': 0.68,
                'volume': 1200000000,
                'timestamp': datetime.now().isoformat(),
                'components_count': 75,
                'market_cap': 567000000000
            }
        ]
    }
    
    return jsonify(indices_data)

@market_bp.route('/indices/<index_code>/composition', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_index_composition(index_code):
    """Composição de índices"""
    # Mock index composition
    composition_data = {
        'index_code': index_code,
        'index_name': f'Índice {index_code}',
        'last_update': datetime.now().isoformat(),
        'composition': [
            {
                'ticker': 'PETR4',
                'company_name': 'Petróleo Brasileiro S.A.',
                'weight': 8.45,
                'shares': 850000000,
                'theoretical_quantity': 425000000,
                'sector': 'Petróleo, Gás e Biocombustíveis'
            },
            {
                'ticker': 'VALE3',
                'company_name': 'Vale S.A.',
                'weight': 7.23,
                'shares': 890000000,
                'theoretical_quantity': 445000000,
                'sector': 'Materiais Básicos'
            },
            {
                'ticker': 'ITUB4',
                'company_name': 'Itaú Unibanco Holding S.A.',
                'weight': 6.87,
                'shares': 780000000,
                'theoretical_quantity': 390000000,
                'sector': 'Intermediários Financeiros'
            }
        ],
        'total_components': 3,
        'total_weight': 22.55
    }
    
    return jsonify(composition_data)

@market_bp.route('/foreign-investors', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_foreign_investors():
    """Fluxo de investidores estrangeiros"""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Mock foreign investors data
    foreign_data = {
        'data': [
            {
                'date': '2023-12-15',
                'net_flow': 1250000000,
                'inflow': 8750000000,
                'outflow': 7500000000,
                'participation_percentage': 47.8,
                'accumulated_month': 5670000000,
                'accumulated_year': 45320000000
            },
            {
                'date': '2023-12-14',
                'net_flow': -850000000,
                'inflow': 6200000000,
                'outflow': 7050000000,
                'participation_percentage': 47.5,
                'accumulated_month': 4420000000,
                'accumulated_year': 44070000000
            }
        ],
        'summary': {
            'period_net_flow': 400000000,
            'average_daily_flow': 200000000,
            'current_participation': 47.8,
            'data_points': 2
        }
    }
    
    return jsonify(foreign_data)
