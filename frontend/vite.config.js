import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import fs from 'fs'

function readEnvFile(envPath) {
  const vars = {}
  try {
    const content = fs.readFileSync(envPath, 'utf-8')
    for (const line of content.split('\n')) {
      const trimmed = line.trim()
      if (!trimmed || trimmed.startsWith('#')) continue
      const eqIndex = trimmed.indexOf('=')
      if (eqIndex === -1) continue
      const key = trimmed.slice(0, eqIndex).trim()
      const value = trimmed.slice(eqIndex + 1).trim().replace(/^["']|["']$/g, '')
      vars[key] = value
    }
  } catch (e) {
    // .env file not found - use defaults
  }
  return vars
}

export default defineConfig(({ mode }) => {
  const projectRoot = path.resolve(__dirname, '..')
  const env = readEnvFile(path.join(projectRoot, '.env'))

  // Use BACKEND_BASE_URL from .env, strip trailing / and /api
  const backendUrl = (env.BACKEND_BASE_URL || env.VITE_BACKEND_BASE_URL || 'http://127.0.0.1:8000')
    .replace(/\/+$/, '')
    .replace(/\/api\/?$/, '')

  console.log(`[vite] .env path: ${path.join(projectRoot, '.env')}`)
  console.log(`[vite] BACKEND_BASE_URL from .env: ${env.BACKEND_BASE_URL || '(not set)'}`)
  console.log(`[vite] Using backend URL: ${backendUrl}`)

  return {
    plugins: [react()],
    define: {
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
