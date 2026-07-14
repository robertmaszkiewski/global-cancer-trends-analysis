import test from "node:test";
import assert from "node:assert/strict";

import { DEFAULT_STATE, parseState, routeDefinitions, serializeState, stateForRoute } from "../assets/js/routes.js";

test("all six analytical branches are declared", () => {
  assert.deepEqual(Object.keys(routeDefinitions), ["ranking", "age", "history", "sex", "country", "future"]);
});

test("state serialises to a stable shareable query and parses back", () => {
  const state = { ...DEFAULT_STATE, route: "age", geography: "POL", cancer: "LUNG", sex: "female", metric: "age_specific_rate" };
  const query = serializeState(state);
  assert.equal(query, "?route=age&geo=POL&cancer=LUNG&measure=incidence&metric=age_specific_rate&sex=female&age=All+ages&year=2024&top=10");
  assert.deepEqual(parseState(query), state);
});

test("unknown and unsafe URL values fall back to defaults", () => {
  const parsed = parseState("?route=javascript%3Aalert(1)&geo=NOPE&top=999");
  assert.equal(parsed.route, "ranking");
  assert.equal(parsed.geography, "WORLD");
  assert.equal(parsed.top, 25);
});

test("branch presets produce compatible starting points", () => {
  assert.deepEqual(stateForRoute("history", DEFAULT_STATE), {
    ...DEFAULT_STATE,
    route: "history",
    geography: "POL",
    cancer: "LUNG",
    measure: "mortality",
    metric: "crude_rate",
  });
  assert.equal(stateForRoute("future", DEFAULT_STATE).year, 2050);
});
