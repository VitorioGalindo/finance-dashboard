# core/models.py (CORRIGIDO)
from sqlalchemy import (Column, String, BigInteger, Date,
                        ForeignKey, TIMESTAMP, NUMERIC, Boolean)
from sqlalchemy.orm import relationship, declarative_base
import datetime

Base = declarative_base()

class Company(Base):
    __tablename__ = 'companies'
    cnpj = Column(String(14), primary_key=True)
    name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Insider(Base):
    __tablename__ = 'insiders'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_cnpj = Column(String(14), ForeignKey('companies.cnpj'), nullable=False)
    name = Column(String(255), nullable=False)
    document = Column(String(14))
    insider_type = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow)
    company = relationship("Company")

class Filing(Base):
    __tablename__ = 'filings'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_cnpj = Column(String(14), ForeignKey('companies.cnpj'), nullable=False)
    reference_date = Column(Date, nullable=False)
    cvm_protocol = Column(String(50), nullable=False, unique=True)
    pdf_url = Column(String)
    processed_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow)
    company = relationship("Company")

class Transaction(Base):
    __tablename__ = 'insider_transactions' # <-- CORREÇÃO APLICADA AQUI
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    filing_id = Column(BigInteger, ForeignKey('filings.id'), nullable=False)
    insider_id = Column(BigInteger, ForeignKey('insiders.id'), nullable=False)
    transaction_date = Column(Date, nullable=False)
    asset_type = Column(String(100))
    asset_class = Column(String(50))
    operation_type = Column(String(100))
    quantity = Column(BigInteger, nullable=False)
    price = Column(NUMERIC(20, 6), nullable=True)
    volume = Column(NUMERIC(20, 4), nullable=True)
    intermediary = Column(String(255), nullable=True)
    filing = relationship("Filing")
    insider = relationship("Insider")
