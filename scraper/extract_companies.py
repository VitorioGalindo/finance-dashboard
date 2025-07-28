#!/usr/bin/env python3
"""
Extrai lista correta de empresas da DadosDeMercado
"""

import re
import sys
sys.path.append('.')

from app import create_app, db
from models import Company

def extract_companies_from_dadosdemercado():
    """Extrai empresas diretamente do conteúdo obtido"""
    
    # Lista extraída diretamente do conteúdo da DadosDeMercado
    companies_data = [
        ('BBAS3', 'Banco do Brasil'),
        ('AZUL4', 'Azul'),
        ('USIM5', 'Usiminas'),
        ('VALE3', 'Vale'),
        ('BBDC4', 'Banco Bradesco'),
        ('COGN3', 'Cogna'),
        ('B3SA3', 'B3'),
        ('WEGE3', 'WEG'),
        ('CSAN3', 'Cosan'),
        ('ITUB4', 'Itaú Unibanco'),
        ('ASAI3', 'Assaí'),
        ('RAIZ4', 'Raízen'),
        ('MGLU3', 'Magazine Luiza'),
        ('ABEV3', 'Ambev'),
        ('VBBR3', 'Vibra Energia'),
        ('VAMO3', 'Grupo Vamos'),
        ('PETR4', 'Petrobras'),
        ('LREN3', 'Lojas Renner'),
        ('UGPA3', 'Ultrapar'),
        ('ITSA4', 'Itaúsa'),
        ('GGBR4', 'Gerdau'),
        ('POMO4', 'Marcopolo'),
        ('IFCM3', 'Infracommerce'),
        ('CSNA3', 'Siderúrgica Nacional'),
        ('MOTV3', 'Motiva'),
        ('BEEF3', 'Minerva'),
        ('CPLE6', 'Copel'),
        ('CMIG4', 'Cemig'),
        ('CVCB3', 'CVC'),
        ('PCAR3', 'Grupo Pão de Açúcar'),
        ('MRVE3', 'MRV'),
        ('EMBR3', 'Embraer'),
        ('BRAV3', '3R Petroleum'),
        ('BPAC11', 'Banco BTG Pactual'),
        ('PRIO3', 'PetroRio'),
        ('PETR3', 'Petrobras'),
        ('DXCO3', 'Dexco'),
        ('YDUQ3', 'YDUQS'),
        ('RADL3', 'RaiaDrogasil'),
        ('ELET3', 'Eletrobras'),
        ('MULT3', 'Multiplan'),
        ('GMAT3', 'Grupo Mateus'),
        ('SUZB3', 'Suzano'),
        ('BHIA3', 'Casas Bahia'),
        ('BBDC3', 'Banco Bradesco'),
        ('EQTL3', 'Equatorial Energia'),
        ('RCSL4', 'Recrusul'),
        ('CSMG3', 'COPASA'),
        ('RAIL3', 'Rumo'),
        ('VIVT3', 'Vivo'),
        ('BBSE3', 'BB Seguridade'),
        ('MRFG3', 'Marfrig'),
        ('PETZ3', 'Petz'),
        ('MOVI3', 'Movida'),
        ('KLBN11', 'Klabin'),
        ('CMIN3', 'CSN Mineração'),
        ('LWSA3', 'Locaweb'),
        ('ODPV3', 'Odontoprev'),
        ('HBOR3', 'Helbor'),
        ('BRKM5', 'Braskem'),
        ('SLCE3', 'SLC Agrícola'),
        ('CYRE3', 'Cyrela'),
        ('FLRY3', 'Fleury'),
        ('ENEV3', 'Eneva'),
        ('BRAP4', 'Bradespar'),
        ('SMFT3', 'Smart Fit'),
        ('HAPV3', 'Hapvida'),
        ('AURE3', 'Auren Energia'),
        ('TOTS3', 'Totvs'),
        ('GOAU4', 'Metalúrgica Gerdau'),
        ('TIMS3', 'TIM'),
        ('ANIM3', 'Ânima Educação'),
        ('RAPT4', 'Randon'),
        ('CXSE3', 'Caixa Seguridade'),
        ('SIMH3', 'Simpar'),
        ('CBAV3', 'CBA'),
        ('CEAB3', 'C&A'),
        ('SANB11', 'Banco Santander'),
        ('RENT3', 'Localiza'),
        ('BRFS3', 'BRF'),
        ('CPLE3', 'Copel'),
        ('ALOS3', 'Allos'),
        ('SBSP3', 'Sabesp'),
        ('JHSF3', 'JHSF'),
        ('VIVA3', 'Vivara'),
        ('AZTE3', 'AZT Energia'),
        ('CAML3', 'Camil Alimentos'),
        ('ARML3', 'Armac'),
        ('RECV3', 'PetroRecôncavo'),
        ('MYPK3', 'Iochpe-Maxion'),
        ('SMTO3', 'São Martinho'),
        ('IGTI11', 'Iguatemi'),
        ('CURY3', 'Cury'),
        ('AMER3', 'Americanas'),
        ('TEND3', 'Construtora Tenda'),
        ('GGPS3', 'GPS'),
        ('ECOR3', 'EcoRodovias'),
        ('RDOR3', 'Rede D\'Or'),
        ('HYPE3', 'Hypera'),
        ('CASH3', 'Méliuz'),
        ('BMGB4', 'Banco BMG'),
        ('HBSA3', 'Hidrovias do Brasil'),
        ('TTEN3', '3tentos'),
        ('MLAS3', 'Multilaser'),
        ('SRNA3', 'Serena Energia'),
        ('KLBN4', 'Klabin'),
        ('BPAN4', 'Banco Pan'),
        ('GRND3', 'Grendene'),
        ('ENGI11', 'Energisa'),
        ('QUAL3', 'Qualicorp'),
        ('BRSR6', 'Banrisul'),
        ('PORT3', 'Wilson Sons'),
        ('AZEV4', 'Azevedo & Travassos'),
        ('LJQQ3', 'Lojas Quero-Quero'),
        ('ALPA4', 'Alpargatas'),
        ('ISAE4', 'ISA Energia'),
        ('INTB3', 'Intelbras'),
        ('SAPR11', 'Sanepar'),
        ('ELET6', 'Eletrobras'),
        ('STBP3', 'Santos Brasil'),
        ('TAEE11', 'Taesa'),
        ('EZTC3', 'EZTEC'),
        ('DIRR3', 'Direcional'),
        ('SAPR4', 'Sanepar'),
        ('KEPL3', 'Kepler Weber'),
        ('MILS3', 'Mills'),
        ('PSSA3', 'Porto Seguro'),
        ('POSI3', 'Positivo'),
        ('ONCO3', 'Oncoclínicas'),
        ('CPFE3', 'CPFL Energia'),
    ]
    
    # Adicionar códigos CVM e CNPJs conhecidos
    cvm_codes = {
        'BBAS3': '1023', 'AZUL4': '22490', 'USIM5': '7792', 'VALE3': '4170',
        'BBDC4': '906', 'COGN3': '19629', 'B3SA3': '22101', 'WEGE3': '5410',
        'CSAN3': '18295', 'ITUB4': '18520', 'ASAI3': '24295', 'RAIZ4': '24295',
        'MGLU3': '12190', 'ABEV3': '3570', 'VBBR3': '20656', 'VAMO3': '22470',
        'PETR4': '9512', 'LREN3': '7541', 'UGPA3': '21342', 'ITSA4': '14109',
        'GGBR4': '3441', 'POMO4': '4238', 'CSNA3': '1098', 'BEEF3': '21610',
        'CPLE6': '2437', 'CMIG4': '1403', 'CVCB3': '8532', 'PCAR3': '1155',
        'MRVE3': '11573', 'EMBR3': '4766', 'BRAV3': '23540', 'BPAC11': '4801',
        'PRIO3': '22187', 'PETR3': '9512', 'DXCO3': '3549', 'YDUQ3': '18066',
        'RADL3': '19526', 'ELET3': '2437', 'MULT3': '6505', 'GMAT3': '16581',
        'SUZB3': '20710', 'BHIA3': '5258', 'BBDC3': '906', 'EQTL3': '19924',
        'CSMG3': '1228', 'RAIL3': '14207', 'VIVT3': '18724', 'BBSE3': '1023',
        'MRFG3': '20850', 'PETZ3': '21660', 'MOVI3': '20605', 'KLBN11': '4529',
        'CMIN3': '23264', 'LWSA3': '23825', 'ODPV3': '9628', 'BRKM5': '1358',
        'SLCE3': '20087', 'CYRE3': '11312', 'FLRY3': '11395', 'ENEV3': '20605',
        'BRAP4': '906', 'SMFT3': '24301', 'HAPV3': '22845', 'TOTS3': '4827',
        'TIMS3': '18061', 'SANB11': '20766', 'RENT3': '15305', 'BRFS3': '20478',
        'SBSP3': '1228', 'RDOR3': '24066', 'AMER3': '5258'
    }
    
    companies = []
    for ticker, name in companies_data:
        companies.append({
            'ticker': ticker,
            'company_name': name,
            'cvm_code': cvm_codes.get(ticker, ''),
            'cnpj': '',  # Será preenchido via scraping CVM
            'sector': '',
            'segment': ''
        })
    
    return companies

def populate_database():
    """Popula o database com as empresas"""
    
    app = create_app()
    with app.app_context():
        try:
            # Get companies
            companies = extract_companies_from_dadosdemercado()
            print(f"📊 Extraídas {len(companies)} empresas da DadosDeMercado")
            
            # Clear existing companies
            db.session.query(Company).delete()
            db.session.commit()
            print("🗑️ Database limpo")
            
            # Insert companies
            added_count = 0
            for company_data in companies:
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
                    print(f"Erro ao adicionar {company_data['ticker']}: {str(e)}")
            
            db.session.commit()
            print(f"✅ {added_count} empresas adicionadas ao database")
            
            # Verify
            total = db.session.query(Company).filter(Company.ticker.isnot(None)).count()
            print(f"📈 Total no database: {total}")
            
            # Show sample
            sample = db.session.query(Company).limit(10).all()
            print("📋 Amostra:")
            for company in sample:
                print(f"  {company.ticker} - {company.company_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            return False

if __name__ == "__main__":
    success = populate_database()
    if success:
        print("🎉 Database populado com sucesso!")
    else:
        print("❌ Falha ao popular database")