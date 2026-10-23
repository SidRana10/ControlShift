import type { NextConfig } from "next";

/**
 * Same-origin proxy to the FastAPI service. The browser only ever calls /api/backend/*, so no CORS
 * is needed and the backend address is never shipped to the client.
 *
 * CONTROLSHIFT_API_URL is read by the Next.js server when `next dev` / `next build` starts
 * (rewrites are resolved at build time for `next start`). Default: http://127.0.0.1:8000.
 *
 * Only the read-only endpoints below are proxied by rewrite (every one is GET-only in FastAPI).
 * POST /ask is served by the route handler in src/app/api/backend/ask/route.ts, which takes
 * precedence over rewrites and forwards a fixed field set. /compare is deliberately absent.
 */
const API_URL = (process.env.CONTROLSHIFT_API_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  async rewrites() {
    return [
      { source: "/api/backend/health", destination: `${API_URL}/health` },
      { source: "/api/backend/catalog/versions", destination: `${API_URL}/catalog/versions` },
      { source: "/api/backend/catalog/elements", destination: `${API_URL}/catalog/elements` },
      {
        source: "/api/backend/catalog/elements/:version/:element_id",
        destination: `${API_URL}/catalog/elements/:version/:element_id`,
      },
    ];
  },
};

export default nextConfig;
