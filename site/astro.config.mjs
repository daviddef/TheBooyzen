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
  /* WHY outDir IS A VARIABLE. Eight archives share this machine and more than one
     session can build THIS repo at once. astro empties its outDir at the start of a
     build, so a second session building into site/dist while this one's gates are
     reading it produces a torrent of false failures - on 21 September that was 205
     anchor errors over a site reporting "0 pages", with nothing whatever wrong.
     Set ARCHIVE_OUT to build somewhere of your own:  ARCHIVE_OUT=dist-verify sh build.sh
     THE DEFAULT MUST STAY 'dist'. The deploy workflow uploads `path: site/dist`,
     so changing it here would publish nothing. */
  outDir: process.env.ARCHIVE_OUT || 'dist',
  build: { format: 'directory' },
  redirects,
});
