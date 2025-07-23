import os
import json
import time
import mimetypes
import zipfile
import shutil # Importado para remoção de diretórios
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import google.generativeai as genai

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

# Lista de MIME types suportados pelo Gemini para envio direto
SUPPORTED_MIME_TYPES = [
    'image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif',
    'text/plain', 'text/markdown', 'text/x-python', 'text/html', 'text/css',
    'text/javascript', 'application/x-javascript', 'application/json', 'application/pdf'
]

# Lista de extensões de texto para extrair de arquivos ZIP
TEXT_EXTENSIONS = [
    ".bat", ".c", ".cfg", ".conf", ".cpp", ".cs", ".css", ".go", ".h",
    ".html", ".ini", ".java", ".js", ".json", ".jsx", ".md", ".php",
    ".ps1", ".py", ".rb", ".rs", ".sh", ".toml", ".ts", ".tsx", ".txt",
    ".xml", ".yaml", ".yml"
]


# --- Funções Auxiliares (mantidas as que já estavam robustas) ---
def get_assistant_data_path(assistant_id): return os.path.join(DATA_DIR, assistant_id)
def get_chats_path(assistant_id): return os.path.join(get_assistant_data_path(assistant_id), "chats")
def get_chat_file_path(assistant_id, chat_id): return os.path.join(get_chats_path(assistant_id), f"{secure_filename(str(chat_id))}.json")
def get_chat_files_path(assistant_id, chat_id): return os.path.join(get_assistant_data_path(assistant_id), "files", secure_filename(str(chat_id)))

def initialize_data_structure():
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    for id in ASSISTANTS:
        os.makedirs(get_chats_path(id), exist_ok=True)
        os.makedirs(os.path.join(get_assistant_data_path(id), "files"), exist_ok=True)

def load_chat_data(assistant_id, chat_id):
    path = get_chat_file_path(assistant_id, chat_id)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except json.JSONDecodeError: return {}
    return {}

def save_chat_data(assistant_id, chat_id, data):
    with open(get_chat_file_path(assistant_id, chat_id), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# --- LÓGICA DE PROMPT (para construir a requisição para o Gemini) ---
def build_current_prompt_parts(assistant_id, chat_id, user_prompt):
    """Constrói as partes para a MENSAGEM ATUAL, incluindo o prompt do usuário e os arquivos."""
    parts = [user_prompt] # Começa com o texto do prompt do usuário
    files_dir = get_chat_files_path(assistant_id, chat_id)
    uploaded_files = []

    if os.path.exists(files_dir):
        # Garante que os arquivos sejam lidos em uma ordem consistente
        for filename in sorted(os.listdir(files_dir)):
            file_path = os.path.join(files_dir, filename)
            if not os.path.isfile(file_path): continue

            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type in SUPPORTED_MIME_TYPES:
                print(f"INFO: Anexando arquivo suportado ao prompt: {filename} ({mime_type})")
                # genai.upload_file retorna um objeto File que pode ser passado para chat.send_message
                uploaded_files.append(genai.upload_file(path=file_path))
            else:
                print(f"AVISO: Ignorando arquivo não suportado: {filename} (Tipo: {mime_type})")
    
    # Adiciona os arquivos depois do texto do usuário, como é comum em prompts multimodais
    parts.extend(uploaded_files)
    return parts


# --- ROTAS DA API ---

@app.route('/api/assistants', methods=['GET'])
def get_assistants_route():
    """Retorna a lista de assistentes configurados."""
    return jsonify(list(ASSISTANTS.values()))

@app.route('/api/chats/<assistant_id>', methods=['POST'])
def create_new_chat(assistant_id):
    """Cria um novo chat para um assistente específico."""
    chat_id = str(int(time.time())) # ID único baseado no timestamp
    chat_name = f"Nova Conversa ({chat_id[-4:]})" # Nome simples para o novo chat
    save_chat_data(assistant_id, chat_id, {"name": chat_name, "messages": []})
    os.makedirs(get_chat_files_path(assistant_id, chat_id), exist_ok=True) # Cria diretório para arquivos do chat
    return jsonify({"id": chat_id, "name": chat_name}), 201

@app.route('/api/chats/<assistant_id>', methods=['GET'])
def get_chats_list(assistant_id):
    """Retorna a lista de chats para um assistente específico."""
    chats_dir = get_chats_path(assistant_id)
    if not os.path.exists(chats_dir): return jsonify([]) # Retorna lista vazia se não houver chats
    
    chat_list = []
    # Lista os arquivos JSON de chat e carrega seus nomes
    for filename in sorted(os.listdir(chats_dir), reverse=True): # Ordena para chats mais recentes primeiro
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
    """Renomeia um chat existente."""
    data = request.json
    if not data or 'name' not in data: abort(400, "Nome não fornecido")
    new_name = data['name']
    chat_data = load_chat_data(assistant_id, chat_id)
    if not chat_data: abort(404, "Chat não encontrado")
    chat_data['name'] = new_name
    save_chat_data(assistant_id, chat_id, chat_data)
    return jsonify({"success": True, "name": new_name})

@app.route('/api/chats/<assistant_id>/<chat_id>', methods=['GET'])
def get_chat_history_route(assistant_id, chat_id):
    """Retorna o histórico de mensagens de um chat específico."""
    chat_data = load_chat_data(assistant_id, chat_id)
    return jsonify(chat_data.get("messages", []))


@app.route('/api/chats/<assistant_id>/<chat_id>', methods=['POST'])
def post_to_chat(assistant_id, chat_id):
    """Envia uma mensagem para o assistente e obtém uma resposta."""
    data = request.json
    if not data or 'prompt' not in data:
        abort(400, "Prompt não fornecido")

    user_prompt = data['prompt']
    chat_data = load_chat_data(assistant_id, chat_id)
    history = chat_data.get("messages", [])
    assistant_config = ASSISTANTS[assistant_id]

    try:
        model = genai.GenerativeModel(
            'gemini-2.5-pro', # Modelo mantido como gemini-2.5-pro, conforme sua solicitação
            system_instruction=assistant_config["system_prompt"]
        )
        
        # Converte o histórico para o formato que o Gemini espera
        gemini_history = []
        for msg in history:
            role = 'model' if msg.get('role') == 'assistant' else 'user'
            # Garante que 'parts' seja sempre uma lista para compatibilidade com o SDK
            content_part = msg.get('content', '')
            gemini_history.append({'role': role, 'parts': [content_part]})

        # Inicia uma sessão de chat com o histórico carregado
        chat_session = model.start_chat(history=gemini_history)
        
        # Constrói o prompt atual, incluindo arquivos
        prompt_parts = build_current_prompt_parts(assistant_id, chat_id, user_prompt)
        
        # Envia a mensagem (com os arquivos anexados) para a sessão de chat
        response = chat_session.send_message(prompt_parts)

        # Trata o caso de resposta bloqueada por segurança
        if not response.parts:
            ai_response_text = "A resposta foi bloqueada devido a políticas de segurança. Por favor, reformule sua pergunta."
        else:
            ai_response_text = response.text

    except Exception as e:
        print(f"Erro na API do Gemini: {e}")
        # Retorna um erro 500 com a mensagem da exceção para facilitar o debug
        abort(500, f"Erro ao comunicar com a API do Gemini: {e}")

    # Salva a conversa no histórico após a resposta
    history.append({"role": "user", "content": user_prompt})
    history.append({"role": "assistant", "content": ai_response_text})
    chat_data["messages"] = history
    save_chat_data(assistant_id, chat_id, chat_data)

    return jsonify({"role": "assistant", "content": ai_response_text})


# --- ROTAS DE ARQUIVOS (com lógica de extração de ZIP integrada) ---

@app.route('/api/chats/<assistant_id>/<chat_id>/files', methods=['POST'])
def upload_file_route(assistant_id, chat_id):
    """Faz o upload de um arquivo para o ambiente de trabalho do chat. Suporta extração de ZIP."""
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nome de arquivo vazio"}), 400

    files_dir = get_chat_files_path(assistant_id, chat_id)
    os.makedirs(files_dir, exist_ok=True)
    filename = secure_filename(file.filename)
    
    # Verifica se é um arquivo ZIP
    if filename.lower().endswith('.zip'):
        extracted_files = []
        try:
            # Abre o arquivo ZIP enviado via stream
            with zipfile.ZipFile(file, 'r') as zip_ref:
                for member in zip_ref.infolist():
                    # Ignora diretórios dentro do ZIP
                    if member.is_dir():
                        continue 
                    
                    member_filename = os.path.basename(member.filename)
                    if not member_filename: # Ignora arquivos sem nome
                        continue

                    # Verifica se a extensão do arquivo dentro do ZIP está na lista de TEXT_EXTENSIONS
                    file_ext = os.path.splitext(member_filename)[1].lower()
                    if file_ext in TEXT_EXTENSIONS:
                        content = zip_ref.read(member.filename).decode('utf-8', errors='replace') # Lê como texto
                        
                        # Salva o arquivo extraído no diretório de arquivos do chat
                        extracted_filename = secure_filename(member_filename)
                        with open(os.path.join(files_dir, extracted_filename), 'w', encoding='utf-8') as f_out:
                            f_out.write(content)
                        extracted_files.append(extracted_filename)

            if not extracted_files:
                return jsonify({"error": "O arquivo ZIP não continha arquivos de texto suportados ou estava vazio.", "filename": filename}), 400
            
            return jsonify({"success": True, "filename": filename, "extracted_files": extracted_files}), 201

        except zipfile.BadZipFile:
            return jsonify({"error": "Arquivo ZIP inválido ou corrompido."}), 400
        except Exception as e:
            return jsonify({"error": f"Erro ao processar o arquivo ZIP: {e}"}), 500
    
    # Lógica original para outros tipos de arquivo (não ZIP)
    else:
        file.save(os.path.join(files_dir, filename))
        return jsonify({"success": True, "filename": filename}), 201


@app.route('/api/chats/<assistant_id>/<chat_id>/files', methods=['GET'])
def get_files_route(assistant_id, chat_id):
    """Retorna a lista de arquivos no ambiente de trabalho de um chat."""
    files_dir = get_chat_files_path(assistant_id, chat_id)
    try:
        filenames = [f for f in os.listdir(files_dir) if os.path.isfile(os.path.join(files_dir, f))]
        return jsonify(filenames)
    except FileNotFoundError:
        # Se o diretório ainda não existe, cria e retorna lista vazia
        os.makedirs(files_dir, exist_ok=True)
        return jsonify([])

@app.route('/api/chats/<assistant_id>/<chat_id>/<filename>', methods=['DELETE'])
def delete_file_route(assistant_id, chat_id, filename):
    """Exclui um único arquivo do ambiente de trabalho do chat."""
    file_path = os.path.join(get_chat_files_path(assistant_id, chat_id), secure_filename(filename))
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({"success": True, "filename": filename})
    else:
        abort(404, "Arquivo não encontrado")


# --- NOVAS ROTAS DE EXCLUSÃO (implementadas anteriormente) ---

@app.route('/api/chats/<assistant_id>/<chat_id>', methods=['DELETE'])
def delete_chat_route(assistant_id, chat_id):
    """Exclui um chat inteiro, incluindo seu arquivo de histórico e a pasta de arquivos associada."""
    chat_path = get_chat_file_path(assistant_id, chat_id)
    files_dir = get_chat_files_path(assistant_id, chat_id)

    chat_deleted = False
    files_deleted = False

    try:
        if os.path.exists(chat_path):
            os.remove(chat_path)
            chat_deleted = True
        
        if os.path.exists(files_dir):
            shutil.rmtree(files_dir) # Remove o diretório e todo o seu conteúdo
            files_deleted = True

        if not chat_deleted and not files_deleted:
            abort(404, "Chat não encontrado ou já excluído.")

        return jsonify({"success": True, "message": "Chat e arquivos associados excluídos."})

    except Exception as e:
        print(f"Erro ao excluir chat {chat_id}: {e}")
        abort(500, f"Erro interno ao excluir o chat: {e}")


@app.route('/api/chats/<assistant_id>/<chat_id>/files', methods=['DELETE'])
def delete_all_files_route(assistant_id, chat_id):
    """Exclui todos os arquivos no ambiente de trabalho de um chat, mas mantém o chat."""
    files_dir = get_chat_files_path(assistant_id, chat_id)

    if not os.path.exists(files_dir):
        # Se o diretório não existe, não há nada para excluir.
        # Recria para garantir que a pasta exista para futuros uploads.
        os.makedirs(files_dir, exist_ok=True) 
        return jsonify({"success": True, "message": "Nenhum arquivo para excluir. Diretório garantido."})

    try:
        shutil.rmtree(files_dir) # Remove o diretório inteiro
        os.makedirs(files_dir) # E o recria vazio para futuros uploads
        return jsonify({"success": True, "message": "Todos os arquivos foram excluídos."})

    except Exception as e:
        print(f"Erro ao limpar arquivos do chat {chat_id}: {e}")
        abort(500, f"Erro interno ao limpar arquivos: {e}")


# --- INICIALIZAÇÃO ---
if __name__ == '__main__':
    initialize_data_structure()
    app.run(debug=True, port=5000)