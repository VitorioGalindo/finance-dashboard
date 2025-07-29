#!/usr/bin/env python3
"""
Script de Atualização de Dados
Mantém os dados do dashboard atualizados automaticamente
"""

import os
import sys
import logging
import schedule
import time
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import json

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class DataUpdater:
    """Atualizador automático de dados"""
    
    def __init__(self):
        self.db_config = {
            'host': 'cvm-insiders-db.cb2uq8cqs3dn.us-east-2.rds.amazonaws.com',
            'port': 5432,
            'database': 'postgres',
            'user': 'pandora',
            'password': 'Pandora337303$'
        }
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """Configura o logger"""
        logger = logging.getLogger('DataUpdater')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Handler para arquivo
            file_handler = logging.FileHandler('data_updater.log')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            # Handler para console
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
        return logger
    
    def get_db_connection(self):
        """Cria conexão com PostgreSQL"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            self.logger.error(f"Erro ao conectar no banco: {e}")
            return None
    
    def update_company_status(self):
        """Atualiza status das empresas"""
        self.logger.info("Iniciando atualização de status das empresas...")
        
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            # Marca empresas como inativas se não têm dados recentes
            cursor.execute("""
                UPDATE companies 
                SET is_active = false, updated_at = %s
                WHERE id NOT IN (
                    SELECT DISTINCT company_id 
                    FROM shareholders 
                    WHERE reference_date >= %s
                ) AND is_active = true
            """, (datetime.utcnow(), datetime.now() - timedelta(days=365)))
            
            updated_count = cursor.rowcount
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.logger.info(f"Status atualizado para {updated_count} empresas")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar status das empresas: {e}")
            return False
    
    def cleanup_old_data(self):
        """Remove dados antigos desnecessários"""
        self.logger.info("Iniciando limpeza de dados antigos...")
        
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            # Remove cotações muito antigas (mais de 2 anos)
            cutoff_date = datetime.now() - timedelta(days=730)
            cursor.execute("""
                DELETE FROM quotes 
                WHERE date < %s
            """, (cutoff_date,))
            
            quotes_deleted = cursor.rowcount
            
            # Remove logs de requisições antigas (mais de 30 dias)
            cursor.execute("""
                DELETE FROM request_logs 
                WHERE timestamp < %s
            """, (datetime.now() - timedelta(days=30),))
            
            logs_deleted = cursor.rowcount
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.logger.info(f"Removidas {quotes_deleted} cotações antigas e {logs_deleted} logs antigos")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza de dados: {e}")
            return False
    
    def update_market_indicators(self):
        """Atualiza indicadores de mercado"""
        self.logger.info("Atualizando indicadores de mercado...")
        
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Busca tickers ativos
            cursor.execute("""
                SELECT DISTINCT q.ticker 
                FROM quotes q
                JOIN tickers t ON q.ticker = t.symbol
                JOIN companies c ON t.company_id = c.id
                WHERE c.is_active = true
                AND q.date >= %s
            """, (datetime.now() - timedelta(days=30),))
            
            tickers = cursor.fetchall()
            
            indicators_updated = 0
            
            for ticker_row in tickers:
                ticker = ticker_row['ticker']
                
                # Calcula indicadores técnicos básicos
                cursor.execute("""
                    SELECT date, close_price, volume
                    FROM quotes 
                    WHERE ticker = %s 
                    AND date >= %s
                    ORDER BY date DESC 
                    LIMIT 200
                """, (ticker, datetime.now() - timedelta(days=200)))
                
                prices = cursor.fetchall()
                
                if len(prices) >= 20:
                    # Calcula SMA 20
                    sma_20 = sum([p['close_price'] for p in prices[:20]]) / 20
                    
                    # Calcula volatilidade (desvio padrão dos últimos 20 dias)
                    avg_price = sma_20
                    variance = sum([(p['close_price'] - avg_price) ** 2 for p in prices[:20]]) / 20
                    volatility = variance ** 0.5
                    
                    # Insere/atualiza indicadores
                    cursor.execute("""
                        INSERT INTO technical_indicators_new (ticker, date, sma_20, volatility, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (ticker, date) DO UPDATE SET
                            sma_20 = EXCLUDED.sma_20,
                            volatility = EXCLUDED.volatility
                    """, (ticker, datetime.now().date(), sma_20, volatility, datetime.utcnow()))
                    
                    indicators_updated += 1
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.logger.info(f"Indicadores atualizados para {indicators_updated} tickers")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar indicadores: {e}")
            return False
    
    def generate_daily_report(self):
        """Gera relatório diário do sistema"""
        self.logger.info("Gerando relatório diário...")
        
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Estatísticas gerais
            cursor.execute("SELECT COUNT(*) as total FROM companies WHERE is_active = true")
            active_companies = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM tickers")
            total_tickers = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM quotes WHERE date = CURRENT_DATE")
            today_quotes = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM insider_transactions WHERE DATE(created_at) = CURRENT_DATE")
            today_transactions = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM news WHERE DATE(created_at) = CURRENT_DATE")
            today_news = cursor.fetchone()['total']
            
            # Gera relatório
            report = {
                "date": datetime.now().isoformat(),
                "statistics": {
                    "active_companies": active_companies,
                    "total_tickers": total_tickers,
                    "today_quotes": today_quotes,
                    "today_transactions": today_transactions,
                    "today_news": today_news
                },
                "system_status": "healthy"
            }
            
            # Salva relatório
            report_filename = f"daily_report_{datetime.now().strftime('%Y%m%d')}.json"
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            conn.close()
            
            self.logger.info(f"Relatório diário salvo: {report_filename}")
            self.logger.info(f"Empresas ativas: {active_companies}, Tickers: {total_tickers}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório: {e}")
            return False
    
    def run_daily_maintenance(self):
        """Executa manutenção diária"""
        self.logger.info("=== INICIANDO MANUTENÇÃO DIÁRIA ===")
        
        tasks = [
            ("Atualização de status das empresas", self.update_company_status),
            ("Limpeza de dados antigos", self.cleanup_old_data),
            ("Atualização de indicadores", self.update_market_indicators),
            ("Geração de relatório diário", self.generate_daily_report)
        ]
        
        results = {}
        
        for task_name, task_function in tasks:
            self.logger.info(f"Executando: {task_name}")
            try:
                result = task_function()
                results[task_name] = "✅ Sucesso" if result else "❌ Falha"
            except Exception as e:
                results[task_name] = f"❌ Erro: {e}"
                self.logger.error(f"Erro em {task_name}: {e}")
        
        # Relatório de execução
        self.logger.info("=== RELATÓRIO DE MANUTENÇÃO ===")
        for task, result in results.items():
            self.logger.info(f"  {task}: {result}")
        
        self.logger.info("=== MANUTENÇÃO CONCLUÍDA ===")
        
        return results
    
    def run_scheduler(self):
        """Executa o agendador de tarefas"""
        self.logger.info("Iniciando agendador de tarefas...")
        
        # Agenda manutenção diária às 02:00
        schedule.every().day.at("02:00").do(self.run_daily_maintenance)
        
        # Agenda limpeza de dados a cada 6 horas
        schedule.every(6).hours.do(self.cleanup_old_data)
        
        # Agenda atualização de indicadores a cada 4 horas
        schedule.every(4).hours.do(self.update_market_indicators)
        
        self.logger.info("Agendador configurado. Aguardando execução...")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verifica a cada minuto

def main():
    """Função principal"""
    updater = DataUpdater()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "daily":
            updater.run_daily_maintenance()
        elif command == "cleanup":
            updater.cleanup_old_data()
        elif command == "indicators":
            updater.update_market_indicators()
        elif command == "report":
            updater.generate_daily_report()
        elif command == "schedule":
            updater.run_scheduler()
        else:
            print("Comandos disponíveis: daily, cleanup, indicators, report, schedule")
    else:
        # Executa manutenção diária por padrão
        updater.run_daily_maintenance()

if __name__ == "__main__":
    main()

