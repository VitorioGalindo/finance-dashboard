# core/database.py
from sqlalchemy.orm import sessionmaker
# Importa a engine centralizada do nosso novo módulo
from backend.database import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
