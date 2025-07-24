
from . import db
from sqlalchemy.sql import func
from sqlalchemy import (
    String, Integer, DateTime, Date, Numeric, Text, ForeignKey
)
from sqlalchemy.orm import relationship

class Company(db.Model):
    __tablename__ = 'companies'

    cnpj = db.Column(String(14), primary_key=True)
    name = db.Column(String(255), nullable=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(DateTime(timezone=True), onupdate=func.now())

    statements = relationship("FinancialStatement", back_populates="company", cascade="all, delete-orphan")
    filings = relationship("Filing", back_populates="company", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'cnpj': self.cnpj,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
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

class Filing(db.Model):
    __tablename__ = 'filings'

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
    
    company = relationship("Company", back_populates="filings")

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
