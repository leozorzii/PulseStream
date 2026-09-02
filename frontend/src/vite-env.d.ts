/// <reference types="vite/client" />

// Sem isto, import.meta.env.VITE_API_BASE_URL nao tem tipo em services/api.ts
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
