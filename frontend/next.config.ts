import type { NextConfig } from "next";

/**
 * The browser only calls same-origin /api/backend/* paths, which are served by route handlers in
 * src/app/api/backend (read-only GET allowlist plus POST /ask). They read CONTROLSHIFT_API_URL at
 * request time, so the backend address is never compiled in or shipped to the browser.
 */
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
};

export default nextConfig;
