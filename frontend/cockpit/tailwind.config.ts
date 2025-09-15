/**
 * Tailwind v4 — Configuration minimale.
 *
 * Remarque importante:
 * - Les tokens de design (couleurs, radius, ombres, etc.) sont centralisés
 *   dans `src/app/globals.css` via `@theme inline`.
 * - Ce fichier sert d’emplacement de configuration pour l’éditeur et
 *   d’extension future si besoin. Aucune dépendance additionnelle.
 */
import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{ts,tsx,js,jsx}"],
  darkMode: ["class", '[data-theme="dark"]'],
  theme: {
    extend: {},
  },
  plugins: [],
} satisfies Config;

