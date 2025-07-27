# core/acquisition.py

import requests
import json
import time
from datetime import date, timedelta
from typing import List, Dict, Any
from bs4 import BeautifulSoup

from .config import settings

def search_and_download_documents(start_date: date, end_date: date) -> List[Dict[str, Any]]:
    """
    Busca e baixa documentos IPE do portal CVM, enviando todos os tokens de estado ASP.NET necessários.
    """
    print(f"Iniciando busca por documentos IPE de {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")

    search_page_url = settings.CVM_PORTAL_URL
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    })

    downloaded_files_metadata = []

    try:
        # ETAPA 1: Fazer requisição GET para a página de busca para obter os tokens de estado
        print(f"Acessando a página de busca para obter tokens de estado: {search_page_url}")
        page_response = session.get(search_page_url, timeout=30)
        page_response.raise_for_status()

        # ETAPA 2: Usar BeautifulSoup para extrair todos os tokens necessários
        soup = BeautifulSoup(page_response.text, 'html.parser')
        
        viewstate = soup.find('input', {'id': '__VIEWSTATE'})
        viewstategenerator = soup.find('input', {'id': '__VIEWSTATEGENERATOR'})
        eventvalidation = soup.find('input', {'id': '__EVENTVALIDATION'})

        if not all([viewstate, viewstategenerator, eventvalidation]):
            print("ERRO CRÍTICO: Não foi possível encontrar os campos de estado ASP.NET (__VIEWSTATE, etc.).")
            return []

        # ETAPA 3: Montar o payload como um formulário, não como JSON
        # Esta é a mudança fundamental que alinha nossa requisição com o funcionamento do site
        form_data = {
            'rdPeriodo': '1',
            'txtDataIni': start_date.strftime('%d/%m/%Y'),
            'txtDataFim': end_date.strftime('%d/%m/%Y'),
            'txtEmpresa': '10.629.105/0001-68',
            'cboTipoDoc': '44', # IPE, conforme a pesquisa original
            'cboCategoria': '-1',
            'cboTipo': '-1',
            'cboEspecie': '-1',
            'txtPalavraChave': '',
            '__EVENTTARGET': 'btnConsulta', # Simula o clique no botão "Consultar"
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATE': viewstate['value'],
            '__VIEWSTATEGENERATOR': viewstategenerator['value'],
            '__EVENTVALIDATION': eventvalidation['value'],
        }
        
        session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': search_page_url,
        })
        
        # ETAPA 4: Fazer a requisição POST com os dados do formulário
        print("Enviando requisição POST com dados de formulário ASP.NET...")
        
        # A requisição agora é para a própria página, como um postback de formulário
        api_response = session.post(search_page_url, data=form_data, timeout=60)
        api_response.raise_for_status()

        # O resultado em postbacks de formulário geralmente está no HTML da resposta
        # Precisamos parsear novamente para encontrar os resultados
        result_soup = BeautifulSoup(api_response.text, 'html.parser')
        
        # A tabela de resultados tem um ID específico, 'grdDocumentos'
        result_table = result_soup.find('table', {'id': 'grdDocumentos'})
        
        if not result_table:
            print("Nenhum documento encontrado para o período.")
            return []
        
        rows = result_table.find_all('tr')
        documents = []
        for row in rows[1:]: # Pula o cabeçalho
            cols = row.find_all('td')
            if len(cols) > 2:
                # O protocolo está no link dentro da terceira coluna
                link = cols[2].find('a')
                if link and 'numProtocolo' in link.get('href', ''):
                    protocol_num = link['href'].split('numProtocolo=')[1].split('&')[0]
                    documents.append({'NumeroProtocolo': protocol_num})

        if not documents:
            print("Tabela de resultados encontrada, mas sem documentos.")
            return []

        print(f"SUCESSO! Encontrados {len(documents)} documentos. Iniciando download...")
        
        for doc in documents:
            protocol = doc.get('NumeroProtocolo')
            if not protocol: continue

            file_path = settings.DOWNLOAD_DIR / f"{protocol}.pdf"
            if file_path.exists():
                print(f"Arquivo {protocol}.pdf já existe. Pulando.")
                downloaded_files_metadata.append({"protocol": protocol, "path": file_path})
                continue

            pdf_response = session.get(settings.CVM_DOWNLOAD_URL, params={'Tela': 'ext', 'descTipo': 'IPE', 'CodigoInstituicao': 1, 'numProtocolo': protocol}, stream=True, timeout=120)
            pdf_response.raise_for_status()

            with open(file_path, 'wb') as f:
                for chunk in pdf_response.iter_content(chunk_size=8192): f.write(chunk)
            
            print(f"Salvo: {file_path}")
            downloaded_files_metadata.append({"protocol": protocol, "path": file_path})
            time.sleep(1)
            
        return downloaded_files_metadata

    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
        
    return downloaded_files_metadata