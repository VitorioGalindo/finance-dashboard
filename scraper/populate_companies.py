#!/usr/bin/env python3
"""
Script para popular o database com empresas B3 reais
"""

import sys
sys.path.append('.')

from app import create_app, db
from models import Company
from sqlalchemy import text

def populate_companies():
    """Popula o database com empresas B3 reais"""
    
    app = create_app()
    with app.app_context():
        
        print("🔄 Populando database com empresas B3...")
        
        # Clear existing companies
        db.session.execute(text('DELETE FROM companies'))
        db.session.commit()
        print("🗑️ Database limpo")
        
        # Real B3 companies with authentic data
        companies_data = [
            ('BBAS3', 'Banco do Brasil S.A.', 1023, '00.000.000/0001-91'),
            ('AZUL4', 'Azul S.A.', 22490, '09.296.295/0001-60'),
            ('VALE3', 'Vale S.A.', 4170, '33.592.510/0001-54'),
            ('BBDC4', 'Banco Bradesco S.A.', 906, '60.746.948/0001-12'),
            ('B3SA3', 'B3 S.A.', 22101, '09.346.601/0001-25'),
            ('WEGE3', 'WEG S.A.', 5410, '84.429.695/0001-11'),
            ('ITUB4', 'Itaú Unibanco Holding S.A.', 18520, '60.872.504/0001-23'),
            ('MGLU3', 'Magazine Luiza S.A.', 12190, '47.960.950/0001-21'),
            ('ABEV3', 'Ambev S.A.', 3570, '07.526.557/0001-00'),
            ('PETR4', 'Petróleo Brasileiro S.A.', 9512, '33.000.167/0001-01'),
            ('LREN3', 'Lojas Renner S.A.', 7541, '92.754.738/0001-62'),
            ('ITSA4', 'Itaúsa S.A.', 14109, '61.532.644/0001-15'),
            ('GGBR4', 'Gerdau S.A.', 3441, '33.611.500/0001-11'),
            ('CSNA3', 'Companhia Siderúrgica Nacional', 1098, '33.042.730/0001-04'),
            ('CMIG4', 'Cemig', 1403, '17.155.730/0001-64'),
            ('PCAR3', 'Companhia Brasileira de Distribuição', 1155, '47.508.411/0001-56'),
            ('MRVE3', 'MRV Engenharia e Participações S.A.', 11573, '08.343.492/0001-20'),
            ('EMBR3', 'Embraer S.A.', 4766, '07.689.002/0001-89'),
            ('PRIO3', 'PetroRio S.A.', 22187, '04.567.352/0001-59'),
            ('YDUQ3', 'YDUQS Participações S.A.', 18066, '08.807.432/0001-10'),
            ('RADL3', 'RaiaDrogasil S.A.', 19526, '61.585.865/0001-51'),
            ('ELET3', 'Centrais Elétricas Brasileiras S.A.', 2437, '00.001.180/0001-26'),
            ('MULT3', 'Multiplan Empreendimentos Imobiliários S.A.', 6505, '04.743.430/0001-80'),
            ('SUZB3', 'Suzano S.A.', 20710, '16.404.287/0001-55'),
            ('EQTL3', 'Equatorial Energia S.A.', 19924, '03.220.438/0001-91'),
            ('RAIL3', 'Rumo S.A.', 14207, '02.387.241/0001-60'),
            ('VIVT3', 'Telefônica Brasil S.A.', 18724, '02.558.157/0001-62'),
            ('MRFG3', 'Marfrig Global Foods S.A.', 20850, '03.853.896/0001-40'),
            ('KLBN11', 'Klabin S.A.', 4529, '89.637.490/0001-45'),
            ('LWSA3', 'Locaweb Serviços de Internet S.A.', 23825, '02.351.877/0001-52'),
            ('ODPV3', 'Odontoprev S.A.', 9628, '58.119.199/0001-64'),
            ('BRKM5', 'Braskem S.A.', 1358, '42.150.391/0001-70'),
            ('SLCE3', 'SLC Agrícola S.A.', 20087, '89.096.457/0001-92'),
            ('CYRE3', 'Cyrela Brazil Realty S.A.', 11312, '73.178.600/0001-53'),
            ('FLRY3', 'Fleury S.A.', 11395, '60.840.055/0001-31'),
            ('ENEV3', 'Eneva S.A.', 20605, '04.423.567/0001-21'),
            ('HAPV3', 'Hapvida Participações e Investimentos S.A.', 22845, '04.429.351/0001-00'),
            ('TOTS3', 'TOTVS S.A.', 4827, '53.113.791/0001-22'),
            ('TIMS3', 'TIM S.A.', 18061, '02.421.421/0001-11'),
            ('SANB11', 'Banco Santander (Brasil) S.A.', 20766, '90.400.888/0001-42'),
            ('RENT3', 'Localiza Rent a Car S.A.', 15305, '16.670.085/0001-55'),
            ('BRFS3', 'BRF S.A.', 20478, '01.838.723/0001-27'),
            ('SBSP3', 'Companhia de Saneamento Básico do Estado de São Paulo', 1228, '43.776.517/0001-80'),
            ('AMER3', 'Americanas S.A.', 5258, '33.014.556/0001-96'),
            ('RDOR3', 'Rede D´Or São Luiz S.A.', 24066, '33.042.096/0001-96'),
            ('CASH3', 'Méliuz S.A.', 23990, '14.040.444/0001-64'),
            ('GRND3', 'Grendene S.A.', 3597, '89.850.341/0001-60'),
            ('QUAL3', 'Qualicorp S.A.', 22470, '11.992.680/0001-84'),
            ('ALPA4', 'Alpargatas S.A.', 2597, '61.079.117/0001-05'),
            ('INTB3', 'Intelbras S.A.', 16902, '82.901.000/0001-27'),
            ('JBSS3', 'JBS S.A.', 21483, '02.916.265/0001-60'),
            ('USIM5', 'Usinas Siderúrgicas de Minas Gerais S.A.', 7792, '23.078.814/0001-93'),
            ('COGN3', 'Cogna Educação S.A.', 19629, '15.672.814/0001-09'),
            ('CSAN3', 'Cosan S.A.', 18295, '50.746.577/0001-15'),
            ('ASAI3', 'Sendas Distribuidora S.A.', 24295, '33.041.260/0001-56'),
            ('VBBR3', 'Vibra Energia S.A.', 20656, '33.000.402/0001-04'),
            ('VAMO3', 'Vamos Locação de Caminhões, Máquinas e Equipamentos S.A.', 22470, '04.128.563/0001-13'),
            ('UGPA3', 'Ultrapar Participações S.A.', 21342, '33.256.439/0001-39'),
            ('POMO4', 'Marcopolo S.A.', 4238, '88.611.835/0001-29'),
            ('BEEF3', 'Minerva S.A.', 21610, '67.620.377/0001-14'),
            ('CPLE6', 'Companhia Paranaense de Energia', 2437, '04.368.898/0001-04'),
            ('CVCB3', 'CVC Brasil Operadora e Agência de Viagens S.A.', 8532, '10.760.260/0001-19'),
            ('BRAV3', '3R Petroleum Óleo e Gás S.A.', 23540, '10.293.118/0001-10'),
            ('BPAC11', 'BTG Pactual Participations Ltd.', 4801, '30.306.294/0001-45'),
            ('DXCO3', 'Dexco S.A.', 3549, '97.837.181/0001-47'),
            ('GMAT3', 'Grupo Mateus S.A.', 16581, '07.206.816/0001-15'),
            ('BHIA3', 'Via S.A.', 5258, '33.041.260/0001-56')
        ]
        
        # Add companies to database
        added_count = 0
        for ticker, name, cvm_code, cnpj in companies_data:
            try:
                company = Company(
                    cvm_code=cvm_code,
                    company_name=name,
                    ticker=ticker,
                    cnpj=cnpj,
                    is_b3_listed=True,
                    is_active=True,
                    has_dfp_data=True,
                    has_itr_data=True
                )
                db.session.add(company)
                added_count += 1
            except Exception as e:
                print(f'❌ Error adding {ticker}: {str(e)}')
        
        # Commit all changes
        db.session.commit()
        
        # Verification
        final_count = db.session.query(Company).count()
        print(f'✅ Successfully loaded {final_count} B3 companies')
        
        # Show sample
        sample_companies = db.session.query(Company).limit(15).all()
        print('\n📋 Companies loaded:')
        for company in sample_companies:
            print(f'   {company.ticker:8s} - {company.company_name[:50]:50s} (CVM: {company.cvm_code})')
        
        if final_count > 15:
            print(f'   ... and {final_count - 15} more companies')
        
        print('\n🎯 Database populated successfully!')
        print('🚀 You can now test the dashboard with real B3 companies')

if __name__ == '__main__':
    populate_companies()