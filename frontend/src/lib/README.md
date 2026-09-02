# lib

Helpers with no screen of their own.

| File | Holds |
| --- | --- |
| `utils.ts` | `cn()` — clsx + tailwind-merge |
| `sentiment.ts` | the `POS`/`NEU`/`NEG` map and `dominantSentiment()` |

`sentiment.ts` is the single source of truth for how a sentiment code becomes
a label, a colour and an icon. Its class names are **complete literal
strings** on purpose: Tailwind's scanner is a regex over source text and never
evaluates JavaScript, so a class built as `` `bg-sentiment-${tone}` `` is not
generated at all — the element renders transparent with no error anywhere.

The old rule here was "nothing imports React". `sentiment.ts` imports lucide
icon *types*, so the rule is now: nothing here renders, holds state, or uses
hooks. Pure data and pure functions.
