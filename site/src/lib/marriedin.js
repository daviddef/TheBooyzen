/* The eleven lines. A line is assigned in the data, person by person — this
   archive's own judgement read back, not a surname matched at build time. */
import P from "../data/people.json";
const byLine = {};
for (const x of P.people) (byLine[x.l] ||= []).push(x);
const OWN = "Booyzen";
export const chartGroups = [
  { key: "own", label: "The name this archive carries",
    families: [{ surname: OWN, n: (byLine[OWN] || []).length }] },
  { key: "in", label: "The lines that married in",
    families: P.lines.filter((n) => n !== OWN)
      .map((n) => ({ surname: n, n: (byLine[n] || []).length }))
      .sort((a, b) => b.n - a.n) },
];
