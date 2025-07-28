import re
from datetime import datetime, timedelta
from flask import request

def validate_ticker(ticker):
    """Validate Brazilian stock ticker format"""
    if not ticker:
        return False, "Ticker is required"
    
    # Brazilian tickers: 4 letters + 1-2 digits (e.g., PETR4, VALE3)
    # Or indices starting with ^ (e.g., ^BVSP)
    pattern = r'^(\^[A-Z]{3,4}|[A-Z]{4}\d{1,2})$'
    
    if not re.match(pattern, ticker.upper()):
        return False, "Invalid ticker format"
    
    return True, None

def validate_cvm_code(cvm_code):
    """Validate CVM code"""
    try:
        code = int(cvm_code)
        if code <= 0:
            return False, "CVM code must be positive"
        return True, None
    except (ValueError, TypeError):
        return False, "CVM code must be a valid integer"

def validate_date_range(date_from, date_to):
    """Validate date range parameters"""
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
        except ValueError:
            return False, "date_from must be in YYYY-MM-DD format"
    else:
        from_date = None
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
        except ValueError:
            return False, "date_to must be in YYYY-MM-DD format"
    else:
        to_date = None
    
    if from_date and to_date and from_date > to_date:
        return False, "date_from cannot be after date_to"
    
    return True, None

def validate_period(period):
    """Validate period parameter for historical data"""
    valid_periods = ['1d', '5d', '1m', '3m', '6m', '1y', '2y', '5y', 'max']
    
    if period and period not in valid_periods:
        return False, f"Period must be one of: {', '.join(valid_periods)}"
    
    return True, None

def validate_interval(interval):
    """Validate interval parameter for historical data"""
    valid_intervals = ['1m', '5m', '15m', '30m', '1h', '1d', '1wk', '1mo']
    
    if interval and interval not in valid_intervals:
        return False, f"Interval must be one of: {', '.join(valid_intervals)}"
    
    return True, None

def validate_pagination():
    """Validate pagination parameters"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        
        if page < 1:
            return False, "Page must be >= 1", None, None
        
        if limit < 1 or limit > 200:
            return False, "Limit must be between 1 and 200", None, None
        
        return True, None, page, limit
    
    except (ValueError, TypeError):
        return False, "Page and limit must be valid integers", None, None

def validate_report_type(report_type):
    """Validate financial report type"""
    valid_types = ['BPA', 'BPP', 'DRE', 'DFC_MI', 'DVA', 'DRA']
    
    if report_type and report_type not in valid_types:
        return False, f"Report type must be one of: {', '.join(valid_types)}"
    
    return True, None

def validate_aggregation(aggregation):
    """Validate aggregation type"""
    valid_aggregations = ['INDIVIDUAL', 'CONSOLIDATED']
    
    if aggregation and aggregation not in valid_aggregations:
        return False, f"Aggregation must be one of: {', '.join(valid_aggregations)}"
    
    return True, None
