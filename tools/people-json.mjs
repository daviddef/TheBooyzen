// people.js is the source of truth. people.json exists only because the Python
// tools need to read the same list, so it is regenerated on every build and never
// edited by hand — the two drifted once, and four people vanished off the index.
import { writeFileSync } from "node:fs";
import { people, lines } from "../site/src/data/people.js";

writeFileSync(
  new URL("../site/src/data/people.json", import.meta.url),
  JSON.stringify({ people, lines }, null, 1) + "\n"
);
console.log(people.length + " people · " + lines.length + " families");
