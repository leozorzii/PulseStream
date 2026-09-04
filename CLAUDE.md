# PulseStream

Sentiment analysis over public content streams. Django + DRF backend, React
dashboard, MCP server, Celery pipeline.

```
apps/ingestion     adapters (RSS) + run_ingestion service + Celery tasks
apps/stream_core   domain: models, services (writes), selectors (reads)
apps/analytics     pure-Python NLP — no ORM, no Django imports
apps/api           DRF serializers, views, urls
mcp_server/        MCP server (repo root, NOT under apps/)
frontend/          React + Vite dashboard
tests/             pytest, mirrors the apps/ layout
```

## Commands

```bash
# backend (venv at ./venv)
venv/Scripts/python.exe -m pytest          # 55 passed, 1 xfailed — fully offline
venv/Scripts/python.exe manage.py check

# frontend (cd frontend)
npm run dev          # http://localhost:5173
npm run typecheck    # tsc --noEmit; build runs this first
npm run lint         # oxlint
npm run build        # typecheck THEN build

# everything at once
docker compose up    # web + worker + beat + redis
```

`vite build` strips types without checking them, so `build` gates on
`typecheck`. And oxlint does **no** type-aware analysis — `lint` passing says
nothing about types. The two gates do not overlap; run both.

---

# Frontend

## Tailwind is v3.4.19, not v4

This is the single most common source of silent failure. v4-only utilities
compile to **nothing**, with no error — the component looks structurally right
and renders flat.

| Pasted (v4) | Use (v3) |
| --- | --- |
| `bg-linear-to-r` | `bg-gradient-to-r` |
| `blur-xs` | `blur-sm` (the whole blur scale shifted one name) |
| `aspect-15/8` | `aspect-[15/8]` |
| `shadow-xs`, `inset-shadow-2xs` | `shadow-sm`, `shadow-inner` |
| `ring-3` | `ring-[3px]` |
| `in-data-[…]:` variant | does not exist; `group-data-[…]:` does |
| `h-10.5` | `h-[2.625rem]` (no fractional spacing past 3.5) |

**Arbitrary values: `_` becomes a space, and `calc()` requires spaces around
the operator.** `min-h-[calc(100dvh-var(--x))]` is invalid CSS — no error, no
height. It must be `min-h-[calc(100dvh_-_var(--x))]`.

Do not touch `postcss.config.js`. Adding `@tailwindcss/postcss` is the v4
migration and breaks the build.

`npx shadcn@latest add <component>` is safe. **`npx shadcn init` is not** — it
is v4-first and would rewrite `index.css` and `tailwind.config.js`, destroying
the palette. `components.json` is hand-written so `add` works without it.

## Design tokens

shadcn convention, so components from shadcn and 21st.dev paste in unmodified.
Values live in `src/index.css` as **bare HSL triplets** (`200 20% 6%`) and are
wrapped as `hsl(var(--x))` in `tailwind.config.js`. The bare triplet is what
lets Tailwind emit `hsl(var(--card) / 0.5)` for `bg-card/50`.

**A bare `var(--background)` is not a valid CSS colour here.** Pasted snippets
that use it inside a gradient produce an invalid colour stop, which invalidates
the whole gradient, which makes the browser drop the entire declaration. Always
`hsl(var(--background))`. Prefer `hsl(var(--x) / 0)` over the `transparent`
keyword, which is `rgba(0,0,0,0)` and drags interpolation toward black.

⚠️ **`accent` is not the brand colour.** Under shadcn it is a hover surface;
the brand teal is `primary`. This is the one rename that fails silently —
`bg-accent` compiles fine and renders near-invisible grey.

⚠️ **`bg-background` may appear on `body` and nowhere else.** The background
layer sits at `-z-10`; an opaque background on in-flow or positioned content
paints over it and the page goes flat, with no error. Use `bg-card/80` +
`backdrop-blur` for translucent surfaces, or `bg-popover` for panels.

## Colour is computable — compute it

Never eyeball a palette. The `dataviz` skill ships a validator; run it before
shipping any chart colours.

Two findings already baked into the tokens:

- The positive green is `145 63% 33%`, not 45% lightness — the validator failed
  the lighter value's lightness band against the dark surface.
- **Green vs red measures ΔE 6.4 under deuteranopia** (threshold 8). Roughly 8%
  of men cannot separate them. Red/green is kept because it is the convention
  for sentiment, but *only* with secondary encoding.

**So: no coloured mark ever carries meaning alone.** Every sentiment mark ships
with an icon and a label; deltas carry an arrow; the segmented meter encodes
position as well as hue. `lib/sentiment.ts` is the single source — `SENTIMENT[tone]`
gives `label`, `barClass`, `textClass`, `cor` (for SVG/Recharts) and `icon`.

Those class names are **complete literal strings** on purpose. Tailwind's
scanner is a regex over source text and never evaluates JavaScript, so a class
built as `` `bg-sentiment-${tone}` `` is never generated and the element renders
transparent, silently.

Text sitting **directly on the page background** is safe with
`text-muted-foreground` today (6.82:1). It was not while the cross pattern
existed — that is why some files still use `text-foreground/70`. Both pass.

## Layout

The header is `fixed` and does not occupy flow. **Every new route root needs
`pt-[--altura-cabecalho]`** (or more), or its first 64px sit under the bar.
This is the thing a new route silently forgets.

`--altura-cabecalho` in `index.css` is the single source of truth: the header
reads it via `h-[--altura-cabecalho]`, `scroll-padding-top` derives from it, and
the hero's height calc uses it. `ALTURA_CABECALHO` in `lib/nav.ts` is only the
`useScrollSpy` fallback.

Anchor offset is one `html { scroll-padding-top }` rule, never `scroll-mt-*` on
sections — a utility would beat the base-layer rule, and a new section would
silently forget it.

## Animation

Everything animated is gated on `useReducedMotion()`. framer-motion does **not**
gate `layoutId` on its own — that one must be barred by hand.

Two things this project already paid for:

- **Never animate `pathLength`/`pathOffset` on many SVG paths.** They compile to
  `stroke-dasharray`/`stroke-dashoffset`, which are not compositable: every
  frame is a main-thread style recalc plus a full re-raster. 72 of them stuttered
  the whole page.
- **A `layoutId` earns its cost only when two instances of the same logical
  element swap positions.** A panel that only enters and exits wants
  `AnimatePresence`, not a shared id.

Avoid `filter`, `transform` and `contain: paint` on anything that is an ancestor
of a `position: fixed` element — all three turn it into a containing block and
the fixed child stops being viewport-fixed. (`position: fixed` alone does not.)

Check: with the page idle, `document.getAnimations().filter(a => a.playState === 'running').length`
must be **0**.

## Data layer

`src/lib/mock.ts` mirrors the **exact shape** of endpoints that do not exist
yet, and each type names the issue that will create it. Wiring the real API
should be swapping the data source, not redrawing components. Keep it that way.

Mock data must exercise the component: include the empty case, the failure case
and enough variance that a filter visibly changes something. Deterministic —
never `Math.random()`, which also breaks render purity.

## oxlint traps

- `Date.now()` during render is impure. Read the clock once with
  `useState(() => Date.now())` and pass it down.
- A file exporting a component **and** a helper disables fast refresh. Helpers
  go in `lib/`.
- The `src/components/ui/**` override exists because shadcn primitives export a
  component plus a `cva` object from one file.

## Comments

In **Portuguese**, explaining **why**, not what. Especially: why a value is what
it is, what broke before, and what will break if someone "simplifies" it. Code
identifiers follow whatever the surrounding file already does.

---

# Backend

Service / selector split, per the
[HackSoft styleguide](https://github.com/HackSoftware/Django-Styleguide):
**selectors read, services write**, views orchestrate. `apps/analytics` stays
pure Python with no Django import, so it is testable without a database.

**TDD, red before green.** Write the failing test first and confirm it fails for
the *right* reason — an `ImportError` because the function does not exist yet is
the correct red; a syntax error is not.

**The test suite is offline and must stay that way.** Celery `.delay()` is
patched, `feedparser` is patched, and CI runs with no Redis service *on
purpose*: if a test starts needing a broker, it fails there, which is the
signal. A test that quietly depended on live infrastructure already cost this
project a two-minute hang.

Services that write use `transaction.atomic()`. Note that
`processar_sentimentos` catches `IntegrityError` **per post inside the loop**,
and that this is only safe because `save_sentiment_analysis` opens its own
atomic block — the rollback is confined to that savepoint. Remove that atomic
and the except stops working silently.

---

# The API contract the frontend assumes

Quirks worth knowing before changing an endpoint — the client is written against
these:

- The field is spelled **`plataform`** (sic), not `platform`.
- Hand-written errors use the key **`erro`**; DRF's own use `detail`. Both need
  handling.
- `/api/analytics/summary/` answers `{source_id, state, total_analyzed,
  total_pending, sentiment}`. `source_id` is **optional**: without it the scope
  is the whole database and `source_id` comes back `null`. An empty
  `?source_id=` is a **400**, not the overall scope — absent and empty mean
  different things.
- `sentiment` is `null` whenever `state` is not `"ready"`, and carries **all
  three** labels when it is — a label with zero occurrences is `0.0`, not
  absent. Percentages are raw floats (`66.66666666666666`) and can sum to
  `99.99999999999999`.
- List endpoints answer with the DRF envelope — `{count, next, previous,
  results}` — not a bare array. Page size is 20.
- The trigger endpoint does a **synchronous** feed fetch inside the request, and
  sentiment is *not* ready when its 200 returns (Celery runs after).

**`state` describes the data, never the existence.** The enum is `ready |
processing | empty`, and it only ever describes a source that *exists*: an
unknown `source_id` is a **404**, not a 200 with `"empty"`. Keeping those
separate is the whole point — the old endpoint returned `200 {}` for "nothing
analysed yet", "nothing collected yet" and "that source is not a thing", so a
plain bug in the caller was indistinguishable from normal operation.

The state is decided by `total_analyzed` **first**, not by the pending count:
`> 0` is `ready`, else any post at all is `processing`, else `empty`. Reading it
in the other order leaves a hole — a source whose posts are all
`is_processed=True` with zero analyses matches none of the three definitions.
The pipeline cannot produce that (`save_sentiment_analysis` writes the analysis
and flips the flag in one `transaction.atomic()`), but deleting a
`SentimentAnalysis` in the admin can.

`get_sentiment_summary_by_source` still exists **untouched** next to the new
`get_sentiment_summary`, because `mcp_server/server.py` calls it directly and
handles its `{}` with its own message. No test covers that path, so changing its
return shape would break the MCP server in silence. Selectors that something
outside `apps/` imports get a sibling, not a new signature.

**Pagination is applied by hand in each view.** `DEFAULT_PAGINATION_CLASS` in
settings is read by the mixin the DRF *generics* use, and these views are plain
`APIView` — setting it would look enabled and do nothing. Every new list
endpoint has to instantiate `StandardPagination` itself
(`apps/api/pagination.py`), and must `paginate_queryset` **before** serializing,
so the `LIMIT` reaches the database instead of the whole table reaching memory.

A paginated queryset needs a deterministic `order_by`, or the database may
return different sequences across queries and an item lands on two pages or on
none. DRF flags this as `UnorderedObjectListWarning` — treat that warning as a
bug, not noise.

The issues labelled **`dependencia-backend`** (#24–#32) describe the endpoints
the dashboard needs, each with a suggested JSON shape and the reasoning behind
it. `gh issue list --label dependencia-backend` is the live list; a count here
would go stale on the first merge.

Read the issue before designing the endpoint — several record decisions (counts
vs percentages, nesting the source, grouping by `published_at` rather than
`processed_at`) that the frontend already depends on.

---

# Git and PRs

**Conventional Commits, in English.** Scope by app: `feat(frontend)`,
`fix(ingestion)`, `docs(readme)`, `chore(deps)`.

Commit bodies explain **why**, and record what was measured or what failed —
that is the part nobody can reconstruct later. Reference issues with `Closes #N`
only when the work genuinely closes them; `Refs #N` when acceptance is still
unverified.

Branches: `feat/…`, `fix/…`, `docs/…`, `chore/…`. Never commit straight to
`main` — CI runs on pull requests, and that is the only gate.

**CI must be green before merge.** The workflow runs `makemigrations --check`
then `pytest`; a model changed without a migration passes every test and only
fails at deploy.

PR descriptions: what changed and **why**, the trade-offs, and anything measured.
Flag what was deliberately left out. No "Generated with Claude Code" footer.

---

# Environment notes

- `.env` is required — `SECRET_KEY` has no default and the app will not boot
  without it. Copy `.env.example`.
- `requirements.txt` is generated by `pip freeze` on Windows and has carried
  platform-specific packages. `pywin32` is pinned behind
  `; sys_platform == "win32"` for exactly that reason; check any new
  Windows-only dependency the same way, or Linux CI breaks at install.
- Windows Celery needs `--pool=solo`; the default prefork pool needs `fork()`.
- If `pip` or a feed suddenly fails with `CERTIFICATE_VERIFY_FAILED`, check
  whether antivirus TLS scanning is intercepting:
  `echo | openssl s_client -connect pypi.org:443 -servername pypi.org 2>/dev/null | grep issuer=`.
  Switching networks does not help — the interception is local.
