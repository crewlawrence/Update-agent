import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  base: '/', // ensures asset paths work
  plugins: [react()],
  server: {
    port: 5173, // only for dev
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: '0.0.0.0', // important for Render
    port: parseInt(process.env.PORT) || 4173, // use Render's port
    allowedHosts: [
      'update-agent.onrender.com', // Render hostname
      'localhost',
    ],
  },
});
