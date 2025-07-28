import hashlib
import hmac
import time
import json
from datetime import datetime, date
from decimal import Decimal
from flask import jsonify, request
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def create_response(data=None, message="Success", status_code=200, pagination=None):
    """Create standardized API response"""
    response = {
        "status": "success" if status_code < 400 else "error",
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if data is not None:
        response["data"] = data
    
    if pagination:
        response["pagination"] = pagination
    
    return jsonify(response), status_code

def create_error_response(message, status_code=400, error_code=None):
    """Create standardized error response"""
    response = {
        "status": "error",
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status_code": status_code
    }
    
    if error_code:
        response["error_code"] = error_code
    
    return jsonify(response), status_code

def validate_pagination_params():
    """Validate and extract pagination parameters"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        
        if page < 1:
            page = 1
        if limit < 1:
            limit = 50
        if limit > 200:
            limit = 200
            
        return page, limit
    except ValueError:
        return 1, 50

def create_pagination_info(page, limit, total_items):
    """Create pagination metadata"""
    total_pages = (total_items + limit - 1) // limit
    
    return {
        "current_page": page,
        "per_page": limit,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }

def generate_api_key():
    """Generate a new API key"""
    timestamp = str(int(time.time()))
    random_data = hashlib.sha256(timestamp.encode()).hexdigest()
    return f"mb_{random_data[:32]}"

def hash_api_key(api_key):
    """Hash an API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def verify_api_key_signature(api_key, signature, data):
    """Verify API request signature"""
    expected_signature = hmac.new(
        api_key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)

def validate_date_format(date_string):
    """Validate date string format (YYYY-MM-DD)"""
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        return None

def validate_datetime_format(datetime_string):
    """Validate datetime string format (ISO 8601)"""
    try:
        return datetime.fromisoformat(datetime_string.replace('Z', '+00:00'))
    except ValueError:
        return None

def format_currency(value, currency='BRL'):
    """Format currency values"""
    if value is None:
        return None
    
    if currency == 'BRL':
        return f"R$ {value:,.2f}"
    elif currency == 'USD':
        return f"$ {value:,.2f}"
    else:
        return f"{value:,.2f} {currency}"

def format_percentage(value, decimal_places=2):
    """Format percentage values"""
    if value is None:
        return None
    return f"{value:.{decimal_places}f}%"

def sanitize_ticker(ticker):
    """Sanitize and validate ticker symbol"""
    if not ticker:
        return None
    
    # Remove whitespace and convert to uppercase
    ticker = ticker.strip().upper()
    
    # Validate ticker format (basic validation)
    if len(ticker) < 3 or len(ticker) > 10:
        return None
    
    return ticker

def parse_tickers(tickers_string):
    """Parse comma-separated ticker symbols"""
    if not tickers_string:
        return []
    
    tickers = []
    for ticker in tickers_string.split(','):
        sanitized = sanitize_ticker(ticker)
        if sanitized:
            tickers.append(sanitized)
    
    return tickers

def calculate_percentage_change(current, previous):
    """Calculate percentage change between two values"""
    if previous == 0 or previous is None or current is None:
        return None
    
    return ((current - previous) / previous) * 100

def safe_divide(numerator, denominator):
    """Safely divide two numbers, return None if division by zero"""
    if denominator == 0 or denominator is None or numerator is None:
        return None
    return numerator / denominator

def serialize_datetime(obj):
    """JSON serializer for datetime objects"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def log_api_request(endpoint, method, status_code, response_time_ms, api_key_id=None):
    """Log API request for analytics"""
    try:
        from models import RequestLog
        from app import db
        
        log_entry = RequestLog(
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            status_code=status_code,
            response_time_ms=response_time_ms
        )
        
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to log API request: {str(e)}")

def requires_auth(f):
    """Decorator to require API authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for API key in header or query parameter
        api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not api_key:
            api_key = request.args.get('token')
        
        if not api_key:
            return create_error_response("API key required", 401)
        
        # Here you would validate the API key against the database
        # For now, we'll accept any non-empty key
        if len(api_key) < 10:
            return create_error_response("Invalid API key", 401)
        
        return f(*args, **kwargs)
    return decorated_function

def validate_required_params(required_params):
    """Decorator to validate required query parameters"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            missing_params = []
            for param in required_params:
                if not request.args.get(param):
                    missing_params.append(param)
            
            if missing_params:
                return create_error_response(
                    f"Missing required parameters: {', '.join(missing_params)}", 
                    400
                )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def cache_key_builder(prefix, *args, **kwargs):
    """Build cache key from prefix and arguments"""
    key_parts = [prefix]
    key_parts.extend(str(arg) for arg in args)
    
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        key_parts.extend(f"{k}:{v}" for k, v in sorted_kwargs)
    
    return ":".join(key_parts)

def convert_to_float(value, default=None):
    """Safely convert value to float"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def convert_to_int(value, default=None):
    """Safely convert value to integer"""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def filter_dict_none_values(data):
    """Remove None values from dictionary"""
    return {k: v for k, v in data.items() if v is not None}

def calculate_financial_ratios(balance_sheet, income_statement, market_data):
    """Calculate financial ratios from financial statements"""
    ratios = {}
    
    try:
        # Current Ratio = Current Assets / Current Liabilities
        ratios['current_ratio'] = safe_divide(
            balance_sheet.get('current_assets'),
            balance_sheet.get('current_liabilities')
        )
        
        # ROE = Net Income / Shareholders Equity
        ratios['roe'] = safe_divide(
            income_statement.get('net_income'),
            balance_sheet.get('shareholders_equity')
        )
        
        # P/E Ratio = Market Cap / Net Income
        ratios['pe_ratio'] = safe_divide(
            market_data.get('market_cap'),
            income_statement.get('net_income')
        )
        
        # Add more ratio calculations as needed
        
    except Exception as e:
        logger.error(f"Error calculating financial ratios: {str(e)}")
    
    return ratios
