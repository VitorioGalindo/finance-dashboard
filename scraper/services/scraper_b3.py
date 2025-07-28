"""
Scraper para dados da B3 (Brasil, Bolsa, Balcão)
Busca cotações, dividendos e dados de mercado diretamente do site da B3
"""
import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from app import db
from models import Quote, Ticker, Dividend
import trafilatura
import re

logger = logging.getLogger(__name__)

class B3Scraper:
    def __init__(self):
        self.base_url = "https://www.b3.com.br"
        self.quotes_url = "https://cotacoes.b3.com.br"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_ibovespa_composition(self):
        """Scraper da composição atual do Ibovespa"""
        try:
            url = f"{self.base_url}/pt_br/market-data-e-indices/indices/indices-amplos/indice-ibovespa-ibovespa-composicao-da-carteira.htm"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Encontrar tabela de composição
            table = soup.find('table', class_='table')
            if not table:
                # Tentar encontrar por outras classes ou tags
                tables = soup.find_all('table')
                if tables:
                    table = tables[0]
            
            ibov_composition = []
            if table:
                rows = table.find_all('tr')[1:]  # Pular cabeçalho
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        try:
                            ticker = cells[0].get_text(strip=True)
                            company_name = cells[1].get_text(strip=True)
                            weight = float(cells[2].get_text(strip=True).replace(',', '.').replace('%', ''))
                            
                            ibov_composition.append({
                                'ticker': ticker,
                                'company_name': company_name,
                                'weight': weight,
                                'index': 'IBOVESPA',
                                'updated_at': datetime.utcnow()
                            })
                        except (ValueError, IndexError):
                            continue
            
            logger.info(f"Extraída composição do Ibovespa: {len(ibov_composition)} papéis")
            return ibov_composition
            
        except Exception as e:
            logger.error(f"Erro ao extrair composição Ibovespa: {str(e)}")
            return []
    
    def scrape_stock_quotes(self, tickers_list):
        """Scraper de cotações de ações da B3"""
        try:
            quotes_data = []
            
            for ticker in tickers_list:
                try:
                    # URL da página de cotação individual
                    url = f"{self.quotes_url}/mdf/executar/ConsultarInstrumento"
                    
                    params = {
                        'acao': ticker,
                        'idioma': 'pt-br'
                    }
                    
                    response = self.session.get(url, params=params, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Extrair dados da cotação
                        price_elem = soup.find('span', class_='cotacao')
                        if price_elem:
                            price_text = price_elem.get_text(strip=True).replace(',', '.')
                            price = float(re.findall(r'[\d,\.]+', price_text)[0])
                            
                            # Buscar outros dados
                            variation_elem = soup.find('span', class_='variacao')
                            volume_elem = soup.find('span', class_='volume')
                            
                            variation = 0
                            if variation_elem:
                                var_text = variation_elem.get_text(strip=True)
                                var_match = re.search(r'([-+]?\d+[\.,]?\d*)', var_text)
                                if var_match:
                                    variation = float(var_match.group(1).replace(',', '.'))
                            
                            volume = 0
                            if volume_elem:
                                vol_text = volume_elem.get_text(strip=True)
                                vol_match = re.search(r'(\d+[\.,]?\d*)', vol_text)
                                if vol_match:
                                    volume = int(float(vol_match.group(1).replace(',', '.')))
                            
                            quotes_data.append({
                                'ticker': ticker,
                                'price': price,
                                'change': variation,
                                'change_percent': (variation / (price - variation)) * 100 if price > variation else 0,
                                'volume': volume,
                                'timestamp': datetime.utcnow(),
                                'quote_datetime': datetime.utcnow(),
                                'market_status': 'OPEN' if self._is_market_open() else 'CLOSED'
                            })
                
                except Exception as e:
                    logger.warning(f"Erro ao extrair cotação de {ticker}: {str(e)}")
                    continue
            
            logger.info(f"Extraídas {len(quotes_data)} cotações da B3")
            return quotes_data
            
        except Exception as e:
            logger.error(f"Erro ao extrair cotações B3: {str(e)}")
            return []
    
    def scrape_dividends_calendar(self, year=None):
        """Scraper do calendário de dividendos"""
        if not year:
            year = datetime.now().year
            
        try:
            # URL para agenda de dividendos
            url = f"{self.base_url}/pt_br/produtos-e-servicos/negociacao/renda-variavel/acoes/proventos/"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            dividends_data = []
            
            # Procurar tabelas de dividendos
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')[1:]  # Pular cabeçalho
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 5:
                        try:
                            ticker = cells[0].get_text(strip=True)
                            ex_date_str = cells[1].get_text(strip=True)
                            payment_date_str = cells[2].get_text(strip=True)
                            amount_str = cells[3].get_text(strip=True)
                            div_type = cells[4].get_text(strip=True)
                            
                            # Parse datas
                            ex_date = self._parse_date(ex_date_str)
                            payment_date = self._parse_date(payment_date_str)
                            
                            # Parse valor
                            amount = 0
                            if amount_str:
                                amount_clean = re.sub(r'[^\d,\.]', '', amount_str).replace(',', '.')
                                if amount_clean:
                                    amount = float(amount_clean)
                            
                            if ticker and ex_date and amount > 0:
                                dividends_data.append({
                                    'ticker': ticker,
                                    'ex_date': ex_date,
                                    'payment_date': payment_date,
                                    'amount': amount,
                                    'type': div_type.lower() if div_type else 'dividend',
                                    'created_at': datetime.utcnow()
                                })
                        
                        except (ValueError, IndexError) as e:
                            continue
            
            logger.info(f"Extraídos {len(dividends_data)} dividendos")
            return dividends_data
            
        except Exception as e:
            logger.error(f"Erro ao extrair dividendos: {str(e)}")
            return []
    
    def scrape_market_indicators(self):
        """Scraper de indicadores de mercado"""
        try:
            url = f"{self.base_url}/pt_br/market-data-e-indices/"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            indicators = []
            
            # Buscar indicadores principais
            ibov_elem = soup.find('span', {'data-name': 'IBOV'})
            if ibov_elem:
                price_elem = ibov_elem.find_next('span', class_='price')
                if price_elem:
                    price = float(price_elem.get_text(strip=True).replace('.', '').replace(',', '.'))
                    indicators.append({
                        'ticker': 'IBOV',
                        'price': price,
                        'timestamp': datetime.utcnow(),
                        'quote_datetime': datetime.utcnow(),
                        'market_status': 'OPEN' if self._is_market_open() else 'CLOSED'
                    })
            
            # Outros índices importantes
            indices = ['IFIX', 'ICON', 'IMAT', 'UTIL', 'IFNC']
            for index in indices:
                try:
                    index_elem = soup.find('span', {'data-name': index})
                    if index_elem:
                        price_elem = index_elem.find_next('span', class_='price')
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            price = float(price_text.replace('.', '').replace(',', '.'))
                            
                            indicators.append({
                                'ticker': index,
                                'price': price,
                                'timestamp': datetime.utcnow(),
                                'quote_datetime': datetime.utcnow(),
                                'market_status': 'OPEN' if self._is_market_open() else 'CLOSED'
                            })
                except:
                    continue
            
            return indicators
            
        except Exception as e:
            logger.error(f"Erro ao extrair indicadores de mercado: {str(e)}")
            return []
    
    def scrape_sector_performance(self):
        """Scraper de performance por setor"""
        try:
            url = f"{self.base_url}/pt_br/market-data-e-indices/indices/indices-de-segmentos-e-setoriais/"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            sectors_data = []
            
            # Buscar tabela de setores
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')[1:]  # Pular cabeçalho
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        try:
                            sector_name = cells[0].get_text(strip=True)
                            index_value = cells[1].get_text(strip=True)
                            variation = cells[2].get_text(strip=True)
                            
                            # Parse valores
                            value = float(index_value.replace('.', '').replace(',', '.'))
                            var_match = re.search(r'([-+]?\d+[\.,]?\d*)', variation)
                            var_percent = 0
                            if var_match:
                                var_percent = float(var_match.group(1).replace(',', '.'))
                            
                            sectors_data.append({
                                'sector': sector_name,
                                'index_value': value,
                                'variation_percent': var_percent,
                                'timestamp': datetime.utcnow()
                            })
                        
                        except (ValueError, IndexError):
                            continue
            
            return sectors_data
            
        except Exception as e:
            logger.error(f"Erro ao extrair performance setorial: {str(e)}")
            return []
    
    def _is_market_open(self):
        """Verifica se o mercado está aberto"""
        now = datetime.now()
        
        # Mercado brasileiro: Segunda a Sexta, 10h às 17h
        if now.weekday() >= 5:  # Sábado = 5, Domingo = 6
            return False
        
        if now.hour < 10 or now.hour >= 17:
            return False
        
        return True
    
    def _parse_date(self, date_str):
        """Parse date from Brazilian format"""
        if not date_str:
            return None
        
        try:
            # Formatos comuns: DD/MM/YYYY, DD/MM/YY
            date_clean = re.sub(r'[^\d/]', '', date_str)
            if '/' in date_clean:
                parts = date_clean.split('/')
                if len(parts) == 3:
                    day, month, year = parts
                    if len(year) == 2:
                        year = '20' + year
                    return datetime(int(year), int(month), int(day))
        except:
            pass
        
        return None
    
    def load_quotes_to_db(self, quotes_data):
        """Carrega cotações no banco"""
        loaded_count = 0
        
        try:
            for quote_data in quotes_data:
                # Check if ticker exists
                ticker_obj = Ticker.query.filter_by(symbol=quote_data['ticker']).first()
                if ticker_obj:
                    quote_data['ticker_id'] = ticker_obj.id
                
                # Check for recent quote (last 5 minutes)
                recent_quote = Quote.query.filter_by(
                    ticker=quote_data['ticker']
                ).filter(
                    Quote.timestamp > datetime.utcnow() - timedelta(minutes=5)
                ).first()
                
                if recent_quote:
                    # Update existing quote
                    for key, value in quote_data.items():
                        if hasattr(recent_quote, key):
                            setattr(recent_quote, key, value)
                else:
                    # Create new quote
                    quote = Quote(**quote_data)
                    db.session.add(quote)
                
                loaded_count += 1
                
                if loaded_count % 50 == 0:
                    db.session.commit()
                    logger.info(f"Carregadas {loaded_count} cotações...")
            
            db.session.commit()
            logger.info(f"Total de {loaded_count} cotações carregadas")
            return loaded_count
            
        except Exception as e:
            logger.error(f"Erro ao carregar cotações: {str(e)}")
            db.session.rollback()
            return 0
    
    def load_dividends_to_db(self, dividends_data):
        """Carrega dividendos no banco"""
        loaded_count = 0
        
        try:
            for dividend_data in dividends_data:
                # Check if dividend already exists
                existing = Dividend.query.filter_by(
                    ticker=dividend_data['ticker'],
                    ex_date=dividend_data['ex_date']
                ).first()
                
                if not existing:
                    dividend = Dividend(**dividend_data)
                    db.session.add(dividend)
                    loaded_count += 1
                    
                    if loaded_count % 100 == 0:
                        db.session.commit()
                        logger.info(f"Carregados {loaded_count} dividendos...")
            
            db.session.commit()
            logger.info(f"Total de {loaded_count} dividendos carregados")
            return loaded_count
            
        except Exception as e:
            logger.error(f"Erro ao carregar dividendos: {str(e)}")
            db.session.rollback()
            return 0
    
    def run_full_scraping(self):
        """Executa scraping completo da B3"""
        logger.info("Iniciando scraping completo da B3")
        
        # 1. Composição do Ibovespa
        ibov_composition = self.scrape_ibovespa_composition()
        main_tickers = [item['ticker'] for item in ibov_composition[:20]]  # Top 20
        
        # 2. Cotações das principais ações
        quotes_data = self.scrape_stock_quotes(main_tickers)
        quotes_loaded = self.load_quotes_to_db(quotes_data)
        
        # 3. Indicadores de mercado
        market_indicators = self.scrape_market_indicators()
        indicators_loaded = self.load_quotes_to_db(market_indicators)
        
        # 4. Dividendos
        dividends_data = self.scrape_dividends_calendar()
        dividends_loaded = self.load_dividends_to_db(dividends_data)
        
        # 5. Performance setorial
        sectors_data = self.scrape_sector_performance()
        
        results = {
            'quotes_loaded': quotes_loaded,
            'indicators_loaded': indicators_loaded,
            'dividends_loaded': dividends_loaded,
            'ibov_composition': len(ibov_composition),
            'sectors_found': len(sectors_data)
        }
        
        logger.info(f"Scraping B3 concluído: {results}")
        return results

if __name__ == '__main__':
    scraper = B3Scraper()
    scraper.run_full_scraping()