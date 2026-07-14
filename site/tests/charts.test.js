import test from "node:test";
import assert from "node:assert/strict";

import { evidenceClass, evidenceStyle, formatCompact, linePath } from "../assets/js/charts.js";

test("evidence types have distinct visual encodings", () => {
  assert.equal(evidenceClass("observed"), "evidence-observed");
  assert.equal(evidenceStyle("observed").dash, "0");
  assert.notEqual(evidenceStyle("modelled").dash, evidenceStyle("projected").dash);
  assert.notEqual(evidenceStyle("observed").color, evidenceStyle("projected").color);
});

test("compact values remain readable across scales", () => {
  assert.equal(formatCompact(2637005, "en"), "2.64M");
  assert.equal(formatCompact(2637005, "pl"), "2,64 mln");
  assert.equal(formatCompact(84.5, "en"), "84.5");
});

test("line path handles constant and empty series", () => {
  assert.equal(linePath([], { width: 100, height: 50 }), "");
  assert.match(linePath([{ x: 2024, y: 10 }, { x: 2050, y: 10 }], { width: 100, height: 50 }), /^M/);
});
