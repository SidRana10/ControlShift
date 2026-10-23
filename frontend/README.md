# ControlShift frontend

Next.js (App Router) + React + TypeScript + Tailwind CSS 4 + selectively customized shadcn/ui
(Base UI primitives). Design reference: [`../docs/frontend-design-spec.md`](../docs/frontend-design-spec.md).

## Run locally

Requires Node 20.9+ (developed on Node 26) and the FastAPI backend from the repository root.

```bash
# 1. backend (from the repository root, venv active)
controlshift-serve                      # http://127.0.0.1:8000

# 2. frontend (from frontend/)
npm install
cp .env.example .env.local              # optional: only needed if the API is not on 127.0.0.1:8000
npm run dev                             # http://localhost:3000
```

Production check: `npm run build && npm run start`. Other checks: `npm run lint`, `npm test` (Vitest + Testing Library; component tests use recorded Catalog API data and an in-memory router, no backend needed) and `npm run typecheck`
(`typecheck` first runs `next typegen`, so it works on a fresh clone; the generated `.next/` types and
`next-env.d.ts` are git-ignored).

The app renders without the backend; the sidebar shows "API unreachable" and Control Explorer shows
a retryable error.

## API proxy

The browser calls only same-origin `/api/backend/*` paths. `next.config.ts` rewrites exactly five
read-only endpoints to FastAPI (`CONTROLSHIFT_API_URL`, default `http://127.0.0.1:8000`):

| Browser path | FastAPI |
|---|---|
| `/api/backend/health` | `GET /health` |
| `/api/backend/crosswalk` | `GET /crosswalk` |
| `/api/backend/catalog/versions` | `GET /catalog/versions` |
| `/api/backend/catalog/elements` | `GET /catalog/elements` |
| `/api/backend/catalog/elements/{version}/{element_id}` | `GET /catalog/elements/{version}/{element_id}` |

`POST /api/backend/ask` is a route handler (`src/app/api/backend/ask/route.ts`), not a rewrite: it accepts only
`question` (1-2000 characters) and optional `version`, forwards them to `POST /ask`, applies a 100s upstream timeout and answers
failures in the API's error envelope. The LLM-backed `POST /compare` is not proxied (the Compare page uses `GET /crosswalk`). No CORS is needed. The variable is read when the Next.js
server starts (`next build` for `next start`), so rebuild after changing it.

## Layout

- `src/app/` routes (`/`, `/ask`, `/explorer`, `/compare`), root layout and fonts, `globals.css` (design tokens)
- `src/components/ui/` shadcn primitives, restyled to the tokens
- `src/components/layout/` application shell, sidebar navigation
- `src/components/shared/` reusable pieces (VersionChip, SourceTag/DerivedTag, Notice, StateBlock, BrandMark)
- `src/features/explorer/` Control Explorer: provider (URL state), navigator (tree, search, filters), version toggle, record pane (identity, provenance, crosswalk, children, references)
- `src/features/ask/` Ask ControlShift: workspace, question form, answer view, evidence inspector, `useAsk` (one in-flight request, stale-response guard)
- `src/features/health/` sidebar API status
- `src/lib/explorer/` pure logic (URL parsing, hierarchy, search helpers), request cache, `useLoader`; `src/test/` test setup and fixtures
- `src/lib/ask/` `/ask` types, runtime response parser, citation helpers, error copy; `src/test/fixtures/ask/` recorded responses
- `src/lib/api/` typed client, response types (backend snake_case), `useApi` hook

## Known dependency advisory

`npm audit` reports 9 high-severity entries, all in development-only packages (`npm audit --omit=dev`
reports 0). They all trace to one advisory:
[GHSA-vfj7-8cjw-p6xm](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm), a stack-exhaustion denial of
service in `braces` (installed 3.0.3, affected `<= 3.0.3`, **no patched release exists**). It reaches the
project through `micromatch` and `fast-glob`, used by `eslint-config-next` (ESLint) and `shadcn` (CLI).

**Status: not remediated.** Exposure assessment: it needs a crafted brace pattern passed to glob
expansion; both users only expand fixed patterns on the developer's own machine or CI. None of the
affected packages are in the production bundle or loaded by the running server, and `shadcn` is a
dev dependency (build-time CSS import and CLI only). Do not use `npm audit fix --force`; its suggested
fixes are major downgrades. Re-check with `npm audit` and `npm update` once `braces` publishes a patch.
