const API_BASE_URL = 'http://127.0.0.1:5000';

let activeAssistantId = null;
let activeChatId = null;

// Elementos da UI
const assistantsSidebar = document.getElementById('assistants-sidebar');
const chatListContainer = document.getElementById('chat-list-container');
const newChatButton = document.getElementById('new-chat-btn');
const mainContent = document.getElementById('main-content');
const welcomeScreen = document.getElementById('welcome-screen');
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const chatThinkingIndicator = document.getElementById('chat-thinking-indicator');
const fileList = document.getElementById('file-list');
const fileUploadInput = document.getElementById('file-upload');

// NOVOS ELEMENTOS: Título do chat e botões de exclusão
// É CRUCIAL que estes elementos existam no index.html com estes IDs!
const chatTitle = document.getElementById('chat-title');
const deleteChatButton = document.getElementById('delete-chat-btn');
const deleteAllFilesButton = document.getElementById('delete-all-files-btn');

// Botões de expandir/recolher painéis
// É CRUCIAL que estes elementos existam no index.html com estes IDs!
const toggleChatPaneBtn = document.getElementById('toggle-chat-pane');
const toggleFilesPaneBtn = document.getElementById('toggle-files-pane');


// --- INICIALIZAÇÃO E CARREGAMENTO ---

document.addEventListener('DOMContentLoaded', async () => {
    // Carrega os assistentes ao iniciar a página
    await loadAssistants();

    // Adiciona event listeners para os botões e input
    if (newChatButton) newChatButton.addEventListener('click', createNewChat);
    if (sendButton) sendButton.addEventListener('click', sendMessage);
    if (chatInput) {
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) { // Enviar com Enter, nova linha com Shift+Enter
                e.preventDefault();
                sendMessage();
            }
        });
    }
    if (fileUploadInput) fileUploadInput.addEventListener('change', handleFileUpload);
    
    // NOVOS LISTENERS para os botões de exclusão
    // Adicionando verificação para garantir que os elementos existem antes de adicionar listeners
    if (deleteChatButton) {
        deleteChatButton.addEventListener('click', deleteCurrentChat);
    } else {
        console.warn("Elemento #delete-chat-btn não encontrado. O botão de excluir chat pode não funcionar.");
    }
    
    if (deleteAllFilesButton) {
        deleteAllFilesButton.addEventListener('click', deleteAllFiles);
    } else {
        console.warn("Elemento #delete-all-files-btn não encontrado. O botão de limpar ambiente pode não funcionar.");
    }
    
    // Lógica para expandir/recolher painéis
    [toggleChatPaneBtn, toggleFilesPaneBtn].forEach(btn => {
        if (btn) { // Verifica se o botão existe
            btn.addEventListener('click', () => {
                // Encontra o contêiner pai do botão (o 'card' inteiro)
                const pane = btn.closest('.card');
                
                // Alterna a classe 'expanded-pane' para controlar o CSS (ver style.css)
                if (pane) pane.classList.toggle('expanded-pane');

                // Determina qual é o outro painel
                const otherPaneId = (pane && pane.id === 'chat-pane' ? 'files-pane' : 'chat-pane');
                const otherPane = document.getElementById(otherPaneId);

                // Se o painel atual expandiu, esconde o outro. Caso contrário, mostra o outro.
                if (pane && pane.classList.contains('expanded-pane')) {
                    if (otherPane) otherPane.classList.add('hidden');
                } else {
                    if (otherPane) otherPane.classList.remove('hidden');
                }
            });
        } else {
            console.warn(Um dos botões de alternância de painel não foi encontrado: ${btn === toggleChatPaneBtn ? '#toggle-chat-pane' : '#toggle-files-pane'}.);
        }
    });
});

async function loadAssistants() {
    try {
        const response = await fetch(${API_BASE_URL}/api/assistants);
        const assistants = await response.json();
        
        // Garante que o container da sidebar existe e está limpo
        if (!assistantsSidebar) {
            console.error("Elemento #assistants-sidebar não encontrado. Não é possível carregar assistentes.");
            return;
        }

        // Limpa a barra lateral antes de adicionar os assistentes
        // Poderia ser mais granular, mas para este projeto simples, limpar e recriar é ok.
        // Assegura que o botão newChatButton e chatListContainer são preservados.
        const existingAssistantCards = assistantsSidebar.querySelectorAll('.assistant-card');
        existingAssistantCards.forEach(card => card.remove());
        
        assistants.forEach(assistant => {
            const assistantCard = document.createElement('div');
            assistantCard.className = 'card assistant-card'; // Classe para estilização e seleção
            assistantCard.dataset.assistantId = assistant.id; // Armazena o ID para referência
            assistantCard.innerHTML = 
                <h3 class="font-semibold text-lg text-white">${assistant.name}</h3>
                <p class="text-sm text-gray-400">${assistant.description}</p>;
            assistantCard.addEventListener('click', () => selectAssistant(assistant.id));
            
            // Adiciona o card antes do container da lista de chats (se existir)
            if (chatListContainer) {
                assistantsSidebar.insertBefore(assistantCard, chatListContainer);
            } else {
                assistantsSidebar.appendChild(assistantCard); // Se chatListContainer não existir, adiciona no final
            }
        });
    } catch (error) {
        console.error('Falha ao carregar assistentes:', error);
        alert('Erro ao carregar assistentes. Verifique a API do backend e a chave GOOGLE_API_KEY.');
    }
}

async function selectAssistant(assistantId) {
    // Remove a classe 'active' de todos os cards e adiciona ao selecionado
    document.querySelectorAll('.assistant-card').forEach(card => card.classList.remove('active'));
    const selectedAssistantCard = document.querySelector(.assistant-card[data-assistant-id="${assistantId}"]);
    if (selectedAssistantCard) {
        selectedAssistantCard.classList.add('active');
    }
    
    activeAssistantId = assistantId;
    if (newChatButton) newChatButton.classList.remove('hidden'); // Mostra o botão "Novo Chat"
    
    await loadChatList(assistantId); // Carrega a lista de chats para o assistente selecionado

    // Esconde o conteúdo principal e mostra a tela de boas-vindas ao mudar de assistente
    if (mainContent) mainContent.classList.add('hidden');
    if (welcomeScreen) welcomeScreen.classList.remove('hidden');
    activeChatId = null; // Reseta o chat ativo
    if (deleteChatButton) { // Verifica se o botão existe antes de manipular
        deleteChatButton.classList.add('hidden'); // Esconde o botão de excluir chat
    }
}

async function loadChatList(assistantId) {
    try {
        const response = await fetch(${API_BASE_URL}/api/chats/${assistantId});
        const chats = await response.json();
        
        if (!chatListContainer) {
            console.error("Elemento #chat-list-container não encontrado. Não é possível carregar a lista de chats.");
            return;
        }
        chatListContainer.innerHTML = ''; // Limpa a lista antes de preencher
        
        chats.forEach(chat => {
            const chatItem = document.createElement('div');
            chatItem.className = 'chat-item'; // Classe para estilização e seleção
            chatItem.dataset.chatId = chat.id; // Armazena o ID do chat
            chatItem.innerHTML = <p>${chat.name}</p>;
            // Event listener para selecionar/abrir um chat existente
            chatItem.addEventListener('click', (e) => {
                e.stopPropagation(); // Evita que o clique se propague para elementos pai
                selectChat(assistantId, chat.id);
            });
            chatListContainer.appendChild(chatItem);
        });
    } catch (error) {
        console.error('Falha ao carregar chats:', error);
        alert('Erro ao carregar lista de chats.');
    }
}

async function selectChat(assistantId, chatId) {
    activeChatId = chatId;
    // Remove a classe 'active' de todos os itens de chat e adiciona ao selecionado
    document.querySelectorAll('.chat-item').forEach(item => item.classList.remove('active'));
    const selectedChatItem = document.querySelector(.chat-item[data-chat-id="${chatId}"]);
    if (selectedChatItem) {
        selectedChatItem.classList.add('active');
    }

    // Mostra o conteúdo principal (chat e arquivos) e esconde a tela de boas-vindas
    if (mainContent) mainContent.classList.remove('hidden');
    if (welcomeScreen) welcomeScreen.classList.add('hidden');

    await loadChatHistory(assistantId, chatId); // Carrega as mensagens do chat
    await loadFilesForChat(assistantId, chatId); // Carrega os arquivos do ambiente de trabalho

    // ATUALIZADO: Atualiza o título do chat e mostra o botão de exclusão
    const chatElement = document.querySelector(.chat-item[data-chat-id="${chatId}"] p);
    if (chatTitle) { // Verifica se o elemento existe
        chatTitle.textContent = chatElement ? chatElement.textContent : 'Chat'; // Define o título
    }
    if (deleteChatButton) { // Verifica se o botão existe
        deleteChatButton.classList.remove('hidden'); // Mostra o botão de exclusão do chat
    }
}

// --- AÇÕES DO CHAT ---

async function createNewChat() {
    if (!activeAssistantId) return; // Só cria chat se um assistente estiver selecionado
    try {
        const response = await fetch(${API_BASE_URL}/api/chats/${activeAssistantId}, { method: 'POST' });
        const newChat = await response.json();
        await loadChatList(activeAssistantId); // Recarrega a lista para incluir o novo chat
        selectChat(activeAssistantId, newChat.id); // Seleciona e abre o novo chat
    } catch (error) {
        console.error('Falha ao criar novo chat:', error);
        alert('Erro ao criar novo chat.');
    }
}

async function loadChatHistory(assistantId, chatId) {
    if (!chatMessages) {
        console.error("Elemento #chat-messages não encontrado. Não é possível carregar o histórico.");
        return;
    }
    chatMessages.innerHTML = ''; // Limpa as mensagens antes de carregar
    try {
        const response = await fetch(${API_BASE_URL}/api/chats/${assistantId}/${chatId});
        const messages = await response.json();
        messages.forEach(msg => addMessageToUI(msg.role, msg.content)); // Adiciona cada mensagem à UI
    } catch (error) {
        console.error('Falha ao carregar histórico:', error);
        alert('Erro ao carregar histórico do chat.');
    }
}

async function sendMessage() {
    const prompt = chatInput.value.trim();
    if (!prompt || !activeChatId) return; // Não envia se o prompt estiver vazio ou nenhum chat selecionado

    addMessageToUI('user', prompt); // Adiciona a mensagem do usuário à UI
    chatInput.value = ''; // Limpa o input
    if (chatThinkingIndicator) chatThinkingIndicator.classList.remove('hidden'); // Mostra o indicador de "digitando"
    if (sendButton) sendButton.disabled = true; // Desabilita o botão para evitar múltiplos envios

    try {
        const response = await fetch(${API_BASE_URL}/api/chats/${activeAssistantId}/${activeChatId}, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt }),
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Erro desconhecido ao enviar mensagem.');
        }
        const data = await response.json();
        addMessageToUI(data.role, data.content); // Adiciona a resposta do assistente à UI
    } catch (error) {
        console.error('Falha ao enviar mensagem:', error);
        addMessageToUI('system', Erro: ${error.message}); // Exibe erro na UI
    } finally {
        if (chatThinkingIndicator) chatThinkingIndicator.classList.add('hidden'); // Esconde o indicador
        if (sendButton) sendButton.disabled = false; // Habilita o botão novamente
        if (chatInput) chatInput.focus(); // Coloca o foco de volta no input
    }
}

function addMessageToUI(role, content) {
    if (!chatMessages) {
        console.error("Elemento #chat-messages não encontrado. Não é possível adicionar a mensagem.");
        return;
    }
    const messageDiv = document.createElement('div');
    messageDiv.className = message ${role}; // Adiciona classes para estilização (CSS)
    
    // Tratamento básico de Markdown para blocos de código e código inline
    content = content.replace(/
(\w)\n([\s\S]?)
/g, '<pre><code class="language-$1">$2</code></pre>');
    content = content.replace(/([^]+)/g, '<code>$1</code>');
    
    messageDiv.innerHTML = <p>${content.replace(/\n/g, '<br>')}</p>; // Substitui \n por <br> para quebras de linha no HTML
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight; // Rola para o final do chat
}

// --- GERENCIAMENTO DE ARQUIVOS ---

async function loadFilesForChat(assistantId, chatId) {
    if (!fileList) {
        console.error("Elemento #file-list não encontrado. Não é possível carregar arquivos.");
        return;
    }
    fileList.innerHTML = ''; // Limpa a lista de arquivos antes de carregar
    try {
        const response = await fetch(${API_BASE_URL}/api/chats/${assistantId}/${chatId}/files);
        const files = await response.json();
        files.forEach(addFileToUI); // Adiciona cada arquivo à UI
    } catch (error) {
        console.error('Falha ao carregar arquivos:', error);
        alert('Erro ao carregar arquivos do ambiente de trabalho.');
    }
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file || !activeChatId) return; // Não faz upload se não houver arquivo ou chat selecionado

    const formData = new FormData();
    formData.append('file', file); // Adiciona o arquivo ao FormData

    try {
        const response = await fetch(${API_BASE_URL}/api/chats/${activeAssistantId}/${activeChatId}/files, {
            method: 'POST',
            body: formData,
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Erro desconhecido no upload.');
        }

        // Feedback aprimorado para arquivos ZIP
        if (data.extracted_files) {
            alert(ZIP '${data.filename}' enviado. Arquivos extraídos:\n- ${data.extracted_files.join('\n- ')});
            await loadFilesForChat(activeAssistantId, activeChatId); // Recarrega a lista para mostrar os arquivos extraídos
        } else {
            addFileToUI(data.filename); // Adiciona o arquivo único à UI
        }
    } catch (error) {
        console.error('Falha no upload:', error);
        alert(Erro no upload: ${error.message}); // CORRIGIDO: Uso de template literal
    } finally {
        if (fileUploadInput) fileUploadInput.value = ''; // Limpa o input de arquivo após o upload
    }
}

function addFileToUI(filename) {
    if (!fileList) {
        console.error("Elemento #file-list não encontrado. Não é possível adicionar o arquivo à UI.");
        return;
    }
    const fileDiv = document.createElement('div');
    fileDiv.className = 'file-item'; // Classe para estilização
    fileDiv.dataset.filename = filename; // Armazena o nome do arquivo para referência
    fileDiv.innerHTML = 
        <span>${filename}</span>
        <button class="delete-file-btn" title="Excluir arquivo">&times;</button>;
    // Event listener para o botão de exclusão de arquivo individual
    fileDiv.querySelector('.delete-file-btn').addEventListener('click', (e) => {
        e.stopPropagation(); // Evita que o clique se propague
        deleteFile(filename);
    });
    fileList.appendChild(fileDiv);
}

async function deleteFile(filename) {
    if (!confirm(Tem certeza que deseja excluir o arquivo "${filename}"?)) return; // Confirmação
    try {
        const response = await fetch(${API_BASE_URL}/api/chats/${activeAssistantId}/${activeChatId}/${filename}, { method: 'DELETE' });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Erro ao excluir arquivo.');
        }
        document.querySelector(.file-item[data-filename="${filename}"])?.remove(); // Remove o item da UI
    } catch (error) {
        console.error('Falha ao excluir arquivo:', error);
        alert(Não foi possível excluir o arquivo: ${error.message}); // CORRIGIDO: Uso de template literal
    }
}

// --- NOVAS FUNÇÕES DE EXCLUSÃO (para chats e todos os arquivos) ---

async function deleteCurrentChat() {
    if (!activeAssistantId || !activeChatId) return; // Garante que um chat esteja ativo
    
    // Pega o nome do chat para a mensagem de confirmação
    const chatName = document.querySelector(.chat-item[data-chat-id="${activeChatId}"] p)?.textContent || "este chat";
    if (!confirm(Tem certeza que deseja excluir permanentemente "${chatName}" e todos os seus arquivos? Esta ação não pode ser desfeita.)) {
        return; // Cancela se o usuário não confirmar
    }

    try {
        const response = await fetch(${API_BASE_URL}/api/chats/${activeAssistantId}/${activeChatId}, { method: 'DELETE' });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Erro no servidor ao excluir chat.');
        }

        // Remove o chat da lista na UI
        document.querySelector(.chat-item[data-chat-id="${activeChatId}"])?.remove();
        
        // Reseta o estado da UI para a tela de boas-vindas
        activeChatId = null;
        if (mainContent) mainContent.classList.add('hidden');
        if (welcomeScreen) welcomeScreen.classList.remove('hidden');
        if (deleteChatButton) { // Verifica se o botão existe
            deleteChatButton.classList.add('hidden'); // Esconde o botão de exclusão
        }
        
        alert('Chat excluído com sucesso.');
        // Recarrega a lista de chats para garantir que esteja atualizada
        await loadChatList(activeAssistantId);

    } catch (error) {
        console.error('Falha ao excluir chat:', error);
        alert(Não foi possível excluir o chat: ${error.message}); // CORRIGIDO: Uso de template literal
    }
}

async function deleteAllFiles() {
    if (!activeAssistantId || !activeChatId) return; // Garante que um chat esteja ativo
    
    if (!confirm('Tem certeza que deseja excluir TODOS os arquivos do ambiente de trabalho deste chat?')) {
        return; // Cancela se o usuário não confirmar
    }

    try {
        const response = await fetch(${API_BASE_URL}/api/chats/${activeAssistantId}/${activeChatId}/files, { method: 'DELETE' });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Erro no servidor ao limpar arquivos.');
        }
        
        await loadFilesForChat(activeAssistantId, activeChatId); // Recarrega a lista de arquivos (agora estará vazia)
        alert('Ambiente de trabalho limpo com sucesso.');

    } catch (error) {
        console.error('Falha ao excluir todos os arquivos:', error);
        alert(Não foi possível limpar o ambiente: ${error.message}`); // CORRIGIDO: Uso de template literal
    }
}