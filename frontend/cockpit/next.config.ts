import type { NextConfig } from "next";
import fs from "fs";
import path from "path";

// Note de stabilité (Codex):
// - Nettoyage des clés expérimentales: aucune clé obsolète (ex: experimental.allowedDevOrigins) n'est utilisée.
// - Déclaration minimale de Turbopack: on fixe explicitement la racine au package cockpit
//   pour un monorepo, afin d'éviter les résolutions ambiguës.
// - L'objectif est d'éviter tout warning Next inconnu tout en gardant un build/dev stables.

// Charge les variables d'env depuis la racine du repo (un seul .env)
try {
  const rootEnvPath = path.resolve(__dirname, "..", "..", ".env");
  if (fs.existsSync(rootEnvPath)) {
    const raw = fs.readFileSync(rootEnvPath, "utf-8");
    for (const line of raw.split(/\r?\n/)) {
      if (!line || line.trim().startsWith("#")) continue;
      const idx = line.indexOf("=");
      if (idx <= 0) continue;
      const key = line.slice(0, idx).trim();
      let value = line.slice(idx + 1).trim();
      if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }
      if (!(key in process.env)) {
        process.env[key] = value;
      }
    }
  }
} catch {
  // ignore: fallback to existing environment
}

const nextConfig: NextConfig = {
  // Strict mode activé par défaut (Next >=13); laissé implicite.
  // reactStrictMode: true,
  experimental: {
    // Seules options supportées utilisées ici — pas de clés inconnues.
    turbopack: {
      // Racine explicite de l'app cockpit dans un monorepo
      root: __dirname,
    },
  },
};

export default nextConfig;
