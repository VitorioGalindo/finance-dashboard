# backend/routes/companies_routes.py (VERSÃO DE DEPURAÇÃO FINAL E CORRIGIDA)
from flask import Blueprint, jsonify
from backend.models import Company
import sys

companies_bp = Blueprint('companies_bp', __name__)

@companies_bp.route('/companies', methods=['GET'])
def get_companies():
    """Retorna uma lista de todas as empresas, com debug de codificação."""
    print("--- INICIANDO ROTA DE DEPURAÇÃO /api/companies ---", file=sys.stderr)
    try:
        # Busca todas as empresas do banco de dados
        companies = Company.query.all()
        print(f"Banco de dados retornou {len(companies)} empresas.", file=sys.stderr)
        
        companies_list = []
        # Itera sobre cada empresa para encontrar a que causa o erro
        for i, company in enumerate(companies):
            try:
                # Tenta criar o dicionário. O problema geralmente ocorre quando 'jsonify'
                # tenta ler 'company.name'. Vamos forçar a leitura aqui para depurar.
                
                current_name = company.name
                # Imprime no log do console do Flask para vermos o progresso
                print(f"Processando [{i+1}/{len(companies)}]: CNPJ={company.cnpj}, Name='{current_name}'", file=sys.stderr)
                
                company_data = {
                    'cnpj': company.cnpj,
                    'name': current_name,
                    'created_at': company.created_at.isoformat() if company.created_at else None,
                    'updated_at': company.updated_at.isoformat() if company.updated_at else None
                }
                companies_list.append(company_data)

            except Exception as e_inner:
                # Se um erro ocorrer para uma empresa específica, esta é a nossa resposta!
                print("

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", file=sys.stderr)
                print("!!! ERRO DETECTADO AO PROCESSAR A EMPRESA ABAIXO:", file=sys.stderr)
                print(f"!!! CNPJ Problemático: {company.cnpj}", file=sys.stderr)
                print(f"!!! Erro de Decodificação: {e_inner}", file=sys.stderr)
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

", file=sys.stderr)
                
                # Retorna um erro imediatamente para sabermos que encontramos o problema
                return jsonify({
                    "error": "Erro de codificação detectado em uma empresa específica. Verifique o log do console do Flask.",
                    "cnpj_problematico": company.cnpj,
                    "detalhe_erro": str(e_inner)
                }), 500

        print("--- Processamento de todas as empresas concluído com sucesso. ---", file=sys.stderr)
        return jsonify(companies_list)

    except Exception as e_outer:
        # Erro geral na rota (ex: falha ao buscar do DB)
        print(f"!!! ERRO GERAL NA ROTA (antes do loop): {e_outer}", file=sys.stderr)
        return jsonify({"error": str(e_outer)}), 500
