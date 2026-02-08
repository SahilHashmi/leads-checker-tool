import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => {
  // Load .env from project root (one level up from frontend/)
  const projectRoot = path.resolve(__dirname, '..')
  const env = loadEnv(mode, projectRoot, '')

  const backendUrl = env.BACKEND_BASE_URL || 'http://127.0.0.1:8000'

  return {
    plugins: [react()],
    envDir: projectRoot,
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
