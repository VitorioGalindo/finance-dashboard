// frontend/services/geminiService.ts

import { Message } from '../types';

// A URL base da nossa API Flask.
// Em um ambiente de produção, isso viria de uma variável de ambiente.
const API_BASE_URL = 'http://127.0.0.1:5000';

/**
 * Envia um prompt e o histórico da conversa para o backend e obtém a resposta do 'Apex Analyst'.
 *
 * @param prompt - A nova mensagem do usuário.
 * @param history - Uma lista de mensagens anteriores na conversa.
 * @returns Uma string contendo a resposta do assistente de IA.
 * @throws Lança um erro se a resposta da rede não for bem-sucedida.
 */
const getAIAssistantResponse = async (prompt: string, history: Message[]): Promise<string> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/ai/analyst`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt: prompt,
        history: history,
      }),
    });

    if (!response.ok) {
      // Tenta ler a mensagem de erro do backend, se houver
      const errorData = await response.json().catch(() => null);
      const errorMessage = errorData?.description || `Erro do servidor: ${response.status}`;
      console.error('Falha ao obter resposta da API:', errorMessage);
      throw new Error(errorMessage);
    }

    const data = await response.json();
    return data.content;

  } catch (error) {
    console.error('Erro de comunicação com o backend:', error);
    // Propaga um erro mais amigável para a UI
    throw new Error('Não foi possível conectar ao serviço de IA. Verifique sua conexão e tente novamente.');
  }
};

export const geminiService = {
  getAIAssistantResponse,
};
