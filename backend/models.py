# backend/models.py (Arquivo completo para consistência)
from backend import db
from sqlalchemy import (
    String, Integer, DateTime, Date, Numeric, Text, ForeignKey, Float, BigInteger, Boolean
)
from sqlalchemy.orm import relationship

# ... (Código das classes Company e Ticker) ...

class Company(db.Model):
    __tablename__ = 'companies'
    cnpj = db.Column(String(14), primary_key=True)
    name = db.Column(String(255), nullable=False)
    created_at = db.Column(DateTime)
    updated_at = db.Column(DateTime)

    def to_dict(self):
        return {
            'cnpj': self.cnpj,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

class Ticker(db.Model):
    __tablename__ = 'tickers'
    id = db.Column(BigInteger, primary_key=True)
    ticker = db.Column(String(10), unique=True, nullable=False)
    company_cnpj = db.Column(String(14), ForeignKey('companies.cnpj'), nullable=False)
    is_active = db.Column(Boolean)
    created_at = db.Column(DateTime)
    updated_at = db.Column(DateTime)
    
    company = relationship("Company", backref=db.backref('tickers', lazy=True))

    def to_dict(self):
        # ...
        pass

class CvmDocument(db.Model):
    __tablename__ = 'cvm_documents'
    id = db.Column(Integer, primary_key=True)
    company_cnpj = db.Column(String(20), ForeignKey('companies.cnpj'), nullable=False)
    company_name = db.Column(Text)
    # ... (outras colunas) ...
    
    company = relationship("Company", backref=db.backref('documents', lazy=True))

    def to_dict(self):
        # ...
        pass

class FinancialStatement(db.Model):
    __tablename__ = 'financial_statements' # Nome padronizado
    id = db.Column(Integer, primary_key=True)
    company_cnpj = db.Column(String(20), ForeignKey('companies.cnpj'))
    company_name = db.Column(Text)
    cvm_code = db.Column(String(10))
    report_version = db.Column(Integer)
    reference_date = db.Column(Date)
    fiscal_year_start = db.Column(Date)
    fiscal_year_end = db.Column(Date)
    account_code = db.Column(String(30))
    account_description = db.Column(Text)
    account_value = db.Column(Numeric(20, 2))
    currency_scale = db.Column(String(10))
    currency = db.Column(String(5))
    fiscal_year_order = db.Column(String(10))
    report_type = db.Column(String(50))
    period = db.Column(String(20))

    company = relationship("Company", backref=db.backref('financial_statements', lazy=True))

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
# ... (outros modelos) ...
