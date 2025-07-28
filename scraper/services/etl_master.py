"""
ETL Master - Orquestrador de todos os scrapers e ETLs
Coordena a execução de todos os processos de extração de dados
"""
import logging
from datetime import datetime
import schedule
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from app import db, create_app
from services.scraper_cvm import CVMScraper
from services.scraper_bacen import BacenScraper  
from services.scraper_b3 import B3Scraper
from services.scraper_news import NewsScraper

logger = logging.getLogger(__name__)

class ETLMaster:
    def __init__(self):
        self.scrapers = {
            'cvm': CVMScraper(),
            'bacen': BacenScraper(),
            'b3': B3Scraper(),
            'news': NewsScraper()
        }
        
        self.execution_log = []
    
    def run_all_scrapers(self, parallel=True):
        """Executa todos os scrapers"""
        logger.info("Iniciando execução completa de todos os ETLs")
        start_time = datetime.utcnow()
        
        results = {}
        
        if parallel:
            # Execução paralela para melhor performance
            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_scraper = {
                    executor.submit(self.scrapers['cvm'].run_full_scraping): 'cvm',
                    executor.submit(self.scrapers['bacen'].run_full_scraping): 'bacen',
                    executor.submit(self.scrapers['b3'].run_full_scraping): 'b3',
                    executor.submit(self.scrapers['news'].run_full_scraping): 'news'
                }
                
                for future in as_completed(future_to_scraper):
                    scraper_name = future_to_scraper[future]
                    try:
                        result = future.result(timeout=300)  # 5 minutos timeout
                        results[scraper_name] = result
                        logger.info(f"Scraper {scraper_name} concluído: {result}")
                    except Exception as e:
                        logger.error(f"Erro no scraper {scraper_name}: {str(e)}")
                        results[scraper_name] = {'error': str(e)}
        else:
            # Execução sequencial
            for name, scraper in self.scrapers.items():
                try:
                    logger.info(f"Executando scraper: {name}")
                    result = scraper.run_full_scraping()
                    results[name] = result
                except Exception as e:
                    logger.error(f"Erro no scraper {name}: {str(e)}")
                    results[name] = {'error': str(e)}
        
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        # Log da execução
        execution_summary = {
            'start_time': start_time,
            'end_time': end_time,
            'execution_time_seconds': execution_time,
            'results': results,
            'success_count': len([r for r in results.values() if 'error' not in r]),
            'error_count': len([r for r in results.values() if 'error' in r])
        }
        
        self.execution_log.append(execution_summary)
        
        logger.info(f"ETL Master concluído em {execution_time:.2f}s")
        logger.info(f"Sucessos: {execution_summary['success_count']}, Erros: {execution_summary['error_count']}")
        
        return execution_summary
    
    def run_quick_update(self):
        """Executa atualização rápida (apenas dados mais importantes)"""
        logger.info("Executando atualização rápida")
        
        results = {}
        
        try:
            # 1. Cotações da B3 (tempo real)
            b3_result = self.scrapers['b3'].scrape_market_indicators()
            if b3_result:
                loaded = self.scrapers['b3'].load_quotes_to_db(b3_result)
                results['b3_quotes'] = {'loaded': loaded}
            
            # 2. Indicadores do BACEN (principais)
            selic_data = self.scrapers['bacen'].scrape_economic_series('432', days_back=30)  # SELIC
            usd_data = self.scrapers['bacen'].scrape_economic_series('1', days_back=30)     # USD/BRL
            
            all_indicators = selic_data + usd_data
            if all_indicators:
                loaded = self.scrapers['bacen'].load_indicators_to_db(all_indicators)
                results['bacen_indicators'] = {'loaded': loaded}
            
            # 3. Notícias mais recentes
            recent_news = []
            rss_news = self.scrapers['news'].scrape_rss_feeds()
            recent_news.extend(rss_news[:20])  # Top 20
            
            if recent_news:
                loaded = self.scrapers['news'].load_news_to_db(recent_news)
                results['news'] = {'loaded': loaded}
            
            logger.info(f"Atualização rápida concluída: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Erro na atualização rápida: {str(e)}")
            return {'error': str(e)}
    
    def run_companies_update(self):
        """Atualização específica de empresas (execução menos frequente)"""
        logger.info("Executando atualização de empresas")
        
        try:
            # Atualizar cadastro de empresas da CVM
            companies_data = self.scrapers['cvm'].scrape_companies_registry()
            companies_loaded = self.scrapers['cvm'].load_companies_to_db(companies_data)
            
            # Composição do Ibovespa
            ibov_composition = self.scrapers['b3'].scrape_ibovespa_composition()
            
            results = {
                'companies_loaded': companies_loaded,
                'ibov_composition': len(ibov_composition)
            }
            
            logger.info(f"Atualização de empresas concluída: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Erro na atualização de empresas: {str(e)}")
            return {'error': str(e)}
    
    def run_financial_statements_update(self):
        """Atualização de demonstrações financeiras (trimestral)"""
        logger.info("Executando atualização de demonstrações financeiras")
        
        try:
            # Demonstrações financeiras do ano atual
            statements_data = self.scrapers['cvm'].scrape_financial_statements()
            statements_loaded = self.scrapers['cvm'].load_financial_statements_to_db(statements_data)
            
            results = {
                'statements_loaded': statements_loaded
            }
            
            logger.info(f"Atualização de demonstrações concluída: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Erro na atualização de demonstrações: {str(e)}")
            return {'error': str(e)}
    
    def schedule_jobs(self):
        """Configura agendamento automático dos ETLs"""
        logger.info("Configurando agendamento de ETLs")
        
        # Atualização rápida a cada 15 minutos (horário comercial)
        schedule.every(15).minutes.do(self.run_quick_update)
        
        # Atualização completa diária às 6h
        schedule.every().day.at("06:00").do(self.run_all_scrapers)
        
        # Atualização de empresas semanal (domingos às 2h)
        schedule.every().sunday.at("02:00").do(self.run_companies_update)
        
        # Demonstrações financeiras mensalmente (dia 1 às 3h)
        schedule.every().month.do(self.run_financial_statements_update)
        
        logger.info("Agendamento configurado:")
        logger.info("- Atualização rápida: a cada 15 minutos")
        logger.info("- Atualização completa: diariamente às 6h")
        logger.info("- Empresas: domingos às 2h")
        logger.info("- Demonstrações: mensalmente")
    
    def run_scheduler(self):
        """Executa o agendador em loop"""
        logger.info("Iniciando agendador de ETLs")
        
        self.schedule_jobs()
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Verificar a cada minuto
            except KeyboardInterrupt:
                logger.info("Agendador interrompido")
                break
            except Exception as e:
                logger.error(f"Erro no agendador: {str(e)}")
                time.sleep(300)  # Aguardar 5 minutos em caso de erro
    
    def get_execution_status(self):
        """Retorna status das últimas execuções"""
        if not self.execution_log:
            return {'message': 'Nenhuma execução registrada'}
        
        latest = self.execution_log[-1]
        
        return {
            'last_execution': latest['end_time'].isoformat(),
            'execution_time': latest['execution_time_seconds'],
            'success_count': latest['success_count'],
            'error_count': latest['error_count'],
            'total_executions': len(self.execution_log),
            'scrapers_status': {
                name: 'success' if 'error' not in result else 'error'
                for name, result in latest['results'].items()
            }
        }
    
    def run_initial_data_load(self):
        """Executa carga inicial de dados"""
        logger.info("Executando carga inicial de dados - pode demorar alguns minutos")
        
        # 1. Primeiro carregar empresas
        logger.info("1/4 - Carregando empresas da CVM...")
        companies_result = self.run_companies_update()
        
        # 2. Indicadores econômicos
        logger.info("2/4 - Carregando indicadores do BACEN...")
        bacen_result = self.scrapers['bacen'].run_full_scraping()
        
        # 3. Cotações e dados de mercado
        logger.info("3/4 - Carregando dados da B3...")
        b3_result = self.scrapers['b3'].run_full_scraping()
        
        # 4. Notícias
        logger.info("4/4 - Carregando notícias...")
        news_result = self.scrapers['news'].run_full_scraping()
        
        initial_load_summary = {
            'companies': companies_result,
            'bacen': bacen_result,
            'b3': b3_result,
            'news': news_result,
            'completed_at': datetime.utcnow().isoformat()
        }
        
        logger.info("Carga inicial concluída!")
        logger.info(f"Resumo: {initial_load_summary}")
        
        return initial_load_summary

def run_etl_master():
    """Função principal para executar o ETL Master"""
    # Criar contexto da aplicação Flask
    app = create_app()
    
    with app.app_context():
        master = ETLMaster()
        
        # Executar carga inicial
        initial_result = master.run_initial_data_load()
        
        print("=" * 50)
        print("ETL MASTER - CARGA INICIAL CONCLUÍDA")
        print("=" * 50)
        print(f"Empresas carregadas: {initial_result['companies'].get('companies_loaded', 0)}")
        print(f"Indicadores BACEN: {initial_result['bacen'].get('indicators_loaded', 0)}")
        print(f"Cotações B3: {initial_result['b3'].get('quotes_loaded', 0)}")
        print(f"Notícias: {initial_result['news'].get('news_loaded', 0)}")
        print("=" * 50)
        
        return initial_result

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_etl_master()