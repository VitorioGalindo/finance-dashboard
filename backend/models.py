# backend/models.py
from .app import db
from sqlalchemy.sql import func
from sqlalchemy import String, Integer, DateTime

class Company(db.Model):
    __tablename__ = 'companies'

    # CORREÇÃO: O tipo da coluna CNPJ foi alterado de Integer para String(14).
    # CNPJs devem ser tratados como strings para não perder os zeros à esquerda,
    # que são parte fundamental do identificador.
    cnpj = db.Column(String(14), primary_key=True)
    
    name = db.Column(String(255), nullable=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        """
        Serializa o objeto Company para um dicionário, o que facilita a conversão para JSON.
        """
        return {
            'cnpj': self.cnpj,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
