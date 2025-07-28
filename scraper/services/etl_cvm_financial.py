"""
ETL para Dados Financeiros da CVM
Integra os scrapers avançados com o banco de dados
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from sqlalchemy.exc import IntegrityError

from app import db
from models import Company, CVMFinancialData, CVMDocument
from services.scraper_cvm_advanced import CVMAdvancedScraper
from services.scraper_rad_cvm import RADCVMScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CVMFinancialETL:
    """ETL para dados financeiros estruturados da CVM"""
    
    def __init__(self):
        self.cvm_scraper = CVMAdvancedScraper()
        self.rad_scraper = RADCVMScraper()
    
    def populate_companies_from_cvm(self, year: int = 2023) -> int:
        """Popula empresas usando dados da CVM"""
        try:
            logger.info(f"Populando empresas com dados da CVM - {year}")
            
            # Extrair dados básicos de todas as empresas
            companies_df = self.cvm_scraper.get_all_companies_basic_data(year)
            
            if companies_df.empty:
                logger.warning(f"Nenhuma empresa encontrada para {year}")
                return 0
            
            companies_created = 0
            
            for _, row in companies_df.iterrows():
                try:
                    cvm_code = int(row.get('CD_CVM', 0))
                    company_name = row.get('DENOM_CIA', 'Nome não informado')
                    
                    if cvm_code == 0:
                        continue
                    
                    # Verificar se empresa já existe
                    existing = Company.query.filter_by(cvm_code=cvm_code).first()
                    
                    if not existing:
                        # Criar nova empresa
                        company = Company(
                            cvm_code=cvm_code,
                            company_name=company_name,
                            trade_name=company_name,
                            cnpj=row.get('CNPJ_CIA', ''),
                            b3_sector=row.get('SETOR_ATIV', ''),
                            has_dfp_data=True,
                            last_dfp_year=year,
                            created_at=datetime.utcnow()
                        )
                        
                        db.session.add(company)
                        companies_created += 1
                        
                        if companies_created % 50 == 0:
                            db.session.commit()
                            logger.info(f"Criadas {companies_created} empresas...")
                    
                except Exception as e:
                    logger.warning(f"Erro ao processar empresa {row}: {str(e)}")
                    continue
            
            db.session.commit()
            logger.info(f"População concluída: {companies_created} empresas criadas")
            
            return companies_created
            
        except Exception as e:
            logger.error(f"Erro na população de empresas: {str(e)}")
            db.session.rollback()
            return 0
    
    def extract_company_financial_data(self, cvm_code: str, year: int = 2023) -> bool:
        """Extrai e armazena dados financeiros de uma empresa"""
        try:
            logger.info(f"Extraindo dados financeiros - CVM {cvm_code} - {year}")
            
            # Buscar empresa no banco
            company = Company.query.filter_by(cvm_code=int(cvm_code)).first()
            if not company:
                logger.warning(f"Empresa CVM {cvm_code} não encontrada no banco")
                return False
            
            # Extrair dados da CVM
            financial_data = self.cvm_scraper.extract_company_financial_data(cvm_code, year)
            
            if not financial_data:
                logger.warning(f"Nenhum dado financeiro extraído para CVM {cvm_code}")
                return False
            
            # Processar dados DFP
            if financial_data.get('dfp_data'):
                self._process_dfp_data(company, financial_data['dfp_data'], year)
            
            # Processar dados ITR
            if financial_data.get('itr_data'):
                self._process_itr_data(company, financial_data['itr_data'], year)
            
            # Processar dados FRE
            if financial_data.get('fre_data'):
                self._process_fre_data(company, financial_data['fre_data'], year)
            
            # Atualizar flags da empresa
            company.has_dfp_data = bool(financial_data.get('dfp_data'))
            company.has_itr_data = bool(financial_data.get('itr_data'))
            company.has_fre_data = bool(financial_data.get('fre_data'))
            company.last_dfp_year = year
            company.updated_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"Dados financeiros salvos para CVM {cvm_code}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados da empresa {cvm_code}: {str(e)}")
            db.session.rollback()
            return False
    
    def _process_dfp_data(self, company: Company, dfp_data: Dict[str, pd.DataFrame], year: int):
        """Processa dados DFP e salva no banco"""
        try:
            # Verificar se já existe registro DFP
            existing = CVMFinancialData.query.filter_by(
                company_id=company.id,
                cvm_code=company.cvm_code,
                statement_type='DFP',
                year=year
            ).first()
            
            if existing:
                logger.debug(f"DFP {company.cvm_code}-{year} já existe, atualizando...")
                financial_record = existing
            else:
                financial_record = CVMFinancialData(
                    company_id=company.id,
                    cvm_code=company.cvm_code,
                    statement_type='DFP',
                    year=year
                )
            
            # Extrair indicadores principais dos dados DFP
            financial_metrics = self._extract_financial_metrics(dfp_data)
            
            # Atualizar campos calculados
            financial_record.total_assets = financial_metrics.get('total_assets')
            financial_record.current_assets = financial_metrics.get('current_assets')
            financial_record.total_liabilities = financial_metrics.get('total_liabilities')
            financial_record.shareholders_equity = financial_metrics.get('shareholders_equity')
            financial_record.revenue = financial_metrics.get('revenue')
            financial_record.net_income = financial_metrics.get('net_income')
            financial_record.operating_cash_flow = financial_metrics.get('operating_cash_flow')
            
            # Salvar dados brutos como JSON
            financial_record.raw_dfp_data = {
                dataset_name: df.to_dict('records') 
                for dataset_name, df in dfp_data.items()
            }
            
            financial_record.updated_at = datetime.utcnow()
            
            if not existing:
                db.session.add(financial_record)
            
            logger.debug(f"DFP processado para {company.cvm_code}")
            
        except Exception as e:
            logger.error(f"Erro ao processar DFP {company.cvm_code}: {str(e)}")
    
    def _process_itr_data(self, company: Company, itr_data: Dict[str, pd.DataFrame], year: int):
        """Processa dados ITR (trimestrais)"""
        try:
            # ITR pode ter múltiplos trimestres
            quarters = ['1T', '2T', '3T', '4T']
            
            for quarter in quarters:
                # Filtrar dados do trimestre específico
                quarter_data = self._filter_by_quarter(itr_data, quarter, year)
                
                if not quarter_data:
                    continue
                
                # Verificar se já existe
                existing = CVMFinancialData.query.filter_by(
                    company_id=company.id,
                    cvm_code=company.cvm_code,
                    statement_type='ITR',
                    year=year,
                    quarter=quarter
                ).first()
                
                if existing:
                    financial_record = existing
                else:
                    financial_record = CVMFinancialData(
                        company_id=company.id,
                        cvm_code=company.cvm_code,
                        statement_type='ITR',
                        year=year,
                        quarter=quarter
                    )
                
                # Extrair métricas do trimestre
                metrics = self._extract_financial_metrics(quarter_data)
                
                financial_record.total_assets = metrics.get('total_assets')
                financial_record.revenue = metrics.get('revenue')
                financial_record.net_income = metrics.get('net_income')
                
                # Salvar dados brutos
                financial_record.raw_itr_data = {
                    dataset_name: df.to_dict('records') 
                    for dataset_name, df in quarter_data.items()
                }
                
                if not existing:
                    db.session.add(financial_record)
                
                logger.debug(f"ITR {quarter} processado para {company.cvm_code}")
            
        except Exception as e:
            logger.error(f"Erro ao processar ITR {company.cvm_code}: {str(e)}")
    
    def _process_fre_data(self, company: Company, fre_data: Dict[str, pd.DataFrame], year: int):
        """Processa dados FRE"""
        try:
            existing = CVMFinancialData.query.filter_by(
                company_id=company.id,
                cvm_code=company.cvm_code,
                statement_type='FRE',
                year=year
            ).first()
            
            if existing:
                financial_record = existing
            else:
                financial_record = CVMFinancialData(
                    company_id=company.id,
                    cvm_code=company.cvm_code,
                    statement_type='FRE',
                    year=year
                )
            
            # Salvar dados FRE brutos
            financial_record.raw_fre_data = {
                dataset_name: df.to_dict('records') 
                for dataset_name, df in fre_data.items()
            }
            
            if not existing:
                db.session.add(financial_record)
            
            logger.debug(f"FRE processado para {company.cvm_code}")
            
        except Exception as e:
            logger.error(f"Erro ao processar FRE {company.cvm_code}: {str(e)}")
    
    def _extract_financial_metrics(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """Extrai métricas financeiras principais dos dados brutos"""
        metrics = {}
        
        try:
            # Buscar dados do Balanço Patrimonial (BPA/BPP)
            bpa_data = None
            bpp_data = None
            dre_data = None
            dfc_data = None
            
            for dataset_name, df in data.items():
                if 'bpa' in dataset_name.lower():
                    bpa_data = df
                elif 'bpp' in dataset_name.lower():
                    bpp_data = df
                elif 'dre' in dataset_name.lower():
                    dre_data = df
                elif 'dfc' in dataset_name.lower():
                    dfc_data = df
            
            # Extrair métricas do BPA (Ativo)
            if bpa_data is not None and not bpa_data.empty:
                metrics['total_assets'] = self._find_account_value(bpa_data, ['Ativo Total', 'Total do Ativo'])
                metrics['current_assets'] = self._find_account_value(bpa_data, ['Ativo Circulante'])
                metrics['non_current_assets'] = self._find_account_value(bpa_data, ['Ativo Não Circulante'])
            
            # Extrair métricas do BPP (Passivo)  
            if bpp_data is not None and not bpp_data.empty:
                metrics['total_liabilities'] = self._find_account_value(bpp_data, ['Passivo Total', 'Total do Passivo'])
                metrics['current_liabilities'] = self._find_account_value(bpp_data, ['Passivo Circulante'])
                metrics['shareholders_equity'] = self._find_account_value(bpp_data, ['Patrimônio Líquido'])
            
            # Extrair métricas da DRE
            if dre_data is not None and not dre_data.empty:
                metrics['revenue'] = self._find_account_value(dre_data, ['Receita de Venda', 'Receita Operacional'])
                metrics['net_income'] = self._find_account_value(dre_data, ['Lucro Líquido', 'Resultado Líquido'])
                metrics['gross_profit'] = self._find_account_value(dre_data, ['Resultado Bruto', 'Lucro Bruto'])
            
            # Extrair métricas do DFC
            if dfc_data is not None and not dfc_data.empty:
                metrics['operating_cash_flow'] = self._find_account_value(dfc_data, ['Fluxo de Caixa Operacional'])
            
        except Exception as e:
            logger.warning(f"Erro ao extrair métricas financeiras: {str(e)}")
        
        return metrics
    
    def _find_account_value(self, df: pd.DataFrame, account_names: List[str]) -> Optional[float]:
        """Busca valor de uma conta específica no DataFrame"""
        try:
            value_columns = ['VL_CONTA', 'VALOR', 'VL_EXERCICIO']
            name_columns = ['DS_CONTA', 'CONTA', 'DESCRICAO']
            
            for name_col in name_columns:
                if name_col not in df.columns:
                    continue
                    
                for account_name in account_names:
                    mask = df[name_col].str.contains(account_name, case=False, na=False)
                    matches = df[mask]
                    
                    if not matches.empty:
                        for value_col in value_columns:
                            if value_col in matches.columns:
                                value = matches[value_col].iloc[0]
                                if pd.notna(value):
                                    return float(value)
                                    
        except Exception as e:
            logger.debug(f"Erro ao buscar conta {account_names}: {str(e)}")
        
        return None
    
    def _filter_by_quarter(self, data: Dict[str, pd.DataFrame], quarter: str, year: int) -> Dict[str, pd.DataFrame]:
        """Filtra dados por trimestre específico"""
        filtered_data = {}
        
        try:
            for dataset_name, df in data.items():
                # Buscar colunas de data/período
                date_columns = ['DT_REFER', 'DATA_REFERENCIA', 'DT_INI_EXERC', 'DT_FIM_EXERC']
                
                for date_col in date_columns:
                    if date_col in df.columns:
                        # Filtrar por ano e trimestre
                        df_copy = df.copy()
                        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
                        
                        # Filtrar por ano
                        year_mask = df_copy[date_col].dt.year == year
                        
                        # Filtrar por trimestre
                        if quarter == '1T':
                            quarter_mask = df_copy[date_col].dt.month <= 3
                        elif quarter == '2T':
                            quarter_mask = df_copy[date_col].dt.month <= 6
                        elif quarter == '3T':
                            quarter_mask = df_copy[date_col].dt.month <= 9
                        else:  # 4T
                            quarter_mask = df_copy[date_col].dt.month <= 12
                        
                        filtered_df = df_copy[year_mask & quarter_mask]
                        
                        if not filtered_df.empty:
                            filtered_data[dataset_name] = filtered_df
                            break
                        
        except Exception as e:
            logger.debug(f"Erro ao filtrar por trimestre {quarter}: {str(e)}")
        
        return filtered_data
    
    def batch_extract_top_companies(self, limit: int = 50, year: int = 2023) -> int:
        """Extrai dados das principais empresas em lote"""
        try:
            logger.info(f"Extraindo dados das top {limit} empresas - {year}")
            
            # Buscar empresas que ainda não têm dados financeiros
            companies = Company.query.filter_by(has_dfp_data=False).limit(limit).all()
            
            if not companies:
                logger.info("Todas as empresas já têm dados financeiros")
                return 0
            
            success_count = 0
            
            for i, company in enumerate(companies, 1):
                try:
                    logger.info(f"Processando {i}/{len(companies)}: {company.company_name} (CVM: {company.cvm_code})")
                    
                    success = self.extract_company_financial_data(str(company.cvm_code), year)
                    
                    if success:
                        success_count += 1
                    
                    # Delay entre empresas para não sobrecarregar os servidores da CVM
                    if i % 10 == 0:
                        logger.info(f"Processadas {i} empresas, {success_count} com sucesso")
                        import time
                        time.sleep(2)
                        
                except Exception as e:
                    logger.error(f"Erro ao processar empresa {company.company_name}: {str(e)}")
                    continue
            
            logger.info(f"Extração em lote concluída: {success_count}/{len(companies)} empresas processadas")
            return success_count
            
        except Exception as e:
            logger.error(f"Erro na extração em lote: {str(e)}")
            return 0
    
    def get_extraction_status(self) -> Dict[str, Any]:
        """Retorna status da extração de dados"""
        try:
            total_companies = Company.query.count()
            companies_with_dfp = Company.query.filter_by(has_dfp_data=True).count()
            companies_with_itr = Company.query.filter_by(has_itr_data=True).count()
            companies_with_fre = Company.query.filter_by(has_fre_data=True).count()
            
            total_financial_records = CVMFinancialData.query.count()
            dfp_records = CVMFinancialData.query.filter_by(statement_type='DFP').count()
            itr_records = CVMFinancialData.query.filter_by(statement_type='ITR').count()
            fre_records = CVMFinancialData.query.filter_by(statement_type='FRE').count()
            
            return {
                'companies': {
                    'total': total_companies,
                    'with_dfp': companies_with_dfp,
                    'with_itr': companies_with_itr,
                    'with_fre': companies_with_fre,
                    'dfp_coverage': round((companies_with_dfp / total_companies * 100), 2) if total_companies > 0 else 0
                },
                'financial_records': {
                    'total': total_financial_records,
                    'dfp': dfp_records,
                    'itr': itr_records,
                    'fre': fre_records
                },
                'last_updated': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter status: {str(e)}")
            return {}

# Função utilitária
def run_cvm_etl(year: int = 2023, limit: int = 50) -> Dict[str, Any]:
    """Executa ETL completo da CVM"""
    etl = CVMFinancialETL()
    
    results = {
        'started_at': datetime.utcnow(),
        'companies_populated': 0,
        'financial_data_extracted': 0,
        'errors': []
    }
    
    try:
        # 1. Popular empresas
        logger.info("Populando empresas da CVM...")
        companies_created = etl.populate_companies_from_cvm(year)
        results['companies_populated'] = companies_created
        
        # 2. Extrair dados financeiros
        logger.info("Extraindo dados financeiros...")
        financial_extracted = etl.batch_extract_top_companies(limit, year)
        results['financial_data_extracted'] = financial_extracted
        
        # 3. Status final
        results['final_status'] = etl.get_extraction_status()
        results['completed_at'] = datetime.utcnow()
        
        logger.info("ETL CVM concluído com sucesso!")
        return results
        
    except Exception as e:
        error_msg = f"Erro no ETL CVM: {str(e)}"
        logger.error(error_msg)
        results['errors'].append(error_msg)
        return results

if __name__ == "__main__":
    # Executar ETL
    results = run_cvm_etl(year=2023, limit=20)
    print(f"ETL Results: {results}")