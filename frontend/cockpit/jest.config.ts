import type { Config } from "jest";

const ENFORCE = process.env.ENFORCE_COVERAGE === '1' || process.env.ENFORCE_COVERAGE === 'true';

const config: Config = {
  testEnvironment: "jest-environment-jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  testMatch: ["**/__tests__/**/*.(test|spec).(ts|tsx)"],
  collectCoverageFrom: [
    // Cible: noyau DS + composants UI unit-testables + lib
    "src/components/kpi/**/*.{ts,tsx}",
    "src/components/ds/Button.tsx",
    "src/components/ds/Input.tsx",
    // Exclusions spécifiques
    "!src/**/*.stories.{ts,tsx}",
    "!src/components/ds/Skeleton.tsx",
  ],
  coverageDirectory: "coverage",
  coverageReporters: ["text", "text-summary", "lcov", "html"],
  coverageThreshold: ENFORCE
    ? { global: { statements: 85, branches: 85, functions: 85, lines: 85 } }
    : undefined,
  transform: {
    "^.+\\.(t|j)sx?$": [
      "@swc/jest",
      {
        jsc: {
          transform: {
            react: {
              runtime: "automatic",
              development: process.env.NODE_ENV === "test",
            },
          },
        },
      },
    ],
  },
};

export default config;
