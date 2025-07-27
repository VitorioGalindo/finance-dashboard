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
    __tablename__ = 'cvm_documents'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    # CORREÇÃO APLICADA AQUI: O nome da propriedade da classe agora é 'company_cnpj'
    # e ele mapeia para a coluna 'cnpj_companhia' no banco de dados.
    company_cnpj = db.Column('cnpj_companhia', String(20), ForeignKey('companies.cnpj'))
    company_name = db.Column('nome_companhia', Text)
    cvm_code = db.Column('codigo_cvm', String(10))
    category = db.Column('categoria', String(100))
    doc_type = db.Column('tipo', String(100))
    species = db.Column('especie', String(100))
    subject = db.Column('assunto', Text)
    reference_date = db.Column('data_referencia', Date)
    delivery_date = db.Column('data_entrega', Date)
    delivery_protocol = db.Column('protocolo_entrega', String(30))
    download_link = db.Column('link_download', Text)
    
    company = relationship("Company", back_populates="documents")

    def to_dict(self):
        # O método to_dict continua usando os nomes das propriedades da classe
        return {
            'id': self.id,
            'company_cnpj': self.company_cnpj,
            'company_name': self.company_name,
            'cvm_code': self.cvm_code,
            'category': self.category,
            'doc_type': self.doc_type,
            'species': self.species,
            'subject': self.subject,
            'reference_date': self.reference_date.isoformat() if self.reference_date else None,
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'delivery_protocol': self.delivery_protocol,
            'download_link': self.download_link
        }

# ... (outros modelos, se houver)
