import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  return {
  plugins: [react()],
  server: { proxy: { '/agentcore': {
    target: `https://bedrock-agentcore.${env.VITE_AWS_REGION || 'us-east-1'}.amazonaws.com`,
    changeOrigin: true,
    rewrite: path => path.replace(/^\/agentcore/, ''),
  } } },
  }
})
