# backend/models.py
# CORREÇÃO: Importa o 'db' do ponto centralizado em __init__.py
from . import db
from sqlalchemy.sql import func
from sqlalchemy import (
    String, Integer, DateTime, Float, ForeignKey, Date, Numeric, Text
)
from sqlalchemy.orm import relationship

class Company(db.Model):
    __tablename__ = 'companies'

    cnpj = db.Column(String(14), primary_key=True)
    name = db.Column(String(255), nullable=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(DateTime(timezone=True), onupdate=func.now())

    statements = relationship(
        "FinancialStatement", 
        back_populates="company", 
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            'cnpj': self.cnpj,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class FinancialStatement(db.Model):
    __tablename__ = 'cvm_dados_financeiros'

    id = db.Column(Integer, primary_key=True)
    company_cnpj = db.Column('cnpj_cia', String(20), ForeignKey('companies.cnpj'), nullable=False)
    company_name = db.Column('denom_cia', Text)
    cvm_code = db.Column('cd_cvm', String(10))
    report_version = db.Column('versao', Integer)
    reference_date = db.Column('dt_refer', Date)
    fiscal_year_start = db.Column('dt_ini_exerc', Date)
    fiscal_year_end = db.Column('dt_fim_exerc', Date)
    account_code = db.Column('cd_conta', String(30))
    account_description = db.Column('ds_conta', Text)
    account_value = db.Column('vl_conta', Numeric)
    currency_scale = db.Column('escala_moeda', String(10))
    currency = db.Column('moeda', String(5))
    fiscal_year_order = db.Column('ordem_exerc', String(10))
    report_type = db.Column('tipo_demonstracao', String(50))
    # CORREÇÃO DE BUG: O campo 'periodo' estava sendo preenchido com a moeda.
    # Corrigido para ser mapeado para a coluna correta no banco.
    period = db.Column('periodo', String(20))

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
            'periodo': self.period
        }
