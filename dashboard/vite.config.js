import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // Forward API calls during development to the backend to avoid CORS/preflight issues
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // If your backend is mounted under / (default), no path rewrite is needed.
        // To customize: uncomment below.
        // rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
      '/v1': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
