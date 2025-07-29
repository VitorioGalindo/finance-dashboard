#!/usr/bin/env python3
"""
Serviço de Integração do Scraper com Dashboard
Adapta o scraper existente para trabalhar com PostgreSQL
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

# Adiciona o diretório do scraper ao path
scraper_path = os.path.join(os.path.dirname(__file__), '../../Scraper-rad-cvm')
sys.path.append(scraper_path)

class ScraperIntegrationService:
    """Serviço de integração do scraper com o dashboard"""
    
    def __init__(self):
        self.db_config = {
            'host': 'cvm-insiders-db.cb2uq8cqs3dn.us-east-2.rds.amazonaws.com',
            'port': 5432,
            'database': 'postgres',
            'user': 'pandora',
            'password': 'Pandora337303$'
        }
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Configura o logger"""
        logger = logging.getLogger('ScraperIntegration')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def get_db_connection(self):
        """Cria conexão com PostgreSQL"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            self.logger.error(f"Erro ao conectar no banco: {e}")
            return None
    
    def populate_tickers_table(self):
        """Popula a tabela tickers com dados das empresas"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Busca empresas que têm tickers mas não estão na tabela tickers
            cursor.execute("""
                SELECT id, ticker, tickers, company_name 
                FROM companies 
                WHERE ticker IS NOT NULL 
                AND is_active = true
            """)
            
            companies = cursor.fetchall()
            
            for company in companies:
                # Insere ticker principal
                if company['ticker']:
                    cursor.execute("""
                        INSERT INTO tickers (symbol, company_id, type, created_at)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (symbol) DO NOTHING
                    """, (company['ticker'], company['id'], 'principal', datetime.utcnow()))
                
                # Insere tickers adicionais do campo JSON
                if company['tickers'] and isinstance(company['tickers'], list):
                    for ticker in company['tickers']:
                        if ticker != company['ticker']:  # Evita duplicar o ticker principal
                            cursor.execute("""
                                INSERT INTO tickers (symbol, company_id, type, created_at)
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT (symbol) DO NOTHING
                            """, (ticker, company['id'], 'adicional', datetime.utcnow()))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.logger.info(f"Tickers populados para {len(companies)} empresas")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao popular tickers: {e}")
            return False
    
    def create_sample_market_data(self):
        """Cria dados de mercado de exemplo para teste"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            # Busca alguns tickers para criar dados de exemplo
            cursor.execute("SELECT symbol FROM tickers LIMIT 10")
            tickers = cursor.fetchall()
            
            sample_data = []
            base_date = datetime.now() - timedelta(days=30)
            
            for ticker_row in tickers:
                ticker = ticker_row[0]
                
                # Cria 30 dias de dados históricos simulados
                for i in range(30):
                    date = base_date + timedelta(days=i)
                    
                    # Preços simulados (apenas para teste)
                    base_price = 50.0 + (hash(ticker) % 100)  # Preço base baseado no ticker
                    variation = (i % 10 - 5) * 0.02  # Variação de -10% a +10%
                    
                    open_price = base_price * (1 + variation)
                    close_price = open_price * (1 + (i % 5 - 2) * 0.01)
                    high_price = max(open_price, close_price) * 1.02
                    low_price = min(open_price, close_price) * 0.98
                    volume = 1000000 + (i % 1000000)
                    
                    sample_data.append((
                        ticker, date, open_price, high_price, low_price, 
                        close_price, volume, close_price, 0.0, 0.0, 
                        volume * close_price, high_price, low_price, 
                        close_price, None, None, None, None, 
                        'OPEN', datetime.utcnow(), date, datetime.utcnow()
                    ))
            
            # Insere dados na tabela quotes (que é a tabela real de cotações)
            cursor.executemany("""
                INSERT INTO quotes (ticker, date, open_price, high_price, low_price, close_price, volume, 
                                  adjusted_close, price, change, change_percent, volume_financial, high, low, 
                                  previous_close, bid, ask, bid_size, ask_size, market_status, timestamp, 
                                  quote_datetime, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, sample_data)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.logger.info(f"Criados {len(sample_data)} registros de cotações de exemplo")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao criar dados de mercado: {e}")
            return False
    
    def create_sample_financial_data(self):
        """Cria dados financeiros de exemplo"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            # Busca empresas para criar dados financeiros
            cursor.execute("SELECT id, cvm_code, company_name FROM companies LIMIT 20")
            companies = cursor.fetchall()
            
            financial_data = []
            
            for company in companies:
                company_id, cvm_code, company_name = company
                
                # Cria dados para os últimos 3 anos
                for year in [2022, 2023, 2024]:
                    for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
                        # Dados financeiros simulados
                        revenue = 1000000 + (hash(f"{company_id}{year}{quarter}") % 10000000)
                        net_income = revenue * 0.1  # 10% de margem líquida
                        total_assets = revenue * 2.5  # 2.5x o faturamento
                        
                        financial_data.append((
                            company_id, cvm_code, 'DRE', year, quarter,
                            revenue, net_income, total_assets
                        ))
            
            # Insere dados financeiros
            cursor.executemany("""
                INSERT INTO cvm_financial_data (company_id, cvm_code, statement_type, year, quarter, revenue, net_income, total_assets)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, financial_data)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.logger.info(f"Criados {len(financial_data)} registros de dados financeiros de exemplo")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao criar dados financeiros: {e}")
            return False
    
    def create_sample_insider_transactions(self):
        """Cria transações de insider de exemplo"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            # Busca empresas para criar transações
            cursor.execute("SELECT cvm_code, company_name FROM companies LIMIT 15")
            companies = cursor.fetchall()
            
            transactions = []
            
            for company in companies:
                cvm_code, company_name = company
                
                # Cria algumas transações de exemplo
                for i in range(3):
                    insider_name = f"Diretor {i+1} - {company_name[:20]}"
                    position = ["CEO", "CFO", "Diretor"][i % 3]
                    transaction_type = ["Compra", "Venda"][i % 2]
                    quantity = 1000 + (i * 500)
                    unit_price = 25.0 + (i * 5)
                    total_value = quantity * unit_price
                    transaction_date = datetime.now() - timedelta(days=i*10)
                    
                    transactions.append((
                        cvm_code, company_name, 'CVM44', transaction_date, transaction_date,
                        'Ativo', '', 2024, insider_name, position, transaction_type,
                        quantity, unit_price, total_value, transaction_date, quantity, datetime.utcnow()
                    ))
            
            # Insere transações usando a estrutura correta da tabela
            cursor.executemany("""
                INSERT INTO insider_transactions (cvm_code, company_name, document_type, delivery_date, reference_date,
                                                status, download_url, year, insider_name, position, transaction_type,
                                                quantity, unit_price, total_value, transaction_date, remaining_position, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, transactions)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.logger.info(f"Criadas {len(transactions)} transações de insider de exemplo")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao criar transações de insider: {e}")
            return False
    
    def create_sample_news(self):
        """Cria notícias de exemplo"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            # Busca alguns tickers para associar às notícias
            cursor.execute("SELECT symbol FROM tickers LIMIT 10")
            tickers = cursor.fetchall()
            
            news_data = []
            
            for i, ticker_row in enumerate(tickers):
                ticker = ticker_row[0]
                
                # Cria algumas notícias para cada ticker
                for j in range(2):
                    news_id = f"news_{ticker}_{i}_{j}"
                    title = f"Análise de mercado: {ticker} apresenta resultados do {j+1}º trimestre"
                    summary = f"Resumo da análise de {ticker} para o trimestre"
                    content = f"A empresa {ticker} divulgou seus resultados financeiros, mostrando crescimento nas receitas e expansão de mercado. Os analistas recomendam acompanhar os próximos movimentos da companhia."
                    author = ["Analista 1", "Analista 2", "Analista 3"][j % 3]
                    published_at = datetime.now() - timedelta(days=i*2 + j)
                    url = f"https://example.com/news/{news_id}"
                    category = "Mercado"
                    impact_score = 0.5 + (j * 0.2)
                    related_tickers = json.dumps([ticker])
                    
                    news_data.append((
                        news_id, title, summary, content, author, published_at,
                        url, category, impact_score, related_tickers, datetime.utcnow()
                    ))
            
            # Insere notícias usando a estrutura correta
            cursor.executemany("""
                INSERT INTO news (news_id, title, summary, content, author, published_at, url, category, impact_score, related_tickers, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, news_data)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.logger.info(f"Criadas {len(news_data)} notícias de exemplo")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao criar notícias: {e}")
            return False
    
    def run_full_integration(self):
        """Executa integração completa"""
        self.logger.info("Iniciando integração completa do scraper...")
        
        steps = [
            ("Populando tickers", self.populate_tickers_table),
            ("Criando dados de mercado", self.create_sample_market_data),
            ("Criando dados financeiros", self.create_sample_financial_data),
            ("Criando transações de insider", self.create_sample_insider_transactions),
            ("Criando notícias", self.create_sample_news)
        ]
        
        results = {}
        
        for step_name, step_function in steps:
            self.logger.info(f"Executando: {step_name}")
            try:
                result = step_function()
                results[step_name] = "✅ Sucesso" if result else "❌ Falha"
            except Exception as e:
                results[step_name] = f"❌ Erro: {e}"
                self.logger.error(f"Erro em {step_name}: {e}")
        
        # Relatório final
        self.logger.info("Relatório de integração:")
        for step, result in results.items():
            self.logger.info(f"  {step}: {result}")
        
        return results

if __name__ == "__main__":
    service = ScraperIntegrationService()
    service.run_full_integration()

