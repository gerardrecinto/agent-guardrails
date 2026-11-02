// The web demo must agree with the Python hook on every shared case.
import { readFileSync } from "node:fs";
const rules = JSON.parse(readFileSync(new URL("../docs/rules.json", import.meta.url))).rules
  .map((r) => ({ ...r, re: new RegExp(r.pattern, "i") }));
const cases = JSON.parse(readFileSync(new URL("./cases.json", import.meta.url)));
const first = (cmd) => rules.find((r) => r.re.test(cmd))?.id ?? null;
let bad = 0;
for (const [id, cmds] of Object.entries(cases.block))
  for (const c of cmds) if (first(c) !== id) { console.error(`expected ${id}: ${c} -> ${first(c)}`); bad++; }
for (const c of cases.allow) if (first(c) !== null) { console.error(`expected allow: ${c} -> ${first(c)}`); bad++; }
if (bad) process.exit(1);
console.log("web demo matches Python on", Object.values(cases.block).flat().length + cases.allow.length, "cases");
