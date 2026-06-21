import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Auth endpoints -> IAM Server (port 4000)
      '/api/login': {
        target: 'http://localhost:4000',
        changeOrigin: true,
        secure: false
      },
      '/api/mfa': {
        target: 'http://localhost:4000',
        changeOrigin: true,
        secure: false
      },
      '/api/token': {
        target: 'http://localhost:4000',
        changeOrigin: true,
        secure: false
      },
      '/api/logout': {
        target: 'http://localhost:4000',
        changeOrigin: true,
        secure: false
      },
      '/api/me': {
        target: 'http://localhost:4000',
        changeOrigin: true,
        secure: false
      },
      '/api/admin': {
        target: 'http://localhost:4000',
        changeOrigin: true,
        secure: false
      },
      // Data endpoints -> Backend Server (port 3000)
      '/api/patients': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        secure: false
      },
      '/api/appointments': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        secure: false
      },
      '/api/vitals': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        secure: false
      },
      '/api/prescriptions': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        secure: false
      },
      '/api/lab': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        secure: false
      },
      '/api/billing': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        secure: false
      },
      '/api/pharmacy': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        secure: false
      },
      '/api/files': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        secure: false
      },
      '/api/audit': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        secure: false
      },
      '/api/monitoring': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        secure: false
      },
      '/api/health': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        secure: false
      },
      '/api/dashboard': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        secure: false
      },
      // Default fallback -> IAM Server
      '/api': {
        target: 'http://localhost:4000',
        changeOrigin: true,
        secure: false
      }
    }
  }
})