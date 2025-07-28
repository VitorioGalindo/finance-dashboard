from flask import Blueprint, request, jsonify
from utils.auth import require_api_key
from utils.rate_limiter import apply_rate_limit
from utils.validators import validate_pagination, validate_date_range
from services.data_fetcher import data_fetcher
from services.sentiment_analyzer import sentiment_analyzer
from datetime import datetime, timedelta

news_bp = Blueprint('news', __name__)

@news_bp.route('/news', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_news():
    """Feed de notícias com análise de sentimento"""
    # Validate pagination
    valid, error, page, limit = validate_pagination()
    if not valid:
        return jsonify({'error': error}), 400
    
    # Get filter parameters
    category = request.args.get('category')
    ticker = request.args.get('ticker')
    date_from = request.args.get('date_from')
    sentiment = request.args.get('sentiment')
    
    # Validate date range
    if date_from:
        valid, error = validate_date_range(date_from, None)
        if not valid:
            return jsonify({'error': error}), 400
    
    # Fetch news data
    news_data = data_fetcher.fetch_news(category, ticker)
    
    if not news_data or 'news' not in news_data:
        return jsonify({'error': 'No news data available'}), 404
    
    # Analyze sentiment for news items
    analyzed_news = sentiment_analyzer.analyze_news_batch(news_data['news'])
    
    # Apply filters
    filtered_news = analyzed_news
    
    if sentiment:
        filtered_news = [
            news for news in filtered_news 
            if news.get('sentiment') == sentiment
        ]
    
    # Apply pagination
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_news = filtered_news[start_idx:end_idx]
    
    return jsonify({
        'news': paginated_news,
        'pagination': {
            'current_page': page,
            'total_pages': (len(filtered_news) + limit - 1) // limit,
            'total_items': len(filtered_news),
            'per_page': limit
        },
        'filters_applied': {
            'category': category,
            'ticker': ticker,
            'sentiment': sentiment,
            'date_from': date_from
        }
    })

@news_bp.route('/news/<news_id>', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_news_details(news_id):
    """Detalhes da notícia"""
    # Mock detailed news data
    news_detail = {
        'id': news_id,
        'title': 'Mercado brasileiro demonstra sinais de recuperação com alta dos principais índices',
        'summary': 'O Ibovespa fechou em alta de 1,2% nesta sessão, impulsionado pelos resultados positivos do setor financeiro e commodities.',
        'content': '''
        O mercado de ações brasileiro encerrou a sessão desta sexta-feira em território positivo, 
        com o Ibovespa registrando alta de 1,2%, fechando aos 126.543 pontos. O movimento foi 
        impulsionado principalmente pelos papéis do setor financeiro e de commodities.
        
        Entre os destaques do dia, as ações da Petrobras (PETR4) subiram 2,1%, enquanto Vale (VALE3) 
        avançou 1,8%. O setor bancário também apresentou bom desempenho, com Itaú (ITUB4) e Bradesco 
        (BBDC4) registrando altas de 1,5% e 1,3%, respectivamente.
        
        Analistas atribuem o movimento positivo às expectativas de melhora no cenário macroeconômico 
        e aos sinais de estabilização da política monetária.
        ''',
        'author': 'Redação Mercado Financeiro',
        'published_at': datetime.now().isoformat(),
        'url': f'https://example.com/news/{news_id}',
        'category': 'market',
        'tags': ['ibovespa', 'alta', 'financeiro', 'commodities', 'petrobras', 'vale'],
        'sentiment': 'positive',
        'sentiment_score': 0.75,
        'sentiment_confidence': 0.85,
        'impact_score': 7.8,
        'related_tickers': ['IBOV', 'PETR4', 'VALE3', 'ITUB4', 'BBDC4'],
        'read_time_minutes': 3,
        'shares_count': 1254,
        'views_count': 8742,
        'sentiment_analysis': {
            'positive_keywords': ['alta', 'positivo', 'recuperação', 'avanço', 'melhora'],
            'negative_keywords': [],
            'neutral_keywords': ['fechou', 'registrando', 'movimento']
        }
    }
    
    return jsonify(news_detail)

@news_bp.route('/research/reports', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_research_reports():
    """Análises de mercado"""
    # Validate pagination
    valid, error, page, limit = validate_pagination()
    if not valid:
        return jsonify({'error': error}), 400
    
    category = request.args.get('category', 'market_analysis')
    
    # Mock research reports data
    reports_data = {
        'reports': [
            {
                'report_id': 'report_001',
                'title': 'Perspectivas para o Mercado Brasileiro 2024',
                'institution': 'Banco Análise S.A.',
                'analyst': 'Dr. João Santos',
                'published_date': '2023-12-15',
                'category': 'market_outlook',
                'target_assets': ['IBOV', 'IBRX100'],
                'recommendation': 'COMPRAR',
                'target_price': 135000,
                'current_price': 126543,
                'upside_potential': 6.68,
                'summary': 'Esperamos um ano positivo para o mercado brasileiro, com destaque para os setores de commodities e financeiro.',
                'key_points': [
                    'PIB projetado em 2,5% para 2024',
                    'Inflação controlada em torno de 4%',
                    'Juros em trajetória de queda gradual'
                ],
                'risk_rating': 'MODERADO',
                'time_horizon': '12 meses'
            },
            {
                'report_id': 'report_002',
                'title': 'Análise Setorial: Bancos Brasileiros',
                'institution': 'Research Capital',
                'analyst': 'Maria Oliveira',
                'published_date': '2023-12-14',
                'category': 'sector_analysis',
                'target_assets': ['ITUB4', 'BBDC4', 'BBAS3'],
                'recommendation': 'NEUTRO',
                'summary': 'Setor bancário apresenta fundamentos sólidos, mas enfrenta pressões de margem.',
                'key_points': [
                    'ROE médio do setor em 18%',
                    'Inadimplência controlada',
                    'Pressão nas margens de juros'
                ],
                'risk_rating': 'BAIXO',
                'time_horizon': '6 meses'
            }
        ],
        'pagination': {
            'current_page': page,
            'total_pages': 5,
            'total_items': 25,
            'per_page': limit
        }
    }
    
    return jsonify(reports_data)

@news_bp.route('/research/analyst-reports', methods=['GET'])
@require_api_key
@apply_rate_limit
def get_analyst_reports():
    """Relatórios de analistas"""
    ticker = request.args.get('ticker')
    analyst = request.args.get('analyst')
    
    # Mock analyst reports
    analyst_reports = {
        'reports': [
            {
                'report_id': 'analyst_001',
                'ticker': ticker or 'PETR4',
                'company_name': 'Petróleo Brasileiro S.A.',
                'analyst_name': 'Carlos Silva',
                'institution': 'XP Investimentos',
                'recommendation': 'COMPRAR',
                'target_price': 32.50,
                'current_price': 28.45,
                'upside_potential': 14.23,
                'rating_change': 'UPGRADE',
                'previous_rating': 'NEUTRO',
                'report_date': '2023-12-15',
                'price_12m_target': 32.50,
                'dividend_yield_expected': 8.5,
                'key_thesis': [
                    'Preços do petróleo em recuperação',
                    'Forte geração de caixa',
                    'Política de dividendos atrativa'
                ],
                'risks': [
                    'Volatilidade dos preços do petróleo',
                    'Questões regulatórias',
                    'Cenário macroeconômico'
                ],
                'valuation_method': 'DCF + Múltiplos',
                'pe_ratio_target': 8.5,
                'ev_ebitda_target': 4.2
            }
        ],
        'consensus': {
            'average_target_price': 31.25,
            'recommendations_distribution': {
                'COMPRAR': 8,
                'MANTER': 5,
                'VENDER': 1
            },
            'average_upside': 9.85,
            'number_analysts': 14
        }
    }
    
    return jsonify(analyst_reports)
