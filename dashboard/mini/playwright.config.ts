import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './',
  testMatch: ['tests-e2e/**/*.spec.ts', 'tests/e2e/**/*.spec.ts'],
  timeout: 30000,
});
