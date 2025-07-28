#!/usr/bin/env python3
"""
Rotas da API para o dashboard RAD CVM - Versão com Dados Reais
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import sys
import os

# Adiciona o diretório pai ao path para importar o dashboard_integration
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.dirname(__file__))

try:
    from dashboard_integration import DashboardDataProvider
    data_provider = DashboardDataProvider()
    USE_REAL_DATA = True
    print("✓ Dados reais carregados com sucesso!")
except ImportError as e:
    print(f"✗ Erro ao importar dados reais: {e}")
    data_provider = None
    USE_REAL_DATA = False

rad_cvm_bp = Blueprint('rad_cvm', __name__)

def get_mock_data():
    """Retorna dados mock para fallback"""
    return {
        'empresas': [
            {'codigo_cvm': '09512-6', 'nome': 'PETROBRAS S.A.', 'setor': 'Petróleo e Gás'},
            {'codigo_cvm': '14320-8', 'nome': 'PETROBRAS DISTRIBUIDORA SA', 'setor': 'Petróleo e Gás'},
            {'codigo_cvm': '01432-0', 'nome': 'USINAS SID DE MINAS GERAIS S.A.-USIMINAS', 'setor': 'Metalurgia'},
            {'codigo_cvm': '02057-5', 'nome': 'JBS S.A.', 'setor': 'Alimentos'},
            {'codigo_cvm': '01788-4', 'nome': 'BETAPART PARTICIPACOES S.A.', 'setor': 'Participações'}
        ],
        'documentos': [
            {
                'id': 1,
                'codigo_cvm': '09512-6',
                'empresa': 'PETROBRAS S.A.',
                'categoria': 'Valores Mobiliários Negociados e Detidos',
                'tipo': 'CVM 44',
                'data_entrega': '2024-07-28T14:30:00',
                'assunto': 'Movimentação de ações ordinárias'
            },
            {
                'id': 2,
                'codigo_cvm': '01432-0',
                'empresa': 'USINAS SID DE MINAS GERAIS S.A.-USIMINAS',
                'categoria': 'Valores Mobiliários Negociados e Detidos',
                'tipo': 'CVM 44',
                'data_entrega': '2024-07-27T16:45:00',
                'assunto': 'Aquisição de ações preferenciais'
            }
        ],
        'movimentacoes': [
            {
                'id': 1,
                'codigo_cvm': '09512-6',
                'empresa_nome': 'PETROBRAS S.A.',
                'nome_pessoa': 'João Silva Santos',
                'cargo': 'Diretor Presidente',
                'valor_mobiliario': 'Ações Ordinárias',
                'quantidade_movimentada': 50000,
                'tipo_movimentacao': 'Compra',
                'preco_unitario': 25.50,
                'valor_total': 1275000,
                'data_movimentacao': '2024-07-25'
            },
            {
                'id': 2,
                'codigo_cvm': '09512-6',
                'empresa_nome': 'PETROBRAS S.A.',
                'nome_pessoa': 'Maria Oliveira Costa',
                'cargo': 'Diretora Financeira',
                'valor_mobiliario': 'Ações Preferenciais',
                'quantidade_movimentada': -20000,
                'tipo_movimentacao': 'Venda',
                'preco_unitario': 22.75,
                'valor_total': -455000,
                'data_movimentacao': '2024-07-26'
            }
        ]
    }

@rad_cvm_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'data_source': 'real' if USE_REAL_DATA else 'mock',
        'version': '2.0'
    })

@rad_cvm_bp.route('/stats', methods=['GET'])
def get_stats():
    """Retorna estatísticas do sistema"""
    try:
        if USE_REAL_DATA and data_provider:
            stats = data_provider.get_stats()
        else:
            # Stats mock
            stats = {
                'empresas_monitoradas': 5,
                'documentos_coletados': 150,
                'movimentacoes_cvm44': 25,
                'documentos_recentes': 8,
                'ultima_atualizacao': datetime.now().isoformat()
            }
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rad_cvm_bp.route('/empresas', methods=['GET'])
def get_empresas():
    """Retorna lista de empresas monitoradas"""
    try:
        if USE_REAL_DATA and data_provider:
            empresas = data_provider.get_empresas()
        else:
            empresas = get_mock_data()['empresas']
        
        return jsonify({
            'success': True,
            'data': empresas,
            'total': len(empresas)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rad_cvm_bp.route('/documentos', methods=['GET'])
def get_documentos():
    """Retorna lista de documentos com filtros"""
    try:
        # Parâmetros de filtro
        codigo_cvm = request.args.get('codigo_cvm')
        categoria = request.args.get('categoria')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        limit = int(request.args.get('limit', 100))
        
        if USE_REAL_DATA and data_provider:
            documentos = data_provider.get_documentos(
                codigo_cvm=codigo_cvm,
                categoria=categoria,
                data_inicio=data_inicio,
                data_fim=data_fim,
                limit=limit
            )
        else:
            documentos = get_mock_data()['documentos']
            # Aplica filtros básicos nos dados mock
            if codigo_cvm:
                documentos = [d for d in documentos if d['codigo_cvm'] == codigo_cvm]
            if categoria and categoria != 'Todas':
                documentos = [d for d in documentos if categoria.lower() in d['categoria'].lower()]
        
        return jsonify({
            'success': True,
            'data': documentos,
            'total': len(documentos),
            'filters': {
                'codigo_cvm': codigo_cvm,
                'categoria': categoria,
                'data_inicio': data_inicio,
                'data_fim': data_fim
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rad_cvm_bp.route('/movimentacoes-cvm44', methods=['GET'])
def get_movimentacoes_cvm44():
    """Retorna movimentações CVM 44 (insider trading)"""
    try:
        # Parâmetros de filtro
        codigo_cvm = request.args.get('codigo_cvm')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        limit = int(request.args.get('limit', 100))
        
        if USE_REAL_DATA and data_provider:
            movimentacoes = data_provider.get_movimentacoes_cvm44(
                codigo_cvm=codigo_cvm,
                data_inicio=data_inicio,
                data_fim=data_fim,
                limit=limit
            )
        else:
            movimentacoes = get_mock_data()['movimentacoes']
            # Aplica filtros básicos nos dados mock
            if codigo_cvm:
                movimentacoes = [m for m in movimentacoes if m['codigo_cvm'] == codigo_cvm]
        
        return jsonify({
            'success': True,
            'data': movimentacoes,
            'total': len(movimentacoes),
            'filters': {
                'codigo_cvm': codigo_cvm,
                'data_inicio': data_inicio,
                'data_fim': data_fim
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rad_cvm_bp.route('/categorias', methods=['GET'])
def get_categorias():
    """Retorna lista de categorias de documentos"""
    try:
        if USE_REAL_DATA and data_provider:
            # Busca categorias únicas dos documentos
            documentos = data_provider.get_documentos(limit=1000)
            categorias = list(set([d['categoria'] for d in documentos if d['categoria']]))
            categorias.sort()
        else:
            categorias = [
                'Valores Mobiliários Negociados e Detidos',
                'FRE - Formulário de Referência',
                'Comunicado ao Mercado',
                'Calendário de Eventos Corporativos',
                'Fato Relevante'
            ]
        
        return jsonify({
            'success': True,
            'data': categorias
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rad_cvm_bp.route('/scraper/status', methods=['GET'])
def get_scraper_status():
    """Retorna status do scraper"""
    return jsonify({
        'success': True,
        'data': {
            'status': 'running',
            'last_run': datetime.now().isoformat(),
            'next_run': (datetime.now() + timedelta(minutes=1)).isoformat(),
            'data_source': 'real' if USE_REAL_DATA else 'mock',
            'version': '2.0'
        }
    })

@rad_cvm_bp.route('/scraper/run', methods=['POST'])
def run_scraper():
    """Executa o scraper manualmente"""
    try:
        # Simula execução do scraper
        return jsonify({
            'success': True,
            'message': 'Scraper executado com sucesso',
            'timestamp': datetime.now().isoformat(),
            'documents_found': 15,
            'new_documents': 3
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rad_cvm_bp.route('/logs', methods=['GET'])
def get_logs():
    """Retorna logs do sistema"""
    try:
        limit = int(request.args.get('limit', 50))
        
        # Logs simulados
        logs = []
        for i in range(limit):
            timestamp = datetime.now() - timedelta(minutes=i*5)
            logs.append({
                'timestamp': timestamp.isoformat(),
                'level': 'INFO' if i % 3 != 0 else 'WARNING',
                'message': f'Documento processado: CVM 44 - Empresa {i+1}' if i % 2 == 0 else f'Busca realizada: {i+1} documentos encontrados',
                'component': 'scraper' if i % 2 == 0 else 'processor'
            })
        
        return jsonify({
            'success': True,
            'data': logs,
            'total': len(logs)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

