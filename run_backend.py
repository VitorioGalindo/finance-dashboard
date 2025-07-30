#!/usr/bin/env python3
"""
Script para executar o backend do dashboard financeiro
"""

import sys
import os

# Adiciona o diretório raiz ao Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app

if __name__ == '__main__':
    app = create_app()
    print("🚀 Iniciando backend do Dashboard Financeiro...")
    print("📊 Acesse: http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)