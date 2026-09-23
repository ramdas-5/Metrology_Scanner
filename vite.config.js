import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
import tailwindcss from '@tailwindcss/vite'

const rootDir = path.dirname(fileURLToPath(import.meta.url))

/**
 * Minimal KEY=VALUE reader (no extra dependency).
 *
 * The frontend's environment lives in its OWN file so the backend's
 * .env.backend is never mixed into the browser bundle:
 *
 *   .env.frontend      -> what VITE_API_URL (and any other VITE_* value) is
 *
 * Real environment variables always win, so a value set in the Vercel
 * dashboard (Settings -> Environment Variables) overrides the file.
 */
function readEnvFile(fileName) {
  const filePath = path.resolve(rootDir, fileName)
  if (!fs.existsSync(filePath)) return {}

  const values = {}
  for (const rawLine of fs.readFileSync(filePath, 'utf8').split(/\r?\n/)) {
    const line = rawLine.trim()
    if (!line || line.startsWith('#')) continue
    const separator = line.indexOf('=')
    if (separator === -1) continue
    const key = line.slice(0, separator).trim()
    let value = line.slice(separator + 1).trim()
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1)
    }
    values[key] = value
  }
  return values
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const frontendFileEnv = readEnvFile('.env.frontend')
  // Also honour Vite's conventional files (.env, .env.local, .env.[mode]).
  const viteEnv = loadEnv(mode, rootDir, 'VITE_')

  const apiUrl = (
    process.env.VITE_API_URL ||
    frontendFileEnv.VITE_API_URL ||
    viteEnv.VITE_API_URL ||
    'http://localhost:8000'
  ).replace(/\/+$/, '')

  return {
    plugins: [react(), tailwindcss()],
    define: {
      'import.meta.env.VITE_API_URL': JSON.stringify(apiUrl),
    },
  }
})
