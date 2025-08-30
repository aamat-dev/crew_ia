import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Détecte le nom du dépôt pour configurer la base GitHub Pages
const repo = process.env.GITHUB_REPOSITORY?.split('/')[1] ?? '';

// https://vitejs.dev/config/
export default defineConfig({
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
});
