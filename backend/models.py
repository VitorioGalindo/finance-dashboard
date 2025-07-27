# backend/models.py (VERSÃO FINAL PÓS-REATORAÇÃO)
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
    reports = relationship("FinancialReport", back_populates="company", cascade="all, delete-orphan")

class Ticker(db.Model):
    __tablename__ = 'tickers'
    id = db.Column(BigInteger, primary_key=True)
    ticker = db.Column(String(10), unique=True, nullable=False)
    company_cnpj = db.Column(String(14), ForeignKey('companies.cnpj'), nullable=False)
    is_active = db.Column(Boolean, default=True)
    company = relationship("Company", backref=db.backref('tickers', lazy=True))

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

class FinancialStatement(db.Model):
    __tablename__ = 'financial_statements'
    id = db.Column(BigInteger, primary_key=True)
    report_id = db.Column(BigInteger, ForeignKey('financial_reports.id'), nullable=False)
    statement_type = db.Column(String(50), nullable=False)
    account_code = db.Column(String(30), nullable=False)
    account_description = db.Column(Text)
    account_value = db.Column(Numeric(20, 2), nullable=False)
    report = relationship("FinancialReport", back_populates="statements")

    def to_dict(self):
        return {
            'account_code': self.account_code,
            'account_description': self.account_description,
            'account_value': float(self.account_value)
        }
