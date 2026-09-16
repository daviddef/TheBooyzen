# The FindMyPast harvest — raw notes

Subscription opened 16 September 2026, one month, expires 16 October 2026.
Worked from the browser against FindMyPast's own GraphQL endpoint
`https://www.findmypast.co.uk/titan/marshal/graphql`, operation
`searchResultsRecordsAndMetadata`, variables `{filters, order, pageNumber}`.
Filter fields that work: LastName (+`variants`), FirstName, EventYear (+`offset`),
YearOfBirth, YearOfDeath, KeywordsPlace, Keywords, DatasetName, Regiment,
SourceCategory. Twenty rows a page. This lets a whole record set be swept in one
pass instead of clicked page by page.

---

## 1. James Mountjoy and the 21st Light Dragoons — a controlled negative

**The trap, and it is the FamilySearch-offset kind: the first query answered
wrongly, not emptily.** Searching the record set "British Army Service Records"
for `Mountjoy` with no year returns nothing but 1914–20 men, which reads as
"this is the First World War set". It is not. It is a composite, and a year
filter proves it.

Worse, the **Regiment string matters**. FindMyPast indexes the same regiment
under four separate strings, and they hold different War Office series:

| Regiment string | records | series | years |
|---|---|---|---|
| `21st Dragoons` | 342 | WO 22, WO 23, WO 121 | 1801–1886 |
| `21st Regt Of Light Dragoons` | 128 | **WO 97 only** | 1793–1813 |
| `21st Light Dragoons` | 66 | WO 22, WO 23, WO 76 | 1801–1877 |
| `21st Hussars` | 574 | WO 22, 23, 76, 97, 121, 131 | 1801–1919 |

Searching `21st Dragoons` alone would have returned a negative against an index
holding **no WO 97 at all** — and WO 97 is the series this archive needs.

**All four strings swept in full: 1,110 records. No Mountjoy, Montjoy, Monjoy,
Mountjoye or Montjoie under any of them.**

Controls that prove the searches work:
- WO 23/136, the 1806–07 volume: 18 men of the regiment, Mark Allen to Jno
  Warnsnop — James Mountjoy's own window at the Cape.
- WO 23/147, 1817–26: 12 men, Jno Allen to Adam Ross.
- WO 97 for `21st Regt Of Light Dragoons`: 128 men, 1793–1813, WO 97/12 to
  WO 97/97. The alphabetical run through M is Martin, McClay, McCracken, McCue,
  McGregor, McNary, Merrick, Morgan, Morris, Morrison. Nothing between Moses and
  Napier in the other sweep either.

**Eighteen pre-1860 Mountjoys exist in the set**, and not one is in this
regiment: 36th Foot (George, WO 97/533, WO 23/39, WO 22/61, WO 22/106),
44th Foot (Jno 1806–07 WO 23/140; John 1804 WO 121/72; John WO 23/40, WO 22/10),
60th Foot / KRRC (Wm 1806–07 WO 23/138; William 1810 WO 121/171), and one
**William Montjoy, 1801, 60th Rifles, WO 121/44**.

**What the negative means.** WO 22, WO 23 and WO 121 are all Royal Hospital
Chelsea *pension* series — returns of district pension offices, admission books,
and discharge certificates of men admitted to pension. FindMyPast's WO 97 run
for this regiment stops at **1813**. A man discharged at the Cape after 1813 who
stayed there and set up as a saddler is precisely the man who would never enter
any of them. The absence is consistent with the story; it is not evidence
against it.

---

## 2. Johan Gottlieb Kolbe's address — Church Street South, St Anne's Soho

**Westminster Rate Books 1634–1900: 121 entries under 24 spellings of his
forename**, an unbroken run from 1800 to 1831 — Gothel, Gotleb, Gotleib,
Gotlieb, Gotliel, Gotlob, Gotlobe, Goltief, Gottieb, Gottiel, Gottlieb,
Gottlob, Gutlieb, Kottieb, Gilliet, and "Jos Gottiel".

Addresses read off the transcripts:

| Year | Name as written | Address | Parish |
|---|---|---|---|
| 1800 | John Kolbe | **Broad Street North**, folio 41 | St James, Piccadilly |
| 1811 | John G Kolbe | **Church Street South** | St Anne, Soho |
| 1819 | John Gottlob Kolbe | Church Street South | St Anne, Soho |
| 1828 | John Gotlieb Kolbe | Church Street South | St Anne, Soho |
| 1831 | John Gottieb Kolbe | Church St South | St Anne, Soho |
| 1829 | John Gottlieb Kolbe (Land Tax) | Church Street | Westminster, St Anne, Soho |

**The 1800 entry corroborates the 1799 master tailors' list** — "Kolbe, John,
18 Broad-street, Soho", one of 234 men who met over the Combination Act in
December 1799 — from an entirely independent source.

**Brunswick Square appears in no rate book, no land tax return, no census and no
burial register.** These are Westminster sources and Brunswick Square is in
Bloomsbury, so they cannot disprove it; but they place him continuously in Soho
from 1800 to 1831 and in St George Hanover Square in 1841 and 1845, with no gap
into which a Bloomsbury address fits. Conduit Street is in St George Hanover
Square.

Also found: **1841 census, St George Hanover Square** — John G Kolbe with
Amelia A, Charlotte and Marianne Kolbe (GBC/1841/0008142283-6).

---

## 3. The eight sons — five of them named for the first time

Baptisms at Westminster, father John / John Gottleb / John Gottlow / John
Gottlob Kolbe, mother **Mary** in every single one:

| Baptised | Name | Sex | Father as written | FS batch |
|---|---|---|---|---|
| 9 Jan 1792 | Juliet Rosinia | F | John | C72301-3 |
| 11 Jun 1794 | Mary Ann | F | John | C32052-8 |
| 29 Dec 1795 | Elizabeth | F | John | C15051-2 |
| 17 Jan 1798 | **Charles** | M | John | C15051-2 |
| 29 Jul 1800 | **John Henry** | M | John | I02559-1 |
| 2 Feb 1803 | **George Augustus** | M | John Gottlow | — |
| 12 Mar 1805 | **Frederick Charles** | M | John Gottleb | C15051-2 |
| 3 Feb 1807 | **Charles Samuel** | M | John Gottleb | C15051-2 |
| 18 Aug 1813 | Frederica Carolina | F | John Gottleb | C06236-1 |
| 4 Jul 1819 | Jane Day | F | John Gottlob | C06236-1 |

George Augustus's entry is the control: baptism 2 February 1803, which is the
date this archive already had from another route.

**Excluded after checking**: Frederick Kolbe, baptised 16 Dec 1816 at
Westminster — father **George**, mother **Elizabeth**, batch C72301-7. A
different family. He is not a brother, and he was one click from being made one.
Henry Kolbe, baptised 2 Feb 1800 at Southwark — father Henry, mother Susannah.
Also not.

Five sons of the eight are now named. Three are still missing, and the gaps in
the baptism run — 1808 to 1812, and 1814 to 1818 — are where they sit.

---

## 4. Charles Samuel Kolbe, the first dead brother to be named

**TNA RG 4/4630, image 0044.** England & Wales Non-Conformist Burials.
Denomination **Lutheran**. Place **St Ann Westmr**.

- Died **6 December 1807**
- Buried **11 December 1807**
- Age **1 year 10 days**

Baptised 3 February 1807 and dead before Christmas. The obituary of 1844 says
George Augustus was "the last remaining of eight sons"; this is the first of the
seven to be given a date.

**RG 4/4630 is not in this archive's list of Savoy registers.** The note in the
work list named RG 4/4625, 4626, 4628, 4631 for deaths and burials and 4627,
4629 for baptisms. 4630 was missing from it.

---

## 5. Johan Gottlieb Kolbe's burial — a documented answer against a tree claim

**Westminster Burials, City of Westminster Archives Centre**
(GBPRS/WSMTN/BUR/0833538):

- Died **18 November 1845**
- Buried **26 November 1845**
- **St John the Baptist, Great Marlborough Street**, page 7
- Year of birth given as **1764**

This archive has been citing, from a tree, "buried at the German Lutheran church
of the Savoy on 26 November 1845, entry 55, grave 7". **The date matches to the
day and the "7" matches**, but the church in the register is St John the Baptist,
Great Marlborough Street — a Soho chapel, five minutes from Church Street. The
death date and the birth year are both new.

Corroborated by the civil registration: **England & Wales Deaths 1837-2007,
John Gottlob Kolbe, 1845 Q4, St George Hanover Square, vol AZ, 000377, p145.**

Other Kolbe deaths in the same window, not yet placed: George Kolbe, buried 1848
at St Margaret Westminster (d. 1848 Q3, Westminster St Margaret); Elizabeth
Kolbe, d. 1852 Q3, Strand; Emanuel Christopher Kolbe, buried 1836 at Bermondsey
St Mary Magdalen.

Also unread: **Old Bailey 1819, John Henry Kolbe** (GBOR/OLDBAILEY/0399292-3)
and five London Gazette notices — Henry Kolbe 1824 (x2), John Gotlob 1824, John
Henry 1824 (x2), J.G. 1836, John Gbttlob 1836, John Gotlieb 1845.
