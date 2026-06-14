import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["127.0.0.1"],
  skipTrailingSlashRedirect: true,
  async rewrites() {
    const backendUrl = process.env.MAINTOLIO_BACKEND_URL ?? "http://127.0.0.1:8000";

    return [
      {
        source: "/api/:path*/",
        destination: `${backendUrl}/api/:path*/`,
      },
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: "/media/:path*/",
        destination: `${backendUrl}/media/:path*/`,
      },
      {
        source: "/media/:path*",
        destination: `${backendUrl}/media/:path*`,
      },
    ];
  },
};

export default nextConfig;
