# services

The HTTP layer. `api.js` holds the configured axios instance; one module per
API area imports it and exposes the calls (`getSources()`,
`getSentimentSummary(sourceId)`).

Keep React out of this folder — services return promises, hooks turn them
into state.
