"""
Scraper para notícias financeiras de fontes públicas brasileiras
Busca notícias de portais como G1, UOL, InfoMoney, Valor Econômico
"""
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime, timedelta
from app import db
from models import News
import trafilatura
import re
from urllib.parse import urljoin, urlparse
import hashlib

logger = logging.getLogger(__name__)

class NewsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Fontes de notícias financeiras gratuitas
        self.news_sources = {
            'g1_economia': {
                'url': 'https://g1.globo.com/economia/',
                'rss': 'https://g1.globo.com/dynamo/economia/rss2.xml',
                'selector': '.feed-post-body'
            },
            'uol_economia': {
                'url': 'https://economia.uol.com.br/',
                'rss': 'https://economia.uol.com.br/index.xml',
                'selector': '.news-list-item'
            },
            'infomoney': {
                'url': 'https://www.infomoney.com.br/',
                'rss': 'https://www.infomoney.com.br/feed/',
                'selector': '.article'
            },
            'cnn_business': {
                'url': 'https://www.cnnbrasil.com.br/business/',
                'selector': '.home__list__tag'
            },
            'exame': {
                'url': 'https://exame.com/economia/',
                'selector': '.ListPostsTemplate'
            }
        }
    
    def scrape_rss_feeds(self):
        """Scraper de feeds RSS de notícias"""
        try:
            all_news = []
            
            for source_name, config in self.news_sources.items():
                if 'rss' not in config:
                    continue
                    
                try:
                    logger.info(f"Processando RSS: {source_name}")
                    
                    response = self.session.get(config['rss'], timeout=30)
                    response.raise_for_status()
                    
                    # Parse XML RSS
                    from xml.etree import ElementTree as ET
                    root = ET.fromstring(response.content)
                    
                    # Processar items do RSS
                    items = root.findall('.//item')
                    
                    for item in items[:10]:  # Limite de 10 por fonte
                        try:
                            title = item.find('title').text if item.find('title') is not None else ''
                            link = item.find('link').text if item.find('link') is not None else ''
                            description = item.find('description').text if item.find('description') is not None else ''
                            pub_date_str = item.find('pubDate').text if item.find('pubDate') is not None else ''
                            
                            # Parse data de publicação
                            pub_date = self._parse_rss_date(pub_date_str)
                            
                            # Gerar ID único
                            news_id = hashlib.md5(f"{source_name}_{link}".encode()).hexdigest()[:20]
                            
                            if title and link:
                                news_item = {
                                    'news_id': news_id,
                                    'title': title.strip(),
                                    'summary': description.strip()[:500] if description else '',
                                    'url': link,
                                    'author': source_name.replace('_', ' ').title(),
                                    'published_at': pub_date or datetime.utcnow(),
                                    'category': 'economia',
                                    'tags': self._extract_tags(title + ' ' + description),
                                    'related_tickers': self._extract_tickers(title + ' ' + description),
                                    'created_at': datetime.utcnow()
                                }
                                all_news.append(news_item)
                        
                        except Exception as e:
                            logger.warning(f"Erro ao processar item RSS de {source_name}: {str(e)}")
                            continue
                
                except Exception as e:
                    logger.warning(f"Erro ao processar RSS de {source_name}: {str(e)}")
                    continue
            
            logger.info(f"Extraídas {len(all_news)} notícias via RSS")
            return all_news
            
        except Exception as e:
            logger.error(f"Erro ao processar feeds RSS: {str(e)}")
            return []
    
    def scrape_website_news(self, source_name, max_articles=10):
        """Scraper direto de websites de notícias"""
        try:
            if source_name not in self.news_sources:
                return []
            
            config = self.news_sources[source_name]
            response = self.session.get(config['url'], timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            news_items = []
            articles = soup.select(config['selector'])[:max_articles]
            
            for article in articles:
                try:
                    # Extrair link do artigo
                    link_elem = article.find('a')
                    if not link_elem or not link_elem.get('href'):
                        continue
                    
                    link = urljoin(config['url'], link_elem['href'])
                    
                    # Extrair título
                    title_elem = article.find(['h1', 'h2', 'h3', 'h4'])
                    if not title_elem:
                        title_elem = link_elem
                    
                    title = title_elem.get_text(strip=True) if title_elem else ''
                    
                    # Buscar conteúdo completo do artigo
                    article_content = self._fetch_article_content(link)
                    
                    if title and article_content:
                        news_id = hashlib.md5(f"{source_name}_{link}".encode()).hexdigest()[:20]
                        
                        news_item = {
                            'news_id': news_id,
                            'title': title[:500],
                            'summary': article_content[:1000] if len(article_content) > 1000 else article_content,
                            'content': article_content,
                            'url': link,
                            'author': source_name.replace('_', ' ').title(),
                            'published_at': datetime.utcnow(),
                            'category': 'economia',
                            'tags': self._extract_tags(title + ' ' + article_content),
                            'related_tickers': self._extract_tickers(title + ' ' + article_content),
                            'created_at': datetime.utcnow()
                        }
                        news_items.append(news_item)
                
                except Exception as e:
                    logger.warning(f"Erro ao processar artigo de {source_name}: {str(e)}")
                    continue
            
            logger.info(f"Extraídas {len(news_items)} notícias de {source_name}")
            return news_items
            
        except Exception as e:
            logger.error(f"Erro ao extrair notícias de {source_name}: {str(e)}")
            return []
    
    def scrape_cvm_news(self):
        """Scraper de comunicados da CVM"""
        try:
            url = "https://www.gov.br/cvm/pt-br/assuntos/noticias"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            cvm_news = []
            articles = soup.find_all('article', class_='tileItem')[:15]
            
            for article in articles:
                try:
                    title_elem = article.find('h2')
                    link_elem = article.find('a')
                    date_elem = article.find('time')
                    
                    if not title_elem or not link_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = urljoin(url, link_elem['href'])
                    
                    # Parse data
                    pub_date = datetime.utcnow()
                    if date_elem and date_elem.get('datetime'):
                        try:
                            pub_date = datetime.fromisoformat(date_elem['datetime'].replace('Z', '+00:00'))
                        except:
                            pass
                    
                    # Buscar conteúdo
                    content = self._fetch_article_content(link)
                    
                    news_id = hashlib.md5(f"cvm_{link}".encode()).hexdigest()[:20]
                    
                    cvm_news.append({
                        'news_id': news_id,
                        'title': title,
                        'summary': content[:500] if content else '',
                        'content': content,
                        'url': link,
                        'author': 'CVM',
                        'published_at': pub_date,
                        'category': 'regulatorio',
                        'tags': ['cvm', 'regulacao', 'mercado_capitais'],
                        'related_tickers': self._extract_tickers(title + ' ' + (content or '')),
                        'created_at': datetime.utcnow()
                    })
                
                except Exception as e:
                    logger.warning(f"Erro ao processar notícia CVM: {str(e)}")
                    continue
            
            logger.info(f"Extraídas {len(cvm_news)} notícias da CVM")
            return cvm_news
            
        except Exception as e:
            logger.error(f"Erro ao extrair notícias CVM: {str(e)}")
            return []
    
    def scrape_bacen_news(self):
        """Scraper de comunicados do Banco Central"""
        try:
            url = "https://www.bcb.gov.br/detalhenoticia"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            bacen_news = []
            articles = soup.find_all('div', class_='noticia')[:10]
            
            for article in articles:
                try:
                    title_elem = article.find('h3')
                    link_elem = article.find('a')
                    date_elem = article.find('span', class_='data')
                    
                    if not title_elem or not link_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = urljoin(url, link_elem['href'])
                    
                    # Parse data brasileira
                    pub_date = datetime.utcnow()
                    if date_elem:
                        date_text = date_elem.get_text(strip=True)
                        pub_date = self._parse_brazilian_date(date_text) or pub_date
                    
                    content = self._fetch_article_content(link)
                    
                    news_id = hashlib.md5(f"bacen_{link}".encode()).hexdigest()[:20]
                    
                    bacen_news.append({
                        'news_id': news_id,
                        'title': title,
                        'summary': content[:500] if content else '',
                        'content': content,
                        'url': link,
                        'author': 'Banco Central',
                        'published_at': pub_date,
                        'category': 'politica_monetaria',
                        'tags': ['bacen', 'politica_monetaria', 'juros'],
                        'related_tickers': self._extract_tickers(title + ' ' + (content or '')),
                        'created_at': datetime.utcnow()
                    })
                
                except Exception as e:
                    logger.warning(f"Erro ao processar notícia BACEN: {str(e)}")
                    continue
            
            logger.info(f"Extraídas {len(bacen_news)} notícias do BACEN")
            return bacen_news
            
        except Exception as e:
            logger.error(f"Erro ao extrair notícias BACEN: {str(e)}")
            return []
    
    def _fetch_article_content(self, url):
        """Busca conteúdo completo do artigo usando trafilatura"""
        try:
            response = self.session.get(url, timeout=20)
            if response.status_code == 200:
                # Usar trafilatura para extrair texto limpo
                content = trafilatura.extract(response.text)
                return content.strip() if content else ''
        except Exception as e:
            logger.warning(f"Erro ao buscar conteúdo de {url}: {str(e)}")
        
        return ''
    
    def _extract_tickers(self, text):
        """Extrai tickers de ações do texto"""
        if not text:
            return []
        
        # Padrões comuns de tickers brasileiros
        ticker_patterns = [
            r'\b([A-Z]{4}[0-9]{1,2})\b',  # PETR4, VALE3, etc.
            r'\b([A-Z]{3,4}[0-9]{1,2})\b',  # Variações
        ]
        
        tickers = set()
        for pattern in ticker_patterns:
            matches = re.findall(pattern, text.upper())
            tickers.update(matches)
        
        # Lista de tickers conhecidos para validação
        known_tickers = ['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'ABEV3', 'WEGE3', 'MGLU3', 'VVAR3', 'SUZB3', 'RENT3']
        
        # Filtrar apenas tickers válidos
        valid_tickers = [t for t in tickers if t in known_tickers or len(t) >= 4]
        
        return list(valid_tickers)[:5]  # Máximo 5 tickers
    
    def _extract_tags(self, text):
        """Extrai tags relevantes do texto"""
        if not text:
            return []
        
        # Palavras-chave financeiras
        keywords = {
            'inflacao': ['inflação', 'ipca', 'igpm', 'preços'],
            'juros': ['juros', 'selic', 'taxa', 'monetária'],
            'dolar': ['dólar', 'câmbio', 'moeda'],
            'bovespa': ['bovespa', 'ibovespa', 'bolsa'],
            'petroleo': ['petróleo', 'petrobras', 'combustível'],
            'banking': ['banco', 'bradesco', 'itaú', 'santander'],
            'mining': ['mineração', 'vale', 'ferro'],
            'retail': ['varejo', 'magazine', 'luiza'],
            'energy': ['energia', 'elétrica', 'renovável'],
            'real_estate': ['imobiliário', 'construção', 'habitação']
        }
        
        text_lower = text.lower()
        tags = []
        
        for tag, terms in keywords.items():
            if any(term in text_lower for term in terms):
                tags.append(tag)
        
        return tags[:5]  # Máximo 5 tags
    
    def _parse_rss_date(self, date_str):
        """Parse date from RSS format"""
        if not date_str:
            return None
        
        try:
            # Formato RFC 2822: Wed, 02 Oct 2002 08:00:00 EST
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except:
            return None
    
    def _parse_brazilian_date(self, date_str):
        """Parse date from Brazilian format"""
        if not date_str:
            return None
        
        try:
            # Formatos: 15/03/2024, 15 de março de 2024
            date_clean = re.sub(r'[^\d/]', '/', date_str)
            if '/' in date_clean:
                parts = [p for p in date_clean.split('/') if p.isdigit()]
                if len(parts) >= 3:
                    day, month, year = parts[:3]
                    return datetime(int(year), int(month), int(day))
        except:
            pass
        
        return None
    
    def load_news_to_db(self, news_data):
        """Carrega notícias no banco de dados"""
        loaded_count = 0
        
        try:
            for news_item in news_data:
                # Verificar se notícia já existe
                existing = News.query.filter_by(news_id=news_item['news_id']).first()
                
                if not existing:
                    # Converter arrays para JSON
                    news_item['tags'] = news_item.get('tags', [])
                    news_item['related_tickers'] = news_item.get('related_tickers', [])
                    
                    news = News(**news_item)
                    db.session.add(news)
                    loaded_count += 1
                    
                    if loaded_count % 50 == 0:
                        db.session.commit()
                        logger.info(f"Carregadas {loaded_count} notícias...")
            
            db.session.commit()
            logger.info(f"Total de {loaded_count} notícias carregadas")
            return loaded_count
            
        except Exception as e:
            logger.error(f"Erro ao carregar notícias: {str(e)}")
            db.session.rollback()
            return 0
    
    def run_full_scraping(self):
        """Executa scraping completo de notícias"""
        logger.info("Iniciando scraping completo de notícias")
        
        all_news = []
        
        # 1. RSS feeds
        rss_news = self.scrape_rss_feeds()
        all_news.extend(rss_news)
        
        # 2. Websites específicos
        for source in ['g1_economia', 'infomoney']:
            site_news = self.scrape_website_news(source, max_articles=5)
            all_news.extend(site_news)
        
        # 3. Notícias da CVM
        cvm_news = self.scrape_cvm_news()
        all_news.extend(cvm_news)
        
        # 4. Notícias do BACEN
        bacen_news = self.scrape_bacen_news()
        all_news.extend(bacen_news)
        
        # 5. Carregar no banco
        news_loaded = self.load_news_to_db(all_news)
        
        results = {
            'news_loaded': news_loaded,
            'sources_processed': len(self.news_sources) + 2,  # +CVM +BACEN
            'total_articles_found': len(all_news)
        }
        
        logger.info(f"Scraping de notícias concluído: {results}")
        return results

if __name__ == '__main__':
    scraper = NewsScraper()
    scraper.run_full_scraping()