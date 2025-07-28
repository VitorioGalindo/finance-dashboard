# scripts/db_inspector.py
import os
import sys
import json
from sqlalchemy import create_engine, select, extract
from sqlalchemy.orm import sessionmaker

# Adiciona o diretório raiz ao path para importações corretas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper.config import DATABASE_URL
from scraper.models import Company, FinancialStatement

def inspect_company_data(cvm_code_to_inspect: str):
    """
    Conecta ao banco de dados e realiza uma inspeção profunda nos dados financeiros
    de uma empresa específica para verificar a integridade dos dados.
    """
    print(f"--- INICIANDO INSPEÇÃO PARA A EMPRESA COM CÓDIGO CVM: {cvm_code_to_inspect} ---")
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        company = session.execute(
            select(Company).where(Company.cvm_code == int(cvm_code_to_inspect))
        ).scalar_one_or_none()
        
        if not company:
            print(f"❌ ERRO: Empresa com código CVM '{cvm_code_to_inspect}' não encontrada.")
            return
            
        print(f"✅ Empresa encontrada: {company.company_name} (ID: {company.id})")
        
        latest_annual_report = session.execute(
            select(FinancialStatement)
            .where(FinancialStatement.company_id == company.id)
            .where(FinancialStatement.report_type == 'DFP')
            .order_by(FinancialStatement.reference_date.desc())
        ).first()
        
        if not latest_annual_report:
            print(f"❌ AVISO: Nenhum relatório anual (DFP) encontrado para {company.company_name}.")
            return

        report = latest_annual_report[0]
        print(f"
--- Inspecionando o relatório de {report.reference_date.strftime('%Y-%m-%d')} (Versão: {report.version}) ---")
        financial_data = report.data
        
        if not financial_data:
            print("❌ ERRO: O campo 'data' do relatório está vazio!")
            return
            
        key_accounts = {
            "Balanço Patrimonial Ativo (BPA)": {"1": "Ativo Total", "1.01": "Ativo Circulante", "1.02": "Ativo Não Circulante"},
            "Balanço Patrimonial Passivo (BPP)": {"2": "Passivo Total", "2.01": "Passivo Circulante", "2.02": "Passivo Não Circulante", "2.03": "Patrimônio Líquido"},
            "Demonstração do Resultado (DRE)": {"3.01": "Receita", "3.03": "Resultado Bruto", "3.11": "Lucro/Prejuízo do Período"},
            "Demonstração do Fluxo de Caixa (DFC)": {"6.01": "Op. Tivities", "6.02": "Inv. Activities", "6.03": "Fin. Activities"}
        }
        
        for statement_name, accounts in key_accounts.items():
            print(f"
[ {statement_name} ]")
            for code, description in accounts.items():
                value = financial_data.get(code)
                print(f"  - {description} (Conta {code}): {f'{value:,.2f}' if value is not None else 'Não encontrado'}")
        
        print("
--- INSPEÇÃO CONCLUÍDA ---")

def inspect_dre_for_years(cvm_code_to_inspect: str, years: list[int]):
    """
    Busca e exibe todas as linhas da DRE para uma empresa em anos específicos.
    """
    print(f"--- BUSCANDO DRE PARA CVM: {cvm_code_to_inspect} NOS ANOS: {years} ---")
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        company = session.execute(
            select(Company).where(Company.cvm_code == int(cvm_code_to_inspect))
        ).scalar_one_or_none()
        
        if not company:
            print(f"❌ ERRO: Empresa com código CVM '{cvm_code_to_inspect}' não encontrada.")
            return
        
        print(f"✅ Empresa encontrada: {company.company_name}")

        reports = session.execute(
            select(FinancialStatement)
            .where(FinancialStatement.company_id == company.id)
            .where(FinancialStatement.report_type == 'DFP')
            .where(extract('year', FinancialStatement.reference_date).in_(years))
            .order_by(FinancialStatement.reference_date.asc())
        ).scalars().all()

        if not reports:
            print(f"❌ AVISO: Nenhum relatório anual (DFP) encontrado para os anos {years}.")
            return

        dre_account_descriptions = {
            "3.01": "Receita de Venda de Bens e/ou Serviços", "3.02": "Custo dos Bens e/ou Serviços Vendidos",
            "3.03": "Resultado Bruto", "3.04": "Despesas/Receitas Operacionais",
            "3.05": "Resultado Antes do Resultado Financeiro e dos Tributos",
            "3.06": "Resultado Financeiro", "3.07": "Resultado Antes dos Tributos sobre o Lucro",
            "3.08": "Imposto de Renda e Contribuição Social sobre o Lucro",
            "3.09": "Resultado Líquido das Operações Continuadas", "3.10": "Resultado Líquido de Operações Descontinuadas",
            "3.11": "Lucro ou Prejuízo Consolidado do Período"
        }

        for report in reports:
            print(f"
--- DRE para o ano de {report.reference_date.year} (Dados Consolidados) ---")
            financial_data = report.data
            
            dre_account_codes = sorted([k for k in financial_data.keys() if k.startswith('3.')])
            
            if not dre_account_codes:
                print("  Nenhuma conta de DRE (código iniciando com '3.') encontrada neste relatório.")
                continue

            for code in dre_account_codes:
                description = dre_account_descriptions.get(code, f"Conta (código {code})")
                value = financial_data.get(code, 0)
                print(f"  - {description:<55}: {value:,.2f}")
    
    print("
--- TESTE CONCLUÍDO ---")

if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == 'dre':
        cvm_code = sys.argv[2]
        try:
            years_int = [int(y) for y in sys.argv[3:]]
            if not years_int: raise ValueError("Pelo menos um ano deve ser fornecido.")
            inspect_dre_for_years(cvm_code, years_int)
        except (ValueError, IndexError) as e:
            print(f"ERRO: Argumentos inválidos. {e}")
            print("Uso: python scripts/db_inspector.py dre <codigo_cvm> <ano1> <ano2> ...")
    elif len(sys.argv) > 1:
        inspect_company_data(sys.argv[1])
    else:
        print("Uso Padrão: python scripts/db_inspector.py <codigo_cvm>")
        print("Novo Teste DRE: python scripts/db_inspector.py dre <codigo_cvm> <ano1> <ano2> ...")
        print("
Executando inspeção padrão para PETR4 (9512)...")
        inspect_company_data("9512")
