import { defineConfig } from 'astro/config';
import { readFileSync } from 'node:fs';
import { whoRedirects } from './src/lib/namesets.js';

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
  /* 23 November 2026: Roots & Routes was removed (David: "roots and routes, remove it"); the Tree Canvas on recordatlas.org replaced it. The
     address was published and indexed, so it keeps answering and lands on the archive's own drawn tree. Only /roots/ itself: /roots/view.html
     is the bare viewer a person's page frames for "Where they lived" (src/pages/roots/view.html.js) and stays. */
  '/roots': '/tree/',
};

/* ONE PAGE PER PERSON (23 November 2026, trial). A name used to have a page, /who/<name>/, beside the person's page. It does not any
   more: every one of those addresses is a static redirect (a meta refresh and a canonical, not in the sitemap). A name one person
   bears goes to that person's page; a name several bear goes to its first bearer's page at #others-of-this-name, the section that
   lists the others (lib/namesets.js: the earliest born who is not living, else slug order). The names read from FamilySearch index
   rows and held in no family file keep their own page, so they are not here. */
const readJson = (p) => JSON.parse(readFileSync(new URL(p, import.meta.url), 'utf8'));
const livingSlugs = new Set(readJson('./src/data/living.json').living.map((x) => x.slug));
const dossiers = Object.values(readJson('./src/data/dossiers.json').people);
Object.assign(redirects, whoRedirects(dossiers, (slug) => livingSlugs.has(slug)));

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
