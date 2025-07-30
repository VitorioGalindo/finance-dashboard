#!/usr/bin/env python3
"""
Testes de Integração do Dashboard Financeiro
Valida toda a integração do sistema
"""

import os
import sys
import unittest
import requests
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import time

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestDashboardIntegration(unittest.TestCase):
    """Testes de integração do dashboard"""
    
    @classmethod
    def setUpClass(cls):
        """Configuração inicial dos testes"""
        cls.base_url = "http://localhost:5001"
        cls.db_config = {
            'host': 'cvm-insiders-db.cb2uq8cqs3dn.us-east-2.rds.amazonaws.com',
            'port': 5432,
            'database': 'postgres',
            'user': 'pandora',
            'password': 'Pandora337303$'
        }
        
        # Aguarda o backend estar disponível
        cls._wait_for_backend()
    
    @classmethod
    def _wait_for_backend(cls, max_attempts=10):
        """Aguarda o backend estar disponível"""
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{cls.base_url}/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Backend está disponível para testes")
                    return
            except requests.exceptions.ConnectionError:
                pass
            
            print(f"Aguardando backend... tentativa {attempt + 1}/{max_attempts}")
            time.sleep(2)
        
        raise Exception("Backend não está disponível para testes")
    
    def get_db_connection(self):
        """Cria conexão com o banco de dados"""
        return psycopg2.connect(**self.db_config)
    
    def test_database_connection(self):
        """Testa conexão com o banco de dados"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()
            
            self.assertEqual(result[0], 1)
            print("✅ Conexão com banco de dados OK")
            
        except Exception as e:
            self.fail(f"Falha na conexão com banco: {e}")
    
    def test_backend_health(self):
        """Testa health check do backend"""
        response = requests.get(f"{self.base_url}/health")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'Finance Dashboard Backend')
        
        print("✅ Health check do backend OK")
    
    def test_companies_endpoint(self):
        """Testa endpoint de empresas"""
        response = requests.get(f"{self.base_url}/api/companies")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        
        # Verifica estrutura do primeiro item
        first_company = data[0]
        required_fields = ['id', 'cvm_code', 'company_name']
        for field in required_fields:
            self.assertIn(field, first_company)
        
        print(f"✅ Endpoint de empresas OK - {len(data)} empresas retornadas")
    
    def test_market_overview_endpoint(self):
        """Testa endpoint de visão geral do mercado"""
        response = requests.get(f"{self.base_url}/api/market/overview")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('statistics', data)
        self.assertIn('top_gainers', data)
        self.assertIn('top_losers', data)
        
        print("✅ Endpoint de visão geral do mercado OK")
    
    def test_market_sectors_endpoint(self):
        """Testa endpoint de setores"""
        response = requests.get(f"{self.base_url}/api/market/sectors")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('sectors', data)
        self.assertIn('total_sectors', data)
        self.assertIn('total_companies', data)
        
        self.assertGreater(data['total_sectors'], 0)
        self.assertGreater(data['total_companies'], 0)
        
        print(f"✅ Endpoint de setores OK - {data['total_sectors']} setores")
    
    def test_tickers_endpoint(self):
        """Testa endpoint de tickers"""
        response = requests.get(f"{self.base_url}/api/market/tickers")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('tickers', data)
        self.assertIn('pagination', data)
        
        self.assertIsInstance(data['tickers'], list)
        
        if len(data['tickers']) > 0:
            first_ticker = data['tickers'][0]
            self.assertIn('symbol', first_ticker)
            self.assertIn('company_name', first_ticker)
        
        print(f"✅ Endpoint de tickers OK - {len(data['tickers'])} tickers na primeira página")
    
    def test_insider_transactions_endpoint(self):
        """Testa endpoint de transações de insider"""
        response = requests.get(f"{self.base_url}/api/market/insider-transactions")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('transactions', data)
        self.assertIn('total', data)
        
        print(f"✅ Endpoint de transações de insider OK - {data['total']} transações")
    
    def test_news_endpoint(self):
        """Testa endpoint de notícias"""
        response = requests.get(f"{self.base_url}/api/market/news")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('news', data)
        self.assertIn('total', data)
        
        print(f"✅ Endpoint de notícias OK - {data['total']} notícias")
    
    def test_financial_data_endpoint(self):
        """Testa endpoint de dados financeiros"""
        # Primeiro busca uma empresa
        companies_response = requests.get(f"{self.base_url}/api/companies")
        companies = companies_response.json()
        
        if len(companies) > 0:
            company_id = companies[0]['id']
            
            response = requests.get(f"{self.base_url}/api/companies/{company_id}/financials")
            
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn('company', data)
            self.assertIn('financial_data', data)
            
            print("✅ Endpoint de dados financeiros OK")
        else:
            print("⚠️  Nenhuma empresa encontrada para testar dados financeiros")
    
    def test_data_consistency(self):
        """Testa consistência dos dados"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Verifica se há empresas ativas
            cursor.execute("SELECT COUNT(*) as count FROM companies WHERE is_active = true")
            active_companies = cursor.fetchone()['count']
            self.assertGreater(active_companies, 0)
            
            # Verifica se há tickers
            cursor.execute("SELECT COUNT(*) as count FROM tickers")
            total_tickers = cursor.fetchone()['count']
            self.assertGreater(total_tickers, 0)
            
            # Verifica se há acionistas
            cursor.execute("SELECT COUNT(*) as count FROM shareholders")
            total_shareholders = cursor.fetchone()['count']
            self.assertGreater(total_shareholders, 0)
            
            # Verifica integridade referencial
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM tickers t 
                LEFT JOIN companies c ON t.company_id = c.id 
                WHERE c.id IS NULL
            """)
            orphaned_tickers = cursor.fetchone()['count']
            self.assertEqual(orphaned_tickers, 0, "Há tickers órfãos sem empresa associada")
            
            conn.close()
            
            print(f"✅ Consistência dos dados OK - {active_companies} empresas ativas, {total_tickers} tickers")
            
        except Exception as e:
            self.fail(f"Erro na verificação de consistência: {e}")
    
    def test_api_response_times(self):
        """Testa tempos de resposta das APIs"""
        endpoints = [
            "/api/companies",
            "/api/market/overview",
            "/api/market/sectors",
            "/api/market/tickers",
            "/api/market/insider-transactions",
            "/api/market/news"
        ]
        
        slow_endpoints = []
        
        for endpoint in endpoints:
            start_time = time.time()
            response = requests.get(f"{self.base_url}{endpoint}")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response_time > 5.0:  # Mais de 5 segundos é considerado lento
                slow_endpoints.append((endpoint, response_time))
            
            print(f"  {endpoint}: {response_time:.2f}s")
        
        if slow_endpoints:
            print(f"⚠️  Endpoints lentos detectados: {slow_endpoints}")
        else:
            print("✅ Tempos de resposta das APIs OK")
    
    def test_cors_headers(self):
        """Testa cabeçalhos CORS"""
        response = requests.get(f"{self.base_url}/api/companies")
        
        # Verifica se CORS está habilitado
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        
        print("✅ Cabeçalhos CORS OK")
    
    def test_error_handling(self):
        """Testa tratamento de erros"""
        # Testa endpoint inexistente
        response = requests.get(f"{self.base_url}/api/nonexistent")
        self.assertEqual(response.status_code, 404)
        
        # Testa empresa inexistente
        response = requests.get(f"{self.base_url}/api/companies/99999")
        self.assertEqual(response.status_code, 404)
        
        print("✅ Tratamento de erros OK")

class TestSystemPerformance(unittest.TestCase):
    """Testes de performance do sistema"""
    
    def setUp(self):
        self.base_url = "http://localhost:5001"
    
    def test_concurrent_requests(self):
        """Testa requisições concorrentes"""
        import threading
        import queue
        
        def make_request(url, results_queue):
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                end_time = time.time()
                
                results_queue.put({
                    'status_code': response.status_code,
                    'response_time': end_time - start_time,
                    'success': response.status_code == 200
                })
            except Exception as e:
                results_queue.put({
                    'status_code': 0,
                    'response_time': 0,
                    'success': False,
                    'error': str(e)
                })
        
        # Faz 10 requisições concorrentes
        threads = []
        results_queue = queue.Queue()
        
        for i in range(10):
            thread = threading.Thread(
                target=make_request, 
                args=(f"{self.base_url}/api/companies", results_queue)
            )
            threads.append(thread)
            thread.start()
        
        # Aguarda todas as threads terminarem
        for thread in threads:
            thread.join()
        
        # Coleta resultados
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Verifica resultados
        successful_requests = sum(1 for r in results if r['success'])
        avg_response_time = sum(r['response_time'] for r in results if r['success']) / max(successful_requests, 1)
        
        self.assertGreaterEqual(successful_requests, 8, "Menos de 80% das requisições foram bem-sucedidas")
        self.assertLess(avg_response_time, 10.0, "Tempo médio de resposta muito alto")
        
        print(f"✅ Teste de concorrência OK - {successful_requests}/10 sucessos, tempo médio: {avg_response_time:.2f}s")

def run_integration_tests():
    """Executa todos os testes de integração"""
    print("🚀 Iniciando testes de integração do Dashboard Financeiro...")
    print("=" * 60)
    
    # Cria suite de testes
    suite = unittest.TestSuite()
    
    # Adiciona testes de integração
    integration_tests = [
        'test_database_connection',
        'test_backend_health',
        'test_companies_endpoint',
        'test_market_overview_endpoint',
        'test_market_sectors_endpoint',
        'test_tickers_endpoint',
        'test_insider_transactions_endpoint',
        'test_news_endpoint',
        'test_financial_data_endpoint',
        'test_data_consistency',
        'test_api_response_times',
        'test_cors_headers',
        'test_error_handling'
    ]
    
    for test_name in integration_tests:
        suite.addTest(TestDashboardIntegration(test_name))
    
    # Adiciona testes de performance
    performance_tests = [
        'test_concurrent_requests'
    ]
    
    for test_name in performance_tests:
        suite.addTest(TestSystemPerformance(test_name))
    
    # Executa testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL DOS TESTES")
    print("=" * 60)
    print(f"Testes executados: {result.testsRun}")
    print(f"Sucessos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Falhas: {len(result.failures)}")
    print(f"Erros: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FALHAS:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n❌ ERROS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n📈 Taxa de sucesso: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("✅ Sistema aprovado nos testes de integração!")
    elif success_rate >= 70:
        print("⚠️  Sistema parcialmente aprovado - algumas correções necessárias")
    else:
        print("❌ Sistema reprovado - correções críticas necessárias")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)

