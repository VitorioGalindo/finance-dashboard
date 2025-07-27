# backend/models.py (VERSÃO FINAL COM to_dict() RESTAURADO)
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

    def to_dict(self):
        return {
            'id': self.id,
            'ticker': self.ticker,
            'company_cnpj': self.company_cnpj,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
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
    
    company = relationship("Company", backref=db.backref('documents', lazy=True))

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
            'download_link': self.download_link,
        }

class FinancialStatement(db.Model):
    __tablename__ = 'cvm_dados_financeiros'
    id = db.Column(Integer, primary_key=True)
    cnpj_cia = db.Column(String(20), ForeignKey('companies.cnpj'))
    denom_cia = db.Column(Text)
    cd_cvm = db.Column(String(10))
    versao = db.Column(Integer)
    dt_refer = db.Column(Date)
    dt_ini_exerc = db.Column(Date)
    dt_fim_exerc = db.Column(Date)
    cd_conta = db.Column(String(30))
    ds_conta = db.Column(Text)
    vl_conta = db.Column(Numeric(20, 2))
    escala_moeda = db.Column(String(10))
    moeda = db.Column(String(5))
    ordem_exerc = db.Column(String(10))
    tipo_demonstracao = db.Column(String(50))
    periodo = db.Column(String(20))

    def to_dict(self):
        return {
            'id': self.id,
            'cnpj_cia': self.cnpj_cia,
            'denom_cia': self.denom_cia,
            'cd_cvm': self.cd_cvm,
            'versao': self.versao,
            'dt_refer': self.dt_refer.isoformat() if self.dt_refer else None,
            'dt_ini_exerc': self.dt_ini_exerc.isoformat() if self.dt_ini_exerc else None,
            'dt_fim_exerc': self.dt_fim_exerc.isoformat() if self.dt_fim_exerc else None,
            'cd_conta': self.cd_conta,
            'ds_conta': self.ds_conta,
            'vl_conta': float(self.vl_conta) if self.vl_conta is not None else None,
            'escala_moeda': self.escala_moeda,
            'moeda': self.moeda,
            'ordem_exerc': self.ordem_exerc,
            'tipo_demonstracao': self.tipo_demonstracao,
            'periodo': self.periodo,
        }
# ... (outros modelos com seus respectivos métodos to_dict(), se necessário)
