# scraper/models.py (CORRIGIDO)
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
)
# CORREÇÃO: Importa 'db' do novo arquivo 'extensions.py'
from extensions import db

# (O resto do arquivo models.py permanece o mesmo, mas agora ele
# depende de 'extensions.py', que não tem dependências circulares)

class Company(db.Model):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True)
    cvm_code = Column(Integer, unique=True, nullable=False)
    # ... e todas as outras colunas e modelos que você já tem
    company_name = Column(String(255), nullable=False)
    trade_name = Column(String(255))
    cnpj = Column(String(20), unique=True)
    # ... (etc) ...

class ApiKey(db.Model):
    __tablename__ = 'api_keys'
    id = Column(Integer, primary_key=True)
    key_hash = Column(String(255), unique=True, nullable=False)
    user_email = Column(String(255))
    plan = Column(String(50), default='basic')
    requests_per_hour = Column(Integer, default=1000)
    requests_used = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)

# Inclua AQUI todas as outras classes de modelo que estão no seu arquivo original
# (Quote, News, InsiderTransaction, FinancialRatio, etc.)
# ...
class Quote(db.Model):
    __tablename__ = 'quotes'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False, index=True)
    # ...
    
# Adicione todas as outras classes aqui
