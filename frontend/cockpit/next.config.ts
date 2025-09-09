import type { NextConfig } from "next";
import fs from "fs";
import path from "path";

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
  experimental: {
    turbopack: {
      root: __dirname, // force le root sur frontend/cockpit
    },
  },
};

export default nextConfig;
