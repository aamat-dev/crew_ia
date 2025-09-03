import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    turbopack: {
      root: __dirname, // force le root sur apps/cockpit
    },
  },
};

export default nextConfig;
