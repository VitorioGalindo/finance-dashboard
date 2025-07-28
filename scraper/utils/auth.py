import os
import hashlib
import jwt
from functools import wraps
from flask import request, jsonify, current_app
from models import ApiKey, db
from datetime import datetime, timedelta

def hash_api_key(api_key):
    """Hash an API key for secure storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def generate_api_key():
    """Generate a new API key"""
    import secrets
    return secrets.token_urlsafe(32)

def validate_api_key(api_key):
    """Validate an API key and return the associated plan"""
    if not api_key:
        return None, "API key required"
    
    key_hash = hash_api_key(api_key)
    api_key_obj = ApiKey.query.filter_by(key_hash=key_hash, is_active=True).first()
    
    if not api_key_obj:
        return None, "Invalid API key"
    
    # Update last used timestamp
    api_key_obj.last_used = datetime.utcnow()
    db.session.commit()
    
    return api_key_obj, None

def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Try to get API key from header first, then query parameter
        api_key = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            api_key = auth_header.split(' ')[1]
        else:
            api_key = request.args.get('token')
        
        if not api_key:
            return jsonify({
                'error': 'Authentication required',
                'message': 'API key must be provided via Authorization header or token parameter'
            }), 401
        
        api_key_obj, error = validate_api_key(api_key)
        if error:
            return jsonify({'error': 'Authentication failed', 'message': error}), 401
        
        # Add api_key_obj to request context
        request.api_key_obj = api_key_obj
        
        return f(*args, **kwargs)
    
    return decorated_function

def create_demo_api_keys():
    """Create demo API keys for testing"""
    demo_keys = [
        {'email': 'demo@basic.com', 'plan': 'basic', 'requests_per_hour': 1000},
        {'email': 'demo@pro.com', 'plan': 'professional', 'requests_per_hour': 10000},
        {'email': 'demo@enterprise.com', 'plan': 'enterprise', 'requests_per_hour': 100000}
    ]
    
    for key_info in demo_keys:
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        
        existing_key = ApiKey.query.filter_by(user_email=key_info['email']).first()
        if not existing_key:
            new_key = ApiKey(
                key_hash=key_hash,
                user_email=key_info['email'],
                plan=key_info['plan'],
                requests_per_hour=key_info['requests_per_hour']
            )
            db.session.add(new_key)
            print(f"Created API key for {key_info['email']} ({key_info['plan']}): {api_key}")
    
    db.session.commit()
