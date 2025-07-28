import time
from flask import request, jsonify
from functools import wraps
from app import redis_client

class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def is_rate_limited(self, key, limit, window=3600):
        """
        Check if a key is rate limited
        key: unique identifier (e.g., API key hash)
        limit: max requests allowed
        window: time window in seconds (default 1 hour)
        """
        try:
            current_time = int(time.time())
            window_start = current_time - window
            
            # Remove old entries
            self.redis.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            current_requests = self.redis.zcard(key)
            
            if current_requests >= limit:
                return True, 0
            
            # Add current request
            self.redis.zadd(key, {str(current_time): current_time})
            self.redis.expire(key, window)
            
            remaining = limit - current_requests - 1
            return False, remaining
        except Exception as e:
            # Fallback: allow request if Redis fails (for demo purposes)
            return False, limit
    
    def get_rate_limit_headers(self, key, limit, window=3600):
        """Get rate limit headers for response"""
        try:
            current_time = int(time.time())
            window_start = current_time - window
            
            # Clean old entries
            self.redis.zremrangebyscore(key, 0, window_start)
            current_requests = self.redis.zcard(key)
            
            remaining = max(0, limit - current_requests)
            reset_time = current_time + window
            
            return {
                'X-RateLimit-Limit': str(limit),
                'X-RateLimit-Remaining': str(remaining),
                'X-RateLimit-Reset': str(reset_time)
            }
        except Exception:
            # Fallback headers
            return {
                'X-RateLimit-Limit': str(limit),
                'X-RateLimit-Remaining': str(limit),
                'X-RateLimit-Reset': str(int(time.time()) + window)
            }

rate_limiter = RateLimiter(redis_client)

def apply_rate_limit(f):
    """Decorator to apply rate limiting based on API key plan"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'api_key_obj'):
            return jsonify({'error': 'Authentication required'}), 401
        
        api_key_obj = request.api_key_obj
        key = f"rate_limit:{api_key_obj.key_hash}"
        limit = api_key_obj.requests_per_hour
        
        is_limited, remaining = rate_limiter.is_rate_limited(key, limit)
        
        if is_limited:
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': f'Rate limit of {limit} requests per hour exceeded',
                'retry_after': 3600
            }), 429
        
        # Execute the function
        response = f(*args, **kwargs)
        
        # Add rate limit headers to response
        if hasattr(response, 'headers'):
            headers = rate_limiter.get_rate_limit_headers(key, limit)
            for header, value in headers.items():
                response.headers[header] = value
        
        return response
    
    return decorated_function
