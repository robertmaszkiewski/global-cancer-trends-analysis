const EXCLUDED_RANKING_CODES = new Set(["ALL", "ALL_EX_NMSC", "OTHER", "UNSPECIFIED"]);

export function rankingRows(rows, { sex = "both", metric = "number", age = "All ages", top = 10 } = {}) {
  return rows
    .filter((row) => row.sex === sex && row.metric === metric && row.age_group_label === age && !EXCLUDED_RANKING_CODES.has(row.cancer_code))
    .sort((a, b) => b.value - a.value)
    .slice(0, top);
}

export function ageProfile(rows, { cancer, sex = "both" } = {}) {
  return rows
    .filter((row) => row.cancer_code === cancer && row.sex === sex && row.metric === "age_specific_rate" && row.age_group_label !== "All ages")
    .sort((a, b) => a.age_start - b.age_start);
}

export function historicalSeries(rows, { sex = "both", age = "All ages" } = {}) {
  return rows
    .filter((row) => row.sex === sex && row.age_group_label === age)
    .sort((a, b) => a.year - b.year);
}

export function futureSeries(rows, { cancer, sex = "both" } = {}) {
  return rows
    .filter((row) => row.cancer_code === cancer && row.sex === sex)
    .sort((a, b) => a.year - b.year);
}

export function sexComparison(rows, { cancer, metric = "age_standardised_rate", age = "All ages" } = {}) {
  return rows
    .filter((row) => row.cancer_code === cancer && row.metric === metric && row.age_group_label === age && (row.sex === "female" || row.sex === "male"))
    .sort((a, b) => a.sex.localeCompare(b.sex));
}

export function currentValue(rows, { cancer, sex = "both", metric = "age_standardised_rate", age = "All ages" } = {}) {
  return rows.find((row) => row.cancer_code === cancer && row.sex === sex && row.metric === metric && row.age_group_label === age) ?? null;
}

export function toCsv(rows) {
  if (!rows.length) return "";
  const columns = Object.keys(rows[0]);
  const escape = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
  return [columns.map(escape).join(","), ...rows.map((row) => columns.map((column) => escape(row[column])).join(","))].join("\n");
}

export function percentageChange(first, last) {
  if (!Number.isFinite(first) || !Number.isFinite(last) || first === 0) return null;
  return ((last - first) / first) * 100;
}
