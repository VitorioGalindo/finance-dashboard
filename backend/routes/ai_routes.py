
import os
from flask import Blueprint, request, jsonify, abort
import google.generativeai as genai
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Cria o Blueprint para as rotas de IA
ai_bp = Blueprint('ai_bp', __name__)

# --- Configuração do Gemini ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    # Em um ambiente de produção, seria melhor logar este erro
    # do que simplesmente imprimir no console.
    print("ALERTA: A variável de ambiente GOOGLE_API_KEY não foi definida.")
    # Não vamos lançar um erro aqui para permitir que a app inicie mesmo sem a chave,
    # mas as rotas de IA falharão.
else:
    genai.configure(api_key=GOOGLE_API_KEY)

# --- Prompt de Sistema para o Analista Financeiro ---
# Este prompt define a persona e as diretrizes para o modelo de IA.
FINANCIAL_ANALYST_PROMPT = """
Você é o 'Apex Analyst', um analista de research CNPI, especializado no mercado de ações brasileiro. Sua função é analisar empresas de capital aberto (listadas na B3) com base em notícias, relatórios e dados fornecidos no prompt.

**Suas Diretrizes:**
1.  **Análise Fundamentalista:** Forneça análises fundamentalistas detalhadas, focando em múltiplos, resultados financeiros, endividamento, e posição competitiva.
2.  **Riscos e Oportunidades:** Identifique e explique claramente os principais riscos e oportunidades para a empresa em questão.
3.  **Resumo Objetivo:** Resuma os principais acontecimentos recentes relacionados à empresa.
4.  **Baseado em Fatos:** Suas respostas devem ser estritamente baseadas nos fatos, dados e contexto fornecidos. Não especule ou invente informações.
5.  **Linguagem Profissional:** Mantenha um tom profissional, objetivo e técnico.
6.  **Idioma:** Responda sempre em Português do Brasil.
7.  **PROIBIÇÃO:** NÃO FAÇA, sob nenhuma circunstância, RECOMENDAÇÃO DE COMPRA, VENDA OU MANUTENÇÃO de ativos. Apenas forneça a análise técnica e factual.
"""

@ai_bp.route('/api/ai/analyst', methods=['POST'])
def ask_financial_analyst():
    """
    Endpoint para receber perguntas para o assistente de análise financeira.
    Espera um JSON com 'history' (uma lista de mensagens) e 'prompt' (a nova pergunta).
    """
    if not GOOGLE_API_KEY:
        abort(503, "Serviço de IA indisponível: a chave de API não foi configurada no servidor.")

    data = request.get_json()
    if not data:
        abort(400, "Requisição inválida: JSON não fornecido.")

    user_prompt = data.get('prompt')
    history = data.get('history', [])

    if not user_prompt:
        abort(400, "Requisição inválida: 'prompt' não fornecido.")

    try:
        # Configura o modelo
        model = genai.GenerativeModel(
            model_name='gemini-1.5-pro-latest',
            system_instruction=FINANCIAL_ANALYST_PROMPT
        )

        # Converte o histórico do nosso formato para o formato do Gemini
        gemini_history = []
        for message in history:
            role = 'model' if message.get('role') == 'assistant' else 'user'
            # Garantir que 'content' seja uma string simples
            content = message.get('content', '')
            if isinstance(content, list): # Lida com casos onde o conteúdo pode ser complexo
                content = " ".join(str(item) for item in content)

            gemini_history.append({'role': role, 'parts': [content]})

        # Inicia o chat com o histórico
        chat_session = model.start_chat(history=gemini_history)

        # Envia a nova mensagem do usuário
        response = chat_session.send_message(user_prompt)

        # Retorna a resposta do modelo
        return jsonify({"role": "assistant", "content": response.text})

    except Exception as e:
        # Log do erro no servidor para depuração
        print(f"ERRO na comunicação com a API do Gemini: {e}")
        # Retorna uma resposta de erro genérica para o cliente
        abort(500, "Ocorreu um erro interno ao processar sua solicitação com o serviço de IA.")

