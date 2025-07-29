# backend/models.py (VERSÃO FINAL ALINHADA COM O ESQUEMA DO SCRAPER)
from backend import db
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime

# Baseado em scraper/models.py, mas integrado à nossa aplicação

class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(Integer, primary_key=True)
    cvm_code = db.Column(Integer, nullable=False)
    company_name = db.Column(String(255), nullable=False)
    trade_name = db.Column(String(255))
    cnpj = db.Column(String(20))
    founded_date = db.Column(DateTime)
    main_activity = db.Column(Text)
    website = db.Column(String(255))
    controlling_interest = db.Column(String(255))
    is_state_owned = db.Column(Boolean)
    is_foreign = db.Column(Boolean)
    is_b3_listed = db.Column(Boolean)
    b3_issuer_code = db.Column(String(50))
    b3_listing_segment = db.Column(String(100))
    b3_sector = db.Column(String(100))
    b3_subsector = db.Column(String(100))
    b3_segment = db.Column(String(100))
    tickers = db.Column(JSON)
    ticker = db.Column(String(10))
    is_active = db.Column(Boolean)
    industry_classification = db.Column(String(255))
    market_cap = db.Column(Float)
    employee_count = db.Column(Integer)
    about = db.Column(Text)
    has_dfp_data = db.Column(Boolean)
    has_itr_data = db.Column(Boolean)
    has_fre_data = db.Column(Boolean)
    last_dfp_year = db.Column(Integer)
    last_itr_quarter = db.Column(String(10))
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow)
    activity_description = db.Column(Text)
    capital_structure_summary = db.Column(JSON)
    
    def to_dict(self):
        return {
            'id': self.id,
            'cvm_code': self.cvm_code,
            'company_name': self.company_name,
            'trade_name': self.trade_name,
            'cnpj': self.cnpj,
            'founded_date': self.founded_date.isoformat() if self.founded_date else None,
            'main_activity': self.main_activity,
            'website': self.website,
            'controlling_interest': self.controlling_interest,
            'is_state_owned': self.is_state_owned,
            'is_foreign': self.is_foreign,
            'is_b3_listed': self.is_b3_listed,
            'b3_issuer_code': self.b3_issuer_code,
            'b3_listing_segment': self.b3_listing_segment,
            'b3_sector': self.b3_sector,
            'b3_subsector': self.b3_subsector,
            'b3_segment': self.b3_segment,
            'tickers': self.tickers,
            'ticker': self.ticker,
            'is_active': self.is_active,
            'industry_classification': self.industry_classification,
            'market_cap': self.market_cap,
            'employee_count': self.employee_count,
            'about': self.about,
            'has_dfp_data': self.has_dfp_data,
            'has_itr_data': self.has_itr_data,
            'has_fre_data': self.has_fre_data,
            'last_dfp_year': self.last_dfp_year,
            'last_itr_quarter': self.last_itr_quarter,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'activity_description': self.activity_description,
            'capital_structure_summary': self.capital_structure_summary
        }

class Ticker(db.Model):
    __tablename__ = 'tickers'
    id = db.Column(Integer, primary_key=True)
    symbol = db.Column(String(10), unique=True, nullable=False)
    company_id = db.Column(Integer, ForeignKey('companies.id'))
    type = db.Column(String(20))
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'company_id': self.company_id,
            'type': self.type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CVMFinancialData(db.Model):
    __tablename__ = 'cvm_financial_data'
    id = db.Column(Integer, primary_key=True)
    company_id = db.Column(Integer, ForeignKey('companies.id'), nullable=False)
    cvm_code = db.Column(Integer, nullable=False, index=True)
    statement_type = db.Column(String(10), nullable=False)
    year = db.Column(Integer, nullable=False)
    quarter = db.Column(String(10))
    revenue = db.Column(Float)
    net_income = db.Column(Float)
    total_assets = db.Column(Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'cvm_code': self.cvm_code,
            'statement_type': self.statement_type,
            'year': self.year,
            'quarter': self.quarter,
            'revenue': self.revenue,
            'net_income': self.net_income,
            'total_assets': self.total_assets
        }

class CvmDocument(db.Model):
    __tablename__ = 'cvm_documents'
    id = db.Column(Integer, primary_key=True)
    company_id = db.Column(Integer, ForeignKey('companies.id'), nullable=False)
    document_type = db.Column(String(50))
    reference_date = db.Column(DateTime)
    file_url = db.Column(String(500))
    processed = db.Column(Boolean, default=False)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    company_cnpj = db.Column(String(20))  # Para compatibilidade com rotas existentes
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'document_type': self.document_type,
            'reference_date': self.reference_date.isoformat() if self.reference_date else None,
            'file_url': self.file_url,
            'processed': self.processed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'company_cnpj': self.company_cnpj
        }

class MarketData(db.Model):
    __tablename__ = 'market_data'
    id = db.Column(Integer, primary_key=True)
    ticker = db.Column(String(10), nullable=False)
    date = db.Column(DateTime, nullable=False)
    open_price = db.Column(Float)
    high_price = db.Column(Float)
    low_price = db.Column(Float)
    close_price = db.Column(Float, nullable=False)
    volume = db.Column(Integer)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'ticker': self.ticker,
            'date': self.date.isoformat() if self.date else None,
            'open_price': self.open_price,
            'high_price': self.high_price,
            'low_price': self.low_price,
            'close_price': self.close_price,
            'volume': self.volume,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Shareholders(db.Model):
    __tablename__ = 'shareholders'
    id = db.Column(Integer, primary_key=True)
    company_id = db.Column(Integer, ForeignKey('companies.id'), nullable=False)
    reference_date = db.Column(DateTime, nullable=False)
    name = db.Column(String(255), nullable=False)
    person_type = db.Column(String(20))
    document = db.Column(String(20))
    is_controller = db.Column(Boolean)
    pct_ordinary_shares = db.Column(Float)
    pct_preferred_shares = db.Column(Float)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'reference_date': self.reference_date.isoformat() if self.reference_date else None,
            'name': self.name,
            'person_type': self.person_type,
            'document': self.document,
            'is_controller': self.is_controller,
            'pct_ordinary_shares': self.pct_ordinary_shares,
            'pct_preferred_shares': self.pct_preferred_shares,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
