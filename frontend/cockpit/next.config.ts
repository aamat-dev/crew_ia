import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    turbopack: {
      root: __dirname, // force le root sur frontend/cockpit
    },
  },
};

export default nextConfig;
