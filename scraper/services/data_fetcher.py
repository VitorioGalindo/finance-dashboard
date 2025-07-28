import requests
import json
import time
from datetime import datetime, timedelta
from flask import current_app
from app import redis_client
from config import Config

class DataFetcher:
    def __init__(self):
        self.brapi_base = Config.BRAPI_BASE_URL
        self.partnr_base = Config.PARTNR_BASE_URL
        self.dados_mercado_base = Config.DADOS_MERCADO_BASE_URL
        self.cache_ttl = Config.CACHE_TTL
    
    def _get_cached_data(self, cache_key):
        """Get data from Redis cache"""
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            current_app.logger.error(f"Cache read error: {e}")
        return None
    
    def _set_cached_data(self, cache_key, data, ttl=3600):
        """Set data in Redis cache"""
        try:
            redis_client.setex(cache_key, ttl, json.dumps(data, default=str))
        except Exception as e:
            current_app.logger.error(f"Cache write error: {e}")
    
    def fetch_quote(self, ticker):
        """Fetch stock quote from brapi.dev"""
        cache_key = f"quote:{ticker}"
        cached_data = self._get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            url = f"{self.brapi_base}/quote/{ticker}"
            headers = {'Authorization': f'Bearer {Config.BRAPI_API_KEY}'}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    quote_data = data['results'][0]
                    self._set_cached_data(cache_key, quote_data, self.cache_ttl['quotes'])
                    return quote_data
            
            return None
            
        except Exception as e:
            current_app.logger.error(f"Error fetching quote for {ticker}: {e}")
            return None
    
    def fetch_historical_data(self, ticker, period='1y', interval='1d'):
        """Fetch historical price data"""
        cache_key = f"historical:{ticker}:{period}:{interval}"
        cached_data = self._get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            url = f"{self.brapi_base}/quote/{ticker}"
            params = {'range': period, 'interval': interval}
            headers = {'Authorization': f'Bearer {Config.BRAPI_API_KEY}'}
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results') and data['results'][0].get('historicalDataPrice'):
                    historical_data = data['results'][0]['historicalDataPrice']
                    self._set_cached_data(cache_key, historical_data, 1800)  # 30 min cache
                    return historical_data
            
            return []
            
        except Exception as e:
            current_app.logger.error(f"Error fetching historical data for {ticker}: {e}")
            return []
    
    def fetch_company_data(self, cvm_code):
        """Fetch company data from multiple sources"""
        cache_key = f"company:{cvm_code}"
        cached_data = self._get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        # Try to fetch from dados de mercado first
        try:
            url = f"{self.dados_mercado_base}/companies/{cvm_code}"
            headers = {'Authorization': f'Bearer {Config.DADOS_MERCADO_API_KEY}'}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                company_data = response.json()
                self._set_cached_data(cache_key, company_data, self.cache_ttl['company_data'])
                return company_data
        
        except Exception as e:
            current_app.logger.error(f"Error fetching company data for {cvm_code}: {e}")
        
        # Return mock structure if API fails
        return {
            'cvm_code': cvm_code,
            'company_name': f'Empresa CVM {cvm_code}',
            'error': 'Data not available - external API unavailable'
        }
    
    def fetch_financial_statements(self, cvm_code, report_type=None, aggregation=None):
        """Fetch financial statements"""
        cache_key = f"statements:{cvm_code}:{report_type}:{aggregation}"
        cached_data = self._get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            url = f"{self.dados_mercado_base}/companies/{cvm_code}/raw-reports"
            params = {}
            if report_type:
                params['report_type'] = report_type
            if aggregation:
                params['aggregation'] = aggregation
            
            headers = {'Authorization': f'Bearer {Config.DADOS_MERCADO_API_KEY}'}
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                statements = response.json()
                self._set_cached_data(cache_key, statements, self.cache_ttl['financial_statements'])
                return statements
            
            return []
            
        except Exception as e:
            current_app.logger.error(f"Error fetching financial statements for {cvm_code}: {e}")
            return []
    
    def fetch_economic_indicators(self, indicator=None):
        """Fetch macroeconomic indicators"""
        cache_key = f"macro:{indicator or 'all'}"
        cached_data = self._get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        # Mock economic indicators data structure
        indicators_data = {
            'indicators': [
                {
                    'indicator_code': 'SELIC',
                    'name': 'Taxa Selic',
                    'value': 11.75,
                    'unit': 'percent_annual',
                    'date': datetime.now().isoformat(),
                    'previous_value': 12.25,
                    'change': -0.50,
                    'source': 'BCB'
                },
                {
                    'indicator_code': 'IPCA',
                    'name': 'IPCA',
                    'value': 4.62,
                    'unit': 'percent_annual',
                    'date': datetime.now().isoformat(),
                    'previous_value': 5.79,
                    'change': -1.17,
                    'source': 'IBGE'
                }
            ]
        }
        
        if indicator:
            indicators_data['indicators'] = [
                ind for ind in indicators_data['indicators'] 
                if ind['indicator_code'].lower() == indicator.lower()
            ]
        
        self._set_cached_data(cache_key, indicators_data, self.cache_ttl['macro_indicators'])
        return indicators_data
    
    def fetch_news(self, category=None, ticker=None):
        """Fetch financial news"""
        cache_key = f"news:{category or 'all'}:{ticker or 'all'}"
        cached_data = self._get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        # Mock news data structure
        news_data = {
            'news': [
                {
                    'id': 'news_123456',
                    'title': 'Mercado brasileiro mostra recuperação',
                    'summary': 'Principais índices sobem com otimismo dos investidores...',
                    'content': 'O mercado brasileiro demonstrou sinais de recuperação...',
                    'author': 'Redação Financeira',
                    'published_at': datetime.now().isoformat(),
                    'url': 'https://example.com/news/123456',
                    'category': category or 'market',
                    'tags': ['mercado', 'brasil', 'economia'],
                    'sentiment': 'positive',
                    'sentiment_score': 0.7,
                    'impact_score': 7.5,
                    'related_tickers': [ticker] if ticker else ['IBOV', 'PETR4', 'VALE3']
                }
            ]
        }
        
        self._set_cached_data(cache_key, news_data, self.cache_ttl['news'])
        return news_data

# Global instance
data_fetcher = DataFetcher()
