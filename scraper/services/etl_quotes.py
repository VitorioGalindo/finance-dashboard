"""
ETL para cotações e dados de mercado
Integração com brapi.dev, Yahoo Finance e outras fontes
"""
import requests
import logging
from datetime import datetime, timedelta
from app import db
from models import Quote, Ticker, Company
from services.external_apis import BrapiAPI

logger = logging.getLogger(__name__)

class QuotesETL:
    def __init__(self):
        self.brapi = BrapiAPI()
        
    def extract_real_time_quotes(self, tickers_list=None):
        """Extrai cotações em tempo real"""
        try:
            if not tickers_list:
                # Buscar todos os tickers ativos
                tickers = Ticker.query.all()
                tickers_list = [t.symbol for t in tickers]
            
            # Limitar a 50 tickers por request para evitar timeout
            batch_size = 50
            all_quotes = []
            
            for i in range(0, len(tickers_list), batch_size):
                batch = tickers_list[i:i+batch_size]
                quotes_batch = self._fetch_quotes_batch(batch)
                all_quotes.extend(quotes_batch)
            
            return all_quotes
            
        except Exception as e:
            logger.error(f"Erro ao extrair cotações: {str(e)}")
            return []
    
    def _fetch_quotes_batch(self, tickers):
        """Busca batch de cotações da brapi"""
        try:
            tickers_str = ','.join(tickers)
            url = f"https://brapi.dev/api/quote/{tickers_str}"
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get('results', [])
            
        except Exception as e:
            logger.error(f"Erro ao buscar batch de cotações: {str(e)}")
            return []
    
    def extract_historical_quotes(self, ticker, days=30):
        """Extrai cotações históricas"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            url = f"https://brapi.dev/api/quote/{ticker}"
            params = {
                'range': f'{days}d',
                'interval': '1d'
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'results' in data and len(data['results']) > 0:
                return data['results'][0].get('historicalDataPrice', [])
            return []
            
        except Exception as e:
            logger.error(f"Erro ao buscar histórico de {ticker}: {str(e)}")
            return []
    
    def transform_quote_data(self, raw_quote):
        """Transforma dados brutos de cotação"""
        if not raw_quote:
            return None
            
        try:
            return {
                'ticker': raw_quote.get('symbol', ''),
                'price': float(raw_quote.get('regularMarketPrice', 0)),
                'change': float(raw_quote.get('regularMarketChange', 0)),
                'change_percent': float(raw_quote.get('regularMarketChangePercent', 0)),
                'volume': int(raw_quote.get('regularMarketVolume', 0)),
                'volume_financial': float(raw_quote.get('regularMarketVolume', 0)) * float(raw_quote.get('regularMarketPrice', 0)),
                'open_price': float(raw_quote.get('regularMarketOpen', 0)),
                'high': float(raw_quote.get('regularMarketDayHigh', 0)),
                'low': float(raw_quote.get('regularMarketDayLow', 0)),
                'previous_close': float(raw_quote.get('regularMarketPreviousClose', 0)),
                'bid': float(raw_quote.get('bid', 0)),
                'ask': float(raw_quote.get('ask', 0)),
                'bid_size': int(raw_quote.get('bidSize', 0)),
                'ask_size': int(raw_quote.get('askSize', 0)),
                'market_status': raw_quote.get('marketState', 'CLOSED'),
                'timestamp': datetime.utcnow(),
                'quote_datetime': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Erro ao transformar cotação: {str(e)}")
            return None
    
    def load_quote(self, quote_data):
        """Carrega cotação no banco"""
        if not quote_data:
            return None
            
        try:
            # Verificar se ticker existe
            ticker_obj = Ticker.query.filter_by(symbol=quote_data['ticker']).first()
            if ticker_obj:
                quote_data['ticker_id'] = ticker_obj.id
            
            # Verificar se já existe cotação recente (últimos 5 minutos)
            recent_quote = Quote.query.filter_by(
                ticker=quote_data['ticker']
            ).filter(
                Quote.timestamp > datetime.utcnow() - timedelta(minutes=5)
            ).first()
            
            if recent_quote:
                # Atualizar cotação existente
                for key, value in quote_data.items():
                    if hasattr(recent_quote, key):
                        setattr(recent_quote, key, value)
                quote = recent_quote
            else:
                # Criar nova cotação
                quote = Quote(**quote_data)
                db.session.add(quote)
            
            db.session.commit()
            return quote
            
        except Exception as e:
            logger.error(f"Erro ao carregar cotação: {str(e)}")
            db.session.rollback()
            return None
    
    def extract_ibovespa_composition(self):
        """Extrai composição do Ibovespa"""
        try:
            url = "https://brapi.dev/api/quote/list"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            ibov_stocks = []
            
            if 'stocks' in data:
                for stock in data['stocks']:
                    if stock.get('type') == 'stock':
                        ibov_stocks.append(stock['stock'])
            
            return ibov_stocks
            
        except Exception as e:
            logger.error(f"Erro ao buscar composição Ibovespa: {str(e)}")
            return []
    
    def extract_currency_rates(self):
        """Extrai taxas de câmbio"""
        try:
            currencies = ['USDBRL', 'EURBRL', 'GBPBRL']
            rates = []
            
            for currency in currencies:
                url = f"https://brapi.dev/api/quote/{currency}=X"
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'results' in data and len(data['results']) > 0:
                        rates.append({
                            'symbol': currency,
                            'rate': data['results'][0].get('regularMarketPrice', 0),
                            'change': data['results'][0].get('regularMarketChange', 0),
                            'change_percent': data['results'][0].get('regularMarketChangePercent', 0),
                            'timestamp': datetime.utcnow()
                        })
            
            return rates
            
        except Exception as e:
            logger.error(f"Erro ao buscar taxas de câmbio: {str(e)}")
            return []
    
    def run_real_time_etl(self):
        """Executa ETL de cotações em tempo real"""
        logger.info("Iniciando ETL de cotações em tempo real")
        
        quotes_processed = 0
        
        # 1. Buscar composição do Ibovespa
        ibov_tickers = self.extract_ibovespa_composition()
        logger.info(f"Encontrados {len(ibov_tickers)} papéis do Ibovespa")
        
        # 2. Buscar cotações principais
        main_quotes = self.extract_real_time_quotes(ibov_tickers[:30])  # Top 30
        
        for quote_data in main_quotes:
            transformed = self.transform_quote_data(quote_data)
            if transformed:
                quote = self.load_quote(transformed)
                if quote:
                    quotes_processed += 1
        
        # 3. Buscar taxas de câmbio
        currency_rates = self.extract_currency_rates()
        for rate_data in currency_rates:
            transformed = self.transform_quote_data(rate_data)
            if transformed:
                quote = self.load_quote(transformed)
                if quote:
                    quotes_processed += 1
        
        logger.info(f"ETL de cotações concluído. {quotes_processed} cotações processadas")
        return quotes_processed
    
    def run_historical_etl(self, days=30):
        """Executa ETL de dados históricos"""
        logger.info(f"Iniciando ETL histórico de {days} dias")
        
        # Buscar principais tickers
        main_tickers = ['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'ABEV3', 'WEGE3', 'MGLU3', 'VVAR3']
        
        for ticker in main_tickers:
            historical_data = self.extract_historical_quotes(ticker, days)
            
            for hist_quote in historical_data:
                # Transformar dados históricos
                quote_data = {
                    'ticker': ticker,
                    'price': float(hist_quote.get('close', 0)),
                    'open_price': float(hist_quote.get('open', 0)),
                    'high': float(hist_quote.get('high', 0)),
                    'low': float(hist_quote.get('low', 0)),
                    'volume': int(hist_quote.get('volume', 0)),
                    'timestamp': datetime.fromtimestamp(hist_quote.get('date', 0)),
                    'quote_datetime': datetime.fromtimestamp(hist_quote.get('date', 0))
                }
                
                # Verificar se já existe
                existing = Quote.query.filter_by(
                    ticker=ticker,
                    timestamp=quote_data['timestamp']
                ).first()
                
                if not existing:
                    self.load_quote(quote_data)
        
        logger.info("ETL histórico concluído")

if __name__ == '__main__':
    etl = QuotesETL()
    etl.run_real_time_etl()