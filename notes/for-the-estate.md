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
