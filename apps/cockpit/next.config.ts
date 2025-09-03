import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Config minimale; on retirera/rajoutera proprement plus tard si besoin.
  experimental: {
    turbopack: {
      root: __dirname,
    },
  },
};

export default nextConfig;
