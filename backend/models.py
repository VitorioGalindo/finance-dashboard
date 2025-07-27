# backend/models.py (VERSÃO FINAL CORRIGIDA COM BASE NA INSPEÇÃO)
from backend import db
from sqlalchemy import (
    String, Integer, DateTime, Date, Numeric, Text, ForeignKey, Float, BigInteger, Boolean
)
from sqlalchemy.orm import relationship

# --- MODELOS PRINCIPAIS ---

class Company(db.Model):
    __tablename__ = 'companies'
    cnpj = db.Column(String(14), primary_key=True)
    name = db.Column(String(255), nullable=False)
    created_at = db.Column(DateTime)
    updated_at = db.Column(DateTime)

class Ticker(db.Model):
    __tablename__ = 'tickers'
    id = db.Column(BigInteger, primary_key=True)
    ticker = db.Column(String(10), unique=True, nullable=False)
    company_cnpj = db.Column(String(14), ForeignKey('companies.cnpj'), nullable=False)
    is_active = db.Column(Boolean)
    created_at = db.Column(DateTime)
    updated_at = db.Column(DateTime)

# --- MODELOS DE DADOS DA CVM ---

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

class FinancialStatement(db.Model):
    __tablename__ = 'cvm_dados_financeiros'
    id = db.Column(Integer, primary_key=True)
    cnpj_cia = db.Column(String(20), ForeignKey('companies.cnpj')) # Nome correto: cnpj_cia
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

# --- MODELOS DE INSIDERS ---

class Filing(db.Model):
    __tablename__ = 'filings'
    id = db.Column(BigInteger, primary_key=True)
    company_cnpj = db.Column(String(14), ForeignKey('companies.cnpj'), nullable=False)
    reference_date = db.Column(Date, nullable=False)
    cvm_protocol = db.Column(String(50), nullable=False, unique=True)
    pdf_url = db.Column(String)
    processed_at = db.Column(DateTime)

class Insider(db.Model):
    __tablename__ = 'insiders'
    id = db.Column(BigInteger, primary_key=True)
    company_cnpj = db.Column(String(14), ForeignKey('companies.cnpj'), nullable=False)
    name = db.Column(String(255), nullable=False)
    document = db.Column(String(14))
    insider_type = db.Column(String(50), nullable=False)
    created_at = db.Column(DateTime)

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
    price = db.Column(Numeric(20, 6))
    volume = db.Column(Numeric(20, 4))
    intermediary = db.Column(String(255))

# --- MODELOS DE PORTFÓLIO ---

class PortfolioConfig(db.Model):
    __tablename__ = 'portfolio_config'
    id = db.Column(Integer, primary_key=True)
    ticker = db.Column(Text, nullable=False)
    quantidade = db.Column(Integer, nullable=False)
    posicao_alvo = db.Column(Float)

class PortfolioHistory(db.Model):
    __tablename__ = 'portfolio_history'
    id = db.Column(Integer, primary_key=True)
    data = db.Column(Date, nullable=False, unique=True)
    cota = db.Column(Float)
    ibov = db.Column(Float)

class PortfolioMetric(db.Model):
    __tablename__ = 'portfolio_metrics'
    metric_key = db.Column(Text, primary_key=True)
    metric_value = db.Column(Float)

class RealtimeQuote(db.Model):
    __tablename__ = 'realtime_quotes'
    ticker = db.Column(Text, primary_key=True)
    last_price = db.Column(Float)
    previous_close = db.Column(Float)
    updated_at = db.Column(DateTime)

# --- OUTROS MODELOS ---

class Transacao(db.Model): # Note o nome da classe 'Transacao' no singular
    __tablename__ = 'transacoes'
    id = db.Column(Integer, primary_key=True)
    data = db.Column(Date)
    descricao = db.Column(Text)
    categoria = db.Column(Text)
    valor = db.Column(Numeric(15, 2))
    moeda = db.Column(String(10))
    cnpj_companhia = db.Column(String(20), ForeignKey('companies.cnpj')) # Nome correto: cnpj_companhia
    nome_companhia = db.Column(Text)
    data_referencia = db.Column(Date)

# (Opcional: Adicionar relacionamentos entre os modelos para facilitar as consultas)
# Ex: Company.tickers = relationship("Ticker", back_populates="company")
# Ex: Ticker.company = relationship("Company", back_populates="tickers")
