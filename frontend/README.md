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

## Layout

| Folder        | Holds                                                        |
| ------------- | ------------------------------------------------------------ |
| `components/` | reusable presentational pieces; no data fetching             |
| `pages/`      | one file per screen; owns its data and composes components   |
| `hooks/`      | custom hooks, mostly data-fetching wrappers around services  |
| `services/`   | the HTTP layer — `api.js` is the configured axios instance   |
| `lib/`        | framework-agnostic helpers; nothing here imports React       |

Each folder has its own README with the conventions for it.

## Styling

Tailwind, driven by **semantic tokens** rather than raw colors: `bg-surface`,
`text-text-muted`, `text-sentiment-positive`. The tokens are declared in
`tailwind.config.js` and their values live as CSS variables in
`src/index.css`, defined once for light and once under `.dark`.

Use the tokens, not `bg-gray-100` — that is what keeps a theme swap from
becoming a refactor.
