import test from "node:test";
import assert from "node:assert/strict";

import { ageProfile, futureSeries, historicalSeries, rankingRows } from "../assets/js/explorer.js";

const current = [
  { year: 2024, cancer_code: "ALL", sex: "both", age_group_label: "All ages", metric: "number", value: 1000 },
  { year: 2024, cancer_code: "LUNG", sex: "both", age_group_label: "All ages", metric: "number", value: 300 },
  { year: 2024, cancer_code: "BREAST", sex: "both", age_group_label: "All ages", metric: "number", value: 250 },
  { year: 2024, cancer_code: "OTHER", sex: "both", age_group_label: "All ages", metric: "number", value: 400 },
  { year: 2024, cancer_code: "LUNG", sex: "female", age_group_label: "50-54", metric: "age_specific_rate", value: 20, age_start: 50 },
  { year: 2024, cancer_code: "LUNG", sex: "female", age_group_label: "55-59", metric: "age_specific_rate", value: 30, age_start: 55 },
];

test("ranking removes aggregate/source-defined categories and narrows top N", () => {
  assert.deepEqual(rankingRows(current, { sex: "both", metric: "number", age: "All ages", top: 1 }), [current[1]]);
});

test("age profile is sorted by numeric age, not label", () => {
  const rows = ageProfile([...current].reverse(), { cancer: "LUNG", sex: "female" });
  assert.deepEqual(rows.map((row) => row.age_group_label), ["50-54", "55-59"]);
});

test("history uses exact sex and age choice and preserves ICD breaks", () => {
  const history = [
    { year: 1970, sex: "both", age_group_label: "All ages", value: 2, icd_revision: "ICD-8" },
    { year: 2000, sex: "both", age_group_label: "All ages", value: 4, icd_revision: "ICD-10" },
    { year: 2000, sex: "male", age_group_label: "All ages", value: 6, icd_revision: "ICD-10" },
  ];
  const selected = historicalSeries(history, { sex: "both", age: "All ages" });
  assert.deepEqual(selected.map(({ year, icd_revision }) => [year, icd_revision]), [[1970, "ICD-8"], [2000, "ICD-10"]]);
});

test("future series selects cancer and sex and sorts years", () => {
  const future = [
    { year: 2050, cancer_code: "LUNG", sex: "both", value: 20 },
    { year: 2024, cancer_code: "LUNG", sex: "both", value: 10 },
    { year: 2050, cancer_code: "BREAST", sex: "both", value: 8 },
  ];
  assert.deepEqual(futureSeries(future, { cancer: "LUNG", sex: "both" }).map((row) => row.year), [2024, 2050]);
});
