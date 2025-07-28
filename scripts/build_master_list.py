# scripts/build_master_list.py (CORRIGIDO)
import os
import sys
import pandas as pd
import io # <-- ADICIONADO AQUI
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# --- CONFIGURAÇÃO DE PATH ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scraper')))

# --- IMPORTAÇÕES ---
from models import Base, Company
from services.scraper_cvm_advanced import CVMAdvancedScraper

def get_db_connection_string():
    """Lê as credenciais do .env na raiz do projeto."""
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    dbname = os.getenv("DB_NAME", "postgres")
    if not all([user, password, host, dbname]):
        raise ValueError("Credenciais do banco de dados não encontradas.")
    return f"postgresql+psycopg2://{user}:{password}@{host}/{dbname}?sslmode=require"

def get_reference_tickers():
    """Carrega apenas o conjunto de tickers da sua lista de referência."""
    csv_data = """"Ticker","Nome"
"BBAS3","Banco do Brasil"
"AZUL4","Azul"
"USIM5","Usiminas"
"VALE3","Vale"
"BBDC4","Banco Bradesco"
"COGN3","Cogna"
"B3SA3","B3"
"WEGE3","WEG"
"CSAN3","Cosan"
"ITUB4","Itaú Unibanco"
"ASAI3","Assaí"
"RAIZ4","Raízen"
"MGLU3","Magazine Luiza"
"ABEV3","Ambev"
"VBBR3","Vibra Energia"
"VAMO3","Grupo Vamos"
"PETR4","Petrobras"
"LREN3","Lojas Renner"
"UGPA3","Ultrapar"
"ITSA4","Itaúsa"
"GGBR4","Gerdau"
"POMO4","Marcopolo"
"IFCM3","Infracommerce"
"CSNA3","Siderúrgica Nacional"
"MOTV3","Motiva"
"BEEF3","Minerva"
"CPLE6","Copel"
"CMIG4","Cemig"
"CVCB3","CVC"
"PCAR3","Grupo Pão de Açúcar"
"MRVE3","MRV"
"EMBR3","Embraer"
"BRAV3","3R Petroleum"
"BPAC11","Banco BTG Pactual"
"PRIO3","PetroRio"
"PETR3","Petrobras"
"DXCO3","Dexco"
"YDUQ3","YDUQS"
"RADL3","RaiaDrogasil"
"ELET3","Eletrobras"
"MULT3","Multiplan"
"GMAT3","Grupo Mateus"
"SUZB3","Suzano"
"BHIA3","Casas Bahia"
"BBDC3","Banco Bradesco"
"EQTL3","Equatorial Energia"
"RCSL4","Recrusul"
"CSMG3","COPASA"
"RAIL3","Rumo"
"VIVT3","Vivo"
"BBSE3","BB Seguridade"
"MRFG3","Marfrig"
"PETZ3","Petz"
"MOVI3","Movida"
"KLBN11","Klabin"
"CMIN3","CSN Mineração"
"LWSA3","Locaweb"
"ODPV3","Odontoprev"
"HBOR3","Helbor"
"BRKM5","Braskem"
"SLCE3","SLC Agrícola"
"CYRE3","Cyrela"
"FLRY3","Fleury"
"ENEV3","Eneva"
"BRAP4","Bradespar"
"SMFT3","Smart Fit"
"HAPV3","Hapvida"
"AURE3","Auren Energia"
"TOTS3","Totvs"
"GOAU4","Metalúrgica Gerdau"
"TIMS3","TIM"
"ANIM3","Ânima Educação"
"RAPT4","Randon"
"CXSE3","Caixa Seguridade"
"SIMH3","Simpar"
"CBAV3","CBA"
"CEAB3","C&A"
"SANB11","Banco Santander"
"RENT3","Localiza"
"BRFS3","BRF"
"CPLE3","Copel"
"ALOS3","Allos"
"SBSP3","Sabesp"
"JHSF3","JHSF"
"VIVA3","Vivara"
"AZTE3","AZT Energia"
"CAML3","Camil Alimentos"
"ARML3","Armac"
"RECV3","PetroRecôncavo"
"MYPK3","Iochpe-Maxion"
"SMTO3","São Martinho"
"IGTI11","Jereissati Participações"
"IGTI11","Iguatemi"
"CURY3","Cury"
"AMER3","Americanas"
"TEND3","Construtora Tenda"
"GGPS3","GPS"
"ECOR3","EcoRodovias"
"RDOR3","Rede D'Or"
"HYPE3","Hypera"
"CASH3","Méliuz"
"BMGB4","Banco BMG"
"HBSA3","Hidrovias do Brasil"
"TTEN3","3tentos"
"MLAS3","Multilaser"
"SRNA3","Serena Energia"
"KLBN4","Klabin"
"BPAN4","Banco Pan"
"GRND3","Grendene"
"ENGI11","Energisa"
"QUAL3","Qualicorp"
"BRSR6","Banrisul"
"PORT3","Wilson Sons"
"AZEV4","Azevedo & Travassos"
"LJQQ3","Lojas Quero-Quero"
"ALPA4","Alpargatas"
"ISAE4","ISA Energia"
"INTB3","Intelbras"
"SAPR11","Sanepar"
"ELET6","Eletrobras"
"STBP3","Santos Brasil"
"TAEE11","Taesa"
"EZTC3","EZTEC"
"DIRR3","Direcional"
"SAPR4","Sanepar"
"KEPL3","Kepler Weber"
"MILS3","Mills"
"PSSA3","Porto Seguro"
"POSI3","Positivo"
"ONCO3","Oncoclínicas"
"CPFE3","CPFL Energia"
"SBFG3","Grupo SBF"
"OPCT3","OceanPact"
"AZZA3","Arezzo"
"TUPY3","Tupy"
"GUAR3","Guararapes"
"FRAS3","Fras-le"
"NEOE3","Neoenergia"
"JALL3","Jalles Machado"
"HBRE3","HBR Realty"
"OIBR3","Oi"
"ORVR3","Orizon"
"DASA3","Dasa"
"VVEO3","Viveo"
"IRBR3","IRB Brasil RE"
"TASA4","Taurus"
"EGIE3","Engie"
"MTRE3","Mitre Realty"
"MDIA3","M. Dias Branco"
"PLPL3","Plano&Plano"
"VULC3","Vulcabras"
"SEER3","Ser Educacional"
"ITUB3","Itaú Unibanco"
"USIM3","Usiminas"
"POMO3","Marcopolo"
"EVEN3","Even"
"SOJA3","Boa Safra Sementes"
"ABCB4","Banco ABC Brasil"
"FESA4","Ferbasa"
"ENJU3","Enjoei"
"AZEV3","Azevedo & Travassos"
"MELK3","Melnick"
"LIGT3","Light"
"MDNE3","Moura Dubeux"
"ALUP11","Alupar"
"PGMN3","Pague Menos"
"TFCO4","Track & Field"
"VTRU3","VITRUBREPCOM"
"JSLG3","JSL"
"PINE4","Banco Pine"
"MATD3","Mater Dei"
"BLAU3","Blau Farmacêutica"
"RANI3","Irani"
"SYNE3","SYN"
"ESPA3","Espaçolaser"
"LOGG3","LOG CP"
"WIZC3","Wiz Soluções"
"ZAMP3","Zamp"
"TAEE4","Taesa"
"PNVL3","Dimed"
"LEVE3","Mahle Metal Leve"
"TRIS3","Trisul"
"LAVV3","Lavvi Incorporadora"
"FIQE3","Unifique"
"PTBL3","Portobello"
"PDGR3","PDG Realty"
"RNEW4","Renova Energia"
"BRBI11","BR Partners"
"KLBN3","Klabin"
"PRNR3","Priner"
"PMAM3","Paranapanema"
"BMOB3","Bemobi"
"CSED3","Cruzeiro do Sul Educacional"
"VITT3","Vittia"
"GFSA3","Gafisa"
"BRST3","Brisanet"
"ETER3","Eternit"
"RCSL3","Recrusul"
"SAPR3","Sanepar"
"MEAL3","IMC Alimentação"
"DESK3","Desktop"
"AGRO3","BrasilAgro"
"SHUL4","Schulz"
"LPSB3","Lopes"
"VLID3","Valid"
"PFRM3","Profarma"
"UCAS3","Unicasa"
"AMAR3","Lojas Marisa"
"UNIP6","Unipar"
"ROMI3","Indústrias ROMI"
"IGTI3","Iguatemi"
"IGTI3","Jereissati Participações"
"SEQL3","Sequoia Logística"
"TGMA3","Tegma"
"TAEE3","Taesa"
"CMIG3","Cemig"
"DEXP3","Dexxos"
"BRKM3","Braskem"
"AMBP3","Ambipar"
"TECN3","Technos"
"AERI3","Aeris Energy"
"ALPK3","Estapar"
"FICT3","Fictor Alimentos"
"OIBR4","Oi"
"WHRL4","Whirlpool"
"ITSA3","Itaúsa"
"RNEW3","Renova Energia"
"DMVF3","D1000 Varejo Farma"
"OFSA3","Ourofino Saúde Animal"
"LAND3","Terra Santa"
"TCSA3","Tecnisa"
"SANB3","Banco Santander"
"EALT4","Electro Aço Altona"
"VIVR3","Viver"
"BRAP3","Bradespar"
"EUCA4","Eucatex"
"SANB4","Banco Santander"
"CSUD3","CSU Cardsystem"
"AGXY3","AgroGalaxy"
"RAPT3","Randon"
"LUPA3","Lupatech"
"ALLD3","Allied"
"PTNT4","Pettenati"
"LVTC3","WDC Networks"
"AMOB3","Automob"
"DEXP4","Dexxos"
"TRAD3","Traders Club"
"SHOW3","Time For Fun"
"INEP3","Inepar"
"ALUP4","Alupar"
"AALR3","Alliança"
"WHRL3","Whirlpool"
"FHER3","Fertilizantes Heringer"
"NGRD3","Neogrid"
"DOTZ3","Dotz"
"VSTE3","LE LIS BLANC"
"TASA3","Taurus"
"BMEB4","Banco Mercantil do Brasil"
"BIOM3","Biomm"
"EPAR3","Embpar Participações"
"PINE3","Banco Pine"
"RSUL4","Metalúrgica Riosulense"
"TELB4","Telebras"
"GGBR3","Gerdau"
"LOGN3","Log-In"
"ENGI3","Energisa"
"HOOT4","Hotéis Othon"
"GOAU3","Metalúrgica Gerdau"
"NUTR3","Nutriplant"
"BRSR3","Banrisul"
"REAG3","REAG3"
"EMAE4","EMAE"
"CLSC4","Celesc"
"RNEW11","Renova Energia"
"BOBR4","Bombril"
"BAZA3","Banco da Amazônia"
"ATED3","ATOM EDUCAÇÃO E EDITORA S.A."
"BEES3","Banestes"
"RSID3","Rossi Residencial"
"ALUP3","Alupar"
"WLMM4","WLM"
"BAUH4","Excelsior"
"CCTY3","RDVC CITY"
"UNIP3","Unipar"
"BGIP4","Banese"
"CGRA4","Grazziotin"
"EALT3","Electro Aço Altona"
"PDTC3","Padtec"
"FRIO3","Metalfrio"
"CAMB3","Cambuci"
"ENGI4","Energisa"
"PTNT3","Pettenati"
"EQPA3","Equatorial Energia Pará"
"TPIS3","Triunfo"
"RPMG3","Refinaria de Manguinhos"
"AVLL3","Alphaville"
"AMAR11","Lojas Marisa"
"ISAE3","ISA Energia"
"CEBR6","CEB"
"WEST3","Westwing"
"BSLI4","Banco de Brasília"
"MGEL4","Mangels"
"INEP4","Inepar"
"LUPA11","LUPA11"
"MTSA4","Metisa"
"BEES4","Banestes"
"AZEV11","Azevedo & Travassos"
"BPAC5","Banco BTG Pactual"
"EQMA3B","Equatorial Maranhão"
"CEBR3","CEB"
"CEED3","CEEE D"
"CTSA3","Santanense"
"RDNI3","RNI"
"ENMT4","Energisa MT"
"MNPR3","Minupar"
"SCAR3","São Carlos"
"CRPG5","Tronox Pigmentos"
"CTSA4","Santanense"
"HAGA3","Haga"
"BPAC3","Banco BTG Pactual"
"REDE3","Rede Energia"
"HAGA4","Haga"
"EKTR4","Elektro"
"CEBR5","CEB"
"ALPA3","Alpargatas"
"AFLT3","Afluente T"
"COCE5","Coelce"
"CEDO3","Cedro Têxtil"
"DTCY3","Dtcom"
"JFEN3","João Fortes"
"CGAS5","Comgás"
"MNDL3","Mundial"
"BRSR5","Banrisul"
"LUXM4","Trevisa"
"PPLA11","PPLA"
"CGRA3","Grazziotin"
"TELB3","Telebras"
"IGTI4","Jereissati Participações"
"IGTI4","Iguatemi"
"BDLL3","Bardella"
"BDLL4","Bardella"
"DOHL4","Döhler"
"BIED3","BIED3"
"SNSY5","Sansuy"
"BMKS3","Monark"
"PSVM11","PORTO VM"
"BMEB3","Banco Mercantil do Brasil"
"OSXB3","OSX Brasil"
"CPLE5","Copel"
"CBEE3","Ampla Energia"
"BMIN4","Banco Mercantil de Investimentos"
"RPAD3","Alfa Holdings"
"NEXP3","Brasil Brokers"
"UNIP5","Unipar"
"GEPA4","Rio Paranapanema Energia"
"BSLI3","Banco de Brasília"
"MOAR3","Monteiro Aranha"
"BGIP3","Banese"
"BALM4","Baumer"
"CGAS3","Comgás"
"EUCA3","Eucatex"
"FIEI3","Fica"
"RPAD5","Alfa Holdings"
"MAPT3","Cemepe"
"CEEB3","COELBA"
"MAPT4","Cemepe"
"PEAB4","Participações Aliança da Bahia"
"EKTR3","Elektro"
"CRPG3","Tronox Pigmentos"
"TKNO3","Tekno"
"SOND5","Sondotécnica"
"MRSA5B","MRS Logística"
"CEDO4","Cedro Têxtil"
"CTKA4","Karsten"
"AHEB3","São Paulo Turismo"
"FESA3","Ferbasa"
"TKNO4","Tekno"
"PATI3","Panatlântica"
"HBTS5","Habitasul"
"SOND6","Sondotécnica"
"PINE11","Banco Pine"
"PLAS3","Plascar"
"ESTR4","Estrela"
"MWET4","Wetzel"
"PATI4","Panatlântica"
"NORD3","Nordon"
"GSHP3","General Shopping & Outlets"
"EQPA6","Equatorial Energia Pará"
"BRKM6","Braskem"
"BALM3","Baumer"
"CRPG6","Tronox Pigmentos"
"BNBR3","Banco do Nordeste"
"MRSA3B","MRS Logística"
"PEAB3","Participações Aliança da Bahia"
"MRSA6B","MRS Logística"
"CEEB5","COELBA"
"""
    df = pd.read_csv(io.StringIO(csv_data))
    return set(df['Ticker'].str.upper())

def run_etl():
    """Orquestra o processo de ETL para criar a lista mestra de empresas."""
    print("--- INICIANDO ETL DA LISTA MESTRA DE EMPRESAS (PROFISSIONAL) ---")
    
    engine = create_engine(get_db_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # FASE 1: EXTRAÇÃO
        reference_tickers = get_reference_tickers()
        
        print("Buscando dados da CVM usando o scraper avançado...")
        cvm_scraper = CVMAdvancedScraper()
        df_cad = cvm_scraper.get_cad_cia_aberta()
        df_fca = cvm_scraper.get_fca_valor_mobiliario()

        if df_cad.empty or df_fca.empty:
            print("Não foi possível obter os dados da CVM com o scraper. Abortando.")
            return

        # FASE 2: TRANSFORMAÇÃO (ENRIQUECIMENTO)
        print("Enriquecendo dados com informações da CVM...")
        
        df_fca_filtered = df_fca[df_fca['ticker'].str.upper().isin(reference_tickers)].copy()
        
        df_merged = pd.merge(df_cad, df_fca_filtered[['cnpj', 'ticker']], on='cnpj', how='inner')
        
        print("Agrupando tickers por empresa...")
        agg_funcs = {
            'ticker': (lambda x: sorted(list(x.unique()))),
            'company_name_cvm': 'first',
            'cvm_code': 'first',
            'sector': 'first',
            'main_activity': 'first',
            'website': 'first'
        }
        df_final_agg = df_merged.groupby('cnpj').agg(agg_funcs).reset_index()

        print(f"{len(df_final_agg)} empresas únicas foram encontradas e enriquecidas.")

        # FASE 3: CARGA
        print("Limpando a tabela 'companies' (e tabelas dependentes)...")
        session.execute(text("TRUNCATE TABLE public.companies RESTART IDENTITY CASCADE;"))
        
        print(f"Populando a tabela 'companies' com {len(df_final_agg)} registros...")
        
        companies_to_load = []
        for _, row in df_final_agg.iterrows():
            companies_to_load.append({
                'cnpj': row['cnpj'],
                'cvm_code': int(row['cvm_code']),
                'company_name': row['company_name_cvm'],
                'trade_name': row['company_name_cvm'],
                'is_b3_listed': True,
                'tickers': row['ticker'],
                'b3_sector': row.get('sector'),
                'main_activity': row.get('main_activity'),
                'website': row.get('website')
            })
        
        if companies_to_load:
            session.bulk_insert_mappings(Company, companies_to_load)

        session.commit()
        print("🎉 Tabela 'companies' populada com sucesso!")

    except Exception as e:
        print(f"❌ ERRO durante o ETL: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    run_etl()
