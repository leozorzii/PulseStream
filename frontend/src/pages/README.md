# pages

One file per screen. A page owns the data for its screen: it calls a hook or
a service, handles loading and error states, and composes `components/`.

| Route | File |
| --- | --- |
| `/` | `Landing.tsx` — the animated hero, outside the app shell |
| `/dashboard` | `Dashboard.tsx` |
| `/sources/:id` | `SourceDetail.tsx` |
| `*` | `NotFound.tsx` |

Routing is declarative (`<Routes>`), not the data-router API — loaders would
contradict the rule above, which puts data ownership in the page.

Pages also decide **layout**: width, grid, spacing. A component should not
carry a `max-w-*` that fights the grid it is dropped into.
