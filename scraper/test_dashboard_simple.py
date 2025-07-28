#!/usr/bin/env python3
"""
Dashboard de teste simples para visualizar os dados coletados
"""

from flask import Flask, render_template, jsonify, request
import sys
sys.path.append('.')

from app import create_app, db
from models import Company, Quote, News
import logging
from datetime import datetime

# Create Flask app
app = create_app() 

@app.route('/')
def financial_dashboard():
    """Dashboard principal com todas as empresas B3"""
    with app.app_context():
        try:
            companies = db.session.query(Company).filter(
                Company.ticker.isnot(None)
            ).order_by(Company.ticker).all()
            
            logging.info(f"Found {len(companies)} companies")
            return render_template('financial_dashboard.html', companies=companies)
        except Exception as e:
            logging.error(f"Error loading companies: {str(e)}")
            return f"Error loading dashboard: {str(e)}"

@app.route('/api/company/<ticker>/complete-data')
def get_complete_company_data(ticker):
    """API para obter TODOS os dados coletados pelo scraper"""
    with app.app_context():
        try:
            company = db.session.query(Company).filter_by(ticker=ticker).first() 
            if not company:
                return jsonify({'success': False, 'message': 'Empresa não encontrada'})
            
            # Get data from services - simulate the 13 data points
            all_data = {
                'financial_statements': [
                    {
                        'year': 2023,
                        'document_type': 'DFP',
                        'net_revenue': 150000000,
                        'net_income': 25000000
                    },
                    {
                        'year': 2024,
                        'document_type': 'ITR',
                        'net_revenue': 180000000,
                        'net_income': 30000000
                    }
                ],
                'insider_transactions': [
                    {
                        'transaction_date': '2024-01-15',
                        'person_name': 'João Silva',
                        'transaction_type': 'Compra',
                        'quantity': 1000
                    },
                    {
                        'transaction_date': '2024-02-20',
                        'person_name': 'Maria Santos',
                        'transaction_type': 'Venda',
                        'quantity': 500
                    }
                ],
                'dividends': [
                    {
                        'ex_date': '2024-03-15',
                        'dividend_type': 'Dividendo',
                        'value_per_share': 2.50,
                        'status': 'Pago'
                    },
                    {
                        'ex_date': '2024-06-15',
                        'dividend_type': 'JCP',
                        'value_per_share': 1.80,
                        'status': 'Aprovado'
                    }
                ],
                'shareholding_composition': [
                    {
                        'shareholder_name': 'Acionista Controlador',
                        'shareholder_type': 'Pessoa Jurídica',
                        'ownership_percentage': 51.2,
                        'shares_quantity': 25600000
                    },
                    {
                        'shareholder_name': 'Minoritários',
                        'shareholder_type': 'Pulverizado',
                        'ownership_percentage': 48.8,
                        'shares_quantity': 24400000
                    }
                ],
                'administrators': [
                    {
                        'name': 'Carlos Eduardo',
                        'position': 'CEO',
                        'start_date': '2020-01-01',
                        'cpf': '***.***.***-**'
                    },
                    {
                        'name': 'Ana Carolina',
                        'position': 'CFO',
                        'start_date': '2021-03-15',
                        'cpf': '***.***.***-**'
                    }
                ],
                'general_meetings': [
                    {
                        'meeting_date': '2024-04-30',
                        'meeting_type': 'AGO',
                        'call_date': '2024-03-30',
                        'location': 'São Paulo - SP'
                    },
                    {
                        'meeting_date': '2024-12-15',
                        'meeting_type': 'AGE',
                        'call_date': '2024-11-15',
                        'location': 'Virtual'
                    }
                ],
                'related_parties': [
                    {
                        'party_name': 'Empresa Controlada',
                        'party_type': 'Subsidiária',
                        'relationship': 'Controlada',
                        'transaction_amount': 5000000
                    }
                ],
                'corporate_events': [
                    {
                        'event_date': '2024-05-20',
                        'event_type': 'Bonificação',
                        'description': 'Bonificação de 10%',
                        'status': 'Aprovado'
                    }
                ],
                'fundraising': [
                    {
                        'issuance_date': '2024-07-01',
                        'security_type': 'Debêntures',
                        'total_value': 100000000,
                        'quantity': 100000
                    }
                ],
                'regulatory_documents': [
                    {
                        'submission_date': '2024-03-31',
                        'document_type': 'ITR',
                        'category': 'Demonstrações Financeiras',
                        'version': '1.0'
                    }
                ],
                'market_data': [
                    {
                        'date': '2024-07-28',
                        'close_price': 25.50,
                        'volume': 1500000,
                        'change_percent': 2.5
                    },
                    {
                        'date': '2024-07-27',
                        'close_price': 24.90,
                        'volume': 1200000,
                        'change_percent': -1.2
                    }
                ],
                'calculated_indicators': [
                    {
                        'indicator_name': 'P/E Ratio',
                        'value': 15.2,
                        'period': '2024',
                        'calculation_date': '2024-07-28'
                    },
                    {
                        'indicator_name': 'ROE',
                        'value': 18.5,
                        'period': '2024',
                        'calculation_date': '2024-07-28'
                    }
                ]
            }
            
            return jsonify({
                'success': True,
                'company': {
                    'ticker': company.ticker,
                    'company_name': company.company_name,
                    'cvm_code': company.cvm_code,
                    'cnpj': getattr(company, 'cnpj', 'N/A')
                },
                'data': all_data
            })
            
        except Exception as e:
            logging.error(f"Error getting complete data for {ticker}: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Erro ao carregar dados: {str(e)}'
            })

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Ensure we have companies in database
    with app.app_context():
        try:
            count = db.session.query(Company).count()
            if count == 0:
                print("No companies found. Loading sample companies...")
                
                from run_cvm_etl import get_companies_dadosdemercado
                companies_data = get_companies_dadosdemercado()
                
                for i, (ticker, name, cvm_code) in enumerate(companies_data[:50]):  # Load first 50
                    try:
                        company = Company(
                            cvm_code=int(cvm_code) if cvm_code else i + 1000,
                            company_name=name,
                            ticker=ticker,
                            cnpj=f'00.000.{i:03d}/0001-00',
                            is_b3_listed=True,
                            is_active=True
                        )
                        db.session.add(company)
                    except Exception as e:
                        print(f"Skip {ticker}: {str(e)}")
                
                db.session.commit()
                print(f"Loaded companies into database")
            
            print(f"Dashboard ready with {count} companies")
            
        except Exception as e:
            print(f"Error preparing database: {str(e)}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)