
from . import db
from sqlalchemy.sql import func
from sqlalchemy import (
    String, Integer, DateTime, Date, Numeric, Text, ForeignKey, Float, BigInteger, Boolean
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
    # Novas Relações para Insiders
    insiders = relationship("Insider", back_populates="company", cascade="all, delete-orphan")
    filings = relationship("Filing", back_populates="company", cascade="all, delete-orphan")


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
    __tablename__ = 'cvm_documentos_ipe'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    cnpj_companhia = db.Column('cnpj_companhia', String(20), ForeignKey('companies.cnpj'))
    nome_companhia = db.Column(Text)
    codigo_cvm = db.Column(String(10))
    categoria = db.Column(String(100))
    tipo = db.Column(String(100))
    especie = db.Column(String(100))
    assunto = db.Column(Text)
    data_referencia = db.Column(Date)
    data_entrega = db.Column(Date)
    protocolo_entrega = db.Column(String(30))
    link_download = db.Column(Text)
    
    company = relationship("Company", back_populates="documents")

    def to_dict(self):
        return {
            'id': self.id,
            'company_cnpj': self.cnpj_companhia,
            'company_name': self.nome_companhia,
            'cvm_code': self.codigo_cvm,
            'category': self.categoria,
            'doc_type': self.tipo,
            'species': self.especie,
            'subject': self.assunto,
            'reference_date': self.data_referencia.isoformat() if self.data_referencia else None,
            'delivery_date': self.data_entrega.isoformat() if self.data_entrega else None,
            'delivery_protocol': self.protocolo_entrega,
            'download_link': self.link_download
        }

class PortfolioConfig(db.Model):
    __tablename__ = 'portfolio_config'
    
    id = db.Column(Integer, primary_key=True)
    ticker = db.Column(String(10), nullable=False)
    quantidade = db.Column(Integer, nullable=False)
    posicao_alvo = db.Column(Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'ticker': self.ticker,
            'quantity': self.quantidade,
            'target_weight': self.posicao_alvo,
        }

class PortfolioHistory(db.Model):
    __tablename__ = 'portfolio_history'

    id = db.Column(Integer, primary_key=True)
    data = db.Column(Date, nullable=False, default=func.current_date())
    cota = db.Column(Float)
    ibov = db.Column(Float)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.data.isoformat() if self.data else None,
            'cota': self.cota,
            'ibov': self.ibov,
        }

class PortfolioMetric(db.Model):
    __tablename__ = 'portfolio_metrics'

    metric_key = db.Column(Text, primary_key=True)
    metric_value = db.Column(Float)
    
    def to_dict(self):
        return {
            'metric_key': self.metric_key,
            'metric_value': self.metric_value,
        }

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

# --- NOVOS MODELOS PARA RADAR DE INSIDERS ---

class Filing(db.Model):
    __tablename__ = 'filings'

    id = db.Column(BigInteger, primary_key=True)
    company_cnpj = db.Column(String(14), ForeignKey('companies.cnpj'), nullable=False)
    reference_date = db.Column(Date, nullable=False)
    cvm_protocol = db.Column(String(50), nullable=False, unique=True)
    pdf_url = db.Column(String)
    processed_at = db.Column(DateTime(timezone=True), onupdate=func.now())
    
    company = relationship("Company", back_populates="filings")
    transactions = relationship("Transaction", back_populates="filing", cascade="all, delete-orphan")


class Insider(db.Model):
    __tablename__ = 'insiders'

    id = db.Column(BigInteger, primary_key=True)
    company_cnpj = db.Column(String(14), ForeignKey('companies.cnpj'), nullable=False)
    name = db.Column(String(255), nullable=False)
    document = db.Column(String(14))
    insider_type = db.Column(String(50), nullable=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    
    company = relationship("Company", back_populates="insiders")
    transactions = relationship("Transaction", back_populates="insider", cascade="all, delete-orphan")


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(BigInteger, primary_key=True)
    filing_id = db.Column(BigInteger, ForeignKey('filings.id'), nullable=False)
    insider_id = db.Column(BigInteger, ForeignKey('insiders.id'), nullable=False)
    transaction_date = db.Column(Date, nullable=False)
    asset_type = db.Column(String(100))
    asset_class = db.Column(String(50))
    operation_type = db.Column(String(100))
    quantity = db.Column(BigInteger, nullable=False)
    price = db.Column(Numeric(20, 6), nullable=True)
    volume = db.Column(Numeric(20, 4), nullable=True)
    intermediary = db.Column(String(255), nullable=True)

    filing = relationship("Filing", back_populates="transactions")
    insider = relationship("Insider", back_populates="transactions")
