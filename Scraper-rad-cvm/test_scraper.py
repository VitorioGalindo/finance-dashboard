#!/usr/bin/env python3
"""
Script de teste para o RAD CVM Scraper
"""

import sys
import logging
from rad_cvm_scraper import RADCVMScraper

def test_basic_functionality():
    """Testa funcionalidades básicas do scraper"""
    print("=== Teste do RAD CVM Scraper ===")
    
    # Configura logging
    logging.basicConfig(level=logging.INFO)
    
    # Cria instância do scraper
    scraper = RADCVMScraper(headless=True)
    
    try:
        print("\n1. Testando acesso ao portal...")
        scraper.start_driver()
        scraper.driver.get(scraper.base_url)
        
        title = scraper.driver.title
        print(f"   Título da página: {title}")
        
        if "Consulta de Documentos" in title:
            print("   ✓ Portal acessível")
        else:
            print("   ✗ Erro ao acessar portal")
            return False
        
        print("\n2. Testando busca por documentos CVM 44...")
        documents = scraper.search_cvm44_documents(days_back=7)
        
        print(f"   Encontrados {len(documents)} documentos")
        
        if documents:
            print("   ✓ Busca funcionando")
            print("\n   Primeiros 3 documentos encontrados:")
            for i, doc in enumerate(documents[:3]):
                print(f"   {i+1}. {doc['empresa']} - {doc['tipo']} ({doc['data_entrega']})")
        else:
            print("   ⚠ Nenhum documento encontrado (pode ser normal)")
        
        print("\n3. Teste concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n   ✗ Erro durante o teste: {e}")
        return False
        
    finally:
        scraper.stop_driver()

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)

