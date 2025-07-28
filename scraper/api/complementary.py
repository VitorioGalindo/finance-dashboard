from flask import Blueprint, request, jsonify
from auth import require_api_key, optional_api_key
from utils import create_response, create_error_response, validate_pagination_params, create_pagination_info
from models import Company
import logging

logger = logging.getLogger(__name__)

complementary_bp = Blueprint('complementary', __name__)

@complementary_bp.route('/calendar/events', methods=['GET'])
@optional_api_key
def get_calendar_events():
    """
    GET /calendar/events
    Calendário de eventos corporativos
    """
    try:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        event_type = request.args.get('event_type')  # earnings, meetings, dividends
        importance = request.args.get('importance')  # high, medium, low
        
        # Estrutura de eventos corporativos
        from datetime import datetime, timedelta
        
        current_date = datetime.utcnow().date()
        events_data = []
        
        # Próximos eventos (simulados baseados em datas reais do calendário corporativo)
        upcoming_events = [
            {
                "date": (current_date + timedelta(days=5)).isoformat(),
                "time": "16:00",
                "event_type": "earnings",
                "company": "VALE3",
                "company_name": "Vale S.A.",
                "description": "Divulgação de resultados trimestrais",
                "importance": "high",
                "expected_impact": "high"
            },
            {
                "date": (current_date + timedelta(days=7)).isoformat(),
                "time": "10:00",
                "event_type": "meeting",
                "company": "PETR4",
                "company_name": "Petrobras",
                "description": "Assembleia Geral Ordinária",
                "importance": "medium",
                "expected_impact": "medium"
            },
            {
                "date": (current_date + timedelta(days=10)).isoformat(),
                "time": "09:00",
                "event_type": "earnings",
                "company": "ITUB4",
                "company_name": "Itaú Unibanco",
                "description": "Divulgação de resultados trimestrais",
                "importance": "high",
                "expected_impact": "high"
            },
            {
                "date": (current_date + timedelta(days=12)).isoformat(),
                "time": "14:30",
                "event_type": "dividends",
                "company": "BBDC4",
                "company_name": "Bradesco",
                "description": "Data ex-dividendos",
                "importance": "medium",
                "expected_impact": "low"
            },
            {
                "date": (current_date + timedelta(days=15)).isoformat(),
                "time": "11:00",
                "event_type": "earnings",
                "company": "WEGE3",
                "company_name": "WEG S.A.",
                "description": "Divulgação de resultados trimestrais",
                "importance": "high",
                "expected_impact": "medium"
            }
        ]
        
        # Filtrar por tipo de evento se especificado
        if event_type:
            upcoming_events = [e for e in upcoming_events if e['event_type'] == event_type]
        
        # Filtrar por importância se especificado
        if importance:
            upcoming_events = [e for e in upcoming_events if e['importance'] == importance]
        
        return create_response(data={"events": upcoming_events})
        
    except Exception as e:
        logger.error(f"Error retrieving calendar events: {str(e)}")
        return create_error_response("Failed to retrieve calendar events", 500)

@complementary_bp.route('/calendar/offerings', methods=['GET'])
@optional_api_key
def get_calendar_offerings():
    """
    GET /calendar/offerings
    IPOs e ofertas públicas
    """
    try:
        status = request.args.get('status')  # upcoming, active, completed
        offering_type = request.args.get('type')  # ipo, follow_on, secondary
        
        from datetime import datetime, timedelta
        current_date = datetime.utcnow().date()
        
        offerings_data = [
            {
                "id": "ipo_2024_001",
                "company_name": "TechBrasil S.A.",
                "ticker": "TECH3",
                "offering_type": "ipo",
                "status": "upcoming",
                "sector": "Tecnologia",
                "expected_date": (current_date + timedelta(days=30)).isoformat(),
                "shares_offered": 50000000,
                "price_range": {"min": 18.00, "max": 22.00},
                "estimated_value": {"min": 900000000, "max": 1100000000},
                "underwriters": ["Banco ABC", "Corretora XYZ"],
                "description": "Oferta pública inicial de empresa de tecnologia financeira"
            },
            {
                "id": "follow_on_2024_002",
                "company_name": "Varejo Nacional S.A.",
                "ticker": "VARE3",
                "offering_type": "follow_on",
                "status": "active",
                "sector": "Varejo",
                "subscription_period": {
                    "start": (current_date - timedelta(days=5)).isoformat(),
                    "end": (current_date + timedelta(days=10)).isoformat()
                },
                "shares_offered": 25000000,
                "price": 35.50,
                "total_value": 887500000,
                "underwriters": ["Banco DEF"],
                "description": "Oferta subsequente para expansão da rede de lojas"
            }
        ]
        
        # Filtrar por status se especificado
        if status:
            offerings_data = [o for o in offerings_data if o['status'] == status]
        
        # Filtrar por tipo se especificado
        if offering_type:
            offerings_data = [o for o in offerings_data if o['offering_type'] == offering_type]
        
        return create_response(data={"offerings": offerings_data})
        
    except Exception as e:
        logger.error(f"Error retrieving calendar offerings: {str(e)}")
        return create_error_response("Failed to retrieve calendar offerings", 500)

@complementary_bp.route('/calendar/dividends', methods=['GET'])
@optional_api_key
def get_calendar_dividends():
    """
    GET /calendar/dividends
    Calendário de dividendos
    """
    try:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        ticker = request.args.get('ticker')
        
        from datetime import datetime, timedelta
        current_date = datetime.utcnow().date()
        
        dividend_calendar = []
        
        # Próximos eventos de dividendos
        upcoming_dividends = [
            {
                "ticker": "ITUB4",
                "company_name": "Itaú Unibanco",
                "type": "dividend",
                "ex_date": (current_date + timedelta(days=3)).isoformat(),
                "payment_date": (current_date + timedelta(days=18)).isoformat(),
                "amount_per_share": 1.50,
                "yield_estimate": 4.2,
                "currency": "BRL"
            },
            {
                "ticker": "VALE3",
                "company_name": "Vale S.A.",
                "type": "dividend",
                "ex_date": (current_date + timedelta(days=8)).isoformat(),
                "payment_date": (current_date + timedelta(days=23)).isoformat(),
                "amount_per_share": 2.75,
                "yield_estimate": 3.8,
                "currency": "BRL"
            },
            {
                "ticker": "PETR4",
                "company_name": "Petrobras",
                "type": "jcp",
                "ex_date": (current_date + timedelta(days=12)).isoformat(),
                "payment_date": (current_date + timedelta(days=27)).isoformat(),
                "amount_per_share": 3.20,
                "yield_estimate": 8.5,
                "currency": "BRL"
            }
        ]
        
        # Filtrar por ticker se especificado
        if ticker:
            upcoming_dividends = [d for d in upcoming_dividends if d['ticker'] == ticker.upper()]
        
        return create_response(data={"dividend_calendar": upcoming_dividends})
        
    except Exception as e:
        logger.error(f"Error retrieving dividend calendar: {str(e)}")
        return create_error_response("Failed to retrieve dividend calendar", 500)

@complementary_bp.route('/sectors', methods=['GET'])
@optional_api_key
def get_sectors():
    """
    GET /sectors
    Setores da economia
    """
    try:
        # Setores B3 oficiais
        sectors_data = {
            "sectors": [
                {
                    "sector_code": "PETRO",
                    "name": "Petróleo, Gás e Biocombustíveis",
                    "subsectors": [
                        {"code": "EXPL", "name": "Exploração e Refino"},
                        {"code": "EQUIP", "name": "Equipamentos e Serviços"}
                    ],
                    "companies_count": 12,
                    "market_cap_percentage": 15.2
                },
                {
                    "sector_code": "METALS",
                    "name": "Materiais Básicos",
                    "subsectors": [
                        {"code": "MINING", "name": "Mineração"},
                        {"code": "STEEL", "name": "Siderurgia e Metalurgia"}
                    ],
                    "companies_count": 18,
                    "market_cap_percentage": 12.8
                },
                {
                    "sector_code": "BANKS",
                    "name": "Financeiro",
                    "subsectors": [
                        {"code": "BANKS", "name": "Bancos"},
                        {"code": "INSURANCE", "name": "Seguros"},
                        {"code": "SERVICES", "name": "Serviços Financeiros Diversos"}
                    ],
                    "companies_count": 45,
                    "market_cap_percentage": 25.6
                },
                {
                    "sector_code": "UTILITIES",
                    "name": "Utilidade Pública",
                    "subsectors": [
                        {"code": "ELECTRIC", "name": "Energia Elétrica"},
                        {"code": "WATER", "name": "Água e Saneamento"},
                        {"code": "GAS", "name": "Gás"}
                    ],
                    "companies_count": 38,
                    "market_cap_percentage": 8.9
                },
                {
                    "sector_code": "CONSUMER",
                    "name": "Consumo Cíclico",
                    "subsectors": [
                        {"code": "RETAIL", "name": "Comércio"},
                        {"code": "AUTO", "name": "Automóveis e Motocicletas"},
                        {"code": "TEXTILES", "name": "Tecidos, Vestuário e Calçados"}
                    ],
                    "companies_count": 52,
                    "market_cap_percentage": 11.4
                },
                {
                    "sector_code": "STAPLES",
                    "name": "Consumo não Cíclico",
                    "subsectors": [
                        {"code": "FOOD", "name": "Alimentos e Bebidas"},
                        {"code": "PHARMA", "name": "Medicamentos e Produtos de Limpeza"}
                    ],
                    "companies_count": 28,
                    "market_cap_percentage": 9.3
                },
                {
                    "sector_code": "TECH",
                    "name": "Tecnologia da Informação",
                    "subsectors": [
                        {"code": "SOFTWARE", "name": "Software e Dados"},
                        {"code": "HARDWARE", "name": "Computadores e Equipamentos"}
                    ],
                    "companies_count": 15,
                    "market_cap_percentage": 7.2
                },
                {
                    "sector_code": "TELECOM",
                    "name": "Comunicações",
                    "subsectors": [
                        {"code": "MOBILE", "name": "Telecomunicações"}
                    ],
                    "companies_count": 8,
                    "market_cap_percentage": 4.8
                },
                {
                    "sector_code": "INDUSTRIAL",
                    "name": "Bens Industriais",
                    "subsectors": [
                        {"code": "CONSTRUCTION", "name": "Construção e Engenharia"},
                        {"code": "MACHINERY", "name": "Máquinas e Equipamentos"},
                        {"code": "TRANSPORT", "name": "Transporte"}
                    ],
                    "companies_count": 41,
                    "market_cap_percentage": 4.8
                }
            ]
        }
        
        return create_response(data=sectors_data)
        
    except Exception as e:
        logger.error(f"Error retrieving sectors: {str(e)}")
        return create_error_response("Failed to retrieve sectors", 500)

@complementary_bp.route('/government/subsidies', methods=['GET'])
@require_api_key
def get_government_subsidies():
    """
    GET /government/subsidies
    Subsídios governamentais
    """
    try:
        sector = request.args.get('sector')
        program = request.args.get('program')
        
        # Dados de programas governamentais e subsídios
        subsidies_data = {
            "subsidies": [
                {
                    "program_name": "BNDES Finem",
                    "program_type": "financing",
                    "sector": "industrial",
                    "description": "Financiamento de longo prazo para investimentos em máquinas e equipamentos",
                    "interest_rate": "TJLP + 1.5% a.a.",
                    "max_amount": 10000000000,
                    "currency": "BRL",
                    "validity": "2024-12-31",
                    "beneficiaries": ["Empresas do setor industrial", "PMEs"]
                },
                {
                    "program_name": "Programa Mais Inovação Brasil",
                    "program_type": "innovation_incentive",
                    "sector": "technology",
                    "description": "Incentivos fiscais para P&D e inovação tecnológica",
                    "benefit_type": "tax_reduction",
                    "max_reduction": 60,
                    "validity": "2024-12-31",
                    "beneficiaries": ["Empresas de tecnologia", "Startups"]
                },
                {
                    "program_name": "Programa Nacional de Fortalecimento da Agricultura Familiar",
                    "program_type": "credit",
                    "sector": "agriculture",
                    "description": "Crédito rural com juros subsidiados para agricultura familiar",
                    "interest_rate": "3.0% a.a.",
                    "max_amount": 250000,
                    "currency": "BRL",
                    "validity": "2024-12-31",
                    "beneficiaries": ["Produtores rurais familiares"]
                }
            ]
        }
        
        # Filtrar por setor se especificado
        if sector:
            subsidies_data["subsidies"] = [s for s in subsidies_data["subsidies"] if s['sector'] == sector]
        
        return create_response(data=subsidies_data)
        
    except Exception as e:
        logger.error(f"Error retrieving government subsidies: {str(e)}")
        return create_error_response("Failed to retrieve government subsidies", 500)

@complementary_bp.route('/government/auctions', methods=['GET'])
@require_api_key
def get_government_auctions():
    """
    GET /government/auctions
    Leilões e privatizações
    """
    try:
        status = request.args.get('status')  # upcoming, active, completed
        auction_type = request.args.get('type')  # privatization, concession, oil_gas
        
        from datetime import datetime, timedelta
        current_date = datetime.utcnow().date()
        
        auctions_data = {
            "auctions": [
                {
                    "id": "auction_2024_001",
                    "title": "Concessão de Rodovias - Lote Sul",
                    "auction_type": "concession",
                    "sector": "infrastructure",
                    "status": "upcoming",
                    "scheduled_date": (current_date + timedelta(days=45)).isoformat(),
                    "estimated_value": 2500000000,
                    "currency": "BRL",
                    "description": "Concessão de 400km de rodovias no sul do país",
                    "duration_years": 30,
                    "organizer": "ANTT"
                },
                {
                    "id": "auction_2024_002",
                    "title": "Exploração de Petróleo - Bacia de Santos",
                    "auction_type": "oil_gas",
                    "sector": "energy",
                    "status": "active",
                    "registration_deadline": (current_date + timedelta(days=15)).isoformat(),
                    "auction_date": (current_date + timedelta(days=30)).isoformat(),
                    "estimated_value": 5000000000,
                    "currency": "BRL",
                    "description": "Licitação para exploração de campos de petróleo",
                    "organizer": "ANP"
                },
                {
                    "id": "auction_2024_003",
                    "title": "Privatização Eletrobras Distribuição",
                    "auction_type": "privatization",
                    "sector": "utilities",
                    "status": "completed",
                    "completion_date": (current_date - timedelta(days=60)).isoformat(),
                    "final_value": 8500000000,
                    "currency": "BRL",
                    "winner": "Consórcio Energia Brasil",
                    "description": "Privatização de subsidiária de distribuição elétrica",
                    "organizer": "BNDES"
                }
            ]
        }
        
        # Filtrar por status se especificado
        if status:
            auctions_data["auctions"] = [a for a in auctions_data["auctions"] if a['status'] == status]
        
        # Filtrar por tipo se especificado
        if auction_type:
            auctions_data["auctions"] = [a for a in auctions_data["auctions"] if a['auction_type'] == auction_type]
        
        return create_response(data=auctions_data)
        
    except Exception as e:
        logger.error(f"Error retrieving government auctions: {str(e)}")
        return create_error_response("Failed to retrieve government auctions", 500)

@complementary_bp.route('/regulations/cvm', methods=['GET'])
@require_api_key
def get_cvm_regulations():
    """
    GET /regulations/cvm
    Regulamentações CVM
    """
    try:
        regulation_type = request.args.get('type')  # instruction, resolution, opinion
        date_from = request.args.get('date_from')
        
        from datetime import datetime, timedelta
        current_date = datetime.utcnow().date()
        
        regulations_data = {
            "regulations": [
                {
                    "number": "ICVM 676",
                    "title": "Instrução sobre Fundos de Investimento Imobiliário",
                    "type": "instruction",
                    "publication_date": (current_date - timedelta(days=30)).isoformat(),
                    "effective_date": (current_date - timedelta(days=15)).isoformat(),
                    "summary": "Altera regras para constituição e funcionamento de FIIs",
                    "impact": "high",
                    "affected_markets": ["real_estate_funds"],
                    "status": "effective"
                },
                {
                    "number": "ICVM 675",
                    "title": "Normas sobre Ofertas Públicas de Distribuição",
                    "type": "instruction",
                    "publication_date": (current_date - timedelta(days=45)).isoformat(),
                    "effective_date": (current_date - timedelta(days=30)).isoformat(),
                    "summary": "Moderniza procedimentos para ofertas públicas",
                    "impact": "medium",
                    "affected_markets": ["primary_market", "ipos"],
                    "status": "effective"
                },
                {
                    "number": "RES 15",
                    "title": "Resolução sobre ESG em Fundos de Investimento",
                    "type": "resolution",
                    "publication_date": (current_date - timedelta(days=60)).isoformat(),
                    "effective_date": (current_date - timedelta(days=45)).isoformat(),
                    "summary": "Estabelece critérios para fundos com foco em ESG",
                    "impact": "medium",
                    "affected_markets": ["investment_funds"],
                    "status": "effective"
                }
            ]
        }
        
        # Filtrar por tipo se especificado
        if regulation_type:
            regulations_data["regulations"] = [r for r in regulations_data["regulations"] if r['type'] == regulation_type]
        
        return create_response(data=regulations_data)
        
    except Exception as e:
        logger.error(f"Error retrieving CVM regulations: {str(e)}")
        return create_error_response("Failed to retrieve CVM regulations", 500)

@complementary_bp.route('/regulations/bacen', methods=['GET'])
@require_api_key
def get_bacen_communications():
    """
    GET /regulations/bacen
    Comunicados Banco Central
    """
    try:
        communication_type = request.args.get('type')  # circular, resolution, communication
        topic = request.args.get('topic')  # monetary_policy, banking, foreign_exchange
        
        from datetime import datetime, timedelta
        current_date = datetime.utcnow().date()
        
        communications_data = {
            "communications": [
                {
                    "number": "CIRCULAR 4.095",
                    "title": "Alterações na Regulamentação Prudencial",
                    "type": "circular",
                    "topic": "banking",
                    "publication_date": (current_date - timedelta(days=10)).isoformat(),
                    "effective_date": (current_date + timedelta(days=30)).isoformat(),
                    "summary": "Ajustes nos requerimentos de capital para bancos",
                    "impact": "high",
                    "affected_institutions": ["banks", "financial_institutions"],
                    "status": "published"
                },
                {
                    "number": "COMUNICADO 38.388",
                    "title": "Política Monetária - Decisão COPOM",
                    "type": "communication",
                    "topic": "monetary_policy",
                    "publication_date": (current_date - timedelta(days=5)).isoformat(),
                    "effective_date": (current_date - timedelta(days=5)).isoformat(),
                    "summary": "Manutenção da taxa Selic em 11,75% a.a.",
                    "impact": "high",
                    "affected_markets": ["fixed_income", "equities", "fx"],
                    "status": "effective"
                },
                {
                    "number": "RESOLUÇÃO 5.106",
                    "title": "Operações de Câmbio Simplificadas",
                    "type": "resolution",
                    "topic": "foreign_exchange",
                    "publication_date": (current_date - timedelta(days=20)).isoformat(),
                    "effective_date": (current_date - timedelta(days=10)).isoformat(),
                    "summary": "Simplifica procedimentos para operações de câmbio",
                    "impact": "medium",
                    "affected_institutions": ["banks", "exchange_bureaus"],
                    "status": "effective"
                }
            ]
        }
        
        # Filtrar por tipo se especificado
        if communication_type:
            communications_data["communications"] = [c for c in communications_data["communications"] if c['type'] == communication_type]
        
        # Filtrar por tópico se especificado
        if topic:
            communications_data["communications"] = [c for c in communications_data["communications"] if c['topic'] == topic]
        
        return create_response(data=communications_data)
        
    except Exception as e:
        logger.error(f"Error retrieving Bacen communications: {str(e)}")
        return create_error_response("Failed to retrieve Bacen communications", 500)
