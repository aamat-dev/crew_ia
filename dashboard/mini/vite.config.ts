import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,        // équivaut à 0.0.0.0
    port: 5173,
    strictPort: true,  // échoue si port occupé
  },
  preview: {
    host: true,
    port: 5173,
    strictPort: true,
  },
});
