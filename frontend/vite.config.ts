import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Precisa concordar com "paths" no tsconfig.json: este resolve o bundle,
      // aquele resolve o editor e o tsc. Configurar so um dos dois da ou
      // squiggle vermelho que builda, ou editor verde que quebra em runtime.
      // fileURLToPath(new URL(...)) porque o config e ESM e nao tem __dirname.
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
