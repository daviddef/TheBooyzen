/* The archive's light markup, rendered — bold, italic, «quoted» and internal
   links — for the registers whose data is written in it.

   WHY THIS FILE EXISTS RATHER THAN A FIFTH PASTE. The conversion was written
   inline on /worklist/ and in the kit's own WorkList.astro, and NOT on
   /searched/, /changes/, /corrections/ or /research-log/ — so four registers
   printed their emphasis as asterisks at the reader. Measured on 9 October
   2026, on a build into site/dist-base:

     searched        2428 literal ** in visible text, 1564 <strong>
     changes          474                                 2
     corrections      302                                93
     research-log     172                                 3

   `md` BUILDS ON THE KIT'S kit/lib/md.js WHERE THAT IS RIGHT. The emphasis
   vocabulary is the estate's, not this archive's, and a second opinion about
   what `**` means is the thing to avoid. What the kit's renderer does not do
   is links, because a link has to be prefixed with THIS deployment's base path
   via `u()` — which is why the kit's WorkList takes `u` as a prop. So links are
   added here and nothing else is restated.

   ONE PLACE IT DELIBERATELY DIFFERS, AND IT IS A FAULT IN THE KIT'S REGEXES
   RATHER THAN A DISAGREEMENT. A run of three asterisks is ambiguous: it is a
   bold close inside an italic in one row of this register and an italic close
   inside a bold in another, and the two need OPPOSITE readings.

     *Agnes Kolbe × Jerg Raisch, 1685, **Evangelisch, ... Wuerttemberg***
     **54 records, and every one is either *Ireland ... Baptisms* or
       *Ireland Births 1864-1958***

   Ordered replacements cannot tell those apart — the kit's `***`-first rule
   turns the second into `<em>Ireland Births 1864-1958</strong></em>`, which is
   misnested and bleeds the bold across the rest of the cell. So emphasis is
   scanned here with a delimiter stack instead, closing the INNERMOST span
   first, which reads both rows correctly. Raised with the kit rather than
   patched there: seven projects share that file, and two of its components
   (AncChart, Trees) render notes through it.

   AND IT IS WHY A LONE ASTERISK SURVIVES. `BOOY* in the Cape depot returns 0
   documents` is a wildcard, not an italic, and so is every asterisk in the
   query column of /searched/ — `q.surname=B*rry · q.motherSurname=Kolb*`.
   A delimiter only opens a span when the character after it is not a space and
   only closes one when the character before it is not a space (the flanking
   rule every markdown parser uses); anything left over is printed as itself.
   That is what keeps the wildcards intact, and it is why the QUERY column is
   not rendered through here at all — three of its asterisks flank on both
   sides and would pair up into an italic across two surnames.

   Everything is escaped BEFORE any markup is produced, so data can never
   inject HTML — only the markers become tags. Returns an HTML string, so the
   caller must use set:html. */

import { u } from "./url.js";

const ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;" };

/* Exported because a register has columns that must NOT be rendered — see the
   query column below — and they still have to be escaped by the same rule as
   the ones that are. /searched/ had its own, which escaped & and < and left >
   alone, so `fulltext=<TERM>&items=60` reached the page half-encoded. */
export const esc = (s) => String(s ?? "").replace(/[&<>]/g, (c) => ESC[c]);

const WS = (c) => c === undefined || /\s/.test(c);

/* How many open spans a run of `n` asterisks closes, innermost first — and 0
   unless it closes them EXACTLY, with nothing left over.

   The remainder is what makes this a function rather than a loop. `*“**The
   decision ... 1987**` opens an italic and then, with no space between, a bold.
   Closing greedily spends one of those two asterisks on the italic and opens a
   second italic with the other, which reads the row as the author did not write
   it. Requiring the run to be spent in full leaves it to open the bold, and the
   bold's own `**` later closes it. */
const closes = (open, n) => {
  let k = 0, rem = n;
  for (let j = open.length - 1; j >= 0 && rem > 0; j--) {
    const need = open[j] === "strong" ? 2 : 1;
    if (rem < need) break;
    rem -= need;
    k++;
  }
  return rem === 0 ? k : 0;
};

/* A delimiter run closes the spans that are open, innermost first, or opens new
   ones with whatever it holds. A run that can do neither is literal. */
function emphasis(s) {
  let out = "";
  const open = [];
  for (let i = 0; i < s.length; ) {
    if (s[i] !== "*") { out += s[i++]; continue; }
    let n = 1;
    while (s[i + n] === "*") n++;
    let rem = n;
    const shut = WS(s[i - 1]) ? 0 : closes(open, n);
    if (shut) {
      for (let k = 0; k < shut; k++) {
        rem -= open[open.length - 1] === "strong" ? 2 : 1;
        out += `</${open.pop()}>`;
      }
    } else if (!WS(s[i + n])) {
      while (rem >= 2) { open.push("strong"); out += "<strong>"; rem -= 2; }
      if (rem === 1) { open.push("em"); out += "<em>"; rem -= 1; }
    }
    out += "*".repeat(rem);
    i += n;
  }
  /* A span left open is malformed data, not a reason to emit malformed HTML. */
  while (open.length) out += `</${open.pop()}>`;
  return out;
}

/* Only a site-root path is based. An external URL run through u() produces
   /TheBooyzen/https://… — the kit's Searched component carries the count. */
const LINK = /\[([^\]]+)\]\((\/[^)]*)\)/g;

/* A CODE SPAN IS LIFTED OUT BEFORE ANYTHING ELSE RUNS, AND THAT ORDER IS THE
   WHOLE POINT. The backtick is already this estate's code marker — 719 closed
   spans across the five registers on 9 October 2026, and NOT ONE stray
   backtick in any of them — and what those spans hold is file names and code,
   which is to say the other markers:

     `*.json`   `a[k]`   `[n, title, why, where, pri]`   a glob of every
     archive's pages, which cannot be written in this comment because it
     would close it

   Rendered in place, the two `*.json` spans in one worklist note pair into an
   italic running between them. So each span is replaced by a sentinel first,
   the markers are rendered around it, and the span comes back last with its
   contents escaped but otherwise untouched. U+E000 is private-use and appears
   nowhere in the data; it is checked rather than assumed.

   BEFORE THIS, THE DATA SAID `code` AND THE READER SAW A BACKTICK. Two files
   had reached for real <code> tags instead, which is what put corrections.json
   and log.json on the raw-HTML contract and kept an escaping renderer off
   three registers. Those are written as backticks now, like the other 719. */
const SENT = "\uE000";
const CODE = /`([^`]+)`/g;

export const md = (x) => {
  const spans = [];
  const held = esc(x).replace(CODE, (_m, c) => SENT + (spans.push(c) - 1) + SENT);
  return emphasis(held)
    .replace(/«(.+?)»/gs, "<em>«$1»</em>")
    .replace(LINK, (_m, t, h) => `<a href="${u(h)}">${t}</a>`)
    .replace(new RegExp(SENT + "(\\d+)" + SENT, "g"), (_m, i) => `<code>${spans[+i]}</code>`);
};
