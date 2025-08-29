import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    env: {
      VITE_API_BASE_URL: 'http://localhost:8000',
      VITE_API_TIMEOUT_MS: '15000',
      VITE_DEMO_API_KEY: 'demo-key',
    },
    coverage: {
      reporter: ['text-summary', 'lcov'],
      thresholds: {
        lines: 85,
        functions: 85,
        branches: 85,
        statements: 85,
      },
    },
  },
  esbuild: {
    jsx: 'automatic',
  },
});
