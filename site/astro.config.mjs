import { defineConfig } from 'astro/config';

// GitHub Pages project site. Change `base` to '/' and `site` to the domain
// if this ever moves to a custom domain.
export default defineConfig({
  site: 'https://daviddef.github.io',
  base: '/TheBooyzen',
  build: { format: 'directory' },
});
