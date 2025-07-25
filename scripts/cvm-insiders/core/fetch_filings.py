# scripts/cvm-insiders/core/fetch_filings.py
import requests
import zipfile
import io
import csv
import pandas as pd
from datetime import datetime
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# Importa a função de conexão com o DB centralizada
from .database import get_db
# Importa o modelo centralizado
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from backend.models import Filing, Company # Importa Company para verificar FK


def fetch_and_save_filings(start_year=2010, end_year=datetime.now().year):
    print("-- Iniciando a busca e salvamento de IPE filings --")
    anos_para_buscar = range(start_year, end_year + 1)

    for ano in anos_para_buscar:
        print(f"Processando ano: {ano}")
        try:
            url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_{ano}.zip"
            response = requests.get(url, timeout=180) # Aumentado timeout
            response.raise_for_status() # Levanta exceção para status codes ruins

            zip_buffer = io.BytesIO(response.content)
            with zipfile.ZipFile(zip_buffer) as z:
                for file_info in z.infolist():
                    if file_info.filename.endswith('.csv'):
                        print(f"  -> Processando arquivo: {file_info.filename}")
                        try:
                            with z.open(file_info.filename) as f:
                                # Lê o CSV, tratando possíveis erros de encoding ou linhas malformadas
                                df = pd.read_csv(f, sep=';', encoding='latin-1', low_memory=False, on_bad_lines='skip')
                                
                                # Garante nomes de coluna em minúsculas
                                df.columns = [col.lower() for col in df.columns]
                                
                                # Mapeamento de colunas do CSV para o modelo Filing
                                column_map = {
                                    'cnpj_companhia': 'company_cnpj',
                                    'data_referencia': 'reference_date',
                                    'protocolo_entrega': 'cvm_protocol',
                                    'link_download': 'pdf_url',
                                }
                                
                                # Renomeia e seleciona apenas as colunas que nos interessam
                                df_filings = df.rename(columns=column_map)[list(column_map.values())]
                                
                                # Converte datas e trata erros (coerce transforma inválidos em NaT)
                                df_filings['reference_date'] = pd.to_datetime(df_filings['reference_date'], errors='coerce').dt.date # Converte para date

                                # Remove linhas com datas inválidas ou CNPJs vazios
                                df_filings.dropna(subset=['reference_date', 'company_cnpj'], inplace=True)
                                
                                # Limpa CNPJ para apenas números
                                df_filings['company_cnpj'] = df_filings['company_cnpj'].astype(str).str.replace(r'D', '', regex=True)

                                # --- Insere no Banco de Dados usando a sessão centralizada ---
                                # Conecta ao DB usando o novo gerenciador de contexto
                                with get_db() as db_session:
                                    # Busca os CNPJs existentes para verificar Foreign Key antes de inserir
                                    # Isso evita erros de ForeignKey no banco e permite pular documentos de empresas não cadastradas
                                    existing_cnpjs = {c[0] for c in db_session.query(Company.cnpj).all()}
                                    
                                    # Filtra os filings para inserir apenas aqueles com CNPJs existentes
                                    filings_to_insert = df_filings[df_filings['company_cnpj'].isin(existing_cnpjs)]

                                    if filings_to_insert.empty:
                                        print("    -> Nenhum filing para inserir após filtrar CNPJs.")
                                        continue
                                        
                                    # Converte DataFrame para lista de objetos Filing
                                    # Trata duplicatas baseando-se no cvm_protocol antes de adicionar à sessão
                                    existing_protocols = {p[0] for p in db_session.query(Filing.cvm_protocol).filter(Filing.cvm_protocol.in_(filings_to_insert['cvm_protocol'].tolist())).all()}

                                    new_filings = []
                                    for index, row in filings_to_insert.iterrows():
                                        if row['cvm_protocol'] not in existing_protocols:
                                            new_filings.append(Filing(**row.to_dict()))

                                    if new_filings:
                                        db_session.bulk_save_objects(new_filings)
                                        try:
                                            db_session.commit()
                                            print(f"    -> Inseridos {len(new_filings)} novos filings.")
                                        except IntegrityError:
                                            db_session.rollback()
                                            print("    -> Erro de integridade ao comitar lote (possivelmente duplicatas), continuando...")
                                        except SQLAlchemyError as e:
                                             db_session.rollback()
                                             print(f"    -> Erro do SQLAlchemy ao comitar lote: {e}")
                                    else:
                                        print("    -> Nenhum novo filing para inserir (todos já existem ou CNPJ não encontrado).")

                        except FileNotFoundError:
                            print("     -> ERRO: Arquivo CSV dentro do ZIP não encontrado ou nome inesperado.")
                        except Exception as e:
                            print(f"     -> ERRO CRÍTICO ao processar o arquivo {file_info.filename}: {e}")

        except requests.exceptions.RequestException as e:
            print(f"  -> ERRO DE REDE ao baixar o ZIP do ano {ano}: {e}")
        except Exception as e:
            print(f"  -> ERRO DESCONHECIDO no processamento do ano {ano}: {e}")

    print("-- Busca e salvamento de IPE filings concluída --")

if __name__ == '__main__':
    fetch_and_save_filings()
