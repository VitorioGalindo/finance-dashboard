"""
Scraper para dados do Banco Central do Brasil (BACEN)
Busca indicadores macroeconômicos e dados do Sistema Financeiro Nacional
"""
import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
from app import db
from models import EconomicIndicator
import json

logger = logging.getLogger(__name__)

class BacenScraper:
    def __init__(self):
        self.base_url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
        self.olinda_url = "https://was.bcb.gov.br/ccs/service/ws/olinda"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Principais séries econômicas do BACEN
        self.economic_series = {
            '432': 'SELIC - Taxa básica de juros',
            '4390': 'IPCA - Índice de Preços ao Consumidor Amplo',
            '4389': 'IGP-M - Índice Geral de Preços do Mercado',
            '1': 'USD/BRL - Taxa de câmbio comercial',
            '10813': 'EUR/BRL - Taxa de câmbio euro',
            '21619': 'PIB - Produto Interno Bruto',
            '4192': 'Reservas Internacionais',
            '11752': 'Base Monetária',
            '1207': 'Dívida Líquida do Setor Público',
            '4513': 'Operações de Crédito do Sistema Financeiro',
            '20542': 'Taxa de Desemprego PNAD',
            '24363': 'Índice de Atividade Econômica do BC',
            '7832': 'Balança Comercial',
            '11777': 'Resultado Nominal do Governo Central',
            '4536': 'Crédito Rural',
            '20714': 'Vendas no Varejo',
            '21864': 'Produção Industrial',
            '4099': 'Confiança do Consumidor',
            '4102': 'Confiança da Indústria'
        }
    
    def scrape_economic_series(self, series_code, days_back=365):
        """Scraper de séries econômicas específicas"""
        try:
            # Calcular datas
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Formato de data para API do BACEN
            start_str = start_date.strftime('%d/%m/%Y')
            end_str = end_date.strftime('%d/%m/%Y')
            
            url = f"{self.base_url}/{series_code}/dados"
            params = {
                'formato': 'json',
                'dataInicial': start_str,
                'dataFinal': end_str
            }
            
            logger.info(f"Buscando série {series_code}: {self.economic_series.get(series_code, 'Desconhecida')}")
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            series_data = []
            for item in data:
                try:
                    indicator_data = {
                        'indicator_code': series_code,
                        'name': self.economic_series.get(series_code, f'Série {series_code}'),
                        'value': float(item['valor']) if item['valor'] else 0.0,
                        'date': datetime.strptime(item['data'], '%d/%m/%Y'),
                        'source': 'BACEN',
                        'created_at': datetime.utcnow()
                    }
                    series_data.append(indicator_data)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Erro ao processar item da série {series_code}: {e}")
                    continue
            
            logger.info(f"Extraídos {len(series_data)} pontos da série {series_code}")
            return series_data
            
        except Exception as e:
            logger.error(f"Erro ao extrair série {series_code}: {str(e)}")
            return []
    
    def scrape_interest_rates(self):
        """Scraper específico para taxas de juros"""
        try:
            # URL da API Olinda para taxas de juros
            url = f"{self.olinda_url}/taxasjuros"
            
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                
                rates_data = []
                if 'value' in data:
                    for rate in data['value']:
                        rate_data = {
                            'indicator_code': f"JUROS_{rate.get('Modalidade', '').upper()}",
                            'name': f"Taxa de Juros - {rate.get('Modalidade', '')}",
                            'value': float(rate.get('TaxaJurosAoMes', 0)),
                            'date': datetime.strptime(rate.get('DataReferencia', ''), '%Y-%m-%d') if rate.get('DataReferencia') else datetime.now(),
                            'unit': '% a.m.',
                            'source': 'BACEN-Olinda',
                            'created_at': datetime.utcnow()
                        }
                        rates_data.append(rate_data)
                
                return rates_data
                
        except Exception as e:
            logger.error(f"Erro ao extrair taxas de juros: {str(e)}")
            return []
    
    def scrape_exchange_rates(self):
        """Scraper de taxas de câmbio em tempo real"""
        try:
            # URL para cotações de moedas
            url = "https://ptax.bcb.gov.br/ptax_internet/consultarUltimaCotacaoPorMoeda.do"
            
            currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF']
            exchange_data = []
            
            for currency in currencies:
                try:
                    params = {
                        'method': 'consultarUltimaCotacaoPorMoeda',
                        'moeda': currency
                    }
                    
                    response = self.session.get(url, params=params, timeout=15)
                    if response.status_code == 200:
                        # Parse HTML response (PTAX retorna HTML)
                        import re
                        
                        # Extrair cotação usando regex
                        price_match = re.search(r'<td[^>]*>([\d,]+)</td>', response.text)
                        if price_match:
                            price_str = price_match.group(1).replace(',', '.')
                            price = float(price_str)
                            
                            exchange_data.append({
                                'indicator_code': f'{currency}BRL',
                                'name': f'Taxa de Câmbio {currency}/BRL',
                                'value': price,
                                'date': datetime.now(),
                                'unit': 'BRL',
                                'source': 'BACEN-PTAX',
                                'created_at': datetime.utcnow()
                            })
                
                except Exception as e:
                    logger.warning(f"Erro ao buscar {currency}: {str(e)}")
                    continue
            
            return exchange_data
            
        except Exception as e:
            logger.error(f"Erro ao extrair câmbio: {str(e)}")
            return []
    
    def scrape_inflation_data(self):
        """Scraper específico para dados de inflação"""
        try:
            inflation_series = {
                '433': 'IPCA - Mensal',
                '13522': 'IPCA - 12 meses',
                '189': 'IGP-M - Mensal', 
                '190': 'IGP-M - 12 meses',
                '4449': 'INPC - Mensal',
                '188': 'IGP-DI - Mensal'
            }
            
            all_inflation_data = []
            
            for series_code, name in inflation_series.items():
                series_data = self.scrape_economic_series(series_code, days_back=730)  # 2 anos
                for item in series_data:
                    item['name'] = name
                all_inflation_data.extend(series_data)
            
            return all_inflation_data
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados de inflação: {str(e)}")
            return []
    
    def scrape_credit_data(self):
        """Scraper de dados de crédito do sistema financeiro"""
        try:
            credit_series = {
                '20539': 'Operações de Crédito - Total',
                '20540': 'Operações de Crédito - Pessoa Física',
                '20541': 'Operações de Crédito - Pessoa Jurídica',
                '21112': 'Taxa de Juros - Pessoa Física',
                '21113': 'Taxa de Juros - Pessoa Jurídica',
                '21085': 'Inadimplência - Total',
                '21086': 'Inadimplência - Pessoa Física',
                '21087': 'Inadimplência - Pessoa Jurídica'
            }
            
            all_credit_data = []
            
            for series_code, name in credit_series.items():
                series_data = self.scrape_economic_series(series_code, days_back=365)
                for item in series_data:
                    item['name'] = name
                all_credit_data.extend(series_data)
            
            return all_credit_data
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados de crédito: {str(e)}")
            return []
    
    def load_indicators_to_db(self, indicators_data):
        """Carrega indicadores econômicos no banco"""
        loaded_count = 0
        
        try:
            for indicator_data in indicators_data:
                # Verificar se indicador já existe
                existing = EconomicIndicator.query.filter_by(
                    indicator_code=indicator_data['indicator_code'],
                    date=indicator_data['date']
                ).first()
                
                if not existing:
                    indicator = EconomicIndicator(**indicator_data)
                    db.session.add(indicator)
                    loaded_count += 1
                    
                    # Commit a cada 100 registros
                    if loaded_count % 100 == 0:
                        db.session.commit()
                        logger.info(f"Carregados {loaded_count} indicadores...")
            
            db.session.commit()
            logger.info(f"Total de {loaded_count} indicadores carregados")
            return loaded_count
            
        except Exception as e:
            logger.error(f"Erro ao carregar indicadores: {str(e)}")
            db.session.rollback()
            return 0
    
    def run_full_scraping(self):
        """Executa scraping completo do BACEN"""
        logger.info("Iniciando scraping completo do BACEN")
        
        all_indicators = []
        
        # 1. Principais séries econômicas
        for series_code in ['432', '4390', '4389', '1', '10813']:  # SELIC, IPCA, IGP-M, USD, EUR
            series_data = self.scrape_economic_series(series_code)
            all_indicators.extend(series_data)
        
        # 2. Taxas de câmbio em tempo real
        exchange_data = self.scrape_exchange_rates()
        all_indicators.extend(exchange_data)
        
        # 3. Dados de inflação
        inflation_data = self.scrape_inflation_data()
        all_indicators.extend(inflation_data)
        
        # 4. Dados de crédito
        credit_data = self.scrape_credit_data()
        all_indicators.extend(credit_data)
        
        # 5. Carregar no banco
        indicators_loaded = self.load_indicators_to_db(all_indicators)
        
        results = {
            'indicators_loaded': indicators_loaded,
            'series_processed': len(self.economic_series),
            'total_data_points': len(all_indicators)
        }
        
        logger.info(f"Scraping BACEN concluído: {results}")
        return results

if __name__ == '__main__':
    scraper = BacenScraper()
    scraper.run_full_scraping()