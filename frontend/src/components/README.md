# components

Reusable presentational pieces, shared across pages — cards, badges, tables,
layout shells. Components sourced from [21st.dev](https://21st.dev) land here.

Rules of thumb:
- No data fetching. Components receive data through props; pages fetch it.
- Style with the semantic tokens (`bg-surface`, `text-text-muted`,
  `text-sentiment-positive`), never raw Tailwind colors — see
  `tailwind.config.js` for the full list.
