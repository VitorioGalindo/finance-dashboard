# backend/models.py (VERSÃO COMPLETA E CORRIGIDA)
from backend import db
from sqlalchemy import (
    String, Integer, DateTime, Date, Numeric, Text, ForeignKey, Float, BigInteger, Boolean
)
from sqlalchemy.orm import relationship

class Company(db.Model):
    __tablename__ = 'companies'
    cnpj = db.Column(String(14), primary_key=True)
    name = db.Column(String(255), nullable=False)
    created_at = db.Column(DateTime)
    updated_at = db.Column(DateTime)

    def to_dict(self):
        return { 'cnpj': self.cnpj, 'name': self.name }

class Ticker(db.Model):
    __tablename__ = 'tickers'
    id = db.Column(BigInteger, primary_key=True)
    ticker = db.Column(String(10), unique=True, nullable=False)
    company_cnpj = db.Column(String(14), ForeignKey('companies.cnpj'), nullable=False)
    is_active = db.Column(Boolean)
    
    company = relationship("Company", backref=db.backref('tickers', lazy=True))

    def to_dict(self):
        return {
            'ticker': self.ticker,
            'company_name': self.company.name,
            'company_cnpj': self.company_cnpj
        }

class CvmDocument(db.Model):
    __tablename__ = 'cvm_documents'
    id = db.Column(Integer, primary_key=True)
    company_cnpj = db.Column(String(20), ForeignKey('companies.cnpj'), nullable=False)
    company_name = db.Column(Text)
    delivery_date = db.Column(Date)
    doc_type = db.Column(String(100))
    subject = db.Column(Text)
    download_link = db.Column(Text)

    company = relationship("Company", backref=db.backref('documents', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'company_cnpj': self.company_cnpj,
            'company_name': self.company_name,
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'doc_type': self.doc_type,
            'subject': self.subject,
            'download_link': self.download_link
        }

class FinancialStatement(db.Model):
    __tablename__ = 'financial_statements'
    id = db.Column(BigInteger, primary_key=True)
    report_id = db.Column(BigInteger, ForeignKey('financial_reports.id'), nullable=False)
    statement_type = db.Column(String(50), nullable=False)
    account_code = db.Column(String(30), nullable=False)
    account_description = db.Column(Text)
    account_value = db.Column(Numeric(20, 2), nullable=False)

    def to_dict(self):
        return {
            'account_code': self.account_code,
            'account_description': self.account_description,
            'account_value': float(self.account_value) if self.account_value is not None else None
        }

class FinancialReport(db.Model):
    __tablename__ = 'financial_reports'
    id = db.Column(BigInteger, primary_key=True)
    company_cnpj = db.Column(String(20), ForeignKey('companies.cnpj'), nullable=False)
    year = db.Column(Integer, nullable=False)
    period = db.Column(String(20), nullable=False)
    report_type = db.Column(String(50), nullable=False)
    
    statements = relationship("FinancialStatement", backref="report", cascade="all, delete-orphan")
