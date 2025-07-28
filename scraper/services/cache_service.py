import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)

class CacheService:
    """Service for caching data using Redis"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_ttl = 3600  # 1 hour default TTL
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            cached_value = self.redis.get(key)
            if cached_value:
                return json.loads(cached_value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=self._json_serializer)
            return self.redis.setex(key, ttl, serialized_value)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {str(e)}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment value in cache"""
        try:
            return self.redis.incr(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {str(e)}")
            return None
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for key"""
        try:
            return bool(self.redis.expire(key, ttl))
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {str(e)}")
            return False
    
    def get_ttl(self, key: str) -> Optional[int]:
        """Get TTL for key"""
        try:
            ttl = self.redis.ttl(key)
            return ttl if ttl >= 0 else None
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {str(e)}")
            return None
    
    def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache flush pattern error for {pattern}: {str(e)}")
            return 0
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        try:
            info = self.redis.info()
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'keys_count': len(self.redis.keys('*'))
            }
        except Exception as e:
            logger.error(f"Cache stats error: {str(e)}")
            return {}
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for datetime objects"""
        if isinstance(obj, (datetime, )):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    # Specialized cache methods for financial data
    
    def cache_quote(self, ticker: str, quote_data: dict, ttl: int = 60):
        """Cache quote data with short TTL"""
        key = f"quote:live:{ticker.upper()}"
        return self.set(key, quote_data, ttl)
    
    def get_cached_quote(self, ticker: str) -> Optional[dict]:
        """Get cached quote data"""
        key = f"quote:live:{ticker.upper()}"
        return self.get(key)
    
    def cache_financial_data(self, company_id: int, data_type: str, data: dict, ttl: int = 86400):
        """Cache financial data with long TTL"""
        key = f"financial:{data_type}:{company_id}"
        return self.set(key, data, ttl)
    
    def get_cached_financial_data(self, company_id: int, data_type: str) -> Optional[dict]:
        """Get cached financial data"""
        key = f"financial:{data_type}:{company_id}"
        return self.get(key)
    
    def cache_market_data(self, data_type: str, data: dict, ttl: int = 3600):
        """Cache market-wide data"""
        key = f"market:{data_type}"
        return self.set(key, data, ttl)
    
    def get_cached_market_data(self, data_type: str) -> Optional[dict]:
        """Get cached market data"""
        key = f"market:{data_type}"
        return self.get(key)
    
    def cache_news(self, news_id: str, news_data: dict, ttl: int = 7200):
        """Cache news data"""
        key = f"news:{news_id}"
        return self.set(key, news_data, ttl)
    
    def get_cached_news(self, news_id: str) -> Optional[dict]:
        """Get cached news data"""
        key = f"news:{news_id}"
        return self.get(key)
    
    def cache_macro_indicator(self, indicator_code: str, data: dict, ttl: int = 86400):
        """Cache macroeconomic indicator"""
        key = f"macro:{indicator_code}"
        return self.set(key, data, ttl)
    
    def get_cached_macro_indicator(self, indicator_code: str) -> Optional[dict]:
        """Get cached macro indicator"""
        key = f"macro:{indicator_code}"
        return self.get(key)
    
    def invalidate_company_data(self, company_id: int):
        """Invalidate all cached data for a company"""
        patterns = [
            f"financial:*:{company_id}",
            f"ratios:*:{company_id}",
            f"company:*:{company_id}"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.flush_pattern(pattern)
        
        return total_deleted
    
    def invalidate_ticker_data(self, ticker: str):
        """Invalidate all cached data for a ticker"""
        patterns = [
            f"quote:*:{ticker.upper()}",
            f"technical:*:{ticker.upper()}",
            f"history:*:{ticker.upper()}"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.flush_pattern(pattern)
        
        return total_deleted
    
    def warm_up_cache(self):
        """Warm up cache with frequently accessed data"""
        logger.info("Starting cache warm-up process")
        
        # This would be implemented to pre-load popular data
        # For example: top 20 most traded stocks, major indices, etc.
        
        popular_tickers = ['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'WEGE3', 'MGLU3', 'JBSS3', 'SUZB3']
        
        # Pre-cache popular ticker data
        for ticker in popular_tickers:
            try:
                # This would call the data service to load and cache the data
                pass
            except Exception as e:
                logger.error(f"Error warming up cache for {ticker}: {str(e)}")
        
        logger.info("Cache warm-up completed")
