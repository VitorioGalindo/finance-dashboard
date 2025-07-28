# scripts/audit_fre_data.py
import os
import sys
from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import sessionmaker

# Adiciona o diretório raiz ao path para importações corretas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper.config import DATABASE_URL
from scraper.models import Company, CapitalStructure, Shareholder, CompanyAdministrator, CompanyRiskFactor

def audit_fre_tables():
    """
    Conecta ao banco de dados e gera um relatório de auditoria sobre as tabelas
    que deveriam ser populadas pelos dados do FRE.
    """
    print("--- INICIANDO AUDITORIA DAS TABELAS DO FRE ---")
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        # 1. Contagem de registros nas novas tabelas
        print("
[1] Contagem de Registros nas Novas Tabelas:")
        
        capital_count = session.query(func.count(CapitalStructure.id)).scalar()
        print(f"  - Tabela 'capital_structure': {capital_count:,} registros encontrados.")
        
        shareholder_count = session.query(func.count(Shareholder.id)).scalar()
        print(f"  - Tabela 'shareholders': {shareholder_count:,} registros encontrados.")
        
        admin_count = session.query(func.count(CompanyAdministrator.id)).scalar()
        print(f"  - Tabela 'company_administrators': {admin_count:,} registros encontrados.")
        
        risk_count = session.query(func.count(CompanyRiskFactor.id)).scalar()
        print(f"  - Tabela 'company_risk_factors': {risk_count:,} registros encontrados.")

        # 2. Verificação das novas colunas na tabela 'companies'
        print("
[2] Verificação das Novas Colunas na Tabela 'companies':")
        
        total_companies = session.query(func.count(Company.id)).scalar()
        
        # Conta quantos registros têm a coluna 'activity_description' preenchida (não nula)
        activity_desc_count = session.query(func.count(Company.id)).filter(Company.activity_description.isnot(None)).scalar()
        print(f"  - Coluna 'activity_description': {activity_desc_count} de {total_companies} empresas preenchidas.")

        # Conta quantos registros têm a coluna 'capital_structure_summary' preenchida
        capital_summary_count = session.query(func.count(Company.id)).filter(Company.capital_structure_summary.isnot(None)).scalar()
        print(f"  - Coluna 'capital_structure_summary': {capital_summary_count} de {total_companies} empresas preenchidas.")

        print("
--- ANÁLISE DA AUDITORIA ---")
        if capital_count > 0 and shareholder_count > 0:
            print("✅ SUCESSO: As tabelas 'capital_structure' e 'shareholders' foram populadas com sucesso.")
        else:
            print("❌ ATENÇÃO: As tabelas 'capital_structure' e 'shareholders' estão vazias ou com poucos dados.")

        if admin_count == 0 and risk_count == 0:
            print("✅ INFO: As tabelas 'company_administrators' e 'company_risk_factors' estão vazias, como esperado.")
            print("  -> Próximo passo: Implementar a lógica de ETL para essas tabelas no 'cvm_service.py'.")
        else:
            print("⚠️ AVISO: As tabelas 'company_administrators' ou 'company_risk_factors' contêm dados, o que não era esperado.")

        print("
--- AUDITORIA CONCLUÍDA ---")

if __name__ == '__main__':
    audit_fre_tables()
