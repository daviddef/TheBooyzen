# For the estate — three things found here that belong to everybody

Written 15 September 2026 by the Booyzen archive. These are not findings about a
family; they are findings about the **tools**, and every archive in this estate
will hit them in turn and spend the same afternoon.

---

## 1. The FamilySearch Dutch Reformed baptism films begin in 1843

**This is the expensive one, because it does not announce itself.**

The filmed church-register collection was checked town by town through the
Baptism Finder: **Paarl (Drakenstein) 54 registers, Graaff-Reinet 48,
Stellenbosch 55** — and sorted earliest first, **the first row in every town is
1843–1844.** It is the post-1842 Nederduitse Gereformeerde Kerk archive series.

It does not reach the eighteenth century at all.

**Why it matters:** a search returns nothing and looks like an absence. It is an
edge. Weeks of work here produced nothing older than the 1840s and the reason was
never that the registers do not survive — they go back two centuries. It was
where the filming started. **If your archive has an eighteenth-century wall and
has been probing it through FamilySearch, that wall may be the collection.**

The originals are at the Western Cape Archives, 72 Roeland Street.

---

## 2. NAAIRS can be driven end to end from a page, and it silently ORs your terms

The national index is a frameset on one host with the search on another, and it
is entirely scriptable. The flow:

1. `GET /sm300cv/smws/sm300dl` → a rotating token in every link
2. `GET sm300gi?<token>%26DB%3D<DB>` → the query form, with a **new** token in the form action
3. `POST sm300dr?<token>` with `K0000001`…`K0000005` (terms), `B0000001`…`B0000004` (operators),
   `A0000000`/`C0000000`/`O0000000`/`A0000001`/`C0000001` (date range), `btnSearch=Search`
4. The result page gives a count and another token
5. `GET sm30ddf0?<token>&DN=00000001&F=P` for each document, re-reading the token from each response

Databases: `RSAE` (all), `KABE` Cape, `TABE` Transvaal, `VABE` Free State,
`NABE` Natal, `SABE`, `GENE` (gravestones), `MANE` (manuscripts — **this is where
a library manuscript collection turned up that no archive index would have
shown**).

**THE TRAP:** NAAIRS treats two keywords as **OR** unless the operator is sent
explicitly. `BARRY` with `BURGERSDORP` returned **6,245 documents — more than
BARRY alone**, and looked for a moment like a rich seam. With `AND` sent, it
returns one. **A search that returns more than its own first term is not a
search.**

---

## 3. The eGGSA newspaper index is an Elasticsearch behind a widget

`newspapers.eggsa.org` draws results by script and the form POST returns the page
and nothing else. But the module exposes the endpoint, and it takes a raw
Elasticsearch query:

```
POST /index.php/elasticsearch?size=60&from=0&type=
{"query":{"bool":{"must":[{"terms":{"state":[1,2]}},{"terms":{"cat_state":[1,2]}},
 {"bool":{"should":[{"match":{"title":{"query":TERM,"operator":"and"}}},
                    {"match":{"description":{"query":TERM,"operator":"and"}}}]}}]}},
 "highlight":{"number_of_fragments":20,"fragment_size":420,
              "fields":{"description":{}}},
 "_source":{"include":["title","path"]}}
```

**`number_of_fragments` is the whole point.** The widget shows one fragment per
article; ask for twenty and you get **every mention in every transcript** in one
request. Two walls came down here that way — a man's regiment and a missionary
school — both from instalments of one memoir nobody knew existed.

**Caveat:** this engine has no AND that can be sent. A two-word query is *scored*,
not filtered, so a pairing like `BARRY BURGERSDORP` returns every Barry it has.
Negatives from paired terms here are **void**, not informative.

---

## And a fourth thing, which is a request rather than a finding

**Which institutions cannot be emailed at all**, so nobody else spends the
afternoon finding out:

- **The National Archives, Kew** — records and research enquiries go through a
  **web form**; no address is published. Their Live Chat runs Tuesday to Saturday
  and answers a technical question in ninety seconds that a form answers in weeks.
- **Department of Sport, Arts and Culture (`dsac.gov.za`)** — where every letter
  to the South African National Archives goes. **No website at all**; the domain
  has MX and nothing else. It takes mail and looks dead to a browser.
- **SANDF Documentation Centre** — `sandfdoc@mweb.co.za` is the only address it
  publishes, on its own directory entries and every guide that lists it, and it
  **bounces with 550 relay access denied**. What is left is the telephone.
- **A caution learned the hard way:** a government domain with no A record is
  often perfectly alive. `kzndac.gov.za` has no website and takes mail. Checking
  for a website and concluding the address is dead is wrong, and this archive was
  one edit from publishing exactly that.

Contact: the Booyzen archive, via David.

---

## The FindMyPast driver (written 16 September 2026; subscription lapses 16 October)

FindMyPast's search UI is a React app that pages twenty rows at a time. Do not
click it. It talks to its own GraphQL endpoint, and so can you, from any of its
own pages:

```
POST https://www.findmypast.co.uk/titan/marshal/graphql
operation: searchResultsRecordsAndMetadata
variables: { filters, order, pageNumber }
```

The easiest way in is to take the query document off the live Apollo client
rather than reconstruct it. From a `/search/results` page:

```js
const oq = [...__APOLLO_CLIENT__.getObservableQueries('all').values()]
  .find(q => (q.queryName || q.options?.query?.definitions?.[0]?.name?.value)
             === 'searchResultsRecordsAndMetadata');
const DOC = oq.options.query;
const Q = async (filters, page = 1, order = null) => {
  const r = await __APOLLO_CLIENT__.query({
    query: DOC, variables: { filters, pageNumber: page, order },
    fetchPolicy: 'network-only' });
  const R = r.data.root.search.recordSearch;              // note the path
  return { n: +R.numberOfRecords,
           recs: R.records.map(x => Object.fromEntries(
             x.fields.map(f => [f.fieldId, f.value]))) };
};
```

`DOC` dies on navigation — re-acquire it after every page load. A whole record
set of a few hundred rows can then be swept in a single call.

**Filter fields that work.** `LastName` (takes `variants: true|false`),
`FirstName`, `EventYear` (takes `offset`, a +/- year window), `YearOfBirth`,
`YearOfDeath`, `KeywordsPlace`, `Keywords`, `DatasetName`, `Regiment`,
`SourceCategory`, `MotherLastName`.

**Added 20 September 2026, after a marriage sweep.** Two more, both tested with a
nonsense value first:

* **`Keywords` FILTERS** — it is not like `KeywordsPlace`. `LastName=downing` with
  `Keywords=zqxwvkj` returns 0 where the same search without it returns 231,425.
  **But it matches place names as well as names**: `Keywords=king` for 1790–1806
  returns 144 records and nearly all of them are *King's Lynn*. A surname that is
  also half a place-name is useless in this field.
* **`SpouseLastName` FILTERS, and it is the right tool for a marriage.** It is not
  in the list above because nothing had needed it; the field exists on every
  marriage transcript beside `SpouseFirstName`. `LastName=downing` +
  `SpouseLastName=pooley` returns exactly the three indexed Downing–Pooley
  marriages in the whole collection; a nonsense spouse returns 0. It is immune to
  the King's Lynn problem.

**Two traps, and both of them nearly produced a wrong answer on the first day.**

1. **`KeywordsPlace` and `YearOfBirth` are scored, not filtered.** They rank the
   results; they do not restrict them. A search for Barry at Bilsdale returns
   112 rows of Barrys anywhere. `EventYear` with an `offset` *does* filter, and
   so does `DatasetName`, `Regiment` and `SourceCategory`. Always check the
   count against an obviously-wrong value before trusting a narrow one.
2. **The same regiment is indexed under several different strings, and they hold
   different record series.** `21st Dragoons` returned 342 records with no WO 97
   in them at all; `21st Regt Of Light Dragoons` returned 128 records that were
   nothing but WO 97. A negative against the first string alone would have been
   worthless. The same is almost certainly true of parishes, ships and
   regiments elsewhere in the index.

**Transcripts.** A result row carries only the fields the list renders. The full
transcript is fetched by a *mutation* (it marshals an entitlement), so it cannot
be batched through `Q`. Navigate to `https://www.findmypast.co.uk/transcript?id=<Id>`
and read it out of the cache:

```js
const c = __APOLLO_CLIENT__.cache.extract();
const k = Object.keys(c).find(x => x.startsWith('FulfilledTranscript:'));
Object.fromEntries(c[k].fields.map(f => [f.fieldId, f.value]));
```

Ids are URL-encoded when they contain slashes. A dead id returns a 500 page and
no `FulfilledTranscript` key — which is how `R_177176049779` was shown not to
exist.

**Useful URL parameters** on `/search/results`, if scripting is not wanted:
`sid=999` makes `sourcecategory=` apply; `o=` and `d=asc|desc` sort by
`lastname`, `firstname`, `eventyear`, `yearofbirth`, `yearofdeath` or
`datasetname`; `_page=` pages.

---

## The FamilySearch film index, pulled by API instead of by eye (17 Sep 2026)

A film's **Image Index** panel — the table under each image giving Name, Birth
Date, Parent Name, Second Parent's Name, Event Type, Event Date, Event Place —
is served by a single endpoint, and it can be driven. This turned a 214-image
hand sweep into about ten minutes.

```
POST /search/filmdatainfo/image-data
{"type":"image-data",
 "args":{"imageURL":"https://www.familysearch.org/ark:/61903/<ARK>?i=<i>&cc=<coll>&groupId=<coll>&lang=en",
         "locale":"en",
         "state":{"imageOrFilmUrl":"","selectedImageIndex":-1,"viewMode":"i"}}}
```

It returns `records[]`, each a GEDCOM-X record with `persons[]` (child first,
then the two parents), `facts` carrying Birth and Baptism with dates and place,
and a `sourceDescriptions[0].citations[0].value` holding a **full citation with
the record ARK** — which is how a find from this route gets a reference.

**It needs the per-image ARK and will not take an image number.** `imageURL`
must carry a real ARK; a film URL with `?i=N` returns 404. The ARKs come from
the thumbnail strip: expand it, scroll it, and harvest
`img[src*=deepzoomcloud]`, whose src contains `3:1:XXXX-XXXX-XXXX`.

**Two traps, and the second one would corrupt a whole sweep silently.**

1. `q.filmNumber` on the personas API is **not combinable**. It filters alone —
   film 008039088 returns 22,059 — and is **discarded entirely** the moment any
   other term joins it: `filmNumber + surname=Barry` returns 6,852,654, which is
   exactly what `surname=Barry` returns on its own. A nonsense surname with the
   film still returns 77,556. So the film cannot be partitioned by name or date
   to get round the 1000-offset wrap. **There is no API route to a whole film.**
   The image-data endpoint above is the way.

2. **The viewer's image number is one more than the URL's `?i=`.** `?i=604`
   displays as "Image 605 of 818". The thumbnail label is the display number, so
   a map built from the strip is keyed 1-based while the API wants the 0-based
   `i`. Four known ARKs were checked against four navigations before any data
   was read. Getting this wrong shifts every row in the sweep by one page and
   nothing anywhere would say so.

Politeness: ~60–120ms between calls, and about thirty images per browser call
before the tool's own timeout — the work continues in the page after the call
returns, so the next call can simply carry on.
