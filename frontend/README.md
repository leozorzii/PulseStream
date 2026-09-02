# PulseStream — frontend

React + Vite client for the PulseStream API. Lives in the same repository as
the Django backend; the two are deployed separately.

## Running

```bash
npm install
npm run dev          # http://localhost:5173
```

The backend must be running too — see the repository root README. The API
base URL comes from `VITE_API_BASE_URL`; copy `.env.example` to `.env.local`
to override the `http://localhost:8000` default.

CORS for `localhost:5173` is already allowed by the backend.

| Script | Does |
| --- | --- |
| `npm run dev` | dev server with HMR |
| `npm run typecheck` | `tsc --noEmit` over the app and the Vite config |
| `npm run lint` | oxlint |
| `npm run build` | **typecheck, then** build |

Vite strips TypeScript types without checking them, so `vite build` alone
would happily ship code with type errors. That is why `build` runs
`typecheck` first, and why `lint` passing tells you nothing about types —
oxlint does no type-aware analysis. The two gates do not overlap.

## Layout

| Folder | Holds |
| --- | --- |
| `components/` | reusable presentational pieces; no data fetching |
| `components/ui/` | unmodified shadcn primitives — regenerable, don't hand-edit |
| `pages/` | one file per screen; owns its data and composes components |
| `hooks/` | custom hooks, mostly data-fetching wrappers around services |
| `services/` | the HTTP layer — `api.ts` is the configured axios instance |
| `lib/` | helpers: `cn()`, the sentiment map |

Each folder has its own README with the conventions for it.

Imports use the `@/` alias for `src/`. It is declared in **both**
`tsconfig.json` (`paths`, for the editor and `tsc`) and `vite.config.ts`
(`resolve.alias`, for the bundle) — they have to agree.

## Styling

Tailwind v3 with the **shadcn/ui token convention**, so components from
[21st.dev](https://21st.dev) and shadcn paste in and inherit this palette
without edits. Components name a role, never a colour:

```
bg-background  bg-card  bg-muted  bg-popover  bg-secondary
text-foreground  text-card-foreground  text-muted-foreground
bg-primary  border-border  ring-ring  bg-destructive
text-sentiment-positive / -neutral / -negative
```

> ⚠️ **`accent` is not the brand colour.** Under the shadcn convention
> `accent` is a subtle hover surface; the brand teal is **`primary`**. This
> is the one name that fails silently — `bg-accent` still compiles and just
> renders near-invisible dark grey.

Values live as HSL triplets in `src/index.css` and are consumed as
`hsl(var(--x))` in `tailwind.config.js`. Storing the bare triplet rather
than a finished colour is what lets Tailwind emit `hsl(var(--card) / 0.5)`
for `bg-card/50`.

The app is dark-only: the palette sits in `:root`, so tokens resolve even if
the `dark` class goes missing. `<html>` still carries `class="dark"` — third
party components ship hardcoded `dark:` variants, and without the class they
would render their light branch against a near-black background.

### Adding shadcn components

`npx shadcn@latest add <component>` — safe, drops a file in `components/ui/`.

**Do not run `npx shadcn init`.** It is Tailwind-v4-first and would rewrite
`index.css`, `tailwind.config.js` and possibly `postcss.config.js` into a v4
shape this project cannot compile — overwriting the palette in the process.
`components.json` is already written by hand so `add` works.

When a pasted component looks structurally right but visually flat, check for
**Tailwind v4-only utilities** (`bg-linear-to-r`, `shadow-xs`, `ring-3`,
oklch colours). They do not compile on v3 and Tailwind reports no error — it
simply does not generate the class.
