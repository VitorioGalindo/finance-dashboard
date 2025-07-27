# main.py (CORRIGIDO COM IMPORTAÇÕES RELATIVAS)
import os
import re
import pandas as pd
import requests
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# CORREÇÃO: Usa importações relativas explícitas
from .core.database import engine, get_db
from .core.models import Base, Company, Insider, Filing, Transaction
from .core.data_portal import download_and_extract_dataframes
from .core.parser import PDFParser
from .core.config import settings

def process_document(doc_metadata: pd.Series, df_consolidado: pd.DataFrame, db: Session):
    # ... (o resto da função permanece o mesmo) ...
    protocol = str(doc_metadata['Protocolo_Entrega'])
    cnpj_cleaned = re.sub(r'\D', '', doc_metadata['CNPJ_Companhia'])
    company_name = doc_metadata['Nome_Companhia']
    
    print(f"--- Processando protocolo: {protocol} para a empresa: {company_name} ---")
    if db.query(Filing).filter_by(cvm_protocol=protocol).first():
        print("Protocolo já processado. Pulando."); return

    pdf_path = settings.DOWNLOAD_DIR / f"{protocol}.pdf"
    if not pdf_path.exists():
        try:
            pdf_response = requests.get(doc_metadata['Link_Download'], timeout=120)
            pdf_response.raise_for_status()
            with open(pdf_path, 'wb') as f: f.write(pdf_response.content)
        except requests.exceptions.RequestException as e:
            print(f"ERRO ao baixar PDF: {e}. Pulando."); return

    parser = PDFParser(pdf_path=pdf_path)
    transactions_from_pdf = parser.extract_transactions()
    if not transactions_from_pdf:
        print("Nenhuma transação encontrada pelo parser no PDF."); return

    lookup_df = df_consolidado[
        (df_consolidado['CNPJ_Companhia'] == doc_metadata['CNPJ_Companhia']) &
        (df_consolidado['Data_Referencia'] == doc_metadata['Data_Referencia'])
    ].copy()
    if lookup_df.empty:
        print("Nenhum registro correspondente no CSV consolidado."); return

    successful_loads = 0
    company, _ = get_or_create(db, Company, cnpj=cnpj_cleaned, defaults={'name': company_name})
    filing, _ = get_or_create(db, Filing,
        cvm_protocol=protocol, company_cnpj=company.cnpj,
        reference_date=pd.to_datetime(doc_metadata['Data_Referencia']).date(),
        pdf_url=doc_metadata['Link_Download']
    )

    for tx_pdf in transactions_from_pdf:
        if not lookup_df['Tipo_Cargo'].empty:
            insider_name = lookup_df['Tipo_Cargo'].mode()[0]
        else:
            insider_name = "N/A"

        if insider_name == "N/A":
            print("Aviso: Não foi possível determinar o grupo de insider. Pulando transação.")
            continue

        insider, _ = get_or_create(db, Insider, company_cnpj=cnpj_cleaned, name=insider_name, defaults={'insider_type': 'Grupo'})
        
        new_transaction = Transaction(
            filing_id=filing.id, insider_id=insider.id,
            transaction_date=tx_pdf["transaction_date"],
            operation_type=tx_pdf["operation_type"],
            asset_type=tx_pdf.get("asset_type"),
            quantity=tx_pdf["quantity"],
            price=tx_pdf.get("price"),
            volume=tx_pdf.get("volume")
        )
        db.add(new_transaction)
        successful_loads += 1
    
    db.commit()
    if successful_loads > 0:
        print(f"Sucesso! {successful_loads} transações do PDF enriquecidas e carregadas.")

def get_or_create(db_session: Session, model, defaults: dict = None, **kwargs):
    instance = db_session.query(model).filter_by(**kwargs).first()
    if instance: return instance, False
    defaults = defaults or {}; params = {**kwargs, **defaults}
    instance = model(**params)
    try:
        db_session.add(instance)
        db_session.commit()
        return instance, True
    except IntegrityError:
        db_session.rollback()
        instance = db_session.query(model).filter_by(**kwargs).first()
        return instance, False

if __name__ == "__main__":
    print("Inicializando tabelas (se não existirem)..."); 
    Base.metadata.create_all(bind=engine)
    
    start_year = int(input("Digite o ano inicial para a carga de dados de insiders (ex: 2023): "))
    end_year = datetime.now().year

    for year in range(start_year, end_year + 1):
        print(f"{'='*20} PROCESSANDO ANO: {year} {'='*20}")
        df_main, df_consolidado = download_and_extract_dataframes(year=year)
        
        if df_main is not None and df_consolidado is not None and not df_main.empty and not df_consolidado.empty:
            filter_value = 'Valores Mobiliários negociados e detidos (art. 11 da Instr. CVM nº 358)'
            df_filtered = df_main[df_main['Categoria'] == filter_value].copy()
            print(f"Encontrados {len(df_filtered)} formulários de interesse para processar no ano de {year}.")
            
            db_session = next(get_db())
            try:
                for index, doc_row in df_filtered.iterrows():
                    process_document(doc_row, df_consolidado, db_session)
            finally:
                db_session.close()
        else:
            print(f"Falha ao obter DataFrames para o ano {year}. Pulando.")

    print("--- Pipeline de ETL de Insiders concluído. ---")
