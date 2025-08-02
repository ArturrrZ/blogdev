import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())

  return {
    plugins: [react()],
    server: { port: 3000 },
    define: {
  __API_URL__: JSON.stringify("http://localhost/"),
  __HOST_URL__: JSON.stringify("http://localhost/"),
}
  }
})
