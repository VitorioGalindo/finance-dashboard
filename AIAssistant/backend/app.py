import os
import json
import time
import mimetypes
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import google.generativeai as genai
import shutil

# --- CONFIGURAÇÃO ---
load_dotenv()
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("A variável de ambiente GOOGLE_API_KEY não foi definida.")
genai.configure(api_key=GOOGLE_API_KEY)
app = Flask(__name__)
CORS(app)
DATA_DIR = os.path.join(os.getcwd(), "data")
ASSISTANTS = {
    "code_assistant": {
        "id": "code_assistant", "name": "Assistente de Código", "description": "Análise, refatoração e desenvolvimento de código.",
        "system_prompt": "Você é um engenheiro de software sênior, especialista em UI/UX, arquitetura de sistemas e um desenvolvedor sênior em todas as linguagens. Sua principal tarefa é desenvolver projetos, com foco especial em criar interfaces de usuário (front-end) a partir de imagens, mockups e descrições. Analise os arquivos de código e as IMAGENS fornecidas, sugira melhorias e, principalmente, ajude no desenvolvimento dos códigos (HTML, CSS, JavaScript) para replicar ou aprimorar os exemplos visuais. Seja preciso, claro e forneça os códigos necessários. Baseie suas respostas primariamente nos arquivos e imagens de contexto. Responda sempre em português do Brasil, de forma didática."
    },
    "financial_assistant": {
        "id": "financial_assistant", "name": "Assistente de Research", "description": "Análise de empresas de capital aberto no Brasil.",
        "system_prompt": "Você é um analista de research CNPI, especializado no mercado de ações brasileiro. Sua função é analisar empresas de capital aberto (listadas na B3) com base em notícias, relatórios e dados fornecidos. Você deve fornecer análises fundamentalistas, identificar riscos, oportunidades e resumir os principais acontecimentos. Suas respostas devem ser objetivas, baseadas em fatos e em português do Brasil. NÃO FAÇA RECOMENDAÇÃO DE COMPRA OU VENDA."
    }
}
# Lista de MIME types que o Gemini consegue processar
SUPPORTED_MIME_TYPES = [
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/heic',
    'image/heif',
    'text/plain',
    'text/markdown',
    'text/x-python',
    'text/html',
    'text/css',
    'text/javascript',
    'application/x-javascript',
    'application/json',
]
# --- Funções Auxiliares ATUALIZADAS ---
def get_assistant_data_path(assistant_id):
    return os.path.join(DATA_DIR, assistant_id)

def get_chats_path(assistant_id):
    return os.path.join(get_assistant_data_path(assistant_id), "chats")

def get_chat_file_path(assistant_id, chat_id):
    return os.path.join(get_chats_path(assistant_id), f"{secure_filename(str(chat_id))}.json")

# ATUALIZADO: O caminho dos arquivos agora depende do chat_id
def get_chat_files_path(assistant_id, chat_id):
    base_files_path = os.path.join(get_assistant_data_path(assistant_id), "files")
    return os.path.join(base_files_path, secure_filename(str(chat_id)))


def initialize_data_structure():
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    for assistant_id in ASSISTANTS:
        assistant_path = get_assistant_data_path(assistant_id)
        chats_path = get_chats_path(assistant_id)
        # Cria o diretório base de arquivos, se não existir
        base_files_path = os.path.join(assistant_path, "files")

        if not os.path.exists(assistant_path): os.makedirs(assistant_path)
        if not os.path.exists(chats_path): os.makedirs(chats_path)
        if not os.path.exists(base_files_path): os.makedirs(base_files_path)

        # Migração do chat antigo (mantida por segurança)
        old_chat_path = os.path.join(assistant_path, "chat_history.json")
        if os.path.exists(old_chat_path):
            print(f"Arquivo de chat antigo encontrado para '{assistant_id}'. Migrando...")
            try:
                with open(old_chat_path, 'r', encoding='utf-8') as f: old_history = json.load(f)
                migrated_chat_id = f"migrated_{int(time.time())}"
                migrated_data = {"name": "Conversa Antiga (Importada)", "messages": old_history}
                save_chat_data(assistant_id, migrated_chat_id, migrated_data)
                os.rename(old_chat_path, old_chat_path + ".migrated")
                print(f"Migração para '{assistant_id}' concluída com sucesso!")
            except Exception as e:
                print(f"Erro ao migrar chat antigo para '{assistant_id}': {e}")


def load_chat_data(assistant_id, chat_id):
    chat_path = get_chat_file_path(assistant_id, chat_id)
    if os.path.exists(chat_path):
        with open(chat_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError: return {}
    return {}

def save_chat_data(assistant_id, chat_id, data):
    chat_path = get_chat_file_path(assistant_id, chat_id)
    with open(chat_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def build_prompt_with_files(assistant_id, chat_id, user_prompt):
    prompt_parts = [ASSISTANTS[assistant_id]["system_prompt"]]
    # ATUALIZADO: Busca arquivos da pasta específica do chat
    files_dir = get_chat_files_path(assistant_id, chat_id)
    if os.path.exists(files_dir):
        for filename in os.listdir(files_dir):
            file_path = os.path.join(files_dir, filename)
            prompt_parts.append(genai.upload_file(path=file_path))
    prompt_parts.append(user_prompt)
    return prompt_parts


# --- ROTAS DA API ---
@app.route('/api/assistants', methods=['GET'])
def get_assistants_route():
    return jsonify(list(ASSISTANTS.values()))

# Rota para criar um novo chat
@app.route('/api/chats/<assistant_id>', methods=['POST'])
def create_new_chat(assistant_id):
    chat_id = str(int(time.time()))
    chat_name = f"Nova Conversa ({chat_id[-4:]})"
    # Salva o arquivo de chat
    save_chat_data(assistant_id, chat_id, {"name": chat_name, "messages": []})
    # Cria a pasta de arquivos para o novo chat
    os.makedirs(get_chat_files_path(assistant_id, chat_id), exist_ok=True)
    return jsonify({"id": chat_id, "name": chat_name}), 201

# Rotas que não mudaram: get_chats_list, rename_chat, get_chat_history_route
@app.route('/api/chats/<assistant_id>', methods=['GET'])
def get_chats_list(assistant_id):
    #...código igual ao anterior...
    chats_dir = get_chats_path(assistant_id)
    if not os.path.exists(chats_dir): return jsonify([])
    chat_list = []
    for filename in sorted(os.listdir(chats_dir), reverse=True):
        if filename.endswith(".json"):
            chat_id = os.path.splitext(filename)[0]
            chat_data = load_chat_data(assistant_id, chat_id)
            if isinstance(chat_data, dict):
                chat_list.append({"id": chat_id, "name": chat_data.get("name", f"Chat {chat_id}")})
            else:
                print(f"Aviso: O arquivo de chat '{filename}' está em um formato inválido/antigo e será ignorado.")
    return jsonify(chat_list)

@app.route('/api/chats/<assistant_id>/<chat_id>', methods=['PUT'])
def rename_chat(assistant_id, chat_id):
    #...código igual ao anterior...
    data = request.json
    if not data or 'name' not in data: abort(400, "Novo nome não fornecido")
    new_name = data['name']
    chat_data = load_chat_data(assistant_id, chat_id)
    if not chat_data: abort(404, "Chat não encontrado")
    chat_data['name'] = new_name
    save_chat_data(assistant_id, chat_id, chat_data)
    return jsonify({"success": True, "name": new_name})

@app.route('/api/chats/<assistant_id>/<chat_id>', methods=['GET'])
def get_chat_history_route(assistant_id, chat_id):
    #...código igual ao anterior...
    chat_data = load_chat_data(assistant_id, chat_id)
    return jsonify(chat_data.get("messages", []))

# Rota de postagem de chat ATUALIZADA
@app.route('/api/chats/<assistant_id>/<chat_id>', methods=['POST'])
def post_to_chat(assistant_id, chat_id):
    data = request.json
    if not data or 'prompt' not in data: abort(400, "Prompt não fornecido")
    
    user_prompt = data['prompt']
    chat_data = load_chat_data(assistant_id, chat_id)
    history = chat_data.get("messages", [])
    
    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        gemini_history = [{'role': 'model' if msg['role'] == 'assistant' else msg['role'], 'parts': [msg['content']]} for msg in history if 'role' in msg and 'content' in msg]
        chat_session = model.start_chat(history=gemini_history)
        # ATUALIZADO: Passa o chat_id para a função de construção do prompt
        prompt_with_files = build_prompt_with_files(assistant_id, chat_id, user_prompt)
        response = chat_session.send_message(prompt_with_files)
        ai_response_text = response.text
    except Exception as e:
        print(f"Erro na API do Gemini: {e}")
        abort(500, f"Erro ao comunicar com a API do Gemini: {e}")
        
    history.append({"role": "user", "content": user_prompt})
    history.append({"role": "assistant", "content": ai_response_text})
    chat_data["messages"] = history
    save_chat_data(assistant_id, chat_id, chat_data)
    
    # **REMOVIDO**: O bloco de limpeza de arquivos foi removido daqui.
    
    return jsonify({"role": "assistant", "content": ai_response_text})

# --- ROTAS DE ARQUIVOS ATUALIZADAS ---
@app.route('/api/chats/<assistant_id>/<chat_id>/files', methods=['GET'])
def get_files_route(assistant_id, chat_id):
    files_dir = get_chat_files_path(assistant_id, chat_id)
    try:
        filenames = [f for f in os.listdir(files_dir) if os.path.isfile(os.path.join(files_dir, f))]
        return jsonify(filenames)
    except FileNotFoundError:
        # Se a pasta não existe, cria e retorna lista vazia
        os.makedirs(files_dir, exist_ok=True)
        return jsonify([])

@app.route('/api/chats/<assistant_id>/<chat_id>/files', methods=['POST'])
def upload_file_route(assistant_id, chat_id):
    if 'file' not in request.files: return jsonify({"error": "Nenhum arquivo enviado"}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({"error": "Nome de arquivo vazio"}), 400
    if file:
        files_dir = get_chat_files_path(assistant_id, chat_id)
        os.makedirs(files_dir, exist_ok=True) # Garante que a pasta existe
        filename = secure_filename(file.filename)
        file.save(os.path.join(files_dir, filename))
        return jsonify({"success": True, "filename": filename}), 201

@app.route('/api/chats/<assistant_id>/<chat_id>/<filename>', methods=['DELETE'])
def delete_file_route(assistant_id, chat_id, filename):
    file_path = os.path.join(get_chat_files_path(assistant_id, chat_id), secure_filename(filename))
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({"success": True, "filename": filename})
    else:
        abort(404, "Arquivo não encontrado")


# --- INICIALIZAÇÃO ---
if __name__ == '__main__':
    initialize_data_structure()
    app.run(debug=True, port=5000)