# scripts/db_inspector.py
import os
import sys
import json
import requests
import zipfile
import pandas as pd
from io import BytesIO
from sqlalchemy import create_engine, select, extract
from sqlalchemy.orm import sessionmaker

# Adiciona o diretório raiz ao path para importações corretas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper.config import DATABASE_URL, CVM_DADOS_ABERTOS_URL
from scraper.models import Company, FinancialStatement

def inspect_company_data(cvm_code_to_inspect: str):
    """Inspeção profunda nos dados financeiros de uma empresa."""
    # ... (código existente, sem alterações)
    pass

def inspect_dre_for_years(cvm_code_to_inspect: str, years: list[int]):
    """Busca e exibe todas as linhas da DRE para uma empresa em anos específicos."""
    # ... (código existente, sem alterações)
    pass

def analyze_fre_zip_structure(year: int):
    """
    Baixa o arquivo ZIP do Formulário de Referência (FRE) de um ano específico,
    analisa sua estrutura, e exibe os arquivos, colunas e dados de exemplo.
    """
    print(f"--- INICIANDO ANÁLISE ESTRUTURAL DO ARQUIVO FRE PARA O ANO: {year} ---")
    
    fre_url = f"{CVM_DADOS_ABERTOS_URL}/CIA_ABERTA/DOC/FRE/DADOS/fre_cia_aberta_{year}.zip"
    
    print(f"Baixando arquivo de: {fre_url}")
    try:
        response = requests.get(fre_url, timeout=180)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ ERRO: Falha ao baixar o arquivo ZIP: {e}")
        return

    print("Download concluído. Analisando arquivos CSV dentro do ZIP...")
    
    try:
        zip_file = zipfile.ZipFile(BytesIO(response.content))
        csv_files = [f for f in zip_file.namelist() if f.endswith('.csv')]

        if not csv_files:
            print("❌ Nenhuma arquivo CSV encontrado no ZIP.")
            return

        for i, filename in enumerate(csv_files):
            print("
" + "="*80)
            print(f"ARQUIVO {i+1}/{len(csv_files)}: {filename}")
            print("="*80)
            
            with zip_file.open(filename) as f:
                try:
                    # Lê apenas as primeiras 1000 linhas para análise rápida
                    df = pd.read_csv(f, sep=';', encoding='latin1', dtype=str, nrows=1000)
                    
                    print("COLUNAS ENCONTRADAS:")
                    for col in df.columns:
                        print(f"  - {col}")
                        
                    print("
AMOSTRA DOS DADOS (primeiras 3 linhas):")
                    print(df.head(3).to_string())
                    
                except Exception as e:
                    print(f"  -> Não foi possível processar este arquivo: {e}")

    except zipfile.BadZipFile:
        print("❌ ERRO: O arquivo baixado não é um ZIP válido.")
        return
        
    print("

--- ANÁLISE ESTRUTURAL DO FRE CONCLUÍDA ---")
    propose_db_schema()

def propose_db_schema():
    """Exibe uma proposta de como os dados do FRE poderiam ser modelados no banco."""
    print("
" + "#"*80)
    print("PROPOSTA DE MODELAGEM DE DADOS PARA O FORMULÁRIO DE REFERÊNCIA (FRE)")
    print("#"*80)
    print("""
Baseado na análise, os dados do FRE são muito ricos e granulares. Em vez de adicionar dezenas de colunas à tabela 'companies',
sugiro a criação de novas tabelas relacionadas para capturar essas informações.

PROPOSTA:

1. Tabela `company_risk_factors` (Fatores de Risco - Um para Muitos)
   - id (PK)
   - company_id (FK para companies.id)
   - reference_date
   - risk_type (de Mercado, Operacionais, Regulatórios, etc.)
   - risk_description (TEXT)
   - mitigation_measures (TEXT)

2. Tabela `company_administrators` (Administradores e seus Comitês - Um para Muitos)
   - id (PK)
   - company_id (FK para companies.id)
   - reference_date
   - name
   - cpf_cnpj (criptografado)
   - position (Diretor Presidente, Conselheiro, etc.)
   - election_date
   - term_of_office
   - committee (Comitê de Auditoria, etc.)
   - professional_background (TEXT)

3. Tabela `auditors` (Auditores Independentes - Um para Muitos)
   - id (PK)
   - company_id (FK para companies.id)
   - reference_date
   - auditor_name
   - auditor_cnpj
   - hiring_date
   - services_provided (TEXT)

4. Tabela `stockholder_structure` (Estrutura Acionista - Um para Muitos, com histórico)
   - id (PK)
   - company_id (FK para companies.id)
   - reference_date
   - stockholder_name
   - stockholder_type (Pessoa Física, Jurídica, Fundo)
   - stake_on (ordinárias, preferenciais)
   - quantity
   - percentage

5. Adicionar colunas à tabela `companies` (para dados mais estáticos):
   - capital_structure_summary (JSON): Um resumo da composição do capital social.
   - activity_description (TEXT): Descrição mais detalhada das atividades da empresa.

Esta abordagem mantém a tabela 'companies' limpa e permite consultas detalhadas e históricas sobre
aspectos específicos da governança e operação da empresa.
""")

if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == 'fre-analysis':
        try:
            year = int(sys.argv[2])
            analyze_fre_zip_structure(year)
        except (ValueError, IndexError):
            print("ERRO: Ano inválido.")
            print("Uso: python scripts/db_inspector.py fre-analysis <ano>")
    elif len(sys.argv) > 2 and sys.argv[1] == 'dre':
        # ... (código existente, sem alterações)
        pass
    elif len(sys.argv) > 1:
        # ... (código existente, sem alterações)
        pass
    else:
        print("Uso Padrão: python scripts/db_inspector.py <codigo_cvm>")
        print("Teste DRE: python scripts/db_inspector.py dre <codigo_cvm> <ano1> ...")
        print("NOVA ANÁLISE FRE: python scripts/db_inspector.py fre-analysis <ano>")
        print("
Executando inspeção padrão para PETR4 (9512)...")
        inspect_company_data("9512")
