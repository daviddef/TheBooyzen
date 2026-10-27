#!/usr/bin/env node
/* THE RIBBON FLAGS MUST NOT MOVE A WORD (27 October 2026): the kit's box gate, checkflagfit.mjs, over every built page that
   draws a flag.

     node ../tools/flagfit.mjs              from site/ (what `npm run check:flagfit` and the build run)

   The kit's gate opens built pages in Google Chrome (through playwright-core, a devDependency here because the kit does not
   carry it), measures every ribbon card with its flag strip and with the strip hidden, at 1440, 1100 and 390px, and fails a
   card whose width or height moves by more than 0px or whose strip touches its glyph, "Gen. n", name or years. It needs
   pages over http, so this serves the built site ($ARCHIVE_OUT, default dist) on a free local port for the length of the
   run, finds every page whose HTML carries a flag strip (the story, the family pages), and hands the kit those addresses.
   It also runs the kit's --selftest first (a fixture ribbon, then three planted faults), so a gate that cannot see is
   caught before it is believed. Exit: the kit's (0 clean, 1 a card changed size, 2 it could not run or saw no flag). */
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { spawnSync, spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const SITE = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "site");
const DIST = path.join(SITE, process.env.ARCHIVE_OUT || "dist");
const GATE = path.join(SITE, "node_modules", "@daviddef", "archive-kit", "kit", "tools", "checkflagfit.mjs");

if (!fs.existsSync(GATE)) { console.error(`flagfit: the kit's checkflagfit.mjs is not installed at ${GATE}`); process.exit(2); }
if (!fs.existsSync(DIST)) { console.error(`flagfit: no built site at ${DIST}`); process.exit(2); }

/* every built page that draws a flag strip */
const pages = [];
(function walk(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p);
    else if (e.name === "index.html" && fs.readFileSync(p, "utf8").includes('class="flag-strip')) pages.push("/" + path.relative(DIST, path.dirname(p)).split(path.sep).join("/") + "/");
  }
})(DIST);
pages.sort();
if (!pages.length) { console.error("flagfit: no built page draws a flag strip: nothing to check"); process.exit(2); }

const TYPES = { ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript", ".mjs": "text/javascript", ".svg": "image/svg+xml",
  ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".avif": "image/avif", ".woff2": "font/woff2", ".woff": "font/woff",
  ".json": "application/json", ".xml": "application/xml", ".ico": "image/x-icon", ".txt": "text/plain" };
const server = http.createServer((req, res) => {
  let rel = decodeURIComponent(new URL(req.url, "http://x").pathname);
  if (rel.endsWith("/")) rel += "index.html";
  const file = path.join(DIST, rel);
  if (!file.startsWith(DIST) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { "content-type": TYPES[path.extname(file).toLowerCase()] || "application/octet-stream" });
  fs.createReadStream(file).pipe(res);
});
/* an off-site request (the counter, a font) is not ours to wait on: the gate loads with waitUntil networkidle */
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const base = `http://127.0.0.1:${server.address().port}`;

const self = spawnSync(process.execPath, [GATE, "--selftest"], { stdio: "inherit" });
if (self.status !== 0) { server.close(); console.error("flagfit: the kit's checkflagfit --selftest did not pass"); process.exit(self.status || 2); }

console.log(`flagfit: ${pages.length} built pages draw flags: ${pages.join(" ")}`);
const run = spawn(process.execPath, [GATE, ...pages.flatMap((p) => ["--url", base + p]), "--widths", "1440,1100,390"], { stdio: "inherit" });
const code = await new Promise((r) => run.on("exit", (c) => r(c ?? 2)));
server.close();
process.exit(code);
