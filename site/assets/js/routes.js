export const DEFAULT_STATE = Object.freeze({
  route: "ranking",
  geography: "WORLD",
  cancer: "LUNG",
  measure: "incidence",
  metric: "number",
  sex: "both",
  age: "All ages",
  year: 2024,
  top: 10,
});

export const routeDefinitions = Object.freeze({
  ranking: { family: "current", titleKey: "route.ranking", icon: "01", controls: ["geography", "measure", "metric", "sex", "age", "top"] },
  age: { family: "current", titleKey: "route.age", icon: "02", controls: ["geography", "cancer", "measure", "sex"] },
  history: { family: "history", titleKey: "route.history", icon: "03", controls: ["geography", "cancer", "metric", "sex", "age"] },
  sex: { family: "current", titleKey: "route.sex", icon: "04", controls: ["geography", "cancer", "measure", "metric", "age"] },
  country: { family: "current", titleKey: "route.country", icon: "05", controls: ["cancer", "measure", "metric", "sex", "age"] },
  future: { family: "projection", titleKey: "route.future", icon: "06", controls: ["geography", "cancer", "measure", "sex", "year"] },
});

const presets = Object.freeze({
  ranking: {},
  age: { metric: "age_specific_rate", age: "All ages" },
  history: { geography: "POL", cancer: "LUNG", measure: "mortality", metric: "crude_rate" },
  sex: { geography: "WORLD", cancer: "LUNG", measure: "incidence", metric: "age_standardised_rate" },
  country: { cancer: "LUNG", measure: "incidence", metric: "age_standardised_rate", geography: "WORLD" },
  future: { cancer: "ALL_EX_NMSC", measure: "incidence", metric: "number", year: 2050 },
});

const valid = {
  route: new Set(Object.keys(routeDefinitions)),
  geography: new Set(["WORLD", "POL", "GBR", "ESP", "USA"]),
  measure: new Set(["incidence", "mortality", "lifetime_risk"]),
  metric: new Set(["number", "crude_rate", "age_specific_rate", "age_standardised_rate", "percent"]),
  sex: new Set(["both", "female", "male"]),
};

export function stateForRoute(route, current = DEFAULT_STATE) {
  const safeRoute = valid.route.has(route) ? route : DEFAULT_STATE.route;
  return { ...current, route: safeRoute, ...presets[safeRoute] };
}

export function parseState(search = "") {
  const params = new URLSearchParams(String(search).replace(/^\?/, ""));
  const state = { ...DEFAULT_STATE };
  const mappings = { route: "route", geo: "geography", cancer: "cancer", measure: "measure", metric: "metric", sex: "sex", age: "age" };
  Object.entries(mappings).forEach(([param, key]) => {
    const value = params.get(param);
    if (!value) return;
    if (valid[key] && !valid[key].has(value)) return;
    if (key === "cancer" && !/^[A-Z0-9_]+$/.test(value)) return;
    if (key === "age" && !/^(All ages|\d{1,3}(?:-\d{1,3}|\+))$/.test(value)) return;
    state[key] = value;
  });
  const year = Number.parseInt(params.get("year"), 10);
  if (Number.isInteger(year) && year >= 1900 && year <= 2100) state.year = year;
  const top = Number.parseInt(params.get("top"), 10);
  if (Number.isInteger(top)) state.top = Math.max(1, Math.min(25, top));
  return state;
}

export function serializeState(state) {
  const params = new URLSearchParams();
  params.set("route", state.route);
  params.set("geo", state.geography);
  params.set("cancer", state.cancer);
  params.set("measure", state.measure);
  params.set("metric", state.metric);
  params.set("sex", state.sex);
  params.set("age", state.age);
  params.set("year", String(state.year));
  params.set("top", String(state.top));
  return `?${params.toString()}`;
}
