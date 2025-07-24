import path from 'path';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    return {
      define: {
        'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
        'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
        }
      },
      // --- Configuração de Proxy para o Backend ---
      server: {
        proxy: {
          '/api': {
            target: 'http://127.0.0.1:5000', // Endereço do seu backend Flask
            changeOrigin: true, // Necessário para hosts virtuais
            rewrite: (path) => path.replace(/^/api/, ''), // Remove /api do path enviado para o backend
          },
        },
      },
      // --- Fim da Configuração de Proxy ---
    };
});
