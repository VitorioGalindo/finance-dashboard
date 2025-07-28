import os
from datetime import timedelta

class Config:
    # API Configuration
    API_VERSION = "v1"
    API_TITLE = "Mercado Brasil API"
    API_DESCRIPTION = "API completa do mercado financeiro brasileiro"
    
    # External API Keys (from environment variables)
    BRAPI_API_KEY = os.getenv("BRAPI_API_KEY", "demo_key")
    PARTNR_API_KEY = os.getenv("PARTNR_API_KEY", "demo_key")
    DADOS_MERCADO_API_KEY = os.getenv("DADOS_MERCADO_API_KEY", "demo_key")
    
    # External API URLs
    BRAPI_BASE_URL = "https://brapi.dev/api"
    PARTNR_BASE_URL = "https://data.partnr.ai/v2"
    DADOS_MERCADO_BASE_URL = "https://api.dadosdemercado.com.br/v1"
    
    # Rate Limiting Configuration
    RATE_LIMITS = {
        'basic': '1000 per hour',
        'professional': '10000 per hour', 
        'enterprise': '100000 per hour'
    }
    
    # Cache Configuration
    CACHE_TTL = {
        'quotes': 60,  # 1 minute
        'company_data': 3600,  # 1 hour
        'financial_statements': 86400,  # 24 hours
        'news': 300,  # 5 minutes
        'macro_indicators': 1800,  # 30 minutes
    }
    
    # WebSocket Configuration
    WEBSOCKET_MAX_CONNECTIONS = 50
    
    # Database Configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
