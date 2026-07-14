import { createI18n } from "./i18n.js";
import { DataClient } from "./data-client.js";
import { evidenceClass, formatCompact, renderBarChart, renderGroupedBars, renderLineChart } from "./charts.js";
import { ageProfile, currentValue, futureSeries, historicalSeries, percentageChange, rankingRows, sexComparison, toCsv } from "./explorer.js";
import { DEFAULT_STATE, parseState, routeDefinitions, serializeState, stateForRoute } from "./routes.js";

const i18n = createI18n();
const client = new DataClient();
let state = parseState(window.location.search);
let renderedRows = [];
let renderToken = 0;

const elements = {
  chart: document.querySelector("#chart"),
  status: document.querySelector("#explorer-status"),
  title: document.querySelector("#analysis-title"),
  kicker: document.querySelector("#route-kicker"),
  provenance: document.querySelector("#provenance"),
  kpis: document.querySelector("#view-kpis"),
  interpretation: document.querySelector("#interpretation p"),
  tableHead: document.querySelector("#data-table thead"),
  tableBody: document.querySelector("#data-table tbody"),
  controls: Object.fromEntries(["route", "geography", "cancer", "measure", "metric", "sex", "age", "year", "top"].map((name) => [name, document.querySelector(`#filter-${name}`)])),
};

const titleKeys = {
  ranking: "chart.ranking.title",
  age: "chart.age.title",
  history: "chart.history.title",
  sex: "chart.sex.title",
  country: "chart.country.title",
  future: "chart.future.title",
};

const interpretationKeys = {
  ranking: "interpret.ranking",
  age: "interpret.age",
  history: "interpret.history",
  sex: "interpret.sex",
  country: "interpret.country",
  future: "interpret.future",
};

function dimensionLabel(dimension, value) {
  return client.manifest?.dimensions?.[dimension]?.[value]?.[i18n.language] ?? value;
}

function setStatus(message, type = "") {
  elements.status.textContent = message;
  elements.status.className = `status-message ${type}`.trim();
}

function replaceOptions(select, values, dimension, selected) {
  const prior = selected ?? select.value;
  select.replaceChildren(...values.map((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = dimension ? dimensionLabel(dimension, value) : String(value);
    return option;
  }));
  if (values.includes(String(prior)) || values.includes(prior)) select.value = String(prior);
  return select.value;
}

function initialiseDimensionControls() {
  const dimensions = client.manifest.dimensions;
  replaceOptions(elements.controls.geography, Object.keys(dimensions.geographies), "geographies", state.geography);
  const cancers = Object.keys(dimensions.cancers).sort((a, b) => dimensionLabel("cancers", a).localeCompare(dimensionLabel("cancers", b), i18n.language));
  replaceOptions(elements.controls.cancer, cancers, "cancers", state.cancer);
  replaceOptions(elements.controls.measure, Object.keys(dimensions.measures), "measures", state.measure);
  replaceOptions(elements.controls.metric, Object.keys(dimensions.metrics), "metrics", state.metric);
  replaceOptions(elements.controls.sex, Object.keys(dimensions.sexes), "sexes", state.sex);
  replaceOptions(elements.controls.age, Object.keys(dimensions.ages), "ages", state.age);
}

function updateOptionLanguage() {
  initialiseDimensionControls();
  syncControls();
}

function syncControls() {
  const geographyValues = state.route === "history" ? ["POL", "GBR", "ESP", "USA"] : ["WORLD", "POL", "GBR", "ESP", "USA"];
  replaceOptions(elements.controls.geography, geographyValues, "geographies", state.geography);
  const measureValues = state.route === "history" ? ["mortality"] : (state.route === "age" || state.route === "future") ? ["incidence", "mortality"] : ["incidence", "mortality", "lifetime_risk"];
  replaceOptions(elements.controls.measure, measureValues, "measures", state.measure);
  Object.entries(elements.controls).forEach(([name, select]) => {
    if (!select) return;
    const value = name === "geography" ? state.geography : state[name];
    if ([...select.options].some((option) => option.value === String(value))) select.value = String(value);
  });
  const shown = new Set(routeDefinitions[state.route].controls);
  shown.add("route");
  document.querySelectorAll("[data-control]").forEach((field) => field.classList.toggle("is-hidden", !shown.has(field.dataset.control)));
  document.querySelectorAll("[data-route]").forEach((button) => button.classList.toggle("active", button.dataset.route === state.route));
  elements.kicker.textContent = `ROUTE ${routeDefinitions[state.route].icon}`;
  elements.title.textContent = i18n.t(titleKeys[state.route]);
  elements.interpretation.textContent = i18n.t(interpretationKeys[state.route]);
}

function updateUrl() {
  history.replaceState(null, "", `${window.location.pathname}${serializeState(state)}${window.location.hash}`);
}

function provenance(partition) {
  const meta = partition?.provenance;
  if (!meta) return;
  elements.provenance.innerHTML = "";
  const badge = document.createElement("span");
  badge.className = `evidence-badge ${evidenceClass(meta.evidence_type)}`;
  badge.textContent = dimensionLabel("evidence", meta.evidence_type);
  const text = document.createElement("span");
  text.textContent = ` ${meta.source_id} · ${meta.source_version}`;
  elements.provenance.append(badge, text);
}

function formatValue(value, metric = state.metric) {
  if (metric === "percent") return `${new Intl.NumberFormat(i18n.language === "pl" ? "pl-PL" : "en-GB", { maximumFractionDigits: 2 }).format(value)}%`;
  return formatCompact(value, i18n.language);
}

function renderKpis(items) {
  elements.kpis.replaceChildren(...items.map(([value, label]) => {
    const card = document.createElement("div");
    card.className = "view-kpi";
    const strong = document.createElement("strong");
    strong.textContent = value;
    const small = document.createElement("small");
    small.textContent = label;
    card.append(strong, small);
    return card;
  }));
}

function renderTable(rows) {
  renderedRows = rows;
  const limited = rows.slice(0, 250);
  const columns = limited.length ? Object.keys(limited[0]).filter((key) => !["population", "quality_flags"].includes(key)) : [];
  const headerRow = document.createElement("tr");
  columns.forEach((column) => {
    const th = document.createElement("th");
    th.scope = "col";
    th.textContent = column.replaceAll("_", " ");
    headerRow.append(th);
  });
  elements.tableHead.replaceChildren(headerRow);
  elements.tableBody.replaceChildren(...limited.map((row) => {
    const tr = document.createElement("tr");
    columns.forEach((column) => {
      const td = document.createElement("td");
      const value = row[column];
      td.textContent = column === "cancer_code" ? dimensionLabel("cancers", value) : column === "sex" ? dimensionLabel("sexes", value) : String(value ?? "");
      tr.append(td);
    });
    return tr;
  }));
}

function validValues(rows, property, constraints = () => true) {
  return [...new Set(rows.filter(constraints).map((row) => row[property]).filter((value) => value != null))];
}

function setCompatibleCurrentState(rows, route) {
  const measures = route === "age" ? ["incidence", "mortality"] : [state.measure];
  if (!measures.includes(state.measure)) state.measure = measures[0];
  const cancerValues = validValues(rows, "cancer_code");
  if (!cancerValues.includes(state.cancer)) state.cancer = cancerValues.includes("LUNG") ? "LUNG" : cancerValues[0];
  replaceOptions(elements.controls.cancer, cancerValues.sort((a, b) => dimensionLabel("cancers", a).localeCompare(dimensionLabel("cancers", b), i18n.language)), "cancers", state.cancer);
  const sexValues = validValues(rows, "sex", (row) => route === "age" ? row.cancer_code === state.cancer && row.metric === "age_specific_rate" : true);
  if (!sexValues.includes(state.sex)) state.sex = sexValues.includes("both") ? "both" : sexValues[0];
  replaceOptions(elements.controls.sex, sexValues, "sexes", state.sex);
  if (route === "age") {
    state.metric = "age_specific_rate";
    return;
  }
  const metricValues = validValues(rows, "metric");
  if (!metricValues.includes(state.metric)) state.metric = metricValues.includes("number") ? "number" : metricValues[0];
  replaceOptions(elements.controls.metric, metricValues, "metrics", state.metric);
  const ages = validValues(rows, "age_group_label", (row) => row.metric === state.metric && row.sex === state.sex);
  if (!ages.includes(state.age)) state.age = ages.includes("All ages") ? "All ages" : ages[0];
  replaceOptions(elements.controls.age, ages.sort((a, b) => (client.manifest.dimensions.ages[a] ? Object.keys(client.manifest.dimensions.ages).indexOf(a) : 0) - (client.manifest.dimensions.ages[b] ? Object.keys(client.manifest.dimensions.ages).indexOf(b) : 0)), "ages", state.age);
}

async function renderRanking(token) {
  const partition = await client.load({ family: "current", geography: state.geography, measure: state.measure });
  if (token !== renderToken) return;
  if (!partition.available) return renderUnavailable();
  setCompatibleCurrentState(partition.objects, "ranking");
  const rows = rankingRows(partition.objects, state);
  const cancerName = (row) => dimensionLabel("cancers", row.cancer_code);
  renderBarChart(elements.chart, rows, { label: i18n.t("chart.ranking.title"), getLabel: cancerName, getValue: (row) => row.value, language: i18n.language, color: "#1f8a5b" });
  const leader = rows[0];
  renderKpis([
    [leader ? cancerName(leader) : "—", i18n.t("common.rank") + " 1"],
    [leader ? formatValue(leader.value) : "—", dimensionLabel("metrics", state.metric)],
    [dimensionLabel("geographies", state.geography), "2024 · " + dimensionLabel("sexes", state.sex)],
  ]);
  renderTable(rows);
  provenance(partition);
}

async function renderAge(token) {
  if (state.measure === "lifetime_risk") state.measure = "incidence";
  const partition = await client.load({ family: "current", geography: state.geography, measure: state.measure });
  if (token !== renderToken) return;
  if (!partition.available) return renderUnavailable();
  setCompatibleCurrentState(partition.objects, "age");
  const rows = ageProfile(partition.objects, state);
  if (!rows.length) return renderUnavailable();
  const labels = new Map(rows.map((row) => [row.age_start, row.age_group_label]));
  renderLineChart(elements.chart, [{ name: dimensionLabel("cancers", state.cancer), evidence: partition.provenance.evidence_type, points: rows.map((row) => ({ x: row.age_start, y: row.value })) }], {
    label: i18n.t("chart.age.title"), language: i18n.language, xLabel: (point) => labels.get(Number(point.x)) ?? point.x,
  });
  const peak = rows.reduce((best, row) => row.value > best.value ? row : best, rows[0]);
  renderKpis([
    [peak.age_group_label, i18n.language === "pl" ? "Szczyt współczynnika" : "Peak rate age"],
    [formatValue(peak.value, "age_specific_rate"), dimensionLabel("metrics", "age_specific_rate")],
    [dimensionLabel("sexes", state.sex), dimensionLabel("geographies", state.geography)],
  ]);
  renderTable(rows);
  provenance(partition);
}

async function renderHistory(token) {
  state.measure = "mortality";
  if (state.geography === "WORLD") state.geography = "POL";
  const routeCancers = client.availableValues("cancer", { family: "history", geography: state.geography });
  replaceOptions(elements.controls.cancer, routeCancers.sort((a, b) => dimensionLabel("cancers", a).localeCompare(dimensionLabel("cancers", b), i18n.language)), "cancers", state.cancer);
  let metrics = client.availableValues("metric", { family: "history", geography: state.geography, cancer: state.cancer });
  if (!metrics.length) {
    const cancers = client.availableValues("cancer", { family: "history", geography: state.geography });
    state.cancer = cancers.includes("LUNG") ? "LUNG" : cancers[0];
    metrics = client.availableValues("metric", { family: "history", geography: state.geography, cancer: state.cancer });
  }
  if (!metrics.includes(state.metric)) state.metric = metrics.includes("crude_rate") ? "crude_rate" : metrics[0];
  replaceOptions(elements.controls.metric, metrics, "metrics", state.metric);
  const partition = await client.load({ family: "history", geography: state.geography, cancer: state.cancer, metric: state.metric });
  if (token !== renderToken) return;
  if (!partition.available) return renderUnavailable();
  const sexes = validValues(partition.objects, "sex");
  if (!sexes.includes(state.sex)) state.sex = sexes.includes("both") ? "both" : sexes[0];
  replaceOptions(elements.controls.sex, sexes, "sexes", state.sex);
  const ages = validValues(partition.objects, "age_group_label", (row) => row.sex === state.sex);
  if (!ages.includes(state.age)) state.age = ages.includes("All ages") ? "All ages" : ages[0];
  replaceOptions(elements.controls.age, ages, "ages", state.age);
  const rows = historicalSeries(partition.objects, state);
  renderLineChart(elements.chart, [{ name: dimensionLabel("cancers", state.cancer), evidence: "observed", points: rows.map((row) => ({ x: row.year, y: row.value })) }], { label: i18n.t("chart.history.title"), language: i18n.language });
  const first = rows[0];
  const last = rows.at(-1);
  const change = first && last ? percentageChange(first.value, last.value) : null;
  renderKpis([
    [first && last ? `${first.year}–${last.year}` : "—", i18n.language === "pl" ? "Dostępny okres" : "Available period"],
    [change == null ? "—" : `${change >= 0 ? "+" : ""}${change.toFixed(1)}%`, i18n.language === "pl" ? "Zmiana od pierwszego roku" : "Change from first year"],
    [[...new Set(rows.map((row) => row.icd_revision))].join(" → "), "ICD"],
  ]);
  renderTable(rows);
  provenance(partition);
}

async function renderSex(token) {
  const partition = await client.load({ family: "current", geography: state.geography, measure: state.measure });
  if (token !== renderToken) return;
  if (!partition.available) return renderUnavailable();
  setCompatibleCurrentState(partition.objects, "sex");
  const rows = sexComparison(partition.objects, state);
  const label = dimensionLabel("cancers", state.cancer);
  renderGroupedBars(elements.chart, [{ label, values: rows.map((row) => ({ value: row.value, color: row.sex === "female" ? "#1f8a5b" : "#3b4ea0" })) }], { label: i18n.t("chart.sex.title"), language: i18n.language });
  const female = rows.find((row) => row.sex === "female");
  const male = rows.find((row) => row.sex === "male");
  const gap = female && male ? percentageChange(female.value, male.value) : null;
  renderKpis([
    [female ? formatValue(female.value) : "—", i18n.t("chart.legend.female")],
    [male ? formatValue(male.value) : "—", i18n.t("chart.legend.male")],
    [gap == null ? "—" : `${gap >= 0 ? "+" : ""}${gap.toFixed(1)}%`, i18n.language === "pl" ? "Mężczyźni względem kobiet" : "Male versus female"],
  ]);
  renderTable(rows);
  provenance(partition);
}

async function renderCountry(token) {
  const geographies = ["WORLD", "POL", "GBR", "ESP", "USA"];
  const partitions = await Promise.all(geographies.map((geography) => client.load({ family: "current", geography, measure: state.measure })));
  if (token !== renderToken) return;
  const world = partitions[0];
  if (!world.available) return renderUnavailable();
  setCompatibleCurrentState(world.objects, "country");
  const rows = partitions.map((partition, index) => {
    if (!partition.available) return null;
    const row = currentValue(partition.objects, state);
    return row ? { ...row, geography_code: geographies[index] } : null;
  }).filter(Boolean).sort((a, b) => b.value - a.value);
  renderBarChart(elements.chart, rows, { label: i18n.t("chart.country.title"), getLabel: (row) => dimensionLabel("geographies", row.geography_code), getValue: (row) => row.value, language: i18n.language, color: "#3b4ea0" });
  renderKpis([
    [rows[0] ? dimensionLabel("geographies", rows[0].geography_code) : "—", i18n.language === "pl" ? "Najwyższa wartość" : "Highest value"],
    [rows[0] ? formatValue(rows[0].value) : "—", dimensionLabel("metrics", state.metric)],
    [String(rows.length), i18n.language === "pl" ? "Porównane geografie" : "Geographies compared"],
  ]);
  renderTable(rows);
  provenance(world);
}

async function renderFuture(token) {
  if (state.measure === "lifetime_risk") state.measure = "incidence";
  state.metric = "number";
  const partition = await client.load({ family: "projection", geography: state.geography, measure: state.measure });
  if (token !== renderToken) return;
  if (!partition.available) return renderUnavailable();
  const cancers = validValues(partition.objects, "cancer_code");
  if (!cancers.includes(state.cancer)) state.cancer = cancers.includes("ALL_EX_NMSC") ? "ALL_EX_NMSC" : cancers[0];
  replaceOptions(elements.controls.cancer, cancers.sort((a, b) => dimensionLabel("cancers", a).localeCompare(dimensionLabel("cancers", b), i18n.language)), "cancers", state.cancer);
  const sexes = validValues(partition.objects, "sex", (row) => row.cancer_code === state.cancer);
  if (!sexes.includes(state.sex)) state.sex = sexes.includes("both") ? "both" : sexes[0];
  replaceOptions(elements.controls.sex, sexes, "sexes", state.sex);
  const years = validValues(partition.objects, "year", (row) => row.cancer_code === state.cancer && row.sex === state.sex).sort((a, b) => a - b);
  if (!years.includes(Number(state.year))) state.year = years.at(-1);
  replaceOptions(elements.controls.year, years.map(String), null, String(state.year));
  const rows = futureSeries(partition.objects, state).filter((row) => row.year <= state.year);
  renderLineChart(elements.chart, [{ name: dimensionLabel("cancers", state.cancer), evidence: "projected", points: rows.map((row) => ({ x: row.year, y: row.value })) }], { label: i18n.t("chart.future.title"), language: i18n.language, evidence: "projected" });
  const first = rows[0];
  const last = rows.at(-1);
  const change = first && last ? percentageChange(first.value, last.value) : null;
  renderKpis([
    [first ? formatValue(first.value, "number") : "—", "2024"],
    [last ? formatValue(last.value, "number") : "—", String(last?.year ?? state.year)],
    [change == null ? "—" : `+${change.toFixed(1)}%`, i18n.language === "pl" ? "Zmiana demograficzna" : "Demographic change"],
  ]);
  renderTable(rows);
  provenance(partition);
}

function renderUnavailable() {
  elements.chart.replaceChildren();
  elements.kpis.replaceChildren();
  renderTable([]);
  setStatus(i18n.t("explorer.unavailable"), "error");
}

async function render() {
  const token = ++renderToken;
  syncControls();
  updateUrl();
  setStatus(i18n.t("explorer.loading"));
  elements.chart.setAttribute("aria-busy", "true");
  try {
    const renderers = { ranking: renderRanking, age: renderAge, history: renderHistory, sex: renderSex, country: renderCountry, future: renderFuture };
    await renderers[state.route](token);
    if (token !== renderToken) return;
    syncControls();
    updateUrl();
    setStatus("");
  } catch (error) {
    console.error(error);
    if (token === renderToken) setStatus(i18n.t("explorer.error"), "error");
  } finally {
    if (token === renderToken) elements.chart.setAttribute("aria-busy", "false");
  }
}

function downloadCsv() {
  if (!renderedRows.length) return;
  const blob = new Blob([toCsv(renderedRows)], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `cancer-${state.route}-${state.geography}-${state.cancer}.csv`;
  link.click();
  URL.revokeObjectURL(link.href);
}

async function copyLink() {
  await navigator.clipboard.writeText(window.location.href);
  setStatus(i18n.t("explorer.copied"));
  window.setTimeout(() => setStatus(""), 1400);
}

Object.entries(elements.controls).forEach(([name, select]) => {
  select?.addEventListener("change", () => {
    const raw = select.value;
    if (name === "route") state = stateForRoute(raw, state);
    else if (name === "top" || name === "year") state[name] = Number(raw);
    else if (name === "geography") state.geography = raw;
    else state[name] = raw;
    render();
  });
});

document.querySelectorAll("[data-route]").forEach((button) => button.addEventListener("click", () => {
  state = stateForRoute(button.dataset.route, state);
  document.querySelector("#explorer").scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  render();
}));

document.querySelectorAll("[data-language]").forEach((button) => button.addEventListener("click", () => i18n.setLanguage(button.dataset.language)));
document.querySelector("#reset-view").addEventListener("click", () => { state = { ...DEFAULT_STATE }; render(); });
document.querySelector("#download-csv").addEventListener("click", downloadCsv);
document.querySelector("#copy-link").addEventListener("click", copyLink);
document.addEventListener("languagechange", () => {
  if (client.manifest) {
    updateOptionLanguage();
    render();
  }
});
window.addEventListener("popstate", () => { state = parseState(window.location.search); render(); });

async function start() {
  i18n.render();
  try {
    await client.initialise();
    initialiseDimensionControls();
    await render();
  } catch (error) {
    console.error(error);
    setStatus(i18n.t("explorer.error"), "error");
  }
}

start();
