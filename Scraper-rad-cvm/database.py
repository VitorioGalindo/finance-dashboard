#!/usr/bin/env python3
"""
Módulo de banco de dados para o RAD CVM Superscraper
Gerencia conexões PostgreSQL e operações de dados
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
from datetime import datetime
import json

class DatabaseManager:
    """Gerenciador de banco de dados PostgreSQL"""
    
    def __init__(self):
        self.connection = None
        self.logger = logging.getLogger('DatabaseManager')
        
        # Configurações do banco (usar variáveis de ambiente)
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'rad_cvm_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password')
        }
    
    def connect(self) -> bool:
        """Conecta ao banco de dados"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.connection.autocommit = True
            self.logger.info("Conectado ao banco de dados PostgreSQL")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao conectar ao banco: {e}")
            return False
    
    def disconnect(self):
        """Desconecta do banco de dados"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("Desconectado do banco de dados")
    
    def create_tables(self):
        """Cria as tabelas necessárias"""
        tables_sql = [
            # Tabela de empresas
            """
            CREATE TABLE IF NOT EXISTS empresas (
                id SERIAL PRIMARY KEY,
                codigo_cvm VARCHAR(20) UNIQUE NOT NULL,
                nome VARCHAR(500) NOT NULL,
                setor VARCHAR(200),
                situacao VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            # Tabela de documentos
            """
            CREATE TABLE IF NOT EXISTS documentos (
                id SERIAL PRIMARY KEY,
                codigo_cvm VARCHAR(20) NOT NULL,
                empresa VARCHAR(500) NOT NULL,
                categoria VARCHAR(200),
                tipo VARCHAR(200),
                especie VARCHAR(200),
                data_referencia DATE,
                data_entrega TIMESTAMP,
                status VARCHAR(50),
                versao INTEGER,
                modalidade VARCHAR(10),
                download_url TEXT,
                arquivo_path TEXT,
                processado BOOLEAN DEFAULT FALSE,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (codigo_cvm) REFERENCES empresas(codigo_cvm)
            );
            """,
            
            # Tabela específica para documentos CVM 44 (insider trading)
            """
            CREATE TABLE IF NOT EXISTS cvm44_movimentacoes (
                id SERIAL PRIMARY KEY,
                documento_id INTEGER NOT NULL,
                codigo_cvm VARCHAR(20) NOT NULL,
                empresa VARCHAR(500) NOT NULL,
                nome_pessoa VARCHAR(500),
                cpf_cnpj VARCHAR(20),
                cargo VARCHAR(200),
                tipo_pessoa VARCHAR(50), -- Administrador, Controlador, etc.
                valor_mobiliario VARCHAR(200),
                quantidade_anterior DECIMAL(20,2),
                quantidade_atual DECIMAL(20,2),
                quantidade_movimentada DECIMAL(20,2),
                tipo_movimentacao VARCHAR(100), -- Compra, Venda, etc.
                preco_unitario DECIMAL(20,4),
                valor_total DECIMAL(20,2),
                data_movimentacao DATE,
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (documento_id) REFERENCES documentos(id),
                FOREIGN KEY (codigo_cvm) REFERENCES empresas(codigo_cvm)
            );
            """,
            
            # Índices para performance
            """
            CREATE INDEX IF NOT EXISTS idx_documentos_codigo_cvm ON documentos(codigo_cvm);
            CREATE INDEX IF NOT EXISTS idx_documentos_data_entrega ON documentos(data_entrega);
            CREATE INDEX IF NOT EXISTS idx_documentos_tipo ON documentos(tipo);
            CREATE INDEX IF NOT EXISTS idx_cvm44_codigo_cvm ON cvm44_movimentacoes(codigo_cvm);
            CREATE INDEX IF NOT EXISTS idx_cvm44_data_movimentacao ON cvm44_movimentacoes(data_movimentacao);
            CREATE INDEX IF NOT EXISTS idx_cvm44_nome_pessoa ON cvm44_movimentacoes(nome_pessoa);
            """
        ]
        
        try:
            cursor = self.connection.cursor()
            for sql in tables_sql:
                cursor.execute(sql)
            cursor.close()
            self.logger.info("Tabelas criadas com sucesso")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao criar tabelas: {e}")
            return False
    
    def insert_empresa(self, empresa_data: Dict) -> bool:
        """Insere ou atualiza dados de uma empresa"""
        try:
            cursor = self.connection.cursor()
            
            sql = """
            INSERT INTO empresas (codigo_cvm, nome, setor, situacao)
            VALUES (%(codigo_cvm)s, %(nome)s, %(setor)s, %(situacao)s)
            ON CONFLICT (codigo_cvm) 
            DO UPDATE SET 
                nome = EXCLUDED.nome,
                setor = EXCLUDED.setor,
                situacao = EXCLUDED.situacao,
                updated_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(sql, empresa_data)
            cursor.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao inserir empresa: {e}")
            return False
    
    def insert_documento(self, documento_data: Dict) -> Optional[int]:
        """Insere um novo documento e retorna o ID"""
        try:
            cursor = self.connection.cursor()
            
            sql = """
            INSERT INTO documentos (
                codigo_cvm, empresa, categoria, tipo, especie,
                data_referencia, data_entrega, status, versao,
                modalidade, download_url, arquivo_path, scraped_at
            ) VALUES (
                %(codigo_cvm)s, %(empresa)s, %(categoria)s, %(tipo)s, %(especie)s,
                %(data_referencia)s, %(data_entrega)s, %(status)s, %(versao)s,
                %(modalidade)s, %(download_url)s, %(arquivo_path)s, %(scraped_at)s
            ) RETURNING id
            """
            
            cursor.execute(sql, documento_data)
            documento_id = cursor.fetchone()[0]
            cursor.close()
            
            self.logger.info(f"Documento inserido com ID: {documento_id}")
            return documento_id
            
        except Exception as e:
            self.logger.error(f"Erro ao inserir documento: {e}")
            return None
    
    def insert_cvm44_movimentacao(self, movimentacao_data: Dict) -> bool:
        """Insere dados de movimentação CVM 44"""
        try:
            cursor = self.connection.cursor()
            
            sql = """
            INSERT INTO cvm44_movimentacoes (
                documento_id, codigo_cvm, empresa, nome_pessoa, cpf_cnpj,
                cargo, tipo_pessoa, valor_mobiliario, quantidade_anterior,
                quantidade_atual, quantidade_movimentada, tipo_movimentacao,
                preco_unitario, valor_total, data_movimentacao, observacoes
            ) VALUES (
                %(documento_id)s, %(codigo_cvm)s, %(empresa)s, %(nome_pessoa)s, %(cpf_cnpj)s,
                %(cargo)s, %(tipo_pessoa)s, %(valor_mobiliario)s, %(quantidade_anterior)s,
                %(quantidade_atual)s, %(quantidade_movimentada)s, %(tipo_movimentacao)s,
                %(preco_unitario)s, %(valor_total)s, %(data_movimentacao)s, %(observacoes)s
            )
            """
            
            cursor.execute(sql, movimentacao_data)
            cursor.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao inserir movimentação CVM 44: {e}")
            return False
    
    def get_documentos_by_empresa(self, codigo_cvm: str, limit: int = 100) -> List[Dict]:
        """Obtém documentos de uma empresa específica"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            sql = """
            SELECT * FROM documentos 
            WHERE codigo_cvm = %s 
            ORDER BY data_entrega DESC 
            LIMIT %s
            """
            
            cursor.execute(sql, (codigo_cvm, limit))
            documentos = cursor.fetchall()
            cursor.close()
            
            return [dict(doc) for doc in documentos]
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar documentos: {e}")
            return []
    
    def get_cvm44_movimentacoes(self, codigo_cvm: str = None, 
                               data_inicio: str = None, data_fim: str = None,
                               limit: int = 100) -> List[Dict]:
        """Obtém movimentações CVM 44 com filtros"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            where_conditions = []
            params = []
            
            if codigo_cvm:
                where_conditions.append("codigo_cvm = %s")
                params.append(codigo_cvm)
            
            if data_inicio:
                where_conditions.append("data_movimentacao >= %s")
                params.append(data_inicio)
            
            if data_fim:
                where_conditions.append("data_movimentacao <= %s")
                params.append(data_fim)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            sql = f"""
            SELECT * FROM cvm44_movimentacoes 
            {where_clause}
            ORDER BY data_movimentacao DESC, created_at DESC
            LIMIT %s
            """
            
            params.append(limit)
            cursor.execute(sql, params)
            movimentacoes = cursor.fetchall()
            cursor.close()
            
            return [dict(mov) for mov in movimentacoes]
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar movimentações CVM 44: {e}")
            return []
    
    def get_empresas_brasileiras(self) -> List[Dict]:
        """Obtém lista de empresas brasileiras (código < 05000)"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            sql = """
            SELECT * FROM empresas 
            WHERE CAST(SPLIT_PART(codigo_cvm, '-', 1) AS INTEGER) < 5000
            ORDER BY nome
            """
            
            cursor.execute(sql)
            empresas = cursor.fetchall()
            cursor.close()
            
            return [dict(emp) for emp in empresas]
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar empresas brasileiras: {e}")
            return []
    
    def mark_documento_processado(self, documento_id: int) -> bool:
        """Marca um documento como processado"""
        try:
            cursor = self.connection.cursor()
            
            sql = "UPDATE documentos SET processado = TRUE WHERE id = %s"
            cursor.execute(sql, (documento_id,))
            cursor.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao marcar documento como processado: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Obtém estatísticas do banco de dados"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            stats = {}
            
            # Total de empresas
            cursor.execute("SELECT COUNT(*) as total FROM empresas")
            stats['total_empresas'] = cursor.fetchone()['total']
            
            # Total de documentos
            cursor.execute("SELECT COUNT(*) as total FROM documentos")
            stats['total_documentos'] = cursor.fetchone()['total']
            
            # Total de movimentações CVM 44
            cursor.execute("SELECT COUNT(*) as total FROM cvm44_movimentacoes")
            stats['total_movimentacoes_cvm44'] = cursor.fetchone()['total']
            
            # Documentos por tipo
            cursor.execute("""
                SELECT tipo, COUNT(*) as total 
                FROM documentos 
                GROUP BY tipo 
                ORDER BY total DESC 
                LIMIT 10
            """)
            stats['documentos_por_tipo'] = cursor.fetchall()
            
            cursor.close()
            return stats
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {e}")
            return {}

# Exemplo de uso
if __name__ == "__main__":
    db = DatabaseManager()
    
    if db.connect():
        db.create_tables()
        stats = db.get_stats()
        print("Estatísticas do banco:", stats)
        db.disconnect()

