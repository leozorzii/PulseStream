import axios from "axios"

/*
 * Configured HTTP client for the PulseStream DRF backend.
 *
 * The base URL comes from VITE_API_BASE_URL (see .env.example). It is read
 * at build time, not runtime — Vite inlines it — so changing it means
 * restarting the dev server.
 *
 * The localhost fallback keeps `npm run dev` working with no .env at all;
 * deployments are expected to set the variable explicitly.
 *
 * No endpoint functions live here on purpose. Add them in sibling modules
 * (sources.js, analytics.js) that import this client, so the transport
 * config stays in one place and the calls stay grouped by domain.
 */
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  timeout: 10000, // fail loudly instead of hanging a screen forever
})

export default api
