# backend/models.py
from backend import db # Importa a instância db do __init__.py do pacote

class Company(db.Model):
    __tablename__ = 'companies'

    cnpj = db.Column(db.String(14), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    # Relacionamento reverso para acessar os tickers a partir de uma empresa
    # tickers = db.relationship('Ticker', back_populates='company')

    def __repr__(self):
        return f"<Company(cnpj='{self.cnpj}', name='{self.name}')>"

class Ticker(db.Model):
    __tablename__ = 'tickers'

    id = db.Column(db.BigInteger, primary_key=True)
    ticker = db.Column(db.String(10), unique=True, nullable=False)
    company_cnpj = db.Column(db.String(14), db.ForeignKey('companies.cnpj'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    
    # Relacionamento para acessar a empresa a partir de um ticker
    company = db.relationship('Company', backref=db.backref('tickers', lazy='dynamic'))

    def __repr__(self):
        return f"<Ticker(ticker='{self.ticker}')>"

class RealtimeQuote(db.Model):
    __tablename__ = 'realtime_quotes'

    ticker = db.Column(db.Text, db.ForeignKey('tickers.ticker'), primary_key=True)
    last_price = db.Column(db.Float)
    previous_close = db.Column(db.Float)
    updated_at = db.Column(db.DateTime, default=db.func.now())

    # Relacionamento para acessar as informações completas do ticker
    ticker_info = db.relationship('Ticker', backref=db.backref('realtime_quote', uselist=False))

    def __repr__(self):
        return f"<RealtimeQuote(ticker='{self.ticker}', last_price={self.last_price})>"
