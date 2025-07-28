#!/usr/bin/env python3
"""
Extended database models for complete CVM data collection
All 13 data points from CVM/RAD specification
"""

from app import db
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

# Ponto 1: Informações Gerais das Companhias
class CompanyInfo(db.Model):
    __tablename__ = 'company_info'
    
    id = Column(Integer, primary_key=True)
    cvm_code = Column(String(20), nullable=False, index=True)
    company_name = Column(String(200), nullable=False)
    cnpj = Column(String(20), nullable=False)
    ticker = Column(String(10), index=True)
    segment = Column(String(100))
    sector = Column(String(100))
    activity_sector = Column(String(200))
    situation = Column(String(50))
    registration_date = Column(DateTime)
    year = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Ponto 2: Demonstrações Financeiras (DFP/ITR)
class FinancialStatements(db.Model):
    __tablename__ = 'financial_statements'
    
    id = Column(Integer, primary_key=True)
    cvm_code = Column(String(20), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    period = Column(Integer)  # Trimestre para ITR
    statement_type = Column(String(10))  # DFP ou ITR
    document_type = Column(String(10))  # BPA, BPP, DRE, DFC, etc
    account_code = Column(String(20))
    account_description = Column(String(500))
    account_value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_financial_cvm_year_type', 'cvm_code', 'year', 'statement_type'),
    )

# Ponto 3: Transações de Pessoas Ligadas (Insider Trading)
class InsiderTrading(db.Model):
    __tablename__ = 'insider_trading'
    
    id = Column(Integer, primary_key=True)
    cvm_code = Column(String(20), nullable=False, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    insider_name = Column(String(200), nullable=False)
    insider_position = Column(String(100))
    transaction_date = Column(DateTime, nullable=False, index=True)
    transaction_type = Column(String(20))  # Compra, Venda
    quantity = Column(Integer)
    unit_price = Column(Float)
    total_value = Column(Float)
    shares_after = Column(Integer)
    percentage_after = Column(Float)
    year = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Ponto 4: Dividendos e Remunerações
class Dividends(db.Model):
    __tablename__ = 'dividends'
    
    id = Column(Integer, primary_key=True)
    cvm_code = Column(String(20), nullable=False, index=True)
    ticker = Column(String(10), index=True)
    dividend_type = Column(String(50))  # Dividendos, JCP, Bonificação
    declaration_date = Column(DateTime, index=True)
    ex_date = Column(DateTime, index=True)
    payment_date = Column(DateTime, index=True)
    value_per_share = Column(Float)
    total_amount = Column(Float)
    year = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Ponto 5: Composição Acionária
class ShareholdingComposition(db.Model):
    __tablename__ = 'shareholding_composition'
    
    id = Column(Integer, primary_key=True)
    cvm_code = Column(String(20), nullable=False, index=True)
    shareholder_name = Column(String(200), nullable=False)
    shareholder_type = Column(String(50))  # Pessoa Física, Jurídica, etc
    nationality = Column(String(50))
    shares_quantity = Column(Integer)
    shares_percentage = Column(Float)
    voting_rights = Column(Float)
    position_date = Column(DateTime, index=True)
    year = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Ponto 6: Administradores e Conselheiros
class BoardMembers(db.Model):
    __tablename__ = 'board_members'
    
    id = Column(Integer, primary_key=True)
    cvm_code = Column(String(20), nullable=False, index=True)
    member_name = Column(String(200), nullable=False)
    position = Column(String(100))  # CEO, CFO, Conselheiro, etc
    position_type = Column(String(50))  # Executivo, Conselho
    appointment_date = Column(DateTime)
    term_end_date = Column(DateTime)
    remuneration = Column(Float)
    education = Column(Text)
    experience = Column(Text)
    year = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Ponto 7: Assembleias Gerais
class GeneralAssemblies(db.Model):
    __tablename__ = 'general_assemblies'
    
    id = Column(Integer, primary_key=True)
    cvm_code = Column(String(20), nullable=False, index=True)
    assembly_type = Column(String(50))  # AGO, AGE
    assembly_date = Column(DateTime, nullable=False, index=True)
    call_notice_date = Column(DateTime)
    matters_discussed = Column(Text)
    resolutions = Column(Text)
    attendance_quorum = Column(Float)
    voting_results = Column(Text)
    year = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Ponto 8: Partes Relacionadas
class RelatedParties(db.Model):
    __tablename__ = 'related_parties'
    
    id = Column(Integer, primary_key=True)
    cvm_code = Column(String(20), nullable=False, index=True)
    related_party_name = Column(String(200), nullable=False)
    relationship_type = Column(String(100))
    transaction_type = Column(String(100))
    transaction_amount = Column(Float)
    transaction_description = Column(Text)
    year = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Ponto 9: Eventos Corporativos
class CorporateEvents(db.Model):
    __tablename__ = 'corporate_events'
    
    id = Column(Integer, primary_key=True)
    cvm_code = Column(String(20), nullable=False, index=True)
    event_type = Column(String(100))  # Fusão, Cisão, Incorporação, etc
    event_date = Column(DateTime, nullable=False, index=True)
    announcement_date = Column(DateTime)
    description = Column(Text)
    impact_description = Column(Text)
    financial_impact = Column(Float)
    year = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Ponto 10: Captações de Recursos
class Fundraising(db.Model):
    __tablename__ = 'fundraising'
    
    id = Column(Integer, primary_key=True)
    cvm_code = Column(String(20), nullable=False, index=True)
    instrument_type = Column(String(50))  # Debêntures, CRA, CRI, etc
    issue_date = Column(DateTime, index=True)
    maturity_date = Column(DateTime)
    nominal_amount = Column(Float)
    interest_rate = Column(Float)
    indexation = Column(String(50))
    rating = Column(String(20))
    guarantees = Column(Text)
    year = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Ponto 11: Documentos Regulatórios
class RegulatoryFilings(db.Model):
    __tablename__ = 'regulatory_filings'
    
    id = Column(Integer, primary_key=True)
    cvm_code = Column(String(20), nullable=False, index=True)
    document_type = Column(String(50))  # FORM_REF, FATO_REL, etc
    filing_date = Column(DateTime, nullable=False, index=True)
    document_title = Column(String(500))
    document_url = Column(String(500))
    summary = Column(Text)
    category = Column(String(100))
    year = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Ponto 12: Dados de Mercado
class MarketData(db.Model):
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False, index=True)
    trade_date = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    trades_count = Column(Integer)
    market_cap = Column(Float)
    year = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_market_ticker_date', 'ticker', 'trade_date'),
    )

# Ponto 13: Indicadores Financeiros Calculados
class FinancialIndicators(db.Model):
    __tablename__ = 'financial_indicators'
    
    id = Column(Integer, primary_key=True)
    cvm_code = Column(String(20), nullable=False, index=True)
    ticker = Column(String(10), index=True)
    year = Column(Integer, nullable=False, index=True)
    period = Column(Integer)  # Trimestre
    
    # Liquidez
    current_ratio = Column(Float)
    quick_ratio = Column(Float)
    cash_ratio = Column(Float)
    
    # Rentabilidade
    roe = Column(Float)  # Return on Equity
    roa = Column(Float)  # Return on Assets
    gross_margin = Column(Float)
    operating_margin = Column(Float)
    net_margin = Column(Float)
    
    # Endividamento
    debt_to_equity = Column(Float)
    debt_to_assets = Column(Float)
    interest_coverage = Column(Float)
    
    # Eficiência
    asset_turnover = Column(Float)
    inventory_turnover = Column(Float)
    receivables_turnover = Column(Float)
    
    # Mercado
    pe_ratio = Column(Float)  # P/L
    pb_ratio = Column(Float)  # P/VP
    ev_ebitda = Column(Float)
    dividend_yield = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_indicators_cvm_year', 'cvm_code', 'year'),
    )