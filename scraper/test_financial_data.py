#!/usr/bin/env python3
"""
Script para extrair e processar dados financeiros específicos da PRIO S.A.
"""
from app import app, db
from models import Company, CVMFinancialData
from services.etl_cvm_financial import CVMFinancialETL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_prio_data():
    """Extrai dados específicos da PRIO S.A."""
    with app.app_context():
        logger.info("🔍 BUSCANDO E EXTRAINDO DADOS DA PRIO S.A.")
        
        # Buscar PRIO por diferentes termos
        search_terms = ['%PRIO%', '%3R%', '%PETRORIO%', '%PETRO RIO%']
        prio_company = None
        
        for term in search_terms:
            companies = Company.query.filter(Company.company_name.ilike(term)).all()
            if companies:
                logger.info(f"Encontradas com termo {term}:")
                for comp in companies:
                    logger.info(f"  - {comp.company_name} (CVM: {comp.cvm_code})")
                    if 'PRIO' in comp.company_name.upper() or '3R' in comp.company_name.upper():
                        prio_company = comp
                        break
        
        if not prio_company:
            logger.warning("PRIO não encontrada, usando empresa exemplo...")
            # Usar outra empresa como exemplo
            prio_company = Company.query.filter_by(has_dfp_data=True).first()
        
        if prio_company:
            logger.info(f"✅ Processando: {prio_company.company_name} (CVM: {prio_company.cvm_code})")
            
            # Extrair dados para múltiplos anos
            etl = CVMFinancialETL()
            years = [2020, 2021, 2022, 2023]
            
            for year in years:
                logger.info(f"Extraindo dados para {year}...")
                success = etl.extract_company_financial_data(str(prio_company.cvm_code), year)
                if success:
                    logger.info(f"✅ Dados {year} extraídos com sucesso")
                else:
                    logger.warning(f"⚠️ Falha ao extrair dados {year}")
            
            return prio_company
        
        return None

if __name__ == "__main__":
    company = extract_prio_data()
    if company:
        print(f"✅ Dados extraídos para {company.company_name}")
    else:
        print("❌ Falha na extração")