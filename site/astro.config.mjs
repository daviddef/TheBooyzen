import { defineConfig } from 'astro/config';

// GitHub Pages project site. Change `base` to '/' and `site` to the domain
// if this ever moves to a custom domain.
/* Phase 1 of the seven-archive standardisation. Two pages renamed to the
   names the other archives use: the changelog was /changed, the research log
   was /log. Both old addresses stay alive. */
const BASE = '/TheBooyzen';
const redirects = {
  '/changed': `${BASE}/changes/`,
  '/log': `${BASE}/research-log/`,
};

export default defineConfig({
  site: 'https://daviddef.github.io',
  base: '/TheBooyzen',
  build: { format: 'directory' },
  redirects,
});
