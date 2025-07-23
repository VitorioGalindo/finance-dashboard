document.addEventListener('DOMContentLoaded', () => {
    // ESTADO DA APLICAÇÃO
    let currentAssistantId = null;
    let currentChatId = null;
    const API_BASE_URL = 'http://127.0.0.1:5000/api';

    // ELEMENTOS DO DOM
    const sidebar = document.getElementById('assistants-sidebar');
    const mainContent = document.getElementById('main-content');
    const welcomeScreen = document.getElementById('welcome-screen');
    const chatPane = document.getElementById('chat-pane');
    const filesPane = document.getElementById('files-pane');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const thinkingIndicator = document.getElementById('chat-thinking-indicator');
    const fileList = document.getElementById('file-list');
    const fileUpload = document.getElementById('file-upload');
    const newChatBtn = document.getElementById('new-chat-btn');
    const chatListContainer = document.getElementById('chat-list-container');
    const toggleChatPaneBtn = document.getElementById('toggle-chat-pane');
    const toggleFilesPaneBtn = document.getElementById('toggle-files-pane');

    // --- FUNÇÕES DE RENDERIZAÇÃO ---
    function renderAssistants(assistants) {
        document.querySelectorAll('.assistant-link').forEach(link => link.remove());
        assistants.forEach(assistant => {
            const link = document.createElement('a');
            link.href = '#';
            link.className = 'sidebar-link assistant-link';
            link.dataset.id = assistant.id;
            link.innerHTML = `<h3 class="text-xl font-bold">${assistant.name}</h3><p class="text-gray-400 text-sm mt-1">${assistant.description}</p>`;
            link.addEventListener('click', (e) => { e.preventDefault(); selectAssistant(assistant.id); });
            sidebar.appendChild(link);
        });
    }

    function renderChatMessage(message) {
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${message.role}`;
        let contentHtml = message.content
            .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/```([\s\S]*?)```/g, '<pre class="bg-gray-800 p-2 rounded-md my-2 overflow-x-auto"><code>$1</code></pre>')
            .replace(/`([^`]+)`/g, '<code class="bg-gray-800 px-1 rounded-sm">$1</code>')
            .replace(/\n/g, '<br>');
        bubble.innerHTML = contentHtml;
        chatMessages.appendChild(bubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function renderFileItem(filename) {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `<span>${filename}</span><button class="delete-file-btn" data-filename="${filename}">&times;</button>`;
        item.querySelector('button').addEventListener('click', () => deleteFile(filename));
        fileList.appendChild(item);
    }
    
    function renderChatList(chats) {
        chatListContainer.innerHTML = '<h4 class="text-gray-400 text-sm font-bold uppercase mb-2">Conversas</h4>';
        if (!chats || chats.length === 0) {
            chatListContainer.innerHTML += '<p class="text-gray-500 text-sm">Nenhum chat salvo.</p>';
            return;
        }
        chats.forEach(chat => {
            const chatLink = document.createElement('a');
            chatLink.href = '#';
            chatLink.className = 'chat-list-item';
            chatLink.dataset.id = chat.id;
            chatLink.innerHTML = `<span>${chat.name}</span> <button class="rename-btn" title="Renomear">✏️</button>`;
            
            chatLink.addEventListener('click', (e) => {
                if (e.target.classList.contains('rename-btn')) return;
                e.preventDefault();
                selectChat(chat.id);
            });
            
            chatLink.querySelector('.rename-btn').addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                renameChat(chat.id, chat.name);
            });

            chatListContainer.appendChild(chatLink);
        });
    }

    // --- FUNÇÕES DE LÓGICA E API ---
    async function apiCall(url, options = {}) {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: response.statusText }));
                throw new Error(errorData.message || 'Erro desconhecido');
            }
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                return response.json();
            }
            return {};
        } catch (error) {
            console.error(`Erro na API (${url}):`, error);
            throw error;
        }
    }

    async function initializeApp() {
        try {
            const assistants = await apiCall(`${API_BASE_URL}/assistants`);
            renderAssistants(assistants);
        } catch (error) {
            sidebar.innerHTML = '<p class="text-red-500">Erro ao carregar assistentes. Verifique o backend.</p>';
        }
    }

    async function selectAssistant(assistantId) {
        currentAssistantId = assistantId;
        currentChatId = null;
        mainContent.classList.add('hidden');
        welcomeScreen.classList.remove('hidden');
        newChatBtn.classList.remove('hidden');
        document.querySelectorAll('.assistant-link').forEach(link => link.classList.toggle('active', link.dataset.id === assistantId));
        fileList.innerHTML = '';
        await loadChatList();
    }
    
    async function selectChat(chatId) {
        currentChatId = chatId;
        mainContent.classList.remove('hidden');
        welcomeScreen.classList.add('hidden');
        document.querySelectorAll('.chat-list-item').forEach(link => link.classList.toggle('active', link.dataset.id === chatId));
        await loadChatHistory();
        await loadFiles();
    }
    
    async function loadChatList() {
        if (!currentAssistantId) return;
        try {
            const chats = await apiCall(`${API_BASE_URL}/chats/${currentAssistantId}`);
            renderChatList(chats);
        } catch (error) {
            chatListContainer.innerHTML = '<p class="text-red-500">Erro ao carregar chats.</p>';
        }
    }

    async function loadChatHistory() {
        if (!currentAssistantId || !currentChatId) return;
        chatMessages.innerHTML = '<p class="text-gray-400">Carregando...</p>';
        try {
            const history = await apiCall(`${API_BASE_URL}/chats/${currentAssistantId}/${currentChatId}`);
            chatMessages.innerHTML = '';
            if (history && history.length > 0) {
                history.forEach(renderChatMessage);
            }
        } catch (error) {
            chatMessages.innerHTML = `<p class="text-red-500">Erro ao carregar histórico: ${error.message}</p>`;
        }
    }
    
    async function loadFiles() {
        if (!currentAssistantId || !currentChatId) {
            fileList.innerHTML = '';
            return;
        }
        fileList.innerHTML = '';
        try {
            const files = await apiCall(`${API_BASE_URL}/chats/${currentAssistantId}/${currentChatId}/files`);
            if (files && files.length > 0) {
                files.forEach(renderFileItem);
            }
        } catch (error) {
            console.error('Erro ao carregar arquivos:', error);
        }
    }

    async function handleSendMessage() {
        const prompt = chatInput.value.trim();
        if (!prompt || !currentAssistantId || !currentChatId) return;
        renderChatMessage({ role: 'user', content: prompt });
        chatInput.value = '';
        chatInput.style.height = 'auto';
        thinkingIndicator.classList.remove('hidden');
        sendButton.disabled = true;
        try {
            const aiMessage = await apiCall(`${API_BASE_URL}/chats/${currentAssistantId}/${currentChatId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt })
            });
            renderChatMessage(aiMessage);
        } catch (error) {
            renderChatMessage({ role: 'assistant', content: `Desculpe, ocorreu um erro: ${error.message}` });
        } finally {
            thinkingIndicator.classList.add('hidden');
            sendButton.disabled = false;
        }
    }
    
    async function createNewChat() {
        if (!currentAssistantId) return;
        try {
            const newChat = await apiCall(`${API_BASE_URL}/chats/${currentAssistantId}`, { method: 'POST' });
            await loadChatList();
            selectChat(newChat.id);
        } catch (error) {
            alert(`Erro ao criar chat: ${error.message}`);
        }
    }

    async function renameChat(chatId, currentName) {
        const newName = prompt("Digite o novo nome para a conversa:", currentName);
        if (newName && newName.trim() !== '' && newName !== currentName) {
            try {
                await apiCall(`${API_BASE_URL}/chats/${currentAssistantId}/${chatId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: newName.trim() })
                });
                await loadChatList();
                const activeChatLink = document.querySelector(`.chat-list-item[data-id='${chatId}']`);
                if (activeChatLink) {
                    activeChatLink.classList.add('active');
                }
            } catch (error) {
                alert(`Erro ao renomear chat: ${error.message}`);
            }
        }
    }

    function togglePane(paneToExpand) {
        const isChat = paneToExpand === 'chat';
        const paneToModify = isChat ? chatPane : filesPane;
        const otherPane = isChat ? filesPane : chatPane;

        if (paneToModify.classList.contains('is-expanded')) {
            paneToModify.classList.remove('is-expanded');
            otherPane.classList.remove('is-collapsed');
        } else {
            paneToModify.classList.add('is-expanded');
            otherPane.classList.add('is-collapsed');
            otherPane.classList.remove('is-expanded');
        }
    }

    async function uploadFile(file) {
        if (!file || !currentAssistantId || !currentChatId) return;
        const formData = new FormData();
        formData.append('file', file);
        try {
            await fetch(`${API_BASE_URL}/chats/${currentAssistantId}/${currentChatId}/files`, { method: 'POST', body: formData });
        } catch (error) {
            console.error('Erro no upload:', error);
            alert(`Erro no upload do arquivo: ${file.name}`);
        }
    }

    async function handleFileInputChange(event) {
        const file = event.target.files[0];
        if (file) {
            await uploadFile(file);
            await loadFiles();
        }
        event.target.value = null;
    }

    async function deleteFile(filename) {
        if (!currentAssistantId || !currentChatId || !confirm(`Tem certeza que deseja excluir "${filename}"?`)) return;
        try {
            await apiCall(`${API_BASE_URL}/chats/${currentAssistantId}/${currentChatId}/${filename}`, { method: 'DELETE' });
            await loadFiles();
        } catch (error) {
            alert(`Erro ao excluir arquivo: ${error.message}`);
        }
    }

    function setupDragAndDrop() {
        const dropZone = mainContent;
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => { e.preventDefault(); e.stopPropagation(); });
        });

        dropZone.addEventListener('dragenter', () => {
            if (currentChatId) { dropZone.classList.add('drag-over'); }
        });

        dropZone.addEventListener('dragleave', (e) => {
            if (!e.currentTarget.contains(e.relatedTarget)) {
                dropZone.classList.remove('drag-over');
            }
        });

        dropZone.addEventListener('drop', async (e) => {
            if (!currentChatId) return;
            dropZone.classList.remove('drag-over');
            const files = e.dataTransfer.files;
            if (files && files.length > 0) {
                const uploadPromises = Array.from(files).map(file => uploadFile(file));
                await Promise.all(uploadPromises);
                await loadFiles();
            }
        });
    }

    // --- EVENT LISTENERS ---
    sendButton.addEventListener('click', handleSendMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); }
    });
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = `${chatInput.scrollHeight}px`;
    });
    fileUpload.addEventListener('change', handleFileInputChange);
    newChatBtn.addEventListener('click', createNewChat);
    toggleChatPaneBtn.addEventListener('click', () => togglePane('chat'));
    toggleFilesPaneBtn.addEventListener('click', () => togglePane('files'));

    // --- INICIALIZAÇÃO ---
    initializeApp();
    setupDragAndDrop();
});