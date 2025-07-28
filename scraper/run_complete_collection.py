#!/usr/bin/env python3
"""
Script principal para executar a coleta completa de dados
Implementa todos os 13 pontos da especificação desde 2012
"""

import sys
import os
sys.path.append('.')

from services.complete_implementation import CompleteBrazilianFinancialAPI
from models_extended import *
from app import create_app, db
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('complete_collection.log'),
        logging.StreamHandler()
    ]
)

def main():
    """Executa a coleta completa de dados financeiros brasileiros"""
    
    print("🚀 INICIANDO COLETA COMPLETA DE DADOS FINANCEIROS BRASILEIROS")
    print("📋 Implementando os 13 pontos da especificação API")
    print("📅 Período: 2012 até presente")
    print("🏢 Escopo: Todas as empresas com ticker B3")
    print()
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # Create extended database tables
            print("📊 Criando tabelas estendidas do database...")
            db.create_all()
            print("✅ Database preparado com sucesso!")
            
            # Initialize the complete collector
            collector = CompleteBrazilianFinancialAPI()
            
            # Execute complete data collection
            print("🔄 Iniciando coleta sistemática...")
            collector.execute_complete_data_collection()
            
            print()
            print("🎉 COLETA COMPLETA FINALIZADA COM SUCESSO!")
            print("✅ Database populado com todos os dados dos 13 pontos")
            print("📈 API pronta para uso com dados completos desde 2012")
            
        except Exception as e:
            print(f"❌ Erro durante a coleta: {str(e)}")
            logging.error(f"Erro na coleta completa: {str(e)}")
            return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)