# backend/routes/companies_routes.py (NOVA ESTRATÉGIA DE DEPURAÇÃO COM ARQUIVO DE LOG)
from flask import Blueprint, jsonify
from backend.models import Company
import sys

companies_bp = Blueprint('companies_bp', __name__)

LOG_FILE = "debug_companies.log" # Define o nome do nosso arquivo de log

@companies_bp.route('/companies', methods=['GET'])
def get_companies():
    """
    Retorna uma lista de empresas e escreve o progresso em um arquivo de log
    para encontrar a linha exata que está causando o erro de codificação.
    """
    # Abre o arquivo de log em modo de escrita, com codificação utf-8
    with open(LOG_FILE, "w", encoding="utf-8") as log_file:
        try:
            log_file.write("--- INICIANDO ROTA DE DEPURAÇÃO /api/companies ---
")
            print("--- INICIANDO ROTA DE DEPURAÇÃO /api/companies ---", file=sys.stderr)

            companies = Company.query.all()
            
            log_file.write(f"Banco de dados retornou {len(companies)} empresas.
")
            print(f"Banco de dados retornou {len(companies)} empresas.", file=sys.stderr)
            
            companies_list = []
            for i, company in enumerate(companies):
                try:
                    current_name = company.name
                    
                    # Escreve no arquivo de log antes de tentar processar
                    log_file.write(f"Processando [{i+1}/{len(companies)}]: CNPJ={company.cnpj}, Name='{current_name}'
")
                    
                    company_data = {
                        'cnpj': company.cnpj,
                        'name': current_name,
                        'created_at': company.created_at.isoformat() if company.created_at else None,
                        'updated_at': company.updated_at.isoformat() if company.updated_at else None
                    }
                    companies_list.append(company_data)

                except Exception as e_inner:
                    # Se um erro ocorrer, loga e retorna
                    error_message = (
                        "

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
"
                        f"!!! ERRO DETECTADO AO PROCESSAR A EMPRESA ACIMA.
"
                        f"!!! CNPJ Problemático: {company.cnpj}
"
                        f"!!! Erro de Decodificação: {e_inner}
"
                        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

"
                    )
                    log_file.write(error_message)
                    print(error_message, file=sys.stderr)
                    
                    return jsonify({
                        "error": "Erro de codificação detectado. Verifique o log do console e o arquivo debug_companies.log na raiz do projeto.",
                        "cnpj_problematico": company.cnpj,
                        "detalhe_erro": str(e_inner)
                    }), 500

            success_message = "--- Processamento de todas as empresas concluído com sucesso. ---
"
            log_file.write(success_message)
            print(success_message, file=sys.stderr)
            return jsonify(companies_list)

        except Exception as e_outer:
            error_message = f"!!! ERRO GERAL NA ROTA (antes do loop): {e_outer}
"
            log_file.write(error_message)
            print(error_message, file=sys.stderr)
            return jsonify({"error": str(e_outer)}), 500
