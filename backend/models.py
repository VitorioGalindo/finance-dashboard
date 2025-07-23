# backend/models.py
from .app import db # Importa a instância do SQLAlchemy criada em app.py

# Exemplo de modelo para a tabela 'companies'
class Company(db.Model):
    __tablename__ = 'companies' # Nome da tabela no banco de dados

    cnpj = db.Column(db.String(14), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    # Opcional: representação em string para debugging
    def __repr__(self):
        return f"<Company(cnpj='{self.cnpj}', name='{self.name}')>"

# Exemplo de modelo para a tabela 'tickers'
class Ticker(db.Model):
    __tablename__ = 'tickers' # Nome da tabela no banco de dados

    id = db.Column(db.BigInteger, primary_key=True)
    ticker = db.Column(db.String(10), unique=True, nullable=False)
    company_cnpj = db.Column(db.String(14), db.ForeignKey('companies.cnpj'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    # Define o relacionamento com a tabela Company
    # Isso permite acessar a empresa associada a um ticker: ticker_obj.company
    company = db.relationship('Company', backref=db.backref('tickers', lazy=True))

    def __repr__(self):
        return f"<Ticker(ticker='{self.ticker}', company_cnpj='{self.company_cnpj}')>"

# Exemplo de modelo para a tabela 'realtime_quotes'
class RealtimeQuote(db.Model):
    __tablename__ = 'realtime_quotes' # Nome da tabela no banco de dados

    # A chave primária é 'ticker' (texto) nesta tabela
    ticker = db.Column(db.Text, primary_key=True)
    last_price = db.Column(db.Float)
    previous_close = db.Column(db.Float)
    updated_at = db.Column(db.DateTime, default=db.func.now()) # Mapeia para o default/trigger do BD

    # Define o relacionamento com a tabela Ticker
    # Isso permite acessar o objeto Ticker associado a uma cotação: quote_obj.ticker_info
    # Usamos remote_side para referenciar a coluna 'ticker' na tabela 'tickers'
    ticker_info = db.relationship('Ticker', foreign_keys=[ticker], remote_side='Ticker.ticker', backref=db.backref('realtime_quote', uselist=False, lazy=True))


    def __repr__(self):
        return f"<RealtimeQuote(ticker='{self.ticker}', last_price={self.last_price})>"

# Adicionar outros modelos aqui conforme necessário
# class CvmFinancialData(db.Model): ...
# class InsiderTransaction(db.Model): ...
# etc.
