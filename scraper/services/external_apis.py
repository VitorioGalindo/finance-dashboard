import os
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

logger = logging.getLogger(__name__)

class ExternalAPIService:
    """Service for integrating with external financial data APIs"""
    
    def __init__(self):
        # API Keys from environment variables
        self.b3_api_key = os.environ.get('B3_API_KEY', 'default-b3-key')
        self.cvm_api_key = os.environ.get('CVM_API_KEY', 'default-cvm-key')
        self.bcb_api_key = os.environ.get('BCB_API_KEY', 'default-bcb-key')
        self.yahoo_finance_key = os.environ.get('YAHOO_FINANCE_KEY', 'default-yahoo-key')
        self.news_api_key = os.environ.get('NEWS_API_KEY', 'default-news-key')
        
        # API Base URLs
        self.b3_base_url = "https://api.b3.com.br/v1"
        self.cvm_base_url = "https://dados.cvm.gov.br/dados"
        self.bcb_base_url = "https://api.bcb.gov.br/dados/serie"
        self.yahoo_base_url = "https://query1.finance.yahoo.com/v8/finance"
        
        # Request session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MercadoBrasil-API/1.0.0',
            'Accept': 'application/json'
        })
    
    def get_b3_quotes(self, tickers: List[str]) -> Dict[str, Any]:
        """Get real-time quotes from B3"""
        try:
            # Add .SA suffix for Brazilian stocks in Yahoo Finance format
            yahoo_tickers = [f"{ticker}.SA" for ticker in tickers]
            ticker_string = ','.join(yahoo_tickers)
            
            url = f"{self.yahoo_base_url}/chart/{ticker_string}"
            params = {
                'interval': '1m',
                'range': '1d',
                'includePrePost': 'false'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            quotes = {}
            
            if 'chart' in data and 'result' in data['chart']:
                for result in data['chart']['result']:
                    symbol = result['meta']['symbol'].replace('.SA', '')
                    meta = result['meta']
                    
                    quotes[symbol] = {
                        'symbol': symbol,
                        'price': meta.get('regularMarketPrice'),
                        'previous_close': meta.get('previousClose'),
                        'change': meta.get('regularMarketPrice', 0) - meta.get('previousClose', 0),
                        'change_percent': ((meta.get('regularMarketPrice', 0) - meta.get('previousClose', 0)) / meta.get('previousClose', 1)) * 100,
                        'volume': meta.get('regularMarketVolume'),
                        'high': meta.get('regularMarketDayHigh'),
                        'low': meta.get('regularMarketDayLow'),
                        'open': meta.get('regularMarketOpen'),
                        'market_cap': meta.get('marketCap'),
                        'timestamp': datetime.utcnow().isoformat()
                    }
            
            return quotes
            
        except Exception as e:
            logger.error(f"Error fetching B3 quotes: {str(e)}")
            return {}
    
    def get_cvm_company_data(self, cvm_code: int) -> Optional[Dict[str, Any]]:
        """Get company data from CVM"""
        try:
            # CVM's public data API
            url = f"{self.cvm_base_url}/CIA_ABERTA/CAD/DADOS"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse CVM data (usually in CSV format)
            # This is a simplified implementation
            # In reality, you'd need to parse CSV data and find the specific company
            
            return {
                'cvm_code': cvm_code,
                'source': 'CVM',
                'message': 'CVM data integration in development'
            }
            
        except Exception as e:
            logger.error(f"Error fetching CVM data for {cvm_code}: {str(e)}")
            return None
    
    def get_bcb_macro_indicators(self, indicator_codes: List[str]) -> Dict[str, Any]:
        """Get macroeconomic indicators from Banco Central"""
        try:
            indicators_data = {}
            
            # BCB SGS (Sistema Gerenciador de Séries Temporais) codes
            bcb_codes = {
                'SELIC': 432,
                'IPCA': 433,
                'IGP_M': 189,
                'PIB': 4380,
                'CAMBIO': 1
            }
            
            for indicator in indicator_codes:
                if indicator.upper() in bcb_codes:
                    code = bcb_codes[indicator.upper()]
                    
                    # Get last 12 months of data
                    end_date = datetime.now().strftime('%d/%m/%Y')
                    start_date = (datetime.now() - timedelta(days=365)).strftime('%d/%m/%Y')
                    
                    url = f"{self.bcb_base_url}/bcdata.sgs.{code}/dados"
                    params = {
                        'formato': 'json',
                        'dataInicial': start_date,
                        'dataFinal': end_date
                    }
                    
                    response = self.session.get(url, params=params, timeout=15)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    if data:
                        latest = data[-1]
                        previous = data[-2] if len(data) > 1 else data[-1]
                        
                        indicators_data[indicator.upper()] = {
                            'code': indicator.upper(),
                            'value': float(latest['valor']),
                            'date': latest['data'],
                            'previous_value': float(previous['valor']),
                            'change': float(latest['valor']) - float(previous['valor']),
                            'source': 'BCB',
                            'historical_data': data[-12:]  # Last 12 points
                        }
            
            return indicators_data
            
        except Exception as e:
            logger.error(f"Error fetching BCB indicators: {str(e)}")
            return {}
    
    def get_financial_news(self, keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Get financial news from multiple sources"""
        try:
            news_items = []
            
            # Using NewsAPI for demonstration
            # In production, you'd integrate with multiple news sources
            
            for keyword in keywords:
                url = "https://newsapi.org/v2/everything"
                params = {
                    'q': f"{keyword} AND (bolsa OR B3 OR investimento)",
                    'language': 'pt',
                    'sortBy': 'publishedAt',
                    'pageSize': limit,
                    'apiKey': self.news_api_key
                }
                
                response = self.session.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for article in data.get('articles', []):
                        news_item = {
                            'title': article.get('title'),
                            'summary': article.get('description'),
                            'content': article.get('content'),
                            'author': article.get('author'),
                            'published_at': article.get('publishedAt'),
                            'url': article.get('url'),
                            'source': article.get('source', {}).get('name'),
                            'category': 'market',
                            'sentiment': self._analyze_sentiment(article.get('title', '') + ' ' + article.get('description', '')),
                            'related_keywords': [keyword]
                        }
                        news_items.append(news_item)
            
            return news_items[:limit]
            
        except Exception as e:
            logger.error(f"Error fetching financial news: {str(e)}")
            return []
    
    def get_dividend_calendar(self, ticker: str) -> List[Dict[str, Any]]:
        """Get dividend calendar for ticker"""
        try:
            # Using Yahoo Finance for dividend data
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}.SA"
            params = {
                'events': 'div',
                'range': '1y'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            dividends = []
            
            if 'chart' in data and 'result' in data['chart']:
                result = data['chart']['result'][0]
                
                if 'events' in result and 'dividends' in result['events']:
                    for timestamp, div_data in result['events']['dividends'].items():
                        dividends.append({
                            'ticker': ticker,
                            'ex_date': datetime.fromtimestamp(int(timestamp)).isoformat(),
                            'amount': div_data.get('amount'),
                            'currency': 'BRL',
                            'type': 'dividend'
                        })
            
            return sorted(dividends, key=lambda x: x['ex_date'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error fetching dividend calendar for {ticker}: {str(e)}")
            return []
    
    def get_economic_calendar(self) -> List[Dict[str, Any]]:
        """Get economic calendar events"""
        try:
            # In a real implementation, this would fetch from economic calendar APIs
            # For now, returning structured data based on typical Brazilian economic events
            
            events = [
                {
                    'date': (datetime.now() + timedelta(days=7)).date().isoformat(),
                    'event': 'COPOM Meeting',
                    'country': 'Brazil',
                    'importance': 'high',
                    'description': 'Central Bank monetary policy meeting',
                    'previous': '11.75%',
                    'forecast': '11.75%',
                    'impact': 'BRL, IBOV'
                },
                {
                    'date': (datetime.now() + timedelta(days=14)).date().isoformat(),
                    'event': 'IPCA Inflation',
                    'country': 'Brazil', 
                    'importance': 'high',
                    'description': 'Monthly inflation rate',
                    'previous': '0.56%',
                    'forecast': '0.45%',
                    'impact': 'BRL, Bonds'
                },
                {
                    'date': (datetime.now() + timedelta(days=21)).date().isoformat(),
                    'event': 'GDP Growth',
                    'country': 'Brazil',
                    'importance': 'high',
                    'description': 'Quarterly GDP growth rate',
                    'previous': '0.9%',
                    'forecast': '0.7%',
                    'impact': 'IBOV, BRL'
                }
            ]
            
            return events
            
        except Exception as e:
            logger.error(f"Error fetching economic calendar: {str(e)}")
            return []
    
    def _analyze_sentiment(self, text: str) -> str:
        """Basic sentiment analysis"""
        positive_words = ['alta', 'subiu', 'ganho', 'lucro', 'crescimento', 'positivo', 'otimista']
        negative_words = ['queda', 'baixa', 'perda', 'prejuízo', 'crise', 'negativo', 'pessimista']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get status of external APIs"""
        apis_status = {}
        
        # Test Yahoo Finance
        try:
            response = self.session.get(f"{self.yahoo_base_url}/chart/PETR4.SA", timeout=5)
            apis_status['yahoo_finance'] = {
                'status': 'online' if response.status_code == 200 else 'offline',
                'response_time': response.elapsed.total_seconds()
            }
        except:
            apis_status['yahoo_finance'] = {'status': 'offline', 'response_time': None}
        
        # Test BCB
        try:
            response = self.session.get(f"{self.bcb_base_url}/bcdata.sgs.432/dados?formato=json", timeout=5)
            apis_status['bcb'] = {
                'status': 'online' if response.status_code == 200 else 'offline',
                'response_time': response.elapsed.total_seconds()
            }
        except:
            apis_status['bcb'] = {'status': 'offline', 'response_time': None}
        
        # Test CVM
        try:
            response = self.session.head(self.cvm_base_url, timeout=5)
            apis_status['cvm'] = {
                'status': 'online' if response.status_code in [200, 403] else 'offline',
                'response_time': response.elapsed.total_seconds()
            }
        except:
            apis_status['cvm'] = {'status': 'offline', 'response_time': None}
        
        return apis_status
    
    def rate_limit_handler(self, func, *args, **kwargs):
        """Handle rate limiting for external APIs"""
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limit exceeded
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Rate limit hit, retrying in {delay} seconds...")
                        time.sleep(delay)
                        continue
                raise e
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"API error, retrying in {delay} seconds: {str(e)}")
                    time.sleep(delay)
                    continue
                raise e
        
        return None
