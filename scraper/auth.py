import hashlib
import secrets
from datetime import datetime, timedelta
from flask import request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from functools import wraps
import redis
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, redis_client):
        self.redis = redis_client
        
    def generate_api_key(self, name, plan='basic'):
        """Generate a new API key"""
        # Create a secure random API key
        key = f"mb_{secrets.token_hex(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        # Store API key info in database
        try:
            from models import APIKey
            from app import db
            
            api_key_record = APIKey(
                key_hash=key_hash,
                name=name,
                plan=plan,
                rate_limit=self._get_rate_limit(plan),
                is_active=True
            )
            
            db.session.add(api_key_record)
            db.session.commit()
            
            return key, api_key_record.id
            
        except Exception as e:
            logger.error(f"Failed to create API key: {str(e)}")
            return None, None
    
    def _get_rate_limit(self, plan):
        """Get rate limit for plan"""
        rate_limits = {
            'basic': 1000,
            'professional': 10000,
            'enterprise': 100000
        }
        return rate_limits.get(plan, 1000)
    
    def validate_api_key(self, api_key):
        """Validate API key and return key info"""
        if not api_key:
            return None
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        try:
            from models import APIKey
            
            api_key_record = APIKey.query.filter_by(
                key_hash=key_hash,
                is_active=True
            ).first()
            
            if api_key_record:
                # Update last used timestamp
                api_key_record.last_used_at = datetime.utcnow()
                from app import db
                db.session.commit()
                
                return {
                    'id': api_key_record.id,
                    'name': api_key_record.name,
                    'plan': api_key_record.plan,
                    'rate_limit': api_key_record.rate_limit
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to validate API key: {str(e)}")
            return None
    
    def check_rate_limit(self, api_key_info):
        """Check if request is within rate limit"""
        if not api_key_info:
            return False, 0, 0
        
        key = f"rate_limit:{api_key_info['id']}"
        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        hour_key = f"{key}:{current_hour.isoformat()}"
        
        try:
            # Get current request count for this hour
            current_count = self.redis.get(hour_key)
            current_count = int(current_count) if current_count else 0
            
            rate_limit = api_key_info['rate_limit']
            
            if current_count >= rate_limit:
                return False, current_count, rate_limit
            
            # Increment counter
            pipeline = self.redis.pipeline()
            pipeline.incr(hour_key)
            pipeline.expire(hour_key, 3600)  # Expire after 1 hour
            pipeline.execute()
            
            return True, current_count + 1, rate_limit
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            # In case of Redis failure, allow the request
            return True, 0, api_key_info['rate_limit']
    
    def create_jwt_token(self, user_id, additional_claims=None):
        """Create JWT access token"""
        claims = additional_claims or {}
        return create_access_token(
            identity=user_id,
            additional_claims=claims
        )
    
    def extract_api_key_from_request(self):
        """Extract API key from request headers or query params"""
        # Check Authorization header
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Check query parameter
        return request.args.get('token')

# Global auth service instance
auth_service = None

def init_auth(redis_client):
    """Initialize authentication service"""
    global auth_service
    auth_service = AuthService(redis_client)
    return auth_service

def require_api_key(f):
    """Decorator to require valid API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract API key
        api_key = auth_service.extract_api_key_from_request()
        
        if not api_key:
            return jsonify({
                "error": "Authentication required",
                "message": "API key must be provided via Authorization header or 'token' query parameter",
                "status_code": 401
            }), 401
        
        # Validate API key
        api_key_info = auth_service.validate_api_key(api_key)
        
        if not api_key_info:
            return jsonify({
                "error": "Invalid API key",
                "message": "The provided API key is invalid or inactive",
                "status_code": 401
            }), 401
        
        # Check rate limit
        allowed, current_count, rate_limit = auth_service.check_rate_limit(api_key_info)
        
        if not allowed:
            return jsonify({
                "error": "Rate limit exceeded",
                "message": f"Rate limit of {rate_limit} requests per hour exceeded",
                "current_usage": current_count,
                "rate_limit": rate_limit,
                "status_code": 429
            }), 429
        
        # Add rate limit headers
        from flask import g
        g.api_key_info = api_key_info
        g.rate_limit_current = current_count
        g.rate_limit_limit = rate_limit
        
        return f(*args, **kwargs)
    
    return decorated_function

def optional_api_key(f):
    """Decorator for optional API key (for public endpoints with rate limiting)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = auth_service.extract_api_key_from_request()
        
        if api_key:
            api_key_info = auth_service.validate_api_key(api_key)
            if api_key_info:
                # Check rate limit for authenticated user
                allowed, current_count, rate_limit = auth_service.check_rate_limit(api_key_info)
                
                if not allowed:
                    return jsonify({
                        "error": "Rate limit exceeded",
                        "message": f"Rate limit of {rate_limit} requests per hour exceeded",
                        "status_code": 429
                    }), 429
                
                from flask import g
                g.api_key_info = api_key_info
                g.rate_limit_current = current_count
                g.rate_limit_limit = rate_limit
            else:
                # Invalid API key, treat as unauthenticated
                from flask import g
                g.api_key_info = None
        else:
            # No API key provided, apply default rate limiting by IP
            ip_address = request.remote_addr
            ip_key = f"rate_limit:ip:{ip_address}"
            current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            hour_key = f"{ip_key}:{current_hour.isoformat()}"
            
            try:
                current_count = auth_service.redis.get(hour_key)
                current_count = int(current_count) if current_count else 0
                
                # Default rate limit for unauthenticated requests
                default_limit = 100
                
                if current_count >= default_limit:
                    return jsonify({
                        "error": "Rate limit exceeded",
                        "message": f"Rate limit of {default_limit} requests per hour exceeded for unauthenticated requests",
                        "status_code": 429
                    }), 429
                
                # Increment counter
                pipeline = auth_service.redis.pipeline()
                pipeline.incr(hour_key)
                pipeline.expire(hour_key, 3600)
                pipeline.execute()
                
                from flask import g
                g.api_key_info = None
                g.rate_limit_current = current_count + 1
                g.rate_limit_limit = default_limit
                
            except Exception as e:
                logger.error(f"IP rate limiting failed: {str(e)}")
                # Continue without rate limiting in case of Redis failure
                from flask import g
                g.api_key_info = None
        
        return f(*args, **kwargs)
    
    return decorated_function

def add_rate_limit_headers(response):
    """Add rate limit headers to response"""
    from flask import g
    
    if hasattr(g, 'rate_limit_current') and hasattr(g, 'rate_limit_limit'):
        response.headers['X-RateLimit-Limit'] = str(g.rate_limit_limit)
        response.headers['X-RateLimit-Remaining'] = str(max(0, g.rate_limit_limit - g.rate_limit_current))
        response.headers['X-RateLimit-Reset'] = str(int((datetime.utcnow().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)).timestamp()))
    
    return response

# Admin functions for API key management
def create_api_key(name, plan='basic'):
    """Create new API key (admin function)"""
    return auth_service.generate_api_key(name, plan)

def revoke_api_key(api_key):
    """Revoke an API key (admin function)"""
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    try:
        from models import APIKey
        from app import db
        
        api_key_record = APIKey.query.filter_by(key_hash=key_hash).first()
        if api_key_record:
            api_key_record.is_active = False
            db.session.commit()
            return True
        return False
        
    except Exception as e:
        logger.error(f"Failed to revoke API key: {str(e)}")
        return False

def list_api_keys():
    """List all API keys (admin function)"""
    try:
        from models import APIKey
        
        keys = APIKey.query.all()
        return [{
            'id': key.id,
            'name': key.name,
            'plan': key.plan,
            'rate_limit': key.rate_limit,
            'is_active': key.is_active,
            'created_at': key.created_at.isoformat(),
            'last_used_at': key.last_used_at.isoformat() if key.last_used_at else None
        } for key in keys]
        
    except Exception as e:
        logger.error(f"Failed to list API keys: {str(e)}")
        return []
