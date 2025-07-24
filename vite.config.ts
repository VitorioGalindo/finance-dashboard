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
      server: {
        proxy: {
          // As chamadas para /api serão redirecionadas para o backend
          '/api': {
            target: 'http://127.0.0.1:5000',
            changeOrigin: true,
            // A linha 'rewrite' foi removida.
            // Agora, uma chamada para /api/portfolio/config será enviada como tal para o backend.
          },
        },
      },
    };
});
