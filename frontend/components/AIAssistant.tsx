import React, { useState, useRef, useEffect } from 'react';
import { Chat, ChatMessage } from '../types';
import { geminiService } from '../services/geminiService';
import { PlusIcon, TrashIcon, PaperclipIcon, SparklesIcon, PaperAirplaneIcon } from '../constants';

const SYSTEM_INSTRUCTION = `Você é um assistente de research financeiro especialista chamado 'Apex Analyst'. Sua função é fornecer análises claras, concisas e perspicazes sobre empresas de capital aberto no Brasil e no mundo. Responda em português do Brasil. Seus usuários são investidores e analistas, então use uma linguagem profissional, mas acessível. Ao fornecer dados numéricos, sempre que possível, indique a fonte e a data de referência. Seja objetivo e evite dar conselhos de investimento diretos. Em vez disso, apresente os fatos, prós e contras, para que o usuário possa tomar sua própria decisão informada. Estruture suas respostas com cabeçalhos, listas e tabelas para facilitar a leitura.`;

const AIAssistant: React.FC = () => {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Start with one default chat
    if (chats.length === 0) {
      handleNewChat();
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chats, activeChatId]);

  const handleNewChat = () => {
    const newChat: Chat = {
      id: `chat-${Date.now()}`,
      title: `Nova Conversa (${new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })})`,
      messages: [],
    };
    setChats(prev => [newChat, ...prev]);
    setActiveChatId(newChat.id);
    setInput('');
    setFiles([]);
  };

  const handleDeleteChat = (chatId: string) => {
    setChats(prev => prev.filter(c => c.id !== chatId));
    if (activeChatId === chatId) {
      if (chats.length > 1) {
        setActiveChatId(chats.filter(c => c.id !== chatId)[0]?.id || null);
      } else {
        handleNewChat();
      }
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setFiles(prev => [...prev, ...Array.from(event.target.files!)]);
    }
  };
  
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !activeChatId) return;

    const userMessageContent = files.length > 0
      ? `Analisando os arquivos: [${files.map(f => f.name).join(', ')}]\n\n${input}`
      : input;
      
    const userMessage: ChatMessage = { 
      role: 'user', 
      content: userMessageContent,
      files: files.map(f => ({ name: f.name, type: f.type, size: f.size })),
    };

    setChats(prev => prev.map(c => c.id === activeChatId ? { ...c, messages: [...c.messages, userMessage] } : c));
    
    setInput('');
    setFiles([]);
    setIsLoading(true);

    try {
      const stream = await geminiService.streamFinancialAnalysis(userMessage.content, SYSTEM_INSTRUCTION);
      
      setChats(prev => prev.map(c => c.id === activeChatId ? { ...c, messages: [...c.messages, { role: 'model', content: ''}] } : c));

      for await (const chunk of stream) {
        setChats(prev => prev.map(c => {
          if (c.id === activeChatId) {
            const lastMessage = c.messages[c.messages.length - 1];
            if (lastMessage.role === 'model') {
              lastMessage.content += chunk;
            }
            return { ...c };
          }
          return c;
        }));
      }

    } catch (error) {
      console.error("Error calling Gemini API:", error);
      const errorMessage: ChatMessage = { role: 'model', content: "Desculpe, ocorreu um erro ao processar sua solicitação." };
       setChats(prev => prev.map(c => c.id === activeChatId ? { ...c, messages: [...c.messages, errorMessage] } : c));
    } finally {
      setIsLoading(false);
    }
  };

  const activeChat = chats.find(c => c.id === activeChatId);

  return (
    <div className="flex h-[calc(100vh-6rem)] bg-slate-900 text-slate-300">
      {/* Left Sidebar for Chats and Assistants */}
      <div className="w-80 bg-slate-800/50 border-r border-slate-700 flex flex-col p-2">
        <button onClick={handleNewChat} className="flex items-center justify-center w-full p-2 mb-4 text-sm font-semibold text-white bg-sky-600 rounded-md hover:bg-sky-500 transition-colors">
          <PlusIcon /> <span className="ml-2">Novo Chat</span>
        </button>
        <p className="text-xs text-slate-500 font-semibold uppercase px-2 mb-2">Conversas</p>
        <div className="flex-grow overflow-y-auto pr-1">
          {chats.map(chat => (
            <div key={chat.id} className="relative group">
              <button 
                onClick={() => setActiveChatId(chat.id)}
                className={`w-full text-left p-2 my-1 text-sm rounded-md truncate ${activeChatId === chat.id ? 'bg-slate-700' : 'hover:bg-slate-700/50'}`}
              >
                {chat.title}
              </button>
              <button onClick={() => handleDeleteChat(chat.id)} className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity">
                <TrashIcon />
              </button>
            </div>
          ))}
        </div>
        <div className="border-t border-slate-700 pt-2 mt-2">
          <div className="w-full text-left p-3 my-1 rounded-lg bg-slate-700 border-2 border-sky-500">
              <h4 className="font-semibold text-white">Apex Analyst</h4>
              <p className="text-xs text-slate-400">Análise de empresas de capital aberto no Brasil.</p>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {activeChat ? (
          <>
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {activeChat.messages.map((msg, index) => (
                 <div key={index} className={`flex items-start gap-4 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                    {msg.role === 'model' && (
                      <div className="w-8 h-8 rounded-full bg-sky-500/20 flex items-center justify-center shrink-0">
                        <SparklesIcon />
                      </div>
                    )}
                    <div className={`max-w-2xl p-4 rounded-lg shadow-md ${msg.role === 'user' ? 'bg-sky-600 text-white' : 'bg-slate-700 text-slate-200'}`}>
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                       {msg.files && msg.files.length > 0 && (
                          <div className="mt-3 border-t border-sky-500/50 pt-2">
                            <p className="text-xs font-semibold">Arquivos Anexados:</p>
                            <ul className="text-xs list-disc list-inside">
                              {msg.files.map(f => <li key={f.name}>{f.name}</li>)}
                            </ul>
                          </div>
                       )}
                    </div>
                  </div>
              ))}
              {isLoading && (
                 <div className="flex items-start gap-4">
                     <div className="w-8 h-8 rounded-full bg-sky-500/20 flex items-center justify-center shrink-0"><SparklesIcon /></div>
                     <div className="bg-slate-700 text-slate-200 p-4 rounded-lg">
                        <div className="flex items-center space-x-1">
                            <span className="w-2 h-2 bg-slate-400 rounded-full animate-pulse delay-0"></span>
                            <span className="w-2 h-2 bg-slate-400 rounded-full animate-pulse delay-200"></span>
                            <span className="w-2 h-2 bg-slate-400 rounded-full animate-pulse delay-400"></span>
                        </div>
                    </div>
                 </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="p-4 border-t border-slate-700">
               {files.length > 0 && (
                  <div className="p-3 mb-2 bg-slate-700/50 rounded-md">
                     <h4 className="text-sm font-semibold mb-2">Ambiente de Trabalho</h4>
                     <div className="flex flex-wrap gap-2">
                        {files.map((file, i) => (
                           <div key={i} className="bg-slate-600 text-xs px-2 py-1 rounded-full flex items-center gap-2">
                              <span>{file.name}</span>
                              <button onClick={() => setFiles(f => f.filter(fl => fl.name !== file.name))} className="text-slate-400 hover:text-white">✕</button>
                           </div>
                        ))}
                     </div>
                     <button onClick={() => setFiles([])} className="text-xs text-red-400 hover:underline mt-2">Limpar</button>
                  </div>
               )}

              <form onSubmit={handleSendMessage} className="relative">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage(e);
                    }
                  }}
                  placeholder="Enviar uma mensagem para Apex Analyst... (Shift+Enter para nova linha)"
                  className="w-full bg-slate-700 border border-slate-600 rounded-md py-3 pl-12 pr-12 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 resize-none"
                  rows={1}
                  disabled={isLoading}
                  style={{ maxHeight: '200px', overflowY: 'auto' }}
                />
                <button type="button" onClick={() => fileInputRef.current?.click()} className="absolute left-3 top-1/2 -translate-y-1/2 p-2 text-slate-400 hover:text-sky-400">
                  <PaperclipIcon />
                </button>
                <input type="file" ref={fileInputRef} onChange={handleFileChange} multiple hidden />
                <button
                  type="submit"
                  disabled={isLoading || !input.trim()}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-md bg-sky-600 text-white hover:bg-sky-500 disabled:bg-slate-600 disabled:cursor-not-allowed transition-colors"
                >
                  <PaperAirplaneIcon />
                </button>
              </form>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-500">
            <p>Selecione ou crie uma nova conversa para começar.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIAssistant;