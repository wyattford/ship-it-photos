import react from '@vitejs/plugin-react'
import { existsSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'

// The API (uvicorn) listens on PORT from the project's .env, one folder up.
// Read the file directly: a PORT variable in the shell (often set by tools to
// Vite's own port) must not win, or /api would be forwarded back to Vite itself.
function apiPort(): string {
  const file = fileURLToPath(new URL('../.env', import.meta.url))
  if (!existsSync(file)) return '8000'
  const match = readFileSync(file, 'utf8').match(/^\s*PORT\s*=\s*"?(\d+)"?\s*$/m)
  return match?.[1] ?? '8000'
}

const api = `http://127.0.0.1:${apiPort()}`

// In development, Vite serves the React app and forwards /api and /uploads to uvicorn.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': api, '/uploads': api },
  },
})
