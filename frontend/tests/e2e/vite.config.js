import { mergeConfig } from 'vite'
import viteConfig from '../../vite.config.js'

export default mergeConfig(viteConfig, {
  server: {
    host: '127.0.0.1',
    port: 5174,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5101',
        changeOrigin: true,
      },
      '/__qa__': {
        target: 'http://127.0.0.1:5101',
        changeOrigin: true,
      },
    },
  },
})
