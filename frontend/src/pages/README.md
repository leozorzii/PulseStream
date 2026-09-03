# pages

One file per screen. A page owns the data for its screen: it calls a hook or
a service, handles loading and error states, and composes `components/`.

| Route | File |
| --- | --- |
| `/` | `Home.tsx` — hero on the first fold, analysis cards below |
| `/sources/:id` | `SourceDetail.tsx` |
| `*` | `NotFound.tsx` |

The app is a single page, but the router stays: `/sources/:id` has to be a
shareable deep link, and the catch-all has to exist somewhere.

Routing is declarative (`<Routes>`), not the data-router API — loaders would
contradict the rule above, which puts data ownership in the page.

Pages also decide **layout**: width, grid, spacing, and their own `container`.
`RootLayout` deliberately draws no chrome, so a page that forgets its padding
renders flush against the viewport edge.

> ⚠️ Never put an opaque `bg-background` on a page root. The cross pattern
> lives on a `-z-10` layer; an opaque background on in-flow content paints
> over it and the page goes flat, with no error anywhere.
