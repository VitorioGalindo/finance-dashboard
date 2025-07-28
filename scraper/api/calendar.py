from flask import Blueprint, request, jsonify
from utils.auth import require_api_key
from utils.rate_limiter import apply_rate_limit
from utils.validators import validate_date_range, validate_pagination
from datetime import datetime, timedelta

calendar_bp = Blueprint('calendar', __name__)

@calendar_bp.route('/calendar/events', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_calendar_events():
    """Calendário de eventos corporativos"""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    event_type = request.args.get('event_type')
    
    # Validate date range
    if date_from or date_to:
        valid, error = validate_date_range(date_from, date_to)
        if not valid:
            return jsonify({'error': error}), 400
    
    # Mock calendar events
    events_data = {
        'events': [
            {
                'date': '2023-12-20',
                'time': '16:00',
                'event_type': 'earnings',
                'company': 'VALE3',
                'company_name': 'Vale S.A.',
                'description': 'Divulgação de resultados 3T23',
                'importance': 'high',
                'estimated_eps': 2.45,
                'consensus_eps': 2.40,
                'previous_eps': 3.21,
                'event_url': 'https://ri.vale.com/earnings-3t23'
            },
            {
                'date': '2023-12-21',
                'time': '10:30',
                'event_type': 'dividend',
                'company': 'PETR4',
                'company_name': 'Petróleo Brasileiro S.A.',
                'description': 'Ex-dividend date - Dividendos 2023',
                'importance': 'medium',
                'dividend_amount': 1.25,
                'dividend_yield': 4.4,
                'payment_date': '2024-01-15'
            },
            {
                'date': '2023-12-22',
                'time': '14:00',
                'event_type': 'meeting',
                'company': 'ITUB4',
                'company_name': 'Itaú Unibanco Holding S.A.',
                'description': 'Assembleia Geral Extraordinária',
                'importance': 'medium',
                'agenda': 'Aprovação de reestruturação societária',
                'location': 'São Paulo - SP'
            },
            {
                'date': '2023-12-25',
                'time': '00:00',
                'event_type': 'holiday',
                'company': 'B3',
                'company_name': 'B3 S.A.',
                'description': 'Natal - Bolsa fechada',
                'importance': 'high',
                'market_impact': 'Não haverá pregão'
            }
        ],
        'filters_applied': {
            'date_from': date_from,
            'date_to': date_to,
            'event_type': event_type
        },
        'event_types_available': ['earnings', 'dividend', 'meeting', 'holiday', 'ipo', 'conference']
    }
    
    # Filter by event type if specified
    if event_type:
        events_data['events'] = [
            event for event in events_data['events']
            if event['event_type'] == event_type
        ]
    
    return jsonify(events_data)

@calendar_bp.route('/calendar/offerings', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_offerings():
    """IPOs e ofertas públicas"""
    status = request.args.get('status', 'all')  # upcoming, ongoing, completed, all
    
    # Mock offerings data
    offerings_data = {
        'offerings': [
            {
                'offering_id': 'ipo_001',
                'company_name': 'TechBrasil S.A.',
                'ticker': 'TECH3',
                'offering_type': 'IPO',
                'status': 'upcoming',
                'announcement_date': '2023-11-15',
                'subscription_start': '2024-01-10',
                'subscription_end': '2024-01-15',
                'pricing_date': '2024-01-16',
                'trading_start': '2024-01-20',
                'price_range': {
                    'min': 18.50,
                    'max': 22.50
                },
                'shares_offered': 50000000,
                'offering_size': {
                    'min': 925000000,
                    'max': 1125000000
                },
                'use_of_proceeds': 'Expansão e investimentos em tecnologia',
                'lead_underwriter': 'XP Investimentos',
                'sector': 'Tecnologia'
            },
            {
                'offering_id': 'follow_on_001',
                'company_name': 'Varejo Brasil S.A.',
                'ticker': 'VBRA3',
                'offering_type': 'Follow-on',
                'status': 'ongoing',
                'announcement_date': '2023-12-01',
                'subscription_start': '2023-12-18',
                'subscription_end': '2023-12-22',
                'pricing_date': '2023-12-23',
                'trading_start': '2023-12-26',
                'final_price': 45.80,
                'shares_offered': 25000000,
                'offering_size': 1145000000,
                'demand_multiple': 2.3,
                'use_of_proceeds': 'Redução de endividamento',
                'lead_underwriter': 'BTG Pactual',
                'sector': 'Varejo'
            }
        ],
        'summary': {
            'total_offerings': 2,
            'upcoming': 1,
            'ongoing': 1,
            'completed_this_year': 15,
            'total_volume_this_year': 45600000000
        }
    }
    
    # Filter by status
    if status != 'all':
        offerings_data['offerings'] = [
            offering for offering in offerings_data['offerings']
            if offering['status'] == status
        ]
    
    return jsonify(offerings_data)

@calendar_bp.route('/calendar/dividends', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_dividends_calendar():
    """Calendário de dividendos"""
    # Validate pagination
    valid, error, page, limit = validate_pagination()
    if not valid:
        return jsonify({'error': error}), 400
    
    month = request.args.get('month')
    year = request.args.get('year')
    
    # Mock dividends calendar
    dividends_calendar = {
        'dividends': [
            {
                'ticker': 'PETR4',
                'company_name': 'Petróleo Brasileiro S.A.',
                'ex_dividend_date': '2023-12-21',
                'payment_date': '2024-01-15',
                'record_date': '2023-12-22',
                'dividend_type': 'dividend',
                'amount_per_share': 1.25,
                'currency': 'BRL',
                'dividend_yield': 4.4,
                'announcement_date': '2023-11-30',
                'frequency': 'trimestral'
            },
            {
                'ticker': 'VALE3',
                'company_name': 'Vale S.A.',
                'ex_dividend_date': '2023-12-28',
                'payment_date': '2024-01-20',
                'record_date': '2023-12-29',
                'dividend_type': 'jcp',
                'amount_per_share': 0.95,
                'currency': 'BRL',
                'dividend_yield': 1.8,
                'announcement_date': '2023-12-15',
                'frequency': 'semestral'
            },
            {
                'ticker': 'BBDC4',
                'company_name': 'Banco Bradesco S.A.',
                'ex_dividend_date': '2024-01-05',
                'payment_date': '2024-01-25',
                'record_date': '2024-01-08',
                'dividend_type': 'dividend',
                'amount_per_share': 0.18,
                'currency': 'BRL',
                'dividend_yield': 1.2,
                'announcement_date': '2023-12-20',
                'frequency': 'mensal'
            }
        ],
        'pagination': {
            'current_page': page,
            'total_pages': 3,
            'total_items': 15,
            'per_page': limit
        },
        'summary': {
            'total_amount_upcoming': 125000000,
            'average_yield': 2.47,
            'companies_paying': 3,
            'period_covered': f"{year or '2023'}-{month or 'all'}"
        }
    }
    
    return jsonify(dividends_calendar)

@calendar_bp.route('/sectors', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_sectors():
    """Setores da economia"""
    # Mock sectors data
    sectors_data = {
        'sectors': [
            {
                'sector_id': 'financials',
                'sector_name': 'Intermediários Financeiros',
                'subsectors': [
                    'Bancos',
                    'Corretoras e Distribuidoras',
                    'Securitizadoras',
                    'Gestão de Recursos'
                ],
                'market_cap': 1250000000000,
                'companies_count': 45,
                'performance_ytd': 15.2,
                'top_companies': ['ITUB4', 'BBDC4', 'BBAS3', 'SANB11']
            },
            {
                'sector_id': 'oil_gas',
                'sector_name': 'Petróleo, Gás e Biocombustíveis',
                'subsectors': [
                    'Exploração e Refino',
                    'Equipamentos e Serviços'
                ],
                'market_cap': 650000000000,
                'companies_count': 12,
                'performance_ytd': 8.7,
                'top_companies': ['PETR4', 'PETR3', 'PRIO3', 'RRRP3']
            },
            {
                'sector_id': 'materials',
                'sector_name': 'Materiais Básicos',
                'subsectors': [
                    'Mineração',
                    'Siderurgia e Metalurgia',
                    'Químicos',
                    'Madeira e Papel'
                ],
                'market_cap': 780000000000,
                'companies_count': 38,
                'performance_ytd': -2.3,
                'top_companies': ['VALE3', 'CSNA3', 'GGBR4', 'USIM5']
            }
        ],
        'market_overview': {
            'total_market_cap': 4567000000000,
            'best_performing_sector': 'Intermediários Financeiros',
            'worst_performing_sector': 'Materiais Básicos',
            'sectors_count': 11,
            'last_update': datetime.now().isoformat()
        }
    }
    
    return jsonify(sectors_data)
