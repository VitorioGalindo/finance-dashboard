# scraper/models.py
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Company(Base):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True)
    cvm_code = Column(Integer, unique=True, nullable=False)
    company_name = Column(String(255), nullable=False)
    trade_name = Column(String(255))
    cnpj = Column(String(20), unique=True)
    founded_date = Column(DateTime)
    main_activity = Column(Text)
    website = Column(String(255))
    controlling_interest = Column(String(100))
    is_state_owned = Column(Boolean, default=False)
    is_foreign = Column(Boolean, default=False)
    is_b3_listed = Column(Boolean, default=False)
    b3_issuer_code = Column(String(10))
    b3_listing_segment = Column(String(50))
    b3_sector = Column(String(100))
    b3_subsector = Column(String(100))
    b3_segment = Column(String(100))
    tickers = Column(JSON)
    ticker = Column(String(10))
    is_active = Column(Boolean, default=True)
    # --- COLUNAS ADICIONADAS DO FRE ---
    activity_description = Column(Text)
    capital_structure_summary = Column(JSON)
    # --- FIM DAS ADIÇÕES ---
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    financial_statements = relationship("FinancialStatement", back_populates="company", cascade="all, delete-orphan")
    capital_events = relationship("CapitalStructure", back_populates="company", cascade="all, delete-orphan")
    shareholders = relationship("Shareholder", back_populates="company", cascade="all, delete-orphan")
    administrators = relationship("CompanyAdministrator", back_populates="company", cascade="all, delete-orphan")
    risk_factors = relationship("CompanyRiskFactor", back_populates="company", cascade="all, delete-orphan")

class FinancialStatement(Base):
    __tablename__ = 'financial_statements'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    cvm_code = Column(Integer, nullable=False, index=True)
    report_type = Column(String(20), nullable=False)
    aggregation = Column(String(20), nullable=False)
    reference_date = Column(DateTime, nullable=False)
    version = Column(Integer, default=1)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    company = relationship("Company", back_populates="financial_statements")

class CapitalStructure(Base):
    __tablename__ = 'capital_structure'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    approval_date = Column(DateTime, nullable=False)
    event_type = Column(String(50), nullable=False)
    value = Column(Float)
    qty_ordinary_shares = Column(Integer)
    qty_preferred_shares = Column(Integer)
    qty_total_shares = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    company = relationship("Company", back_populates="capital_events")

class Shareholder(Base):
    __tablename__ = 'shareholders'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    reference_date = Column(DateTime, nullable=False)
    name = Column(String(255), nullable=False)
    person_type = Column(String(20))
    document = Column(String(20))
    is_controller = Column(Boolean, default=False)
    pct_ordinary_shares = Column(Float)
    pct_preferred_shares = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    company = relationship("Company", back_populates="shareholders")

# --- NOVAS TABELAS ADICIONADAS ---
class CompanyAdministrator(Base):
    """
    Armazena os membros da administração (Conselho, Diretoria, etc).
    Origem: fre_cia_aberta_administrador_membro_*.csv
    """
    __tablename__ = 'company_administrators'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    reference_date = Column(DateTime, nullable=False)
    name = Column(String(255), nullable=False)
    document = Column(String(20)) # CPF
    position = Column(String(100)) # Ex: "Conselho de Administração - Efetivos"
    role = Column(String(100)) # Ex: "Conselheiro(a) de Administração"
    election_date = Column(DateTime)
    term_of_office = Column(String(50))
    professional_background = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    company = relationship("Company", back_populates="administrators")

class CompanyRiskFactor(Base):
    """
    Armazena os fatores de risco reportados pela empresa.
    """
    __tablename__ = 'company_risk_factors'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    reference_date = Column(DateTime, nullable=False)
    risk_type = Column(String(100)) # Ex: "De Mercado", "Operacionais"
    risk_description = Column(Text)
    mitigation_measures = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="risk_factors")

# --- OUTROS MODELOS ---
class Ticker(Base):
    __tablename__ = 'tickers'
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), unique=True, nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
