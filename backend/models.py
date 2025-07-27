# backend/models.py (VERSÃO REATORADA FINAL)
from backend import db
from sqlalchemy import (
    String, Integer, DateTime, Date, Numeric, Text, ForeignKey, Float, BigInteger, Boolean
)
from sqlalchemy.orm import relationship

# --- GRUPO 1: DADOS CENTRAIS ---

class Company(db.Model):
    __tablename__ = 'companies'
    cnpj = db.Column(String(14), primary_key=True)
    name = db.Column(String(255), nullable=False)
    created_at = db.Column(DateTime)
    updated_at = db.Column(DateTime)
    # Futuramente: sector, subsector, segment

    # Relacionamentos
    tickers = relationship("Ticker", back_populates="company")
    reports = relationship("FinancialReport", back_populates="company")

class Ticker(db.Model):
    __tablename__ = 'tickers'
    id = db.Column(BigInteger, primary_key=True)
    ticker = db.Column(String(10), unique=True, nullable=False)
    company_cnpj = db.Column(String(14), ForeignKey('companies.cnpj'), nullable=False)
    is_active = db.Column(Boolean, default=True)
    
    company = relationship("Company", back_populates="tickers")

# --- GRUPO 2: RELATÓRIOS FINANCEIROS (ESTRUTURA OTIMIZADA) ---

class FinancialReport(db.Model):
    __tablename__ = 'financial_reports'
    id = db.Column(BigInteger, primary_key=True)
    company_cnpj = db.Column(String(20), ForeignKey('companies.cnpj'), nullable=False)
    year = db.Column(Integer, nullable=False)
    period = db.Column(String(20), nullable=False)
    report_type = db.Column(String(50), nullable=False)
    
    company = relationship("Company", back_populates="reports")
    statements = relationship("FinancialStatement", back_populates="report", cascade="all, delete-orphan")
    ratios = relationship("CompanyFinancialRatio", back_populates="report", cascade="all, delete-orphan")

class FinancialStatement(db.Model):
    __tablename__ = 'financial_statements'
    id = db.Column(BigInteger, primary_key=True)
    report_id = db.Column(BigInteger, ForeignKey('financial_reports.id'), nullable=False)
    statement_type = db.Column(String(50), nullable=False)
    account_code = db.Column(String(30), nullable=False)
    account_description = db.Column(Text)
    account_value = db.Column(Numeric(20, 2), nullable=False)

    report = relationship("FinancialReport", back_populates="statements")

# --- GRUPO 3: DADOS CALCULADOS (PARA PERFORMANCE) ---

class CompanyFinancialRatio(db.Model):
    __tablename__ = 'company_financial_ratios'
    id = db.Column(BigInteger, primary_key=True)
    report_id = db.Column(BigInteger, ForeignKey('financial_reports.id'), nullable=False)
    ratio_name = db.Column(String(50), nullable=False)
    ratio_value = db.Column(Numeric(20, 4), nullable=False)
    
    report = relationship("FinancialReport", back_populates="ratios")

# --- GRUPO 4: CVM, INSIDERS E NOTÍCIAS ---

class CvmDocument(db.Model):
    __tablename__ = 'cvm_documents'
    id = db.Column(Integer, primary_key=True)
    company_cnpj = db.Column(String(20), ForeignKey('companies.cnpj'), nullable=False)
    # ... (outras colunas como estavam)

# (Modelos para Insiders, Filings, InsiderTransactions permanecem os mesmos)

class InsiderTransaction(db.Model):
    __tablename__ = 'insider_transactions'
    id = db.Column(BigInteger, primary_key=True)
    # ... (resto das colunas)
