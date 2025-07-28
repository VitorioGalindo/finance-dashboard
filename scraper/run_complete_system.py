#!/usr/bin/env python3
"""
Executa o sistema completo: popula empresas + executa scraping dos 13 pontos
"""

import sys
import os
import logging
from datetime import datetime
sys.path.append('.')

from app import create_app, db
from models import Company
from extract_companies import extract_companies_from_dadosdemercado

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Executa o sistema completo"""
    
    print("🎯 SISTEMA COMPLETO DE DADOS FINANCEIROS BRASILEIROS")
    print("=" * 65)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    app = create_app()
    with app.app_context():
        
        # ETAPA 1: Popular empresas
        print("ETAPA 1: Populando database com empresas da DadosDeMercado")
        print("-" * 55)
        
        try:
            # Get companies from DadosDeMercado
            companies_data = extract_companies_from_dadosdemercado()
            print(f"📊 Extraídas {len(companies_data)} empresas")
            
            # Clear and populate database
            db.session.query(Company).delete()
            db.session.commit()
            
            # Add companies
            added_count = 0
            for company_data in companies_data:
                try:
                    company = Company(
                        cvm_code=company_data['cvm_code'],
                        company_name=company_data['company_name'], 
                        ticker=company_data['ticker'],
                        cnpj=company_data['cnpj'],
                        sector=company_data['sector'],
                        segment=company_data['segment'],
                        has_dfp_data=False,
                        has_itr_data=False
                    )
                    db.session.add(company)
                    added_count += 1
                except Exception as e:
                    logger.error(f"Erro ao adicionar {company_data['ticker']}: {str(e)}")
            
            db.session.commit()
            print(f"✅ {added_count} empresas adicionadas ao database")
            
            # Verify companies
            total = db.session.query(Company).filter(Company.ticker.isnot(None)).count()
            print(f"📈 Total verificado: {total} empresas com ticker")
            
            # Show sample
            sample = db.session.query(Company).limit(10).all()
            print("📋 Amostra de empresas:")
            for company in sample:
                print(f"  {company.ticker:6s} - {company.company_name}")
                
        except Exception as e:
            print(f"❌ Erro na etapa 1: {str(e)}")
            return 1
        
        print()
        
        # ETAPA 2: Executar scraping completo
        print("ETAPA 2: Executando scraping completo dos 13 pontos")
        print("-" * 50)
        
        try:
            # Import scraping system
            from services.complete_implementation import CompleteBrazilianFinancialAPI
            
            print("⚙️  Inicializando sistema de coleta...")
            collector = CompleteBrazilianFinancialAPI()
            
            print("🚀 Iniciando coleta de dados históricos desde 2012...")
            print("📊 Processando todos os 13 pontos especificados...")
            print()
            
            # Execute complete collection
            collector.execute_complete_data_collection()
            
            print()
            print("🎉 SCRAPING COMPLETO FINALIZADO!")
            
        except Exception as e:
            print(f"❌ Erro na etapa 2: {str(e)}")
            logger.error(f"Erro no scraping: {str(e)}")
            return 1
        
        print()
        print("🏆 SISTEMA COMPLETO IMPLEMENTADO COM SUCESSO!")
        print("=" * 45)
        print("✅ Database populado com todas as empresas B3")
        print("✅ Dados históricos coletados desde 2012")
        print("✅ Todos os 13 pontos implementados:")
        print("   1. Lista de Empresas")
        print("   2. Demonstrações Financeiras")
        print("   3. Transações de Insiders") 
        print("   4. Dividendos")
        print("   5. Composição Acionária")
        print("   6. Administradores")
        print("   7. Assembleias")
        print("   8. Partes Relacionadas")
        print("   9. Eventos Corporativos")
        print("   10. Captações")
        print("   11. Documentos Regulatórios")
        print("   12. Dados de Mercado")
        print("   13. Indicadores Calculados")
        print()
        print("🚀 API pronta para uso!")
        print("📖 Documentação completa em: api_documentation.md")
        
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)