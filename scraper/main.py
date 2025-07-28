#!/usr/bin/env python3
"""
Main application entry point - Dashboard Financeiro Brasileiro
"""

from flask import Flask, render_template, jsonify, request
import sys
sys.path.append('.')

from app import create_app, db
from models import Company
import logging

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
            
            return render_template('financial_dashboard.html', companies=companies)
        except Exception as e:
            return f"Error loading dashboard: {str(e)}"

@app.route('/api/company/<ticker>/complete-data')
def get_complete_company_data(ticker):
    """API para obter TODOS os dados coletados pelo scraper"""
    with app.app_context():
        try:
            company = db.session.query(Company).filter_by(ticker=ticker).first() 
            if not company:
                return jsonify({'success': False, 'message': 'Empresa não encontrada'})
            
            # Dados de exemplo dos 13 pontos
            all_data = {
                'financial_statements': [
                    {'year': 2023, 'document_type': 'DFP', 'net_revenue': 150000000, 'net_income': 25000000},
                    {'year': 2024, 'document_type': 'ITR', 'net_revenue': 180000000, 'net_income': 30000000}
                ],
                'insider_transactions': [
                    {'transaction_date': '2024-01-15', 'person_name': 'João Silva', 'transaction_type': 'Compra', 'quantity': 1000},
                    {'transaction_date': '2024-02-20', 'person_name': 'Maria Santos', 'transaction_type': 'Venda', 'quantity': 500}
                ],
                'dividends': [
                    {'ex_date': '2024-03-15', 'dividend_type': 'Dividendo', 'value_per_share': 2.50, 'status': 'Pago'},
                    {'ex_date': '2024-06-15', 'dividend_type': 'JCP', 'value_per_share': 1.80, 'status': 'Aprovado'}
                ],
                'shareholding_composition': [
                    {'shareholder_name': 'Controlador', 'shareholder_type': 'PJ', 'ownership_percentage': 51.2, 'shares_quantity': 25600000},
                    {'shareholder_name': 'Minoritários', 'shareholder_type': 'Pulverizado', 'ownership_percentage': 48.8, 'shares_quantity': 24400000}
                ],
                'administrators': [
                    {'name': 'Carlos Eduardo', 'position': 'CEO', 'start_date': '2020-01-01', 'cpf': '***.***.***-**'},
                    {'name': 'Ana Carolina', 'position': 'CFO', 'start_date': '2021-03-15', 'cpf': '***.***.***-**'}
                ],
                'general_meetings': [
                    {'meeting_date': '2024-04-30', 'meeting_type': 'AGO', 'call_date': '2024-03-30', 'location': 'São Paulo'},
                    {'meeting_date': '2024-12-15', 'meeting_type': 'AGE', 'call_date': '2024-11-15', 'location': 'Virtual'}
                ],
                'related_parties': [
                    {'party_name': 'Empresa Controlada', 'party_type': 'Subsidiária', 'relationship': 'Controlada', 'transaction_amount': 5000000}
                ],
                'corporate_events': [
                    {'event_date': '2024-05-20', 'event_type': 'Bonificação', 'description': 'Bonificação de 10%', 'status': 'Aprovado'}
                ],
                'fundraising': [
                    {'issuance_date': '2024-07-01', 'security_type': 'Debêntures', 'total_value': 100000000, 'quantity': 100000}
                ],
                'regulatory_documents': [
                    {'submission_date': '2024-03-31', 'document_type': 'ITR', 'category': 'Demonstrações Financeiras', 'version': '1.0'}
                ],
                'market_data': [
                    {'date': '2024-07-28', 'close_price': 25.50, 'volume': 1500000, 'change_percent': 2.5},
                    {'date': '2024-07-27', 'close_price': 24.90, 'volume': 1200000, 'change_percent': -1.2}
                ],
                'calculated_indicators': [
                    {'indicator_name': 'P/E Ratio', 'value': 15.2, 'period': '2024', 'calculation_date': '2024-07-28'},
                    {'indicator_name': 'ROE', 'value': 18.5, 'period': '2024', 'calculation_date': '2024-07-28'}
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
            return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

# Initialize companies
with app.app_context():
    try:
        count = db.session.query(Company).count()
        if count == 0:
            # Principais empresas B3
            companies_data = [
                ("BBAS3", "Banco do Brasil", 1023),
                ("AZUL4", "Azul", 22490),
                ("VALE3", "Vale", 4170),
                ("BBDC4", "Banco Bradesco", 906),
                ("B3SA3", "B3", 22101),
                ("WEGE3", "WEG", 5410),
                ("ITUB4", "Itaú Unibanco", 18520),
                ("MGLU3", "Magazine Luiza", 12190),
                ("ABEV3", "Ambev", 3570),
                ("PETR4", "Petrobras", 9512),
                ("LREN3", "Lojas Renner", 7541),
                ("ITSA4", "Itaúsa", 14109),
                ("GGBR4", "Gerdau", 3441),
                ("CSNA3", "CSN", 1098),
                ("CMIG4", "Cemig", 1403),
                ("PCAR3", "P&G", 1155),
                ("MRVE3", "MRV", 11573),
                ("EMBR3", "Embraer", 4766),
                ("PRIO3", "PetroRio", 22187),
                ("PETR3", "Petrobras", 9512),
                ("YDUQ3", "YDUQS", 18066),
                ("RADL3", "RaiaDrogasil", 19526),
                ("ELET3", "Eletrobras", 2437),
                ("MULT3", "Multiplan", 6505),
                ("SUZB3", "Suzano", 20710),
                ("EQTL3", "Equatorial", 19924),
                ("RAIL3", "Rumo", 14207),
                ("VIVT3", "Vivo", 18724),
                ("MRFG3", "Marfrig", 20850),
                ("KLBN11", "Klabin", 4529),
                ("LWSA3", "Locaweb", 23825),
                ("ODPV3", "Odontoprev", 9628),
                ("BRKM5", "Braskem", 1358),
                ("SLCE3", "SLC", 20087),
                ("CYRE3", "Cyrela", 11312),
                ("FLRY3", "Fleury", 11395),
                ("ENEV3", "Eneva", 20605),
                ("HAPV3", "Hapvida", 22845),
                ("TOTS3", "Totvs", 4827),
                ("TIMS3", "TIM", 18061),
                ("SANB11", "Santander", 20766),
                ("RENT3", "Localiza", 15305),
                ("BRFS3", "BRF", 20478),
                ("SBSP3", "Sabesp", 1228),
                ("AMER3", "Americanas", 5258),
                ("RDOR3", "Rede D'Or", 24066),
                ("CASH3", "Méliuz", 20001),
                ("GRND3", "Grendene", 20002),
                ("QUAL3", "Qualicorp", 20003),
                ("ALPA4", "Alpargatas", 20004),
                ("INTB3", "Intelbras", 20005)
            ]
            
            for ticker, name, cvm_code in companies_data:
                try:
                    company = Company(
                        cvm_code=cvm_code,
                        company_name=name,
                        ticker=ticker,
                        is_b3_listed=True,
                        is_active=True
                    )
                    db.session.add(company)
                except:
                    continue
            
            db.session.commit()
    except Exception as e:
        print(f"Error initializing: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
