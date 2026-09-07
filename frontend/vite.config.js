import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
    port: 5175,
    proxy: {
      '/api/dataflow': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/dataflow/, '/api')
      },
      '/api/region': {
        target: 'http://localhost:5002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/region/, '/api')
      },
      '/api/voronoi': {
        target: 'http://localhost:5003',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/voronoi/, '/api')
      },
      '/api/auth': {
        target: 'http://localhost:5004',
        changeOrigin: true
      },
      '/api/projects': {
        target: 'http://localhost:5004',
        changeOrigin: true
      },
      '/api/text': {
        target: 'http://localhost:5004',
        changeOrigin: true
      },
      '/api/analysis': {
        target: 'http://localhost:5004',
        changeOrigin: true
      },
      '/api/ev-insight': {
        target: 'http://localhost:5005',
        changeOrigin: true
      },
      '/api/import': {
        target: 'http://localhost:5004',
        changeOrigin: true
      },
      '/api/export': {
        target: 'http://localhost:5004',
        changeOrigin: true
      },
      '/api/datasets': {
        target: 'http://localhost:5004',
        changeOrigin: true
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'element-plus': ['element-plus'],
          'echarts': ['echarts'],
          'd3': ['d3']
        }
      }
    }
  }
})
