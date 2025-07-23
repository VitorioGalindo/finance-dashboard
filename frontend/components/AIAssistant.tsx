import React, { useState, useRef, useEffect } from 'react';
import { geminiService } from '../services/geminiService';
import { SparklesIcon, PaperAirplaneIcon } from '../constants';

// Definimos a interface da mensagem aqui para manter o componente autocontido
// e garantir que ela corresponda ao que o backend e o serviço esperam.
interface Message {
  role: 'user' | 'assistant';
  content: string;
}

// A persona do assistente é definida no backend, mas usamos estes
// detalhes para a interface do usuário.
const assistantDetails = {
  name: 'Apex Analyst',
  description: 'Seu especialista em análise de ações brasileiras.',
};

const AIAssistant: React.FC = () => {
  // Estado simplificado para uma única conversa contínua
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Efeito para rolar para a última mensagem sempre que a lista for atualizada
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Efeito para exibir uma mensagem de boas-vindas na primeira carga
  useEffect(() => {
    setMessages([
      {
        role: 'assistant',
        content: `Olá! Eu sou o ${assistantDetails.name}. Envie uma pergunta ou o nome de uma empresa para começar a análise.`
      }
    ]);
  }, []);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input };
    const newMessages = [...messages, userMessage];
    
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);

    try {
      // O histórico enviado para a API não deve incluir a mensagem inicial de boas-vindas do frontend.
      const history = newMessages.slice(1);
      
      // Chama o nosso novo serviço, que se comunica com o backend seguro.
      const aiResponseContent = await geminiService.getAIAssistantResponse(input, history);
      
      const aiMessage: Message = { role: 'assistant', content: aiResponseContent };
      setMessages(prev => [...prev, aiMessage]);

    } catch (error: any) {
      console.error("Falha ao chamar a API do backend:", error);
      const errorMessage: Message = { 
        role: 'assistant', 
        content: `Desculpe, ocorreu um erro: ${error.message || "Não foi possível conectar ao servidor."}` 
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-6rem)] bg-slate-900 text-slate-300">
      {/* Sidebar Simplificada com informações do Assistente */}
      <div className="w-80 bg-slate-800/50 border-r border-slate-700 flex flex-col p-4">
          <div className="flex items-center mb-4">
             <div className="w-12 h-12 rounded-full bg-sky-500/20 flex items-center justify-center shrink-0 mr-3">
                <SparklesIcon />
              </div>
              <div>
                <h2 className="font-semibold text-white text-lg">{assistantDetails.name}</h2>
                <p className="text-sm text-slate-400">{assistantDetails.description}</p>
              </div>
          </div>
          <div className="text-xs text-slate-500 bg-slate-800 p-3 rounded-lg">
            <p><strong>Aviso Legal:</strong> As análises são geradas por um modelo de linguagem e não constituem recomendação financeira. Utilize apenas para fins educacionais e de demonstração.</p>
          </div>
      </div>

      {/* Área Principal do Chat */}
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg, index) => (
             <div key={index} className={`flex items-start gap-4 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-sky-500/20 flex items-center justify-center shrink-0">
                    <SparklesIcon />
                  </div>
                )}
                <div className={`max-w-3xl p-4 rounded-lg shadow-md prose prose-invert prose-slate ${msg.role === 'user' ? 'bg-sky-600 text-white' : 'bg-slate-700 text-slate-200'}`}>
                  <p className="whitespace-pre-wrap">{msg.content}</p>
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
              placeholder={`Enviar uma mensagem para ${assistantDetails.name}...`}
              className="w-full bg-slate-700 border border-slate-600 rounded-md py-3 pl-4 pr-12 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 resize-none"
              rows={1}
              disabled={isLoading}
              style={{ maxHeight: '200px', overflowY: 'auto' }}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-md bg-sky-600 text-white hover:bg-sky-500 disabled:bg-slate-600 disabled:cursor-not-allowed transition-colors"
            >
              <PaperAirplaneIcon />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AIAssistant;
