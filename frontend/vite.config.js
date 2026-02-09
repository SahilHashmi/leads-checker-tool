import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => {
  // Load .env from project root (one level up from frontend/)
  const projectRoot = path.resolve(__dirname, '..')
  const env = loadEnv(mode, projectRoot, '')

  // Use VITE_BACKEND_BASE_URL if set, otherwise fall back to BACKEND_BASE_URL
  const backendUrl = (env.VITE_BACKEND_BASE_URL || env.BACKEND_BASE_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '').replace(/\/api\/?$/, '')

  return {
    plugins: [react()],
    envDir: projectRoot,
    define: {
      // Inject backend URL so it's always available in client JS at build time
      '__BACKEND_BASE_URL__': JSON.stringify(backendUrl),
    },
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: backendUrl,
          changeOrigin: true,
        },
      },
    },
  }
})
