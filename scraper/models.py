# scraper/models.py (VERSÃO COMPLETA E CORRIGIDA)
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

# Cria uma Base da qual todos os modelos herdarão
Base = declarative_base()

# --- MODELOS ---

class Company(Base):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True)
    cvm_code = Column(Integer, unique=True, nullable=False)
    company_name = Column(String(255), nullable=False)
    trade_name = Column(String(255))
    cnpj = Column(String(20), unique=True)
    founded_date = Column(DateTime)
    main_activity = Column(Text)
    website = Column(String(255))
    controlling_interest = Column(String(100))
    is_state_owned = Column(Boolean, default=False)
    is_foreign = Column(Boolean, default=False)
    is_b3_listed = Column(Boolean, default=False)
    b3_issuer_code = Column(String(10))
    b3_listing_segment = Column(String(50))
    b3_sector = Column(String(100))
    b3_subsector = Column(String(100))
    b3_segment = Column(String(100))
    tickers = Column(JSON)
    ticker = Column(String(10))
    is_active = Column(Boolean, default=True)
    industry_classification = Column(String(255))
    market_cap = Column(Float)
    employee_count = Column(Integer)
    about = Column(Text)
    has_dfp_data = Column(Boolean, default=False)
    has_itr_data = Column(Boolean, default=False)
    has_fre_data = Column(Boolean, default=False)
    last_dfp_year = Column(Integer)
    last_itr_quarter = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Adiciona o relacionamento para que possamos acessar os demonstrativos a partir de uma empresa
    financial_statements = relationship("FinancialStatement", back_populates="company")

class Quote(Base):
    __tablename__ = 'quotes'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float, nullable=False)
    volume = Column(Integer)
    adjusted_close = Column(Float)
    price = Column(Float, nullable=False)
    change = Column(Float)
    change_percent = Column(Float)
    volume_financial = Column(Float)
    high = Column(Float)
    low = Column(Float)
    previous_close = Column(Float)
    bid = Column(Float)
    ask = Column(Float)
    bid_size = Column(Integer)
    ask_size = Column(Integer)
    market_status = Column(String(20))
    timestamp = Column(DateTime, default=datetime.utcnow)
    quote_datetime = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class News(Base):
    __tablename__ = 'news'
    id = Column(Integer, primary_key=True)
    news_id = Column(String(50), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    content = Column(Text)
    author = Column(String(255))
    published_at = Column(DateTime, nullable=False)
    url = Column(String(500))
    category = Column(String(50))
    impact_score = Column(Float)
    related_tickers = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class InsiderTransaction(Base):
    __tablename__ = 'insider_transactions'
    id = Column(Integer, primary_key=True)
    cvm_code = Column(Integer, nullable=False, index=True)
    company_name = Column(String(255))
    document_.type = Column(String(50))
    delivery_date = Column(DateTime)
    reference_date = Column(DateTime)
    status = Column(String(50))
    download_url = Column(String(500))
    year = Column(Integer, index=True)
    insider_name = Column(String(255))
    position = Column(String(255))
    transaction_type = Column(String(50))
    quantity = Column(Integer)
    unit_price = Column(Float)
    total_value = Column(Float)
    transaction_date = Column(DateTime)
    remaining_position = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class FinancialRatio(Base):
    __tablename__ = 'financial_ratios'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False, index=True)
    cvm_code = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    quarter = Column(String(5))
    pe_ratio = Column(Float)
    pb_ratio = Column(Float)
    roe = Column(Float)
    roa = Column(Float)
    debt_to_equity = Column(Float)
    current_ratio = Column(Float)
    gross_margin = Column(Float)
    net_margin = Column(Float)
    dividend_yield = Column(Float)
    ebitda_margin = Column(Float)
    net_debt_ebitda = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class TechnicalIndicatorNew(Base):
    __tablename__ = 'technical_indicators_new'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    sma_20 = Column(Float)
    sma_50 = Column(Float)
    sma_200 = Column(Float)
    ema_12 = Column(Float)
    ema_26 = Column(Float)
    rsi = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    bollinger_upper = Column(Float)
    bollinger_lower = Column(Float)
    volatility = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class EconomicIndicator(Base):
    __tablename__ = 'economic_indicators'
    id = Column(Integer, primary_key=True)
    indicator_code = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(50))
    date = Column(DateTime, nullable=False)
    previous_value = Column(Float)
    change = Column(Float)
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

class ApiKey(Base):
    __tablename__ = 'api_keys'
    id = Column(Integer, primary_key=True)
    key_hash = Column(String(255), unique=True, nullable=False)
    user_email = Column(String(255))
    plan = Column(String(50), default='basic')
    requests_per_hour = Column(Integer, default=1000)
    requests_used = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)

class FinancialStatement(Base):
    __tablename__ = 'financial_statements'
    id = Column(Integer, primary_key=True)
    
    # --- CHAVE ESTRANGEIRA ADICIONADA ---
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    
    cvm_code = Column(Integer, nullable=False, index=True)
    report_type = Column(String(20), nullable=False)
    aggregation = Column(String(20), nullable=False)
    reference_date = Column(DateTime, nullable=False)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    publish_date = Column(DateTime)
    version = Column(Integer, default=1)
    data = Column(JSON)
    tree_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Adiciona o relacionamento reverso para acessar a empresa a partir do demonstrativo
    company = relationship("Company", back_populates="financial_statements")

class Ticker(Base):
    __tablename__ = 'tickers'
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), unique=True, nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id'))
    type = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

class MarketRatio(Base):
    __tablename__ = 'market_ratios'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False)
    ratio_type = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Dividend(Base):
    __tablename__ = 'dividends'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False)
    ex_date = Column(DateTime, nullable=False)
    payment_date = Column(DateTime)
    amount = Column(Float, nullable=False)
    type = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

class CVMFinancialData(Base):
    __tablename__ = 'cvm_financial_data'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    cvm_code = Column(Integer, nullable=False, index=True)
    statement_type = Column(String(10), nullable=False)
    year = Column(Integer, nullable=False)
    quarter = Column(String(10))
    reference_date = Column(DateTime)
    version = Column(Integer, default=1)
    total_assets = Column(Float)
    current_assets = Column(Float)
    non_current_assets = Column(Float)
    total_liabilities = Column(Float)
    current_liabilities = Column(Float)
    non_current_liabilities = Column(Float)
    shareholders_equity = Column(Float)
    revenue = Column(Float)
    gross_profit = Column(Float)
    operating_profit = Column(Float)
    net_income = Column(Float)
    ebitda = Column(Float)
    operating_cash_flow = Column(Float)
    investing_cash_flow = Column(Float)
    financing_cash_flow = Column(Float)
    raw_dfp_data = Column(JSON)
    raw_itr_data = Column(JSON)
    raw_fre_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CVMDocument(Base):
    __tablename__ = 'cvm_documents'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    cvm_code = Column(Integer, nullable=False, index=True)
    document_type = Column(String(100), nullable=False)
    document_category = Column(String(200))
    title = Column(String(500))
    delivery_date = Column(DateTime)
    reference_date = Column(DateTime)
    status = Column(String(50))
    download_url = Column(String(1000))
    file_size = Column(Integer)
    file_type = Column(String(20))
    content_text = Column(Text)
    content_summary = Column(Text)
    extracted_at = Column(DateTime)
    processing_status = Column(String(50), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)

class RequestLog(Base):
    __tablename__ = 'request_logs'
    id = Column(Integer, primary_key=True)
    api_key_hash = Column(String(255))
    endpoint = Column(String(255))
    method = Column(String(10))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    response_code = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Alias para compatibilidade
APIKey = ApiKey
