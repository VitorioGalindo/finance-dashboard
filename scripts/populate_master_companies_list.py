# scripts/populate_master_companies_list.py
import os
import sys
import re
import pandas as pd
import requests
import zipfile
import io
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Adiciona a pasta 'scraper' ao path para que possamos importar seus modelos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scraper')))
from models import Base, Company  # Importa a Base e o modelo Company

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

def normalize_company_name(name):
    """Limpa e padroniza o nome de uma empresa para facilitar a correspondência."""
    if not isinstance(name, str):
        return ""
    # Remove S.A, S/A, HOLDING, PARTICIPACOES, etc. para um matching mais flexível
    name = re.sub(r'\s+S\.A\.|\s+S/A|\s+SA', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+HOLDING|\s+PARTICIPACOES', '', name, flags=re.IGNORECASE)
    return name.strip().upper()

def get_reference_list():
    """Carrega a lista de tickers e nomes fornecida como um DataFrame."""
    print("Carregando a lista de referência de empresas...")
    
    # Seus dados, formatados como uma string CSV
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
"BEEF3","Minerva"
"CPLE6","Copel"
"CMIG4","Cemig"
"CVCB3","CVC"
"PCAR3","Grupo Pão de Açúcar"
"MRVE3","MRV"
"EMBR3","Embraer"
"RRRP3","3R Petroleum"
"BPAC11","Banco BTG Pactual"
"PRIO3","Prio"
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
"SBSP3","Sabesp"
"JHSF3","JHSF"
"VIVA3","Vivara"
"CAML3","Camil Alimentos"
"ARML3","Armac"
"RECV3","PetroRecôncavo"
"MYPK3","Iochpe-Maxion"
"SMTO3","São Martinho"
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
"SRNA3","Serena Energia"
"BPAN4","Banco Pan"
"GRND3","Grendene"
"ENGI11","Energisa"
"QUAL3","Qualicorp"
"BRSR6","Banrisul"
"PORT3","Wilson Sons"
"AZEV4","Azevedo & Travassos"
"LJQQ3","Lojas Quero-Quero"
"ALPA4","Alpargatas"
"INTB3","Intelbras"
"SAPR11","Sanepar"
"STBP3","Santos Brasil"
"TAEE11","Taesa"
"EZTC3","EZTEC"
"DIRR3","Direcional"
"KEPL3","Kepler Weber"
"MILS3","Mills"
"PSSA3","Porto Seguro"
"POSI3","Positivo"
"ONCO3","Oncoclínicas"
"SBFG3","Grupo SBF"
"OPCT3","OceanPact"
"TUPY3","Tupy"
"GUAR3","Guararapes"
"FRAS3","Fras-le"
"NEOE3","Neoenergia"
"JALL3","Jalles Machado"
"OIBR3","Oi"
"ORVR3","Orizon"
"IRBR3","IRB Brasil RE"
"TASA4","Taurus"
"EGIE3","Engie"
"MTRE3","Mitre Realty"
"MDIA3","M. Dias Branco"
"PLPL3","Plano&Plano"
"VULC3","Vulcabras"
"SEER3","Ser Educacional"
"EVEN3","Even"
"SOJA3","Boa Safra Sementes"
"ABCB4","Banco ABC Brasil"
"FESA4","Ferbasa"
"ENJU3","Enjoei"
"MELK3","Melnick"
"LIGT3","Light"
"MDNE3","Moura Dubeux"
"ALUP11","Alupar"
"PGMN3","Pague Menos"
"TFCO4","Track & Field"
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
"PNVL3","Dimed"
"LEVE3","Mahle Metal Leve"
"TRIS3","Trisul"
"LAVV3","Lavvi"
"FIQE3","Unifique"
"PTBL3","Portobello"
"PDGR3","PDG Realty"
"PRNR3","Priner"
"PMAM3","Paranapanema"
"BMOB3","Bemobi"
"CSED3","Cruzeiro do Sul Educacional"
"VITT3","Vittia"
"GFSA3","Gafisa"
"ETER3","Eternit"
"MEAL3","IMC Alimentação"
"DESK3","Desktop"
"AGRO3","BrasilAgro"
"SHUL4","Schulz"
"LPSB3","Lopes"
"VLID3","Valid"
"PFRM3","Profarma"
"UCAS3","Unicasa"
"AMAR3,"Lojas Marisa"
"UNIP6","Unipar"
"ROMI3","Indústrias ROMI"
"VIVR3","Viver"
"BRAP3","Bradespar"
"EUCA4","Eucatex"
"CSUD3","CSU Cardsystem"
"AGXY3","AgroGalaxy"
"LUPA3","Lupatech"
"ALLD3","Allied"
"DOTZ3","Dotz"
"TASA3","Taurus"
"BMEB4","Banco Mercantil do Brasil"
"BIOM3","Biomm"
"EPAR3","Embpar Participações"
"TELB4","Telebras"
"LOGN3","Log-In"
"HOOT4","Hotéis Othon"
"NUTR3","Nutriplant"
"BRSR3","Banrisul"
"EMAE4","EMAE"
"CLSC4","Celesc"
"BOBR4","Bombril"
"BAZA3","Banco da Amazônia"
"BEES3","Banestes"
"RSID3","Rossi Residencial"
"WLMM4","WLM"
"CGRA4","Grazziotin"
"TPIS3","Triunfo"
"RPMG3","Refinaria de Manguinhos"
"AVLL3","Alphaville"
"AFLT3","Afluente T"
"COCE5","Coelce"
"DTCY3","Dtcom"
"JFEN3","João Fortes"
"CGAS5","Comgás"
"MNDL3","Mundial"
"LUXM4","Trevisa"
"CEDO4","Cedro Têxtil"
"CTKA4","Karsten"
"FESA3","Ferbasa"
"PATI3","Panatlântica"
"HBTS5","Habitasul"
"NORD3","Nordon"
"GSHP3","General Shopping & Outlets"
"BNBR3","Banco do Nordeste"
"PEAB3","Participações Aliança da Bahia"
"ESTR4","Estrela"
"MWET4","Wetzel"
"""
    
    df = pd.read_csv(io.StringIO(csv_data))
    df['normalized_name'] = df['Nome'].apply(normalize_company_name)
    print(f"Carregadas {len(df)} empresas da lista de referência.")
    return df

def get_cvm_master_data():
    """Baixa e processa o arquivo de cadastro da CVM."""
    print("Baixando dados cadastrais da CVM...")
    url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        cvm_data = pd.read_csv(io.StringIO(response.content.decode('latin-1')), sep=';', dtype=str)
        cvm_data['normalized_name'] = cvm_data['DENOM_SOCIAL'].apply(normalize_company_name)
        print("Dados da CVM processados.")
        return cvm_data
    except Exception as e:
        print(f"ERRO ao baixar ou processar dados da CVM: {e}")
        return pd.DataFrame()

def run_etl():
    """Orquestra o processo de ETL para criar a lista mestra de empresas."""
    print("--- INICIANDO ETL DA LISTA MESTRA DE EMPRESAS ---")
    
    engine = create_engine(get_db_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # FASE 1: EXTRAÇÃO
        df_reference = get_reference_list()
        df_cvm = get_cvm_master_data()

        if df_reference.empty or df_cvm.empty:
            print("Não foi possível obter os dados de referência ou da CVM. Abortando.")
            return

        # FASE 2: TRANSFORMAÇÃO (ENRIQUECIMENTO)
        print("Enriquecendo dados com informações da CVM...")
        df_merged = pd.merge(df_reference, df_cvm, on='normalized_name', how='left')
        
        df_final = df_merged.dropna(subset=['CNPJ_CIA', 'CD_CVM']).drop_duplicates(subset=['Ticker'])
        print(f"{len(df_final)} empresas tiveram correspondência e foram enriquecidas com sucesso.")

        # FASE 3: CARGA
        print("Limpando a tabela 'companies' (e tabelas dependentes)...")
        session.execute(text("TRUNCATE TABLE public.companies RESTART IDENTITY CASCADE;"))
        
        print(f"Populando a tabela 'companies' com {len(df_final)} registros...")
        
        companies_to_load = []
        for _, row in df_final.iterrows():
            # Limpa o CNPJ para ter apenas dígitos
            cnpj_cleaned = ''.join(filter(str.isdigit, row['CNPJ_CIA']))
            
            companies_to_load.append({
                'cvm_code': int(row['CD_CVM']),
                'company_name': row['DENOM_SOCIAL'], # Usando o nome oficial da CVM
                'trade_name': row['Nome'], # Usando o nome mais amigável da lista de referência
                'cnpj': cnpj_cleaned,
                'b3_listing_segment': row.get('SEGMENTO'), # O .get() evita erros se a coluna não existir
                'is_b3_listed': True
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
