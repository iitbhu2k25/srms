import type { NextConfig } from "next";

// /api/* is proxied to the FastAPI backend by src/app/api/[...path]/route.ts (API_URL in .env),
// so the browser only ever calls this site.
const nextConfig: NextConfig = {
  output: "standalone",
  reactStrictMode: true,
};

export default nextConfig;
