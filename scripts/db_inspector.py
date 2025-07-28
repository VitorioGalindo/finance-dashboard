# scripts/db_inspector.py
import os
import sys
import json
from sqlalchemy import create_engine, select
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
        # 1. Buscar a empresa pelo código CVM
        company = session.execute(
            select(Company).where(Company.cvm_code == int(cvm_code_to_inspect))
        ).scalar_one_or_none()
        
        if not company:
            print(f"❌ ERRO: Empresa com código CVM '{cvm_code_to_inspect}' não encontrada na tabela 'companies'.")
            return
            
        print(f"✅ Empresa encontrada: {company.company_name} (ID: {company.id})")
        
        # 2. Buscar o último relatório anual (DFP) disponível para essa empresa
        latest_annual_report = session.execute(
            select(FinancialStatement)
            .where(FinancialStatement.company_id == company.id)
            .where(FinancialStatement.report_type == 'DFP')
            .order_by(FinancialStatement.reference_date.desc())
        ).first()
        
        if not latest_annual_report:
            print(f"❌ AVISO: Nenhum relatório anual (DFP) encontrado para {company.company_name}.")
            return

        # latest_annual_report é uma tupla (Row), o objeto está no primeiro elemento
        report = latest_annual_report[0]
        
        print(f"
--- Inspecionando o relatório de {report.reference_date.strftime('%Y-%m-%d')} (Versão: {report.version}) ---")

        # 3. Carregar o campo 'data' que contém todos os dados financeiros
        financial_data = report.data
        
        if not financial_data:
            print("❌ ERRO: O campo 'data' do relatório está vazio!")
            return
            
        print(f"O relatório contém {len(financial_data)} contas (linhas) diferentes.")

        # 4. Exibir exemplos de contas-chave de cada demonstrativo
        print("
--- AMOSTRA DE DADOS ---")
        
        # Mapeamento de algumas contas importantes para verificação
        key_accounts = {
            "Balanço Patrimonial Ativo (BPA)": {
                "1": "Ativo Total",
                "1.01": "Ativo Circulante",
                "1.02": "Ativo Não Circulante"
            },
            "Balanço Patrimonial Passivo (BPP)": {
                "2": "Passivo Total",
                "2.01": "Passivo Circulante",
                "2.02": "Passivo Não Circulante",
                "2.03": "Patrimônio Líquido Consolidado"
            },
            "Demonstração do Resultado (DRE)": {
                "3.01": "Receita de Venda de Bens e/ou Serviços",
                "3.03": "Resultado Bruto",
                "3.05": "Resultado Antes do Resultado Financeiro e dos Tributos",
                "3.11": "Lucro ou Prejuízo Consolidado do Período"
            },
            "Demonstração do Fluxo de Caixa (DFC)": {
                "6.01": "Atividades Operacionais",
                "6.02": "Atividades de Investimento",
                "6.03": "Atividades de Financiamento"
            }
        }
        
        found_any_key = False
        for statement_name, accounts in key_accounts.items():
            print(f"
[ {statement_name} ]")
            for code, description in accounts.items():
                value = financial_data.get(code)
                if value is not None:
                    print(f"  - {description} (Conta {code}): {value:,.2f}")
                    found_any_key = True
                else:
                    print(f"  - {description} (Conta {code}): Não encontrado")

        if not found_any_key:
            print("
AVISO: Nenhuma das contas-chave de exemplo foi encontrada. O plano de contas pode ser diferente.")
            print("Abaixo, uma amostra bruta do JSON para análise:")
            print(json.dumps({k: v for i, (k, v) in enumerate(financial_data.items()) if i < 10}, indent=2))
            
        print("
--- INSPEÇÃO CONCLUÍDA ---")


if __name__ == '__main__':
    # Pega o código CVM da linha de comando, ou usa um padrão (ex: Petrobras)
    if len(sys.argv) > 1:
        cvm_code = sys.argv[1]
    else:
        print("Nenhum código CVM fornecido. Usando '9512' (Petrobras) como padrão.")
        print("Uso: python scripts/db_inspector.py <codigo_cvm>")
        cvm_code = "9512" 
        
    inspect_company_data(cvm_code)
