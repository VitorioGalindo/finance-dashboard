import logging
from datetime import datetime, timedelta
from sqlalchemy import func
from models import Company, Ticker, Quote, FinancialStatement, FinancialRatio, MarketRatio, Dividend
from .cache_service import CacheService

logger = logging.getLogger(__name__)

class DataService:
    """Service for data processing and business logic"""
    
    def __init__(self, db, cache_service):
        self.db = db
        self.cache = cache_service
    
    def get_company_by_cvm_code(self, cvm_code):
        """Get company by CVM code with caching"""
        cache_key = f"company:cvm:{cvm_code}"
        
        # Try cache first
        cached_company = self.cache.get(cache_key)
        if cached_company:
            return cached_company
        
        # Query database
        company = Company.query.filter_by(cvm_code=cvm_code).first()
        
        if company:
            company_data = {
                'id': company.id,
                'cvm_code': company.cvm_code,
                'company_name': company.company_name,
                'trade_name': company.trade_name,
                'cnpj': company.cnpj,
                'is_b3_listed': company.is_b3_listed,
                'b3_sector': company.b3_sector,
                'market_cap': company.market_cap
            }
            
            # Cache for 1 hour
            self.cache.set(cache_key, company_data, ttl=3600)
            return company_data
        
        return None
    
    def get_latest_quote(self, ticker_symbol):
        """Get latest quote for ticker with caching"""
        cache_key = f"quote:latest:{ticker_symbol.upper()}"
        
        # Try cache first (short TTL for real-time data)
        cached_quote = self.cache.get(cache_key)
        if cached_quote:
            return cached_quote
        
        # Query database
        ticker = Ticker.query.filter_by(symbol=ticker_symbol.upper()).first()
        if not ticker:
            return None
        
        latest_quote = Quote.query.filter_by(
            ticker_id=ticker.id
        ).order_by(Quote.quote_datetime.desc()).first()
        
        if latest_quote:
            quote_data = {
                'ticker': ticker_symbol.upper(),
                'price': latest_quote.price,
                'change': latest_quote.change,
                'change_percent': latest_quote.change_percent,
                'volume': latest_quote.volume,
                'high': latest_quote.high_price,
                'low': latest_quote.low_price,
                'timestamp': latest_quote.quote_datetime.isoformat()
            }
            
            # Cache for 1 minute (real-time data)
            self.cache.set(cache_key, quote_data, ttl=60)
            return quote_data
        
        return None
    
    def get_company_financial_ratios(self, company_id):
        """Get latest financial ratios for company"""
        cache_key = f"ratios:financial:{company_id}"
        
        cached_ratios = self.cache.get(cache_key)
        if cached_ratios:
            return cached_ratios
        
        latest_ratio = FinancialRatio.query.filter_by(
            company_id=company_id
        ).order_by(FinancialRatio.reference_date.desc()).first()
        
        if latest_ratio:
            ratios_data = {
                'reference_date': latest_ratio.reference_date.isoformat(),
                'liquidity': {
                    'current_ratio': latest_ratio.current_ratio,
                    'quick_ratio': latest_ratio.quick_ratio,
                    'cash_ratio': latest_ratio.cash_ratio
                },
                'profitability': {
                    'gross_margin': latest_ratio.gross_margin,
                    'operating_margin': latest_ratio.operating_margin,
                    'net_margin': latest_ratio.net_margin,
                    'roe': latest_ratio.roe,
                    'roa': latest_ratio.roa,
                    'roic': latest_ratio.roic
                },
                'leverage': {
                    'debt_to_equity': latest_ratio.debt_to_equity,
                    'debt_to_assets': latest_ratio.debt_to_assets,
                    'interest_coverage': latest_ratio.interest_coverage
                }
            }
            
            # Cache for 24 hours
            self.cache.set(cache_key, ratios_data, ttl=86400)
            return ratios_data
        
        return None
    
    def get_company_market_ratios(self, company_id):
        """Get latest market ratios for company"""
        cache_key = f"ratios:market:{company_id}"
        
        cached_ratios = self.cache.get(cache_key)
        if cached_ratios:
            return cached_ratios
        
        latest_ratio = MarketRatio.query.filter_by(
            company_id=company_id
        ).order_by(MarketRatio.reference_date.desc()).first()
        
        if latest_ratio:
            ratios_data = {
                'reference_date': latest_ratio.reference_date.isoformat(),
                'valuation': {
                    'pe_ratio': latest_ratio.pe_ratio,
                    'pb_ratio': latest_ratio.pb_ratio,
                    'ev_ebitda': latest_ratio.ev_ebitda,
                    'price_to_sales': latest_ratio.price_to_sales
                },
                'per_share': {
                    'earnings_per_share': latest_ratio.earnings_per_share,
                    'book_value_per_share': latest_ratio.book_value_per_share,
                    'dividend_per_share': latest_ratio.dividend_per_share
                },
                'market_data': {
                    'market_cap': latest_ratio.market_cap,
                    'enterprise_value': latest_ratio.enterprise_value,
                    'shares_outstanding': latest_ratio.shares_outstanding
                }
            }
            
            # Cache for 1 hour (market data changes frequently)
            self.cache.set(cache_key, ratios_data, ttl=3600)
            return ratios_data
        
        return None
    
    def get_dividend_history(self, company_id, years=5):
        """Get dividend history for company"""
        cache_key = f"dividends:{company_id}:{years}"
        
        cached_dividends = self.cache.get(cache_key)
        if cached_dividends:
            return cached_dividends
        
        # Calculate date range
        start_date = datetime.utcnow().date() - timedelta(days=years * 365)
        
        dividends = Dividend.query.filter(
            Dividend.company_id == company_id,
            Dividend.ex_date >= start_date
        ).order_by(Dividend.ex_date.desc()).all()
        
        dividend_data = []
        for dividend in dividends:
            dividend_data.append({
                'type': dividend.dividend_type,
                'ex_date': dividend.ex_date.isoformat(),
                'payment_date': dividend.payment_date.isoformat() if dividend.payment_date else None,
                'amount_per_share': dividend.amount_per_share,
                'yield_percentage': dividend.yield_percentage,
                'ticker': dividend.ticker_symbol
            })
        
        # Cache for 6 hours
        self.cache.set(cache_key, dividend_data, ttl=21600)
        return dividend_data
    
    def calculate_sector_performance(self):
        """Calculate sector performance metrics"""
        cache_key = "sector:performance"
        
        cached_performance = self.cache.get(cache_key)
        if cached_performance:
            return cached_performance
        
        # Query sector performance from database
        sector_query = self.db.session.query(
            Company.b3_sector,
            func.count(Company.id).label('company_count'),
            func.sum(Company.market_cap).label('total_market_cap'),
            func.avg(Company.market_cap).label('avg_market_cap')
        ).filter(
            Company.is_b3_listed == True,
            Company.b3_sector.isnot(None),
            Company.market_cap.isnot(None)
        ).group_by(Company.b3_sector).all()
        
        sector_data = []
        total_market_cap = sum(row.total_market_cap or 0 for row in sector_query)
        
        for row in sector_query:
            sector_info = {
                'sector': row.b3_sector,
                'company_count': row.company_count,
                'total_market_cap': row.total_market_cap or 0,
                'avg_market_cap': row.avg_market_cap or 0,
                'market_cap_percentage': round((row.total_market_cap or 0) / total_market_cap * 100, 2) if total_market_cap > 0 else 0
            }
            sector_data.append(sector_info)
        
        # Sort by market cap percentage
        sector_data.sort(key=lambda x: x['market_cap_percentage'], reverse=True)
        
        # Cache for 4 hours
        self.cache.set(cache_key, sector_data, ttl=14400)
        return sector_data
    
    def get_top_gainers_losers(self, limit=10):
        """Get top gainers and losers"""
        cache_key = f"movers:top:{limit}"
        
        cached_movers = self.cache.get(cache_key)
        if cached_movers:
            return cached_movers
        
        # Get latest quotes with significant changes
        current_date = datetime.utcnow().date()
        
        # Top gainers
        gainers_query = self.db.session.query(
            Ticker.symbol,
            Quote.price,
            Quote.change,
            Quote.change_percent,
            Quote.volume,
            Company.company_name
        ).join(Ticker).join(Company).filter(
            func.date(Quote.quote_datetime) == current_date,
            Quote.change_percent > 0
        ).order_by(Quote.change_percent.desc()).limit(limit)
        
        gainers = []
        for row in gainers_query:
            gainers.append({
                'ticker': row.symbol,
                'company_name': row.company_name,
                'price': row.price,
                'change': row.change,
                'change_percent': row.change_percent,
                'volume': row.volume
            })
        
        # Top losers
        losers_query = self.db.session.query(
            Ticker.symbol,
            Quote.price,
            Quote.change,
            Quote.change_percent,
            Quote.volume,
            Company.company_name
        ).join(Ticker).join(Company).filter(
            func.date(Quote.quote_datetime) == current_date,
            Quote.change_percent < 0
        ).order_by(Quote.change_percent.asc()).limit(limit)
        
        losers = []
        for row in losers_query:
            losers.append({
                'ticker': row.symbol,
                'company_name': row.company_name,
                'price': row.price,
                'change': row.change,
                'change_percent': row.change_percent,
                'volume': row.volume
            })
        
        movers_data = {
            'gainers': gainers,
            'losers': losers,
            'date': current_date.isoformat()
        }
        
        # Cache for 5 minutes
        self.cache.set(cache_key, movers_data, ttl=300)
        return movers_data
    
    def get_market_summary(self):
        """Get overall market summary"""
        cache_key = "market:summary"
        
        cached_summary = self.cache.get(cache_key)
        if cached_summary:
            return cached_summary
        
        current_date = datetime.utcnow().date()
        
        # Market statistics
        total_companies = Company.query.filter_by(is_b3_listed=True).count()
        total_market_cap = self.db.session.query(
            func.sum(Company.market_cap)
        ).filter(
            Company.is_b3_listed == True,
            Company.market_cap.isnot(None)
        ).scalar() or 0
        
        # Trading volume
        daily_volume = self.db.session.query(
            func.sum(Quote.volume_financial)
        ).filter(
            func.date(Quote.quote_datetime) == current_date,
            Quote.volume_financial.isnot(None)
        ).scalar() or 0
        
        # Advancing vs declining
        advancing = self.db.session.query(func.count(Quote.id)).filter(
            func.date(Quote.quote_datetime) == current_date,
            Quote.change > 0
        ).scalar() or 0
        
        declining = self.db.session.query(func.count(Quote.id)).filter(
            func.date(Quote.quote_datetime) == current_date,
            Quote.change < 0
        ).scalar() or 0
        
        summary_data = {
            'date': current_date.isoformat(),
            'total_companies': total_companies,
            'total_market_cap': total_market_cap,
            'daily_volume': daily_volume,
            'advancing_stocks': advancing,
            'declining_stocks': declining,
            'unchanged_stocks': total_companies - advancing - declining
        }
        
        # Cache for 10 minutes
        self.cache.set(cache_key, summary_data, ttl=600)
        return summary_data
    
    def invalidate_company_cache(self, company_id, cvm_code=None):
        """Invalidate cache entries for a company"""
        cache_keys = [
            f"ratios:financial:{company_id}",
            f"ratios:market:{company_id}",
            f"dividends:{company_id}:5"
        ]
        
        if cvm_code:
            cache_keys.append(f"company:cvm:{cvm_code}")
        
        for key in cache_keys:
            self.cache.delete(key)
    
    def invalidate_market_cache(self):
        """Invalidate market-wide cache entries"""
        cache_keys = [
            "market:summary",
            "sector:performance",
            "movers:top:10"
        ]
        
        for key in cache_keys:
            self.cache.delete(key)
