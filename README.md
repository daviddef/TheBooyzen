# The Booyzen Archive

An evidence-first family archive for the **Booyzen** family — of Graaff-Reinet and Cradock, of
**Barkly East** and Dordrecht, and of Johannesburg.

> *Booyzen* is borne by **646 people in the whole world**. *Booysen* is borne by **53,764**.
> The family says one of its men changed the spelling during the Anglo-Boer War so as not to be taken
> for a Booysen who fought on the British side. **The distribution data agrees with them**, and it was
> not collected to.

## Where this one starts

**Unusually well.** The Lerena archive began with almost nothing documented. This one begins with a
MyHeritage tree of **15,643 people** in which the Booyzen line already runs back **seven generations**,
much of it citing Dutch Reformed Church registers and Cape and Transvaal probate records.

That changes the job. The work here is not to find the family — it is to **test what has been assembled**,
because a tree that good will be believed, and parts of it are demonstrably wrong.

## What the family remembers

Recorded on the tree from **Tersia Booyzen**, as told to her by her father:

> "They were living in the Cape Colony and were rebels fighting on the side of the Boer republics … but
> there were some Booysens who were joiners, fighting on the side of the British, so our great grandfather
> changed the spelling to Booyzen so as not to be associated with them. Our great great grandfather was
> shot and killed by the British and all the women and children were put in a concentration camp and the
> family farm in the Eastern Cape was burned to the ground … After the war our great great grandmother
> (with nothing but a pumpkin to eat) put herself and her kids on a train to Johannesburg where the boys
> initially all got jobs on the mines."

## What the documents said

The tree's photo store held **civil records nobody had transcribed** — not snapshots. Reading them on
9 September 2026 corrected three dates, killed one family legend, and caught the surname changing.

- **Willem Hermanus Booysen died of an ULCER OF THE STOMACH** at Doorn Street, Indwe, on **13 September
  1905**, after **fourteen months** of illness, under a doctor's care, his eldest son present.
  **He was not shot by the British.** The tree's *"To be confirmed, not sure"* is retired — the date was
  right, the legend was not.
- **On that same form the clerk writes BOOYSEN and the son signs BOOYZEN**, four lines apart, three years
  after the war. That is as close to a photograph of the name changing as we will get.
- **But the groom's own 1879 signature may already show a z** — which would move the break back twenty
  years and make the joiners a remembered motive rather than the original one. *The reading is not
  certain, and the archive says so.* This is now the most consequential open question here.
- **He was a *Boer* (farmer) in 1879 and a *Mason* in 1905.** Something took the land away in between.
  First documentary support the burned-farm claim has ever had — and it is circumstantial.
- **George Downing Mountjoy Booyzen died on 11 December 1947, not 21 February.** "21 February" is when the
  notice was *signed* — in **1948**. His employer was the **South African Railways and Harbours**.
- **John Barry's 1915 death notice** types his birthplace as **"At sea (exact whereabouts unknown),
  British"** and his mother as **"born Neagle"**. His farm is **Manorowen** — one word, *a village in
  Pembrokeshire, Wales* — and he **owned no immovable property**.
- **A duplicate person resolved:** "Kathleen Mary Barry (Booysen)" is the same woman as Catherine Maria
  Sophia "Kathleen" Barry. The claim of "two Barry sisters married Booysens" is **withdrawn**.

## What this archive found

- **The name change is on the record.** MyHeritage carries *"Former name: Booysen"* as a formal fact on
  **Willem Hermanus "William Henry" Booyzen (1851–1905)**.
- **The surname statistics corroborate the story independently.** Booyzen is **83× rarer** than Booysen,
  and — unlike its parent name, which is a Cape name — it concentrates in **Gauteng (45%)**. A small group
  broke off a Cape name and reproduced on the Rand.
- **They lived inside the rebellion.** Burgersdorp produced **1,048** Cape Rebels; Barkly East and
  Dordrecht about **550** before Stormberg, with a commando of their own. The family married, bore
  children and was buried across all of those districts.
- **A lead worth chasing.** The family married on **8 July 1901**, mid-war, *"at the home of D Schoeman,
  'Caerlaverock', Barkly East"* — and a **Commandant D. Schoeman** led ~400 Cape Rebels at Labuschagne's
  Nek in March 1900. The bride's mother was a **Schoemann**.
- **The 1820 Settler is Kolbe, not Barry.** **George Augustus Kolbe** sailed on the ***Nautilus*** from
  Gravesend on 3 Dec 1819 in **Owen's party** and landed at **Algoa Bay on 14 Apr 1820** — a London
  tailor's son who became an LMS missionary and died in 1844 on a Karoo farm he had named **"Wurtemburg"**
  after his father's German homeland.
- **Every forename in "George Downing Mountjoy Booyzen" is a woman's surname** — Kolbe, Downing, Mountjoy.
- **It is a cousin marriage.** George Booyzen and Anna Pretorius were **first cousins once removed**, so
  Catherine Mary Sophia Booyzen descends from John Augustus Barry I and Margaretha Kolbe **twice**.
- **The line stops at seven generations**, on a man with no dates and no parents.
- **The Barry line above 1819 is broken** — one profile has a man **buried in Yorkshire five days before
  he died in the Eastern Cape**.

## The blocking question

**Gerthardus Lodewikus Booysen has no parents, no dates, and no records.** See `notes/QUEUE.md` § 0.

## Method

| | |
|---|---|
| **Documented** | A named source with a reference, and where possible the scan. |
| **Inferred** | A reasoned conclusion from documented facts, with the reasoning written out so it can be overturned. |
| **Superseded** | Asserted in the family record, and now displaced by a document that says otherwise. |
| **Disputed** | Asserted in the record and contradicted elsewhere in it. All fourteen are listed. |
| **Family lore** | Told, remembered, not corroborated. Kept because it is precious; labelled because pretending otherwise is how family myths become family history. |

**Living people are omitted from the build entirely** — not hidden, not gated, not present in the output.
A removal request is honoured within days, without argument and without requiring a reason.

## Running it

```bash
cd site
npm install
npm run dev      # http://localhost:4324
npm run build    # static output in site/dist
```

Deploys to GitHub Pages on every push to `main`.

## Layout

```
data/                  direct-line.tsv, surname-distribution.tsv, provincial-split.tsv
notes/                 documents-transcribed.md, raw-myheritage.md, the-name-change.md, the-barry-conflation.md,
                       john-augustus-barry.md, the-1820-settler.md, the-kolbe-line.md,
                       the-cousin-marriage.md, the-name-george-downing-mountjoy.md, QUEUE.md
site/src/pages/        the archive itself
sources/booyzen-photos/ full-resolution civil records extracted from MyHeritage
requests/              drafted archive and record requests
```

## Sibling archives

**The Defranceski** (Istria), **The Falco** (Arienzo, Campania) and **The Lerena** (Rosario, the Cape,
Brisbane) — same method, same author. **Catherine Mary Sophia Booyzen's marriage to Nuno Fernando
Lerena** at St Joseph's, Mayfair, in 1949 is the hinge between this archive and the Lerena one.

## Sources

MyHeritage *Defranceski Family Site (23andMe)* · FamilySearch (DRC registers; Cape and Transvaal probate;
Transvaal civil registration) · FindMyPast · Forebears · Wikipedia (*Booysen*) · Hilary Anne Shearing,
*The Cape Rebel of the South African War, 1899–1902* · The Van Plettenberg Historical Society ·
angloboerwar.com · family testimony from Tersia Booyzen and David Defranceski.

Identified and not yet worked: NAAIRS · Cape Archives (KAB) MOOC · Transvaal Archives (TAB) ·
Anglo-Boer War camp and rebel registers · *Suid-Afrikaanse Geslagsregisters* · Witwatersrand mining
employment registers · Cape deeds and quitrent records.
