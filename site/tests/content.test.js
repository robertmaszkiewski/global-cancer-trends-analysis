import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const siteRoot = resolve(fileURLToPath(new URL("..", import.meta.url)));
const html = readFileSync(resolve(siteRoot, "index.html"), "utf8");

test("page has all six analytical entry routes and filter controls", () => {
  for (const route of ["ranking", "age", "history", "sex", "country", "future"]) {
    assert.match(html, new RegExp(`data-route=["']${route}["']`));
  }
  for (const control of ["route", "geography", "cancer", "measure", "metric", "sex", "age", "year", "top"]) {
    assert.match(html, new RegExp(`id=["']filter-${control}["']`));
  }
});

test("source provenance, evidence legend and limitations are first-class content", () => {
  assert.match(html, /WHO Mortality Database/);
  assert.match(html, /Global Cancer Observatory/);
  assert.match(html, /evidence\.observed/);
  assert.match(html, /evidence\.modelled/);
  assert.match(html, /evidence\.projected/);
  assert.match(html, /method\.title/);
});

test("page is accessible before JavaScript and announces dynamic updates", () => {
  assert.match(html, /href="#main-content"/);
  assert.match(html, /<main[^>]+id="main-content"/);
  assert.match(html, /aria-live="polite"/);
  assert.match(html, /<noscript>/);
  assert.match(html, /<table[^>]+id="data-table"/);
});

test("copy avoids unsupported mortality-to-incidence survival claims", () => {
  assert.doesNotMatch(html, /mortality[- ]to[- ]incidence ratio[^<]*(survival|quality)/i);
  assert.doesNotMatch(html, /MIR[^<]*(survival|quality)/i);
});
