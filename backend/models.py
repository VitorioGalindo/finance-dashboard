# backend/models.py (VERSÃO FINAL ALINHADA COM O ESQUEMA DO SCRAPER)
from backend import db
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
)
from sqlalchemy.orm import relationship

# Baseado em scraper/models.py, mas integrado à nossa aplicação

class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(Integer, primary_key=True)
    cvm_code = db.Column(Integer, unique=True, nullable=False)
    company_name = db.Column(String(255), nullable=False)
    # Adicione mais campos conforme necessário...

class Ticker(db.Model):
    __tablename__ = 'tickers'
    id = db.Column(Integer, primary_key=True)
    symbol = db.Column(String(10), unique=True, nullable=False)
    company_id = db.Column(Integer, ForeignKey('companies.id'))

class CVMFinancialData(db.Model):
    __tablename__ = 'cvm_financial_data'
    id = db.Column(Integer, primary_key=True)
    company_id = db.Column(Integer, ForeignKey('companies.id'), nullable=False)
    cvm_code = db.Column(Integer, nullable=False, index=True)
    statement_type = db.Column(String(10), nullable=False)
    year = db.Column(Integer, nullable=False)
    quarter = db.Column(String(10))
    revenue = db.Column(Float)
    net_income = db.Column(Float)
    total_assets = db.Column(Float)
    # ... (outros campos pivotados)

# (Adicione outras classes de modelo do scraper/models.py conforme necessário para os endpoints)
