#!/usr/bin/env python3
"""
Debug Scraper RAD CVM
Versão para debug e análise da resposta
"""

import requests
from bs4 import BeautifulSoup
import logging

def debug_rad_cvm():
    """Debug do portal RAD CVM"""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('DebugRADCVM')
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    base_url = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx"
    
    try:
        # 1. Carrega página inicial
        logger.info("1. Carregando página inicial...")
        response = session.get(base_url)
        logger.info(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error("Erro ao carregar página inicial")
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 2. Extrai campos hidden
        logger.info("2. Extraindo campos hidden...")
        form_data = {}
        hidden_inputs = soup.find_all('input', {'type': 'hidden'})
        
        for input_field in hidden_inputs:
            name = input_field.get('name')
            value = input_field.get('value', '')
            if name:
                form_data[name] = value
        
        logger.info(f"Campos hidden encontrados: {len(form_data)}")
        
        # 3. Monta parâmetros de busca simples (sem filtro de data)
        logger.info("3. Testando busca simples...")
        search_params = {
            '__VIEWSTATE': form_data.get('__VIEWSTATE', ''),
            '__VIEWSTATEGENERATOR': form_data.get('__VIEWSTATEGENERATOR', ''),
            '__EVENTVALIDATION': form_data.get('__EVENTVALIDATION', ''),
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            'ctl00$ContentPlaceHolder1$btnConsultar': 'Consultar'
        }
        
        # Adiciona outros campos hidden
        for key, value in form_data.items():
            if key not in search_params and key.startswith('ctl00'):
                search_params[key] = value
        
        # 4. Faz busca simples
        logger.info("4. Executando busca simples...")
        response = session.post(base_url, data=search_params, timeout=30)
        logger.info(f"Status da busca: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Erro na busca: {response.status_code}")
            return
        
        # 5. Analisa resposta
        logger.info("5. Analisando resposta...")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Salva HTML para análise
        with open('/home/ubuntu/rad_cvm_superscraper/debug_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        # Procura por tabelas
        tables = soup.find_all('table')
        logger.info(f"Tabelas encontradas: {len(tables)}")
        
        for i, table in enumerate(tables):
            rows = table.find_all('tr')
            if len(rows) > 3:
                logger.info(f"Tabela {i}: {len(rows)} linhas")
                
                # Mostra cabeçalho
                if rows:
                    header_cells = rows[0].find_all(['th', 'td'])
                    header_text = [cell.get_text().strip() for cell in header_cells]
                    logger.info(f"  Cabeçalho: {header_text}")
                    
                    # Se parece com tabela de documentos
                    if any('código' in text.lower() or 'empresa' in text.lower() for text in header_text):
                        logger.info(f"  *** Esta parece ser a tabela de documentos! ***")
                        
                        # Mostra algumas linhas de dados
                        for j, row in enumerate(rows[1:6]):  # Primeiras 5 linhas
                            cells = row.find_all('td')
                            if cells:
                                row_data = [cell.get_text().strip() for cell in cells]
                                logger.info(f"  Linha {j+1}: {row_data}")
        
        # Procura por mensagens de erro
        error_msgs = soup.find_all(string=lambda text: text and ('erro' in text.lower() or 'error' in text.lower()))
        if error_msgs:
            logger.warning(f"Mensagens de erro encontradas: {error_msgs}")
        
        # Procura por indicadores de resultados
        result_indicators = soup.find_all(string=lambda text: text and ('documento' in text.lower() or 'resultado' in text.lower()))
        if result_indicators:
            logger.info(f"Indicadores de resultado: {result_indicators[:5]}")
        
        logger.info("Debug concluído! Verifique o arquivo debug_response.html")
        
    except Exception as e:
        logger.error(f"Erro durante debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_rad_cvm()

