# services

The HTTP layer. `api.ts` holds the configured axios instance; one module per
API area imports it and exposes the calls (`getSources()`,
`getSentimentSummary(sourceId)`).

Keep React out of this folder — services return promises, hooks turn them
into state.

Two things the backend does that this layer will have to absorb:

- Errors use the key `erro` (Portuguese), while DRF's own errors use `detail`.
  Both have to be handled.
- `/api/analytics/summary/` answers `{}` for "no analyses yet", "still
  processing" and "no such source" alike, and returns **500** if `source_id`
  is empty or non-numeric — so validate the id before calling.
