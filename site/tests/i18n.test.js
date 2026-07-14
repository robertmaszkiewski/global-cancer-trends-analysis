import test from "node:test";
import assert from "node:assert/strict";

import { createI18n, interpolate, translationKeys, translations } from "../assets/js/i18n.js";

test("English and Polish dictionaries have exactly the same keys", () => {
  assert.deepEqual(translationKeys(translations.en), translationKeys(translations.pl));
  assert.ok(translationKeys(translations.en).length >= 100);
});

test("interpolation replaces named values without losing zero", () => {
  assert.equal(interpolate("{count} records · {year}", { count: 0, year: 2024 }), "0 records · 2024");
});

test("language choice is persisted and restored", () => {
  const values = new Map();
  const storage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
  };
  const first = createI18n({ storage, initialLanguage: "en" });
  first.setLanguage("pl", { render: false });
  const second = createI18n({ storage, initialLanguage: "en" });
  assert.equal(second.language, "pl");
  assert.equal(second.t("nav.explore"), "Eksploruj dane");
});

test("unknown keys remain visible for QA", () => {
  const i18n = createI18n({ storage: null, initialLanguage: "en" });
  assert.equal(i18n.t("missing.key"), "[missing.key]");
});
