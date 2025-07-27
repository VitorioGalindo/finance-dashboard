# backend/models.py (Arquivo completo para consistência)
from backend import db
from sqlalchemy.sql import func
from sqlalchemy import (
    String, Integer, DateTime, Date, Numeric, Text, ForeignKey, Float, BigInteger, Boolean
)
from sqlalchemy.orm import relationship

class Company(db.Model):
    __tablename__ = 'companies'
    cnpj = db.Column(String(14), primary_key=True)
    name = db.Column(String(255), nullable=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(DateTime(timezone=True), onupdate=func.now())
    documents = relationship("CvmDocument", back_populates="company", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'cnpj': self.cnpj,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

class CvmDocument(db.Model):
    __tablename__ = 'cvm_documents' # Nome correto da tabela

    # Mapeamento explícito das colunas
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    cnpj_companhia = db.Column(String(20), ForeignKey('companies.cnpj')) # CORREÇÃO APLICADA AQUI
    nome_companhia = db.Column(Text)
    codigo_cvm = db.Column(String(10))
    categoria = db.Column(String(100))
    tipo = db.Column(String(100))
    especie = db.Column(String(100))
    assunto = db.Column(Text)
    data_referencia = db.Column(Date)
    data_entrega = db.Column(Date)
    protocolo_entrega = db.Column(String(30))
    link_download = db.Column(Text)
    
    company = relationship("Company", back_populates="documents")

    def to_dict(self):
        return {
            'id': self.id,
            'company_cnpj': self.cnpj_companhia,
            'company_name': self.nome_companhia,
            'cvm_code': self.codigo_cvm,
            'category': self.categoria,
            'doc_type': self.tipo,
            'species': self.especie,
            'subject': self.assunto,
            'reference_date': self.data_referencia.isoformat() if self.data_referencia else None,
            'delivery_date': self.data_entrega.isoformat() if self.data_entrega else None,
            'delivery_protocol': self.protocolo_entrega,
            'download_link': self.link_download
        }

# ... (outros modelos, se houver)
