import { svelte } from '@sveltejs/vite-plugin-svelte';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [svelte()],
  build: { outDir: 'dist', assetsInlineLimit: 0, sourcemap: false, chunkSizeWarningLimit: 900 },
});
