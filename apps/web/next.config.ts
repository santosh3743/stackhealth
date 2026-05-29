import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Standalone output produces a self-contained server bundle for Docker.
  output: "standalone",
  experimental: {
    typedRoutes: true,
  },
  async rewrites() {
    // Proxy /api/* to the backend during local development.
    // In production, the frontend talks directly to api.stackhealth.dev.
    if (process.env.NODE_ENV === "development") {
      return [
        {
          source: "/api/:path*",
          destination: `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/:path*`,
        },
      ];
    }
    return [];
  },
};

export default nextConfig;
