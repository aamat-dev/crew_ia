import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    // Autorise l'accès dev depuis l'IP locale et localhost
    allowedDevOrigins: [
      "http://192.168.1.50:3000",
      "http://localhost:3000",
    ],
  },
};

export default nextConfig;
