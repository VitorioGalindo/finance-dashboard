# backend/models.py
from .. import db # <-- Importa a instância db de __init__.py no nível acima

# Remova ou comente a linha db = SQLAlchemy() se você a adicionou temporariamente
# db = SQLAlchemy() # <-- REMOVER ou COMENTAR esta linha se você a adicionou temporariamente

# ... definições dos modelos ...


# Vamos usar a instância db de app, mas a importação precisa ser feita
# de forma que não cause o ciclo. A forma padrão é importar 'db' de
# sua_aplicacao.extensions (onde Flask-SQLAlchemy a colocaria),
# ou, de forma mais simples, garantir a ordem de importação/inicialização.

# O problema é que models.py importa db de app.py,
# e app.py importa routes que importa models.

# Solução comum: importar db de flask_sqlalchemy e passá-la para a função create_app
# ou inicializá-la de forma diferente.

# Alternativa mais simples para a estrutura atual: importar db APENAS quando usada,
# ou usar uma abordagem diferente de organização.

# Vamos tentar a abordagem padrão de Flask-SQLAlchemy onde db é importado
# no nível superior, mas a estrutura de importação evita o ciclo.
# O ciclo acontece porque app importa routes que importa models que importa app.

# A estrutura recomendada para Flask-SQLAlchemy é:
# project/
# ├── __init__.py  (Cria a instância db aqui, mas sem inicializá-la com app)
# ├── app.py       (Cria a app, inicializa db com app)
# ├── models.py    (Importa db de project)
# └── routes.py    (Importa db e models de project)

# Na sua estrutura atual, com 'backend' como pacote:
# backend/
# ├── __init__.py  (Vazio ou com db = SQLAlchemy())
# ├── app.py       (Cria app, db.init_app(app), importa blueprints)
# ├── models.py    (Importa db de backend)
# └── routes/      (Importa db e models de backend)

# O erro sugere que a importação de 'db' de .app em models.py está acontecendo
# cedo demais.

# Vamos tentar importar db APÓS a definição dos modelos, se necessário,
# ou confiar que a instância db está disponível no contexto.

# Remova a importação de .app aqui por enquanto:
# from .app import db # <-- REMOVER OU COMENTAR ESTA LINHA

# Defina a instância db temporariamente para as definições de modelo
# Esta não é a instância real conectada, apenas para que as definições funcionem
db = SQLAlchemy() # <-- IMPORTAR SQLAlchemy e criar uma instância TEMPORÁRIA aqui

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
    # backref='tickers' cria uma propriedade 'tickers' na classe Company
    company = db.relationship('Company', backref=db.backref('tickers', lazy=True))

    def __repr__(self):
        return f"<Ticker(ticker='{self.ticker}', company_cnpj='{self.company_cnpj}')>"

# Exemplo de modelo para a tabela 'realtime_quotes'
class RealtimeQuote(db.Model):
    __tablename__ = 'realtime_quotes' # Nome da tabela no banco de dados

    ticker = db.Column(db.Text, primary_key=True)
    last_price = db.Column(db.Float)
    previous_close = db.Column(db.Float)
    updated_at = db.Column(db.DateTime, default=db.func.now())

    # Relacionamento com a tabela Ticker
    # foreign_keys aponta para a coluna LOCAL que é a chave estrangeira
    # remote_side aponta para a coluna na TABELA REFERENCIADA ('Ticker')
    # backref cria uma propriedade 'realtime_quote' na classe Ticker
    ticker_info = db.relationship('Ticker', foreign_keys=[ticker], remote_side='Ticker.ticker', backref=db.backref('realtime_quote', uselist=False, lazy=True))


    def __repr__(self):
        return f"<RealtimeQuote(ticker='{self.ticker}', last_price={self.last_price})>"

# Adicionar outros modelos aqui conforme necessário
# class CvmFinancialData(db.Model): ...
# class InsiderTransaction(db.Model): ...
# etc.

# Importe a instância 'db' REAL de .app APÓS a definição dos modelos,
# ou confie que ela será disponibilizada no contexto da aplicação
# (que é como Flask-SQLAlchemy funciona geralmente).
# Vamos deixar a importação real em routes.py, e models.py apenas define as classes.

# Remover a instância db temporária se você for importar a real em routes.py
# ou se a instância real for injetada no contexto.
# O erro sugere que models.py está causando o ciclo ao importar de .app.

# A forma mais limpa é ter a instância db criada em __init__.py e importá-la em models.py
# Vamos ajustar __init__.py e models.py para isso.
