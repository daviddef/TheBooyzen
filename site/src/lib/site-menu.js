/* THE WHOLE MENU, one list. 12 November 2026 (the menu regroup, PR A, menu only): the seven groups other than Research became five, and
   Research (lib/research-menu.js, unchanged) is the sixth. The header menu and the drawer read THIS list (layouts/Base.astro does), so
   there is one place to change a label or move a page. No page was renamed, merged or deleted and no address changed: every href below
   was already a built page, only its group moved.
     a menu is  [label, items]
     items      a flat list of [href, label]                        (a short menu: one column)
                or a list of groups { head, href?, items }          (a group is a column; `href` makes its heading a link)
   What left a menu by name, and where it is reached from instead:
     /whats-new/       left Start: it is the heading of Research / What's new, and the pulse button in the header.
     eight family pages (Pretorius, Botha, van der Merwe, Schoeman, Downing, Daschner, Lowies, van Niekerk) left the menu: the families
                       index /families/ ("All the families") links every one of them (proved in docs/menu-reach.md).
   /women/ and /cousins/ are NOT linked from the /families/ index, so they stay in the menu until the index is fixed. */
import famData from "../data/families.json";
import { navGroups } from "./research-menu.js";

/* the four families with a page of their own stay named in the menu; the others are reached through /families/ */
const NAMED = ["booyzen", "mountjoy", "barry", "kolbe"];
const named = famData.families.filter((f) => NAMED.includes(f.slug))
  .map((f) => [f.page || `/families/${f.slug}/`, f.title]);

export const MENU = [
  ["Start", [
    ["/", "Home"], ["/story/", "The story"], ["/about/", "About"],
  ]],
  ["Our line", [
    ["/direct-line/", "The Spine"], ["/rebels/", "The Rebels"], ["/johannesburg/", "Johannesburg"],
  ]],
  ["People", [
    { head: "Lists", items: [
      ["/people/", "The People"], ["/who/", "Every Name"], ["/register/", "The Register"], ["/households/", "Households"],
      ["/marriages/", "The Marriages"],
    ] },
    { head: "Drawn", items: [
      ["/tree/", "Our line, drawn"], ["/trees/", "The trees"], ["/roots/", "Roots & Routes"], ["/timeline/", "The Timeline"],
      ["/bloodline/", "Blood relatives, drawn"],
    ] },
  ]],
  ["Places & families", [
    { head: "Places", items: [
      ["/lines/", "The Lines"], ["/atlas/", "The Atlas"], ["/places/", "Places"],
    ] },
    { head: "The families", items: [
      ["/families/", "All the families"], ...named, ["/women/", "The Women"], ["/cousins/", "The Cousin Marriage"],
    ] },
  ]],
  /* THE NAME IS ITS OWN GROUP, AND IT IS THE ESTATE'S NAME FOR IT (unchanged). */
  ["The name", [["/name/", "The Name"], ["/namesakes/", "The forenames"]]],
  ["Research", navGroups],
];
