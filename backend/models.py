
from . import db
from sqlalchemy.sql import func
from sqlalchemy import (
    String, Integer, DateTime, Date, Numeric, Text, ForeignKey, Float
)
from sqlalchemy.orm import relationship

class Company(db.Model):
    __tablename__ = 'companies'

    cnpj = db.Column(String(14), primary_key=True)
    name = db.Column(String(255), nullable=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(DateTime(timezone=True), onupdate=func.now())

    statements = relationship("FinancialStatement", back_populates="company", cascade="all, delete-orphan")
    documents = relationship("CvmDocument", back_populates="company", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'cnpj': self.cnpj,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
class Ticker(db.Model):
    __tablename__ = 'tickers'

    ticker = db.Column(String(10), primary_key=True)
    company_cnpj = db.Column(String(14), ForeignKey('companies.cnpj'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(DateTime(timezone=True), onupdate=func.now())

    company = relationship("Company")

    def to_dict(self):
        return {
            'ticker': self.ticker,
            'company_cnpj': self.company_cnpj,
            'is_active': self.is_active
        }

class FinancialStatement(db.Model):
    __tablename__ = 'cvm_dados_financeiros'

    id = db.Column(Integer, primary_key=True)
    company_cnpj = db.Column(String(20), ForeignKey('companies.cnpj'), nullable=False)
    company_name = db.Column(Text)
    cvm_code = db.Column(String(10))
    report_version = db.Column(Integer)
    reference_date = db.Column(Date)
    fiscal_year_start = db.Column(Date)
    fiscal_year_end = db.Column(Date)
    account_code = db.Column(String(30))
    account_description = db.Column(Text)
    account_value = db.Column(Numeric)
    currency_scale = db.Column(String(10))
    currency = db.Column(String(5))
    fiscal_year_order = db.Column(String(10))
    report_type = db.Column(String(50))
    period = db.Column(String(20))

    company = relationship("Company", back_populates="statements")

    def to_dict(self):
        return {
            'id': self.id,
            'company_cnpj': self.company_cnpj,
            'company_name': self.company_name,
            'cvm_code': self.cvm_code,
            'report_version': self.report_version,
            'reference_date': self.reference_date.isoformat() if self.reference_date else None,
            'fiscal_year_start': self.fiscal_year_start.isoformat() if self.fiscal_year_start else None,
            'fiscal_year_end': self.fiscal_year_end.isoformat() if self.fiscal_year_end else None,
            'account_code': self.account_code,
            'account_description': self.account_description,
            'account_value': float(self.account_value) if self.account_value is not None else None,
            'currency_scale': self.currency_scale,
            'currency': self.currency,
            'fiscal_year_order': self.fiscal_year_order,
            'report_type': self.report_type,
            'period': self.period
        }

class CvmDocument(db.Model):
    __tablename__ = 'cvm_documents'

    id = db.Column(Integer, primary_key=True)
    company_cnpj = db.Column(String(20), ForeignKey('companies.cnpj'), nullable=False)
    company_name = db.Column(Text)
    cvm_code = db.Column(String(10))
    category = db.Column(String(100))
    doc_type = db.Column(String(100))
    species = db.Column(String(100))
    subject = db.Column(Text)
    reference_date = db.Column(Date)
    delivery_date = db.Column(Date)
    delivery_protocol = db.Column(String(50))
    download_link = db.Column(Text)
    
    company = relationship("Company", back_populates="documents")

    def to_dict(self):
        return {
            'id': self.id,
            'company_cnpj': self.company_cnpj,
            'company_name': self.company_name,
            'cvm_code': self.cvm_code,
            'category': self.category,
            'doc_type': self.doc_type,
            'species': self.species,
            'subject': self.subject,
            'reference_date': self.reference_date.isoformat() if self.reference_date else None,
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'delivery_protocol': self.delivery_protocol,
            'download_link': self.download_link
        }

# --- NOVOS MODELOS DE PORTFÓLIO ---

class PortfolioConfig(db.Model):
    __tablename__ = 'portfolio_config'
    
    id = db.Column(Integer, primary_key=True)
    ticker = db.Column(String(10), nullable=False)
    quantity = db.Column(Integer, nullable=False)
    target_weight = db.Column(Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'ticker': self.ticker,
            'quantity': self.quantity,
            'target_weight': self.target_weight,
        }

class PortfolioHistory(db.Model):
    __tablename__ = 'portfolio_history'

    id = db.Column(Integer, primary_key=True)
    date = db.Column(Date, nullable=False, default=func.current_date())
    net_liquidity = db.Column(Float)
    quote_value = db.Column(Float)
    daily_change = db.Column(Float)
    buy_position = db.Column(Float)
    sell_position = db.Column(Float)
    net_long = db.Column(Float)
    exposure = db.Column(Float)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'net_liquidity': self.net_liquidity,
            'quote_value': self.quote_value,
            'daily_change': self.daily_change,
            'buy_position': self.buy_position,
            'sell_position': self.sell_position,
            'net_long': self.net_long,
            'exposure': self.exposure,
        }

class PortfolioMetric(db.Model):
    __tablename__ = 'portfolio_metrics'

    id = db.Column(Integer, primary_key=True)
    metric_name = db.Column(String(100), nullable=False)
    metric_value = db.Column(Float, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
        }
# Em backend/models.py, adicione esta classe ao final do arquivo

class RealtimeQuote(db.Model):
    __tablename__ = 'realtime_quotes'

    ticker = db.Column(String(10), primary_key=True)
    last_price = db.Column(Float)
    previous_close = db.Column(Float)
    updated_at = db.Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            'ticker': self.ticker,
            'last_price': self.last_price,
            'previous_close': self.previous_close,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }