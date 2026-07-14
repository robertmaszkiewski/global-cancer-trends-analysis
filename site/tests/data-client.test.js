import test from "node:test";
import assert from "node:assert/strict";

import { DataClient, rowsToObjects } from "../assets/js/data-client.js";

const fixtures = {
  "/data/manifest.json": { version: 1, dimensions: { cancers: { LUNG: { en: "Lung", pl: "Płuco" } } } },
  "/data/routes.json": {
    version: 1,
    routes: [
      { family: "current", geography: "WORLD", measure: "incidence", file: "partitions/current/WORLD/incidence.json" },
      { family: "history", geography: "POL", cancer: "LUNG", metric: "age_specific_rate", file: "partitions/history/POL/LUNG/age_specific_rate.json" },
    ],
  },
  "/data/starter.json": { summary: { records: 386916 } },
  "/data/partitions/current/WORLD/incidence.json": { schema: ["year", "cancer_code", "value"], rows: [[2024, "LUNG", 2637005]] },
};

const fakeFetch = async (url) => ({
  ok: Object.hasOwn(fixtures, url),
  status: Object.hasOwn(fixtures, url) ? 200 : 404,
  json: async () => fixtures[url],
});

test("client initialises metadata and caches route partitions", async () => {
  let calls = 0;
  const client = new DataClient({ baseUrl: "/data", fetchFn: async (url) => { calls += 1; return fakeFetch(url); } });
  await client.initialise();
  const first = await client.load({ family: "current", geography: "WORLD", measure: "incidence" });
  const second = await client.load({ family: "current", geography: "WORLD", measure: "incidence" });
  assert.equal(first.rows[0][2], 2637005);
  assert.equal(second, first);
  assert.equal(calls, 4);
});

test("unavailable combination returns a structured result instead of inventing data", async () => {
  const client = new DataClient({ baseUrl: "/data", fetchFn: fakeFetch });
  await client.initialise();
  const result = await client.load({ family: "history", geography: "WORLD", cancer: "LUNG", metric: "number" });
  assert.deepEqual(result, { available: false, reason: "combination_unavailable" });
});

test("compact row arrays are decoded from the declared schema", () => {
  assert.deepEqual(rowsToObjects({ schema: ["year", "value"], rows: [[2024, 12], [2025, 13]] }), [
    { year: 2024, value: 12 },
    { year: 2025, value: 13 },
  ]);
});
