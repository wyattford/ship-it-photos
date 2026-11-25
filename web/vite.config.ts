import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// In development, Vite serves the React app and forwards /api and /uploads to uvicorn.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/uploads': 'http://127.0.0.1:8000',
    },
  },
})
