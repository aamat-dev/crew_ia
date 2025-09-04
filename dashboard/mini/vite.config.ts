import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, resolve(__dirname, '../..'), '');
  const repo = env.GITHUB_REPOSITORY?.split('/')[1] ?? '';
  return {
    envDir: '../..',
    base: repo ? `/${repo}/` : '/',
    plugins: [react()],
    resolve: {
      alias: {
        'node-websocket': false,
        ws: false,
      },
    },
    server: {
      host: true, // équivaut à 0.0.0.0
      port: 5173,
      strictPort: true, // échoue si port occupé
    },
    preview: {
      host: true,
      port: 5173,
      strictPort: true,
    },
  };
});
