from flask import Blueprint, request, jsonify
from utils.auth import require_api_key
from utils.rate_limiter import apply_rate_limit
from utils.validators import validate_date_range
from services.data_fetcher import data_fetcher
from datetime import datetime, timedelta

macro_bp = Blueprint('macroeconomics', __name__)

@macro_bp.route('/macroeconomics/indicators', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_economic_indicators():
    """Indicadores econômicos"""
    indicator = request.args.get('indicator')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Validate date range
    if date_from or date_to:
        valid, error = validate_date_range(date_from, date_to)
        if not valid:
            return jsonify({'error': error}), 400
    
    # Fetch indicators data
    indicators_data = data_fetcher.fetch_economic_indicators(indicator)
    
    return jsonify(indicators_data)

@macro_bp.route('/macroeconomics/expectations', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_market_expectations():
    """Expectativas de mercado"""
    indicator = request.args.get('indicator')
    
    # Mock expectations data
    expectations_data = {
        'expectations': [
            {
                'indicator': 'SELIC',
                'reference_date': '2024-01-01',
                'median': 11.50,
                'mean': 11.52,
                'standard_deviation': 0.25,
                'minimum': 11.00,
                'maximum': 12.00,
                'coefficient_variation': 2.17,
                'number_respondents': 145
            },
            {
                'indicator': 'IPCA',
                'reference_date': '2024-12-31',
                'median': 4.25,
                'mean': 4.31,
                'standard_deviation': 0.35,
                'minimum': 3.80,
                'maximum': 5.20,
                'coefficient_variation': 8.12,
                'number_respondents': 142
            },
            {
                'indicator': 'PIB',
                'reference_date': '2024-12-31',
                'median': 2.10,
                'mean': 2.15,
                'standard_deviation': 0.45,
                'minimum': 1.50,
                'maximum': 3.00,
                'coefficient_variation': 20.93,
                'number_respondents': 128
            }
        ],
        'last_update': datetime.now().isoformat()
    }
    
    if indicator:
        expectations_data['expectations'] = [
            exp for exp in expectations_data['expectations']
            if exp['indicator'].lower() == indicator.lower()
        ]
    
    return jsonify(expectations_data)

@macro_bp.route('/macroeconomics/focus-report', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_focus_report():
    """Boletim Focus"""
    # Mock Focus report data
    focus_data = {
        'report_date': datetime.now().isoformat(),
        'indicators': {
            'ipca': {
                'current_year': 4.62,
                'next_year': 3.75,
                'current_year_change': -0.15,
                'next_year_change': -0.05
            },
            'selic': {
                'end_current_year': 11.75,
                'end_next_year': 10.00,
                'current_year_change': -0.25,
                'next_year_change': -0.50
            },
            'pib': {
                'current_year': 2.85,
                'next_year': 2.10,
                'current_year_change': 0.05,
                'next_year_change': 0.00
            },
            'cambio': {
                'end_current_year': 5.15,
                'end_next_year': 5.20,
                'current_year_change': 0.02,
                'next_year_change': 0.01
            }
        },
        'consensus_changes': {
            'indicators_revised_up': 1,
            'indicators_revised_down': 2,
            'indicators_unchanged': 1
        },
        'methodology': 'Top 5 Focus',
        'number_institutions': 145
    }
    
    return jsonify(focus_data)

@macro_bp.route('/macroeconomics/yield-curves', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_yield_curves():
    """Curvas de juros"""
    curve_type = request.args.get('curve_type', 'di_futures')
    
    # Mock yield curve data
    curves_data = {
        'curves': [
            {
                'curve_type': curve_type,
                'date': datetime.now().isoformat(),
                'points': [
                    {
                        'maturity': '2024-01-02',
                        'days_to_maturity': 18,
                        'rate': 11.85,
                        'contract': 'F24',
                        'volume': 125000,
                        'open_interest': 89000
                    },
                    {
                        'maturity': '2024-04-01',
                        'days_to_maturity': 108,
                        'rate': 11.65,
                        'contract': 'J24',
                        'volume': 98000,
                        'open_interest': 156000
                    },
                    {
                        'maturity': '2024-07-01',
                        'days_to_maturity': 199,
                        'rate': 11.40,
                        'contract': 'N24',
                        'volume': 67000,
                        'open_interest': 134000
                    },
                    {
                        'maturity': '2025-01-02',
                        'days_to_maturity': 384,
                        'rate': 11.10,
                        'contract': 'F25',
                        'volume': 45000,
                        'open_interest': 98000
                    }
                ]
            }
        ],
        'metadata': {
            'source': 'B3',
            'last_update': datetime.now().isoformat(),
            'curve_types_available': ['di_futures', 'government_bonds', 'swap_rates']
        }
    }
    
    return jsonify(curves_data)

@macro_bp.route('/macroeconomics/exchange-rates', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_exchange_rates():
    """Taxas de câmbio"""
    currency_pair = request.args.get('currency_pair', 'USD/BRL')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Validate date range
    if date_from or date_to:
        valid, error = validate_date_range(date_from, date_to)
        if not valid:
            return jsonify({'error': error}), 400
    
    # Mock exchange rates data
    exchange_data = {
        'currency_pair': currency_pair,
        'data': [
            {
                'date': '2023-12-15',
                'rate': 5.1245,
                'high': 5.1387,
                'low': 5.1089,
                'variation': 0.0156,
                'variation_percent': 0.305,
                'buy_rate': 5.1189,
                'sell_rate': 5.1301
            },
            {
                'date': '2023-12-14',
                'rate': 5.1089,
                'high': 5.1234,
                'low': 5.0967,
                'variation': -0.0123,
                'variation_percent': -0.240,
                'buy_rate': 5.1034,
                'sell_rate': 5.1144
            }
        ],
        'summary': {
            'current_rate': 5.1245,
            'period_high': 5.1387,
            'period_low': 5.0967,
            'period_variation': 0.0278,
            'period_variation_percent': 0.544
        },
        'last_update': datetime.now().isoformat()
    }
    
    return jsonify(exchange_data)

@macro_bp.route('/macroeconomics/commodities', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_commodities():
    """Preços de commodities"""
    commodity = request.args.get('commodity')
    
    # Mock commodities data
    commodities_data = {
        'commodities': [
            {
                'commodity': 'Iron Ore',
                'symbol': 'IO',
                'price': 115.50,
                'currency': 'USD',
                'unit': 'per tonne',
                'change': 2.75,
                'change_percent': 2.44,
                'last_update': datetime.now().isoformat(),
                'exchange': 'Dalian',
                'category': 'Metals'
            },
            {
                'commodity': 'Soybeans',
                'symbol': 'SOYB',
                'price': 1345.25,
                'currency': 'USD',
                'unit': 'per bushel',
                'change': -12.50,
                'change_percent': -0.92,
                'last_update': datetime.now().isoformat(),
                'exchange': 'CBOT',
                'category': 'Agriculture'
            },
            {
                'commodity': 'WTI Crude Oil',
                'symbol': 'WTI',
                'price': 72.45,
                'currency': 'USD',
                'unit': 'per barrel',
                'change': 1.23,
                'change_percent': 1.73,
                'last_update': datetime.now().isoformat(),
                'exchange': 'NYMEX',
                'category': 'Energy'
            }
        ]
    }
    
    if commodity:
        commodities_data['commodities'] = [
            comm for comm in commodities_data['commodities']
            if commodity.lower() in comm['commodity'].lower()
        ]
    
    return jsonify(commodities_data)
