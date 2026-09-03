# components

Reusable presentational pieces, shared across pages — cards, badges, tables,
layout shells. Components sourced from [21st.dev](https://21st.dev) land here.

Two kinds live side by side:

- **`ui/`** — unmodified shadcn primitives, written by `npx shadcn add`.
  Regenerable, so don't hand-edit them; kebab-case filenames, because that is
  what the CLI writes and a future `add` should land on the existing file.
- **the folder root** — PulseStream's own components. PascalCase.

Rules of thumb:
- No data fetching. Components receive data through props; pages fetch it.
- Style with the shadcn tokens (`bg-card`, `text-muted-foreground`,
  `text-sentiment-positive`), never raw Tailwind colors — see
  `tailwind.config.js` for the full list.

> ⚠️ `accent` is **not** the brand colour. Under the shadcn convention it is a
> subtle hover surface; the brand teal is `primary`. `bg-accent` compiles fine
> and renders near-invisible dark grey, so this one fails silently.
