/* THE MINI FLAGS, PUT ON THE RIBBON CARDS AT BUILD TIME (27 October 2026).
   The flags are the kit's (kit/tools/ribbonflags.py, run by tools/ribbonflags.py) and live in src/data/ribbon-flags.json, not on the
   cards of story.json or family-lines.json, whose kit contract gates do not know a `flags` field. A living card is keyed by its
   position and `living` (the file names no living person). The kit's StoryRibbon and
   FamilyRibbon draw `card.flags` (FlagMini) and the credit line; this hands them cards that carry them. A card is matched by its
   position AND its name: a card that has moved or been renamed since the flags were made gets none, and check:ribbonflags then
   fails until tools/ribbonflags.py is run again. Nothing here chooses a flag. */
import ribbonFlags from "../data/ribbon-flags.json";

const put = (cards, rows) => (cards || []).map((c, i) => {
  const r = (rows || []).find((x) => x.card === i + 1);
  const same = r && (r.living ? !!(c.living || c.minor) && !("name" in r) : !(c.living || c.minor) && r.name === c.name);
  return same ? { ...c, flags: r.flags } : c;
});

/** the story (story.json) with its ribbon's cards carrying their flags */
export const storyWithFlags = (book) => (book && book.ribbon ? { ...book, ribbon: { ...book.ribbon, cards: put(book.ribbon.cards, ribbonFlags.story) } } : book);

/** one family-lines.json entry with its cards carrying their flags */
export const familyWithFlags = (family) => (family ? { ...family, cards: put(family.cards, (ribbonFlags.families || {})[family.id]) } : family);
