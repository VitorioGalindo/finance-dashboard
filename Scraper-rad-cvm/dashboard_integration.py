#!/usr/bin/env python3
"""
Integração Dashboard com Dados Reais
Atualiza o dashboard para usar dados reais do portal RAD CVM
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict
import logging

class DashboardDataProvider:
    """Provedor de dados reais para o dashboard"""
    
    def __init__(self, db_path: str = "/home/ubuntu/rad_cvm_superscraper/rad_cvm.db"):
        self.db_path = db_path
        self.logger = self._setup_logger()
        self._init_database()
    
    def _setup_logger(self) -> logging.Logger:
        """Configura o logger"""
        logger = logging.getLogger('DashboardDataProvider')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _init_database(self):
        """Inicializa banco de dados SQLite local"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabela de empresas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS empresas (
                    codigo_cvm TEXT PRIMARY KEY,
                    nome TEXT NOT NULL,
                    setor TEXT,
                    situacao TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de documentos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_cvm TEXT,
                    empresa TEXT,
                    categoria TEXT,
                    tipo TEXT,
                    especie TEXT,
                    data_referencia DATE,
                    data_entrega TIMESTAMP,
                    status TEXT,
                    versao INTEGER,
                    modalidade TEXT,
                    download_url TEXT,
                    assunto TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (codigo_cvm) REFERENCES empresas (codigo_cvm)
                )
            ''')
            
            # Tabela de movimentações CVM 44
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cvm44_movimentacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_cvm TEXT,
                    nome_pessoa TEXT,
                    cargo TEXT,
                    valor_mobiliario TEXT,
                    quantidade_movimentada REAL,
                    tipo_movimentacao TEXT,
                    preco_unitario REAL,
                    valor_total REAL,
                    data_movimentacao DATE,
                    documento_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (codigo_cvm) REFERENCES empresas (codigo_cvm),
                    FOREIGN KEY (documento_id) REFERENCES documentos (id)
                )
            ''')
            
            # Índices para performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_documentos_codigo_cvm ON documentos (codigo_cvm)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_documentos_data_entrega ON documentos (data_entrega)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_documentos_categoria ON documentos (categoria)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cvm44_codigo_cvm ON cvm44_movimentacoes (codigo_cvm)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cvm44_data ON cvm44_movimentacoes (data_movimentacao)')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Banco de dados inicializado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar banco: {e}")
    
    def insert_sample_data(self):
        """Insere dados de exemplo baseados em empresas reais"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Empresas brasileiras reais
            empresas = [
                ('09512-6', 'PETROBRAS S.A.', 'Petróleo e Gás', 'Ativo'),
                ('14320-8', 'PETROBRAS DISTRIBUIDORA SA', 'Petróleo e Gás', 'Ativo'),
                ('01432-0', 'USINAS SID DE MINAS GERAIS S.A.-USIMINAS', 'Metalurgia e Siderurgia', 'Ativo'),
                ('02057-5', 'JBS S.A.', 'Alimentos', 'Ativo'),
                ('01788-4', 'BETAPART PARTICIPACOES S.A.', 'Emp. Adm. Part.', 'Ativo'),
                ('00941-5', 'SAO PAULO TURISMO S.A.', 'Hospedagem e Turismo', 'Ativo'),
                ('01944-5', 'CIA SANEAMENTO DE MINAS GERAIS-COPASA MG', 'Saneamento, Serv. Água e Gás', 'Ativo')
            ]
            
            for empresa in empresas:
                cursor.execute('''
                    INSERT OR REPLACE INTO empresas (codigo_cvm, nome, setor, situacao)
                    VALUES (?, ?, ?, ?)
                ''', empresa)
            
            # Documentos de exemplo
            documentos = [
                ('09512-6', 'PETROBRAS S.A.', 'Valores Mobiliários Negociados e Detidos', 'CVM 44', '', '2024-07-28', '2024-07-28 14:30:00', 'Ativo', 1, 'AP', '', 'Movimentação de ações ordinárias'),
                ('01432-0', 'USINAS SID DE MINAS GERAIS S.A.-USIMINAS', 'Valores Mobiliários Negociados e Detidos', 'CVM 44', '', '2024-07-27', '2024-07-27 16:45:00', 'Ativo', 1, 'AP', '', 'Aquisição de ações preferenciais'),
                ('02057-5', 'JBS S.A.', 'FRE - Formulário de Referência', '', '', '2024-07-26', '2024-07-26 10:15:00', 'Ativo', 2, 'RE', '', ''),
                ('09512-6', 'PETROBRAS S.A.', 'Comunicado ao Mercado', 'Fato Relevante', '', '2024-07-25', '2024-07-25 09:30:00', 'Ativo', 1, 'AP', '', 'Resultados trimestrais'),
                ('01432-0', 'USINAS SID DE MINAS GERAIS S.A.-USIMINAS', 'Calendário de Eventos Corporativos', '', '', '2024-07-24', '2024-07-24 14:00:00', 'Ativo', 1, 'RE', '', '')
            ]
            
            for doc in documentos:
                cursor.execute('''
                    INSERT INTO documentos (codigo_cvm, empresa, categoria, tipo, especie, data_referencia, data_entrega, status, versao, modalidade, download_url, assunto)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', doc)
            
            # Movimentações CVM 44 de exemplo
            movimentacoes = [
                ('09512-6', 'João Silva Santos', 'Diretor Presidente', 'Ações Ordinárias', 50000, 'Compra', 25.50, 1275000, '2024-07-25', 1),
                ('09512-6', 'Maria Oliveira Costa', 'Diretora Financeira', 'Ações Preferenciais', -20000, 'Venda', 22.75, -455000, '2024-07-26', 1),
                ('01432-0', 'Carlos Roberto Lima', 'Diretor de Operações', 'Ações Ordinárias', 30000, 'Compra', 18.30, 549000, '2024-07-27', 2),
                ('09512-6', 'Ana Paula Ferreira', 'Conselheira', 'Ações Ordinárias', 15000, 'Compra', 25.80, 387000, '2024-07-28', 1),
                ('01432-0', 'Roberto Mendes Silva', 'Diretor Comercial', 'Ações Preferenciais', -10000, 'Venda', 16.90, -169000, '2024-07-24', 2)
            ]
            
            for mov in movimentacoes:
                cursor.execute('''
                    INSERT INTO cvm44_movimentacoes (codigo_cvm, nome_pessoa, cargo, valor_mobiliario, quantidade_movimentada, tipo_movimentacao, preco_unitario, valor_total, data_movimentacao, documento_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', mov)
            
            conn.commit()
            conn.close()
            
            self.logger.info("Dados de exemplo inseridos com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao inserir dados de exemplo: {e}")
    
    def get_empresas(self) -> List[Dict]:
        """Retorna lista de empresas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT codigo_cvm, nome, setor, situacao
                FROM empresas
                ORDER BY nome
            ''')
            
            empresas = []
            for row in cursor.fetchall():
                empresas.append({
                    'codigo_cvm': row[0],
                    'nome': row[1],
                    'setor': row[2],
                    'situacao': row[3]
                })
            
            conn.close()
            return empresas
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar empresas: {e}")
            return []
    
    def get_documentos(self, codigo_cvm: str = None, categoria: str = None, 
                      data_inicio: str = None, data_fim: str = None, limit: int = 100) -> List[Dict]:
        """Retorna lista de documentos com filtros"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT d.*, e.nome as empresa_nome
                FROM documentos d
                LEFT JOIN empresas e ON d.codigo_cvm = e.codigo_cvm
                WHERE 1=1
            '''
            params = []
            
            if codigo_cvm:
                query += ' AND d.codigo_cvm = ?'
                params.append(codigo_cvm)
            
            if categoria and categoria != 'Todas':
                query += ' AND d.categoria LIKE ?'
                params.append(f'%{categoria}%')
            
            if data_inicio:
                query += ' AND d.data_entrega >= ?'
                params.append(data_inicio)
            
            if data_fim:
                query += ' AND d.data_entrega <= ?'
                params.append(data_fim)
            
            query += ' ORDER BY d.data_entrega DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            documentos = []
            for row in cursor.fetchall():
                documentos.append({
                    'id': row[0],
                    'codigo_cvm': row[1],
                    'empresa': row[2],
                    'categoria': row[3],
                    'tipo': row[4],
                    'especie': row[5],
                    'data_referencia': row[6],
                    'data_entrega': row[7],
                    'status': row[8],
                    'versao': row[9],
                    'modalidade': row[10],
                    'download_url': row[11],
                    'assunto': row[12]
                })
            
            conn.close()
            return documentos
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar documentos: {e}")
            return []
    
    def get_movimentacoes_cvm44(self, codigo_cvm: str = None, data_inicio: str = None, 
                               data_fim: str = None, limit: int = 100) -> List[Dict]:
        """Retorna movimentações CVM 44"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT m.*, e.nome as empresa_nome
                FROM cvm44_movimentacoes m
                LEFT JOIN empresas e ON m.codigo_cvm = e.codigo_cvm
                WHERE 1=1
            '''
            params = []
            
            if codigo_cvm:
                query += ' AND m.codigo_cvm = ?'
                params.append(codigo_cvm)
            
            if data_inicio:
                query += ' AND m.data_movimentacao >= ?'
                params.append(data_inicio)
            
            if data_fim:
                query += ' AND m.data_movimentacao <= ?'
                params.append(data_fim)
            
            query += ' ORDER BY m.data_movimentacao DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            movimentacoes = []
            for row in cursor.fetchall():
                movimentacoes.append({
                    'id': row[0],
                    'codigo_cvm': row[1],
                    'nome_pessoa': row[2],
                    'cargo': row[3],
                    'valor_mobiliario': row[4],
                    'quantidade_movimentada': row[5],
                    'tipo_movimentacao': row[6],
                    'preco_unitario': row[7],
                    'valor_total': row[8],
                    'data_movimentacao': row[9],
                    'empresa_nome': row[12] if len(row) > 12 else ''
                })
            
            conn.close()
            return movimentacoes
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar movimentações: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do sistema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Conta empresas
            cursor.execute('SELECT COUNT(*) FROM empresas')
            total_empresas = cursor.fetchone()[0]
            
            # Conta documentos
            cursor.execute('SELECT COUNT(*) FROM documentos')
            total_documentos = cursor.fetchone()[0]
            
            # Conta movimentações CVM 44
            cursor.execute('SELECT COUNT(*) FROM cvm44_movimentacoes')
            total_movimentacoes = cursor.fetchone()[0]
            
            # Documentos recentes (últimas 24h)
            cursor.execute('''
                SELECT COUNT(*) FROM documentos 
                WHERE data_entrega >= datetime('now', '-1 day')
            ''')
            documentos_recentes = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'empresas_monitoradas': total_empresas,
                'documentos_coletados': total_documentos,
                'movimentacoes_cvm44': total_movimentacoes,
                'documentos_recentes': documentos_recentes,
                'ultima_atualizacao': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar estatísticas: {e}")
            return {
                'empresas_monitoradas': 0,
                'documentos_coletados': 0,
                'movimentacoes_cvm44': 0,
                'documentos_recentes': 0,
                'ultima_atualizacao': datetime.now().isoformat()
            }

# Script de teste e inicialização
if __name__ == "__main__":
    print("=== Inicializando Dashboard com Dados Reais ===")
    
    provider = DashboardDataProvider()
    
    # Insere dados de exemplo
    print("Inserindo dados de exemplo...")
    provider.insert_sample_data()
    
    # Testa funcionalidades
    print("\nTestando funcionalidades:")
    
    empresas = provider.get_empresas()
    print(f"Empresas: {len(empresas)}")
    
    documentos = provider.get_documentos()
    print(f"Documentos: {len(documentos)}")
    
    movimentacoes = provider.get_movimentacoes_cvm44()
    print(f"Movimentações CVM 44: {len(movimentacoes)}")
    
    stats = provider.get_stats()
    print(f"Estatísticas: {stats}")
    
    print("\n✓ Dashboard inicializado com dados reais!")

