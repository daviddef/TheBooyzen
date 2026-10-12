import { defineConfig } from 'astro/config';

// Custom domain, from 12 October 2026: https://booyzen.defranceski.com/
// Served by GitHub Pages from this project repo. `base` is '/' because every
// link here is site-root relative, and site/public/CNAME is what keeps the domain
// attached across Actions deploys — a CNAME that exists only in dist/ is wiped by
// the next build. The DNS was already right: booyzen.defranceski.com has pointed
// at daviddef.github.io all along.
/* Phase 1 of the seven-archive standardisation. Two pages renamed to the
   names the other archives use: the changelog was /changed, the research log
   was /log. Both old addresses stay alive. */
const redirects = {
  '/changed': '/changes/',
  '/log': '/changes/',
  /* 9 October 2026: the research log folded into /changes/, which draws the same log.json. */
  '/research-log': '/changes/',
  /* 9 October 2026: the letters page folded into /errands/, which is the same
     subject. The address was published and linked from other archives. */
  '/letters': '/errands/#sent',
};

export default defineConfig({
  site: 'https://booyzen.defranceski.com',
  base: '/',
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
