import path from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: [
      { find: "@", replacement: path.resolve(import.meta.dirname, "src") },
      // Component tests run without the Next.js router: small in-memory stand-ins.
      { find: /^next\/navigation$/, replacement: path.resolve(import.meta.dirname, "src/test/next-navigation.ts") },
      { find: /^next\/link$/, replacement: path.resolve(import.meta.dirname, "src/test/next-link.tsx") },
    ],
  },
  test: {
    environment: "jsdom",
    setupFiles: ["src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    css: false,
    restoreMocks: true,
  },
});
