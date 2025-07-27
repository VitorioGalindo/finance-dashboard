# scripts/audit_financial_data.py
import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine

def get_db_connection_string():
    """Lê as credenciais do .env."""
    load_dotenv()
    # ... (código igual aos outros scripts)
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    dbname = os.getenv("DB_NAME", "postgres")
    if not all([user, password, host, dbname]):
        raise ValueError("Credenciais do banco de dados não encontradas.")
    return f"postgresql+psycopg2://{user}:{password}@{host}/{dbname}?sslmode=require"

def audit_company_financials(company_cnpj):
    """
    Realiza uma auditoria nos dados financeiros de uma empresa específica,
    simulando a busca que a API fará.
    """
    print("" + "="*60)
    print(f"📊 AUDITORIA DE DADOS FINANCEIROS PARA O CNPJ: {company_cnpj}")
    print("="*60)

    engine = create_engine(get_db_connection_string())
    with engine.connect() as connection:
        # Contas chave que nosso frontend precisa para a DRE e Balanço
        DRE_ACCOUNTS = ('3.01', '3.02', '3.03', '3.04') # Receita, Custo, Lucro Bruto, Despesas
        BALANCE_SHEET_ACCOUNTS = ('1', '1.01', '2', '2.01') # Ativo, Ativo Circulante, Passivo, Passivo Circulante
        
        # Busca os relatórios anuais (DFP) da empresa
        reports_sql = """
        SELECT id, year FROM financial_reports
        WHERE company_cnpj = %(cnpj)s AND period = 'ANUAL' AND report_type = 'DFP'
        ORDER BY year DESC;
        """
        df_reports = pd.read_sql(reports_sql, connection, params={'cnpj': company_cnpj})
        
        if df_reports.empty:
            print(f"❌ Nenhum relatório anual (DFP) encontrado para o CNPJ {company_cnpj}.")
            return

        print(f"Encontrados {len(df_reports)} relatórios anuais (DFP). Analisando o mais recente (Ano: {df_reports.iloc[0]['year']}).")
        latest_report_id = int(df_reports.iloc[0]['id'])

        # --- AUDITORIA DA DRE ---
        print("--- Auditoria da DRE (Demonstração de Resultado) ---")
        dre_sql = """
        SELECT account_code, account_description, account_value
        FROM financial_statements
        WHERE report_id = %(report_id)s AND statement_type = 'DRE'
        AND account_code IN %(accounts)s;
        """
        df_dre = pd.read_sql(dre_sql, connection, params={'report_id': latest_report_id, 'accounts': DRE_ACCOUNTS})
        
        if not df_dre.empty:
            print("✅ Contas essenciais da DRE encontradas:")
            print(df_dre.to_string(index=False))
        else:
            print("❌ Nenhuma das contas essenciais da DRE foi encontrada para o último relatório.")

        # --- AUDITORIA DO BALANÇO PATRIMONIAL ---
        print("--- Auditoria do Balanço Patrimonial ---")
        bs_sql = """
        SELECT statement_type, account_code, account_description, account_value
        FROM financial_statements
        WHERE report_id = %(report_id)s AND statement_type IN ('BPA', 'BPP')
        AND account_code IN %(accounts)s;
        """
        df_bs = pd.read_sql(bs_sql, connection, params={'report_id': latest_report_id, 'accounts': BALANCE_SHEET_ACCOUNTS})

        if not df_bs.empty:
            print("✅ Contas essenciais do Balanço encontradas:")
            print(df_bs.to_string(index=False))
        else:
            print("❌ Nenhuma das contas essenciais do Balanço foi encontrada para o último relatório.")
            
        print("" + "="*60)
        print("✅ AUDITORIA CONCLUÍDA")
        print("="*60)

if __name__ == "__main__":
    # Pega um CNPJ de uma empresa que sabemos que tem dados (ex: Petrobras)
    # Você pode alterar este CNPJ para auditar outras empresas.
    target_cnpj = input("Digite o CNPJ da empresa para auditar (ex: 33000167000101 para Petrobras): ")
    if target_cnpj:
        audit_company_financials(target_cnpj)
