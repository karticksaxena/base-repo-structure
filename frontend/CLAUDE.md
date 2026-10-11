@AGENTS.md

# Frontend Coding Rules

## Dev tooling

Follow **`../SETUP.md`**. Lint rules live in `.oxlintrc.json`, format rules in `.prettierrc` — never in `.vscode/settings.json`. Never add ESLint (`create-next-app` ships it; this repo uses oxlint).

## Stack

Next.js (App Router, `src/`, Turbopack) · React · Tailwind CSS · TypeScript · Vitest + React Testing Library · `pnpm` (never npm/yarn) · Node LTS (`.nvmrc`)

Added only when a feature needs them (`../SETUP.md` → Frontend libraries by use case): **shadcn/ui** (all UI) · **Zod** (validation) · **CopilotKit** over AG-UI + A2UI (agent UI)

Always the latest stable, mutually compatible versions — never prereleases, never versions hardcoded in docs. The `@AGENTS.md` block above is maintained by `next dev` — keep it. For Next.js APIs, read `node_modules/next/dist/docs/` first; it may differ from training data.

## Rules

1. **SERVER COMPONENTS BY DEFAULT** — `'use client'` only for state, effects, event handlers or browser APIs; keep client components small and at the leaves
2. **FETCH ON THE SERVER** — call the backend from Server Components, Server Actions or Route Handlers
3. **NO SECRETS IN `NEXT_PUBLIC_*`** — those ship to the browser
4. **ZOD AT BOUNDARIES** (once Zod is added) — validate form input and backend responses
5. **NO `any`, NO FLOATING PROMISES, EXPLICIT RETURN TYPES** — enforced by oxlint; components return `React.JSX.Element`
6. **`next/link` AND `next/image`** — never raw `<a>` for internal links or raw `<img>`
7. **SHADCN/UI FOR ALL UI** (once shadcn is initialised) — never hand-roll a component shadcn provides; merge classes with `cn()`; theme through the CSS variables in `globals.css`
8. **COPILOTKIT FOR AGENT UI** (once agents are added) — chat and agent interactions go through CopilotKit over AG-UI; never a custom streaming client; never render agent-supplied HTML

## Structure

Starts as the `create-next-app` default. Folders are created only when needed:

```
src/
  app/             # routes only (page, layout, loading, error, route.ts) — thin
  components/ui/   # shadcn components (generated, owned source)
  features/<name>/ # feature components, hooks, server actions, schemas
  lib/             # cn(), API client, shared Zod schemas
```

- Next.js itself enforces the `app/` file conventions and server/client boundaries (build errors; live in the editor via its TypeScript plugin); oxlint enforces `next/link`, `next/image` and no import cycles
- No cross-feature imports — share through `components/` or `lib/` (not checked by a tool — keep it by hand)
- Import with the `@/` alias

## Tests

- Tests sit next to the code (`page.test.tsx` beside `page.tsx`); query by role/label
- Vitest can't render `async` Server Components — test their logic separately
- Never hit the real backend or an LLM in tests — mock them
