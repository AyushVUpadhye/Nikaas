import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// three.js is vendored (src/vendor/three, MIT licence) so the site builds without the npm registry
export default defineConfig({
  plugins: [react()],
  resolve: { alias: { three: '/src/vendor/three/three.module.js' } },
})
