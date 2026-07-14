# Global Cancer Trends Explorer Implementation Plan

**Goal:** Build a reproducible, high-granularity cancer data pipeline and a standalone bilingual EN/PL interactive explorer for global data plus Poland, the United Kingdom, Spain, and the United States.

**Architecture:** Python source adapters normalise observed, modelled, and projected cancer datasets into one validated long-form schema. The pipeline writes compact indexed JSON partitions for a static Chart.js application that exposes branching analysis routes by cancer type, age, sex, geography, year, measure, metric, and evidence type. Raw downloads remain reproducible but untracked; processed analysis outputs and web assets are versioned.

**Tech Stack:** Python 3.12, pandas, pyarrow, pydantic, pandera, requests, openpyxl, pytest, Jupyter, vanilla HTML/CSS/JavaScript, Chart.js 4, Node built-in test runner, GitHub CLI.

---

### Task 1: Project scaffold and reproducible environment

**Files:**
- Create: `README.md`
- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `src/cancer_explorer/__init__.py`
- Create: `tests/test_package.py`
- Create: `data/raw/.gitkeep`
- Create: `data/staging/.gitkeep`
- Create: `data/processed/.gitkeep`
- Create: `data/web/.gitkeep`
- Create: `reports/figures/.gitkeep`

**Step 1: Write the failing package test**

```python
def test_package_exposes_version():
    import cancer_explorer
    assert cancer_explorer.__version__ == "0.1.0"
```

**Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_package.py -v`  
Expected: FAIL because `cancer_explorer` is not installed.

**Step 3: Add the minimal package and environment**

Declare runtime dependencies and a `dev` extra in `pyproject.toml`, configure `src` packaging and pytest, expose `__version__`, and ignore downloaded raw/staging files while keeping directory placeholders.

**Step 4: Install and rerun**

Run: `python -m pip install -e ".[dev]"`  
Run: `python -m pytest tests/test_package.py -v`  
Expected: PASS.

**Step 5: Commit**

```bash
git add .gitignore README.md pyproject.toml src tests data reports
git commit -m "chore: scaffold cancer explorer project"
```

### Task 2: Source registry and provenance manifest

**Files:**
- Create: `config/sources.yml`
- Create: `src/cancer_explorer/sources.py`
- Create: `tests/test_sources.py`
- Create: `docs/sources.md`

**Step 1: Write failing registry tests**

Test that every source has `id`, `publisher`, `title`, `url`, `version`, `retrieved_at`, `evidence_type`, `licence`, `geographies`, and `notes`. Require entries for WHO Mortality Database, WHO GHE, GBD, IARC GLOBOCAN 2022, IARC Cancer Tomorrow, CI5 Plus/Cancer Over Time, ECIS, KRN, CRUK/ONS, REDECAN, and SEER.

```python
def test_required_sources_are_registered(source_registry):
    required = {"who_mortality", "who_ghe", "gbd_2023", "iarc_globocan_2022",
                "iarc_cancer_tomorrow", "iarc_ci5plus", "ecis", "krn",
                "uk_cancer", "redecan", "seer"}
    assert required <= set(source_registry)
```

**Step 2: Verify failure**

Run: `python -m pytest tests/test_sources.py -v`  
Expected: FAIL because the registry does not exist.

**Step 3: Implement registry loading and validation**

Use a small Pydantic model and YAML loader. Add `write_source_manifest()` that writes JSON with local filename, byte size, SHA-256 checksum, retrieval timestamp, and upstream metadata.

**Step 4: Verify passing tests**

Run: `python -m pytest tests/test_sources.py -v`  
Expected: PASS.

**Step 5: Commit**

```bash
git add config/sources.yml src/cancer_explorer/sources.py tests/test_sources.py docs/sources.md
git commit -m "feat: add cancer data source registry"
```

### Task 3: Canonical schema and compatibility rules

**Files:**
- Create: `src/cancer_explorer/schemas.py`
- Create: `src/cancer_explorer/compatibility.py`
- Create: `tests/test_schemas.py`
- Create: `tests/test_compatibility.py`

**Step 1: Write failing schema tests**

Create representative rows for observed mortality, modelled incidence with uncertainty, and projected cases. Test required columns, enums, non-negative values, age bounds, and uniqueness of the canonical key.

```python
def test_observed_and_modelled_rows_cannot_share_a_series_key(valid_rows):
    keys = canonical_series_key(valid_rows)
    assert "evidence_type" in keys
```

Test compatibility rules such as survival not combining with DALY metrics, age-standardised rates requiring a named standard population, and projected rows requiring a base year.

**Step 2: Verify failure**

Run: `python -m pytest tests/test_schemas.py tests/test_compatibility.py -v`  
Expected: FAIL.

**Step 3: Implement the canonical schema**

Define the approved long-form fields from the design document and return validation errors with source id plus row examples. Implement `is_valid_combination()` and `valid_routes()` for later browser manifests.

**Step 4: Verify passing tests**

Run: `python -m pytest tests/test_schemas.py tests/test_compatibility.py -v`  
Expected: PASS.

**Step 5: Commit**

```bash
git add src/cancer_explorer/schemas.py src/cancer_explorer/compatibility.py tests/test_schemas.py tests/test_compatibility.py
git commit -m "feat: define canonical cancer data schema"
```

### Task 4: Cancer taxonomy, ICD revisions, geography, sex, and age mappings

**Files:**
- Create: `config/cancer_taxonomy.csv`
- Create: `config/icd_mappings.csv`
- Create: `config/geographies.csv`
- Create: `config/age_groups.csv`
- Create: `src/cancer_explorer/mappings.py`
- Create: `tests/test_mappings.py`

**Step 1: Write failing mapping tests**

Cover all cancers with and without non-melanoma skin cancer, major individual cancer sites, ICD-7 through ICD-10 revisions, country code aliases, sex labels, open-ended ages, and five-year to broad-age aggregation.

```python
def test_age_65_plus_requires_all_constituent_groups(age_rows):
    incomplete = age_rows[age_rows.age_start != 75]
    with pytest.raises(IncompleteAggregationError):
        aggregate_age(incomplete, "65+")
```

**Step 2: Verify failure**

Run: `python -m pytest tests/test_mappings.py -v`  
Expected: FAIL.

**Step 3: Implement mappings**

Map source labels without discarding original codes. Make cancer labels bilingual. Reject unknown codes by default and write them to a review table rather than silently grouping them as “other”.

**Step 4: Verify passing tests**

Run: `python -m pytest tests/test_mappings.py -v`  
Expected: PASS.

**Step 5: Commit**

```bash
git add config src/cancer_explorer/mappings.py tests/test_mappings.py
git commit -m "feat: add cancer age and geography mappings"
```

### Task 5: Download, cache, checksum, and extraction layer

**Files:**
- Create: `src/cancer_explorer/download.py`
- Create: `tests/test_download.py`
- Create: `scripts/download_sources.py`

**Step 1: Write failing download tests**

Mock HTTP responses and test retry behaviour, content-length checks, ZIP validation, atomic writes, cache hits by checksum, explicit licence/manual-download blockers, and manifest generation.

**Step 2: Verify failure**

Run: `python -m pytest tests/test_download.py -v`  
Expected: FAIL.

**Step 3: Implement download logic**

Download to a temporary filename, validate, then rename. Never replace a valid cached file with an error page. For sources requiring interactive acceptance or authentication, generate `data/raw/MANUAL_DOWNLOADS.md` with exact instructions and expected filenames.

**Step 4: Verify passing tests and run source discovery**

Run: `python -m pytest tests/test_download.py -v`  
Run: `python scripts/download_sources.py --discover`  
Expected: PASS; source availability report created without downloading restricted data.

**Step 5: Commit**

```bash
git add src/cancer_explorer/download.py tests/test_download.py scripts/download_sources.py
git commit -m "feat: add reproducible source downloader"
```

### Task 6: WHO Mortality Database parser and longest historical series

**Files:**
- Create: `src/cancer_explorer/adapters/who_mortality.py`
- Create: `src/cancer_explorer/adapters/__init__.py`
- Create: `tests/fixtures/who_mortality_sample.csv`
- Create: `tests/test_who_mortality.py`

**Step 1: Write failing adapter tests**

Test ICD revision recognition, age-format conversion, cancer-code mapping, population joins, country-year completeness filtering, duplicate detection, and preservation of observed status.

```python
def test_who_rows_are_always_observed(parsed_who):
    assert set(parsed_who.evidence_type) == {"observed"}
```

**Step 2: Verify failure**

Run: `python -m pytest tests/test_who_mortality.py -v`  
Expected: FAIL.

**Step 3: Implement the adapter**

Stream large files in chunks, retain raw cause fields, join population and quality tables, and write Parquet partitions by country and ICD revision.

**Step 4: Download and transform the selected countries**

Run: `python scripts/download_sources.py --source who_mortality`  
Run: `python -m cancer_explorer.adapters.who_mortality --countries POL GBR ESP USA --output data/staging/who_mortality`  
Expected: observed mortality partitions plus a coverage summary.

**Step 5: Run tests and commit**

Run: `python -m pytest tests/test_who_mortality.py -v`  
Expected: PASS.

```bash
git add src/cancer_explorer/adapters tests/fixtures tests/test_who_mortality.py
git commit -m "feat: parse WHO cancer mortality history"
```

### Task 7: Global comparable, IARC snapshot, incidence, and projection adapters

**Files:**
- Create: `src/cancer_explorer/adapters/gbd.py`
- Create: `src/cancer_explorer/adapters/who_ghe.py`
- Create: `src/cancer_explorer/adapters/iarc.py`
- Create: `tests/fixtures/gbd_sample.csv`
- Create: `tests/fixtures/iarc_sample.csv`
- Create: `tests/test_global_adapters.py`

**Step 1: Write failing adapter tests**

Test GBD uncertainty bounds, WHO GHE fallback, IARC age/sex/type parsing, 2024 snapshot labels, 2050 projection base years, and the prohibition on combining separate GLOBOCAN releases as a trend.

**Step 2: Verify failure**

Run: `python -m pytest tests/test_global_adapters.py -v`  
Expected: FAIL.

**Step 3: Implement adapters with an explicit fallback**

Prefer a reproducible GBD 2023 export. If unavailable, ingest WHO GHE for comparable mortality/burden and mark unsupported measures absent. Parse IARC Cancer Today, CI5 Plus/Cancer Over Time, and Cancer Tomorrow exports without confusing registry populations with countries.

**Step 4: Acquire and transform available global sources**

Run: `python scripts/download_sources.py --source who_ghe --source iarc_globocan_2024 --source iarc_cancer_tomorrow --source iarc_ci5plus --source gbd_2023`
Run: `python -m cancer_explorer.adapters.iarc --output data/staging/iarc`  
Run: `python -m cancer_explorer.adapters.gbd --output data/staging/gbd`  
Expected: source-specific staging tables or a documented GBD access blocker with WHO GHE fallback.

**Step 5: Run tests and commit**

Run: `python -m pytest tests/test_global_adapters.py -v`  
Expected: PASS.

```bash
git add src/cancer_explorer/adapters tests/fixtures tests/test_global_adapters.py
git commit -m "feat: ingest global cancer burden and projections"
```

### Task 8: National deep-dive adapters

**Files:**
- Create: `src/cancer_explorer/adapters/krn.py`
- Create: `src/cancer_explorer/adapters/uk.py`
- Create: `src/cancer_explorer/adapters/ecis_redecan.py`
- Create: `src/cancer_explorer/adapters/seer.py`
- Create: `tests/test_national_adapters.py`

**Step 1: Write failing national-source tests**

Use small representative fixtures to test KRN bilingual tables and ASW versus ESP2013 rates, UK nation/UK total scope, ECIS registry versus country coverage, REDECAN estimates, and SEER incidence versus national mortality.

**Step 2: Verify failure**

Run: `python -m pytest tests/test_national_adapters.py -v`  
Expected: FAIL.

**Step 3: Implement national adapters**

Retain source-specific standard populations and geography scopes. Add survival, stage, prevalence, or lifetime risk only where published definitions and periods are explicit.

**Step 4: Acquire and transform sources**

Run: `python scripts/download_sources.py --source krn --source uk_cancer --source ecis --source redecan --source seer`  
Run: `python -m cancer_explorer.adapters.krn --output data/staging/krn`  
Run analogous module commands for UK, ECIS/REDECAN, and SEER.  
Expected: national staging tables plus coverage metadata.

**Step 5: Run tests and commit**

Run: `python -m pytest tests/test_national_adapters.py -v`  
Expected: PASS.

```bash
git add src/cancer_explorer/adapters tests/test_national_adapters.py tests/fixtures
git commit -m "feat: add national cancer deep dives"
```

### Task 9: Canonical transform, validation, reconciliation, and data-quality report

**Files:**
- Create: `src/cancer_explorer/transform.py`
- Create: `src/cancer_explorer/validate.py`
- Create: `tests/test_transform.py`
- Create: `tests/test_validate.py`
- Create: `scripts/build_dataset.py`
- Create: `docs/data-quality.md`

**Step 1: Write failing pipeline tests**

Test canonical key uniqueness, non-negative values, complete uncertainty ordering, safe age aggregation, source/evidence separation, NMSC definition separation, and published-total reconciliation tolerance.

**Step 2: Verify failure**

Run: `python -m pytest tests/test_transform.py tests/test_validate.py -v`  
Expected: FAIL.

**Step 3: Implement transformation and validation**

Write canonical Parquet plus CSV summary tables. Generate machine-readable validation results and a human-readable Markdown quality report with per-source year, geography, age, sex, cancer, and measure coverage.

**Step 4: Build the full available dataset**

Run: `python scripts/build_dataset.py --countries POL GBR ESP USA --strict`  
Expected: `data/processed/cancer_observations.parquet`, dimensions, coverage tables, and no unexplained reconciliation failures.

**Step 5: Run tests and commit**

Run: `python -m pytest tests/test_transform.py tests/test_validate.py -v`  
Expected: PASS.

```bash
git add src/cancer_explorer/transform.py src/cancer_explorer/validate.py tests scripts/build_dataset.py docs/data-quality.md data/processed
git commit -m "feat: build validated cancer analysis dataset"
```

### Task 10: Analysis engine and documented findings

**Files:**
- Create: `src/cancer_explorer/analyse.py`
- Create: `tests/test_analyse.py`
- Create: `analysis/findings.json`
- Create: `analysis/summary_tables/`
- Create: `docs/methodology.md`

**Step 1: Write failing analytical tests**

Test absolute and relative change, compound annual change, ranked cancer mix, age peaks, country comparison using like-for-like metrics, minimum-volume ranking rules, uncertainty-aware change labels, and demographic projection separation.

**Step 2: Verify failure**

Run: `python -m pytest tests/test_analyse.py -v`  
Expected: FAIL.

**Step 3: Implement analysis functions**

Functions must take explicit filters and return both results and provenance. Do not calculate survival from mortality-to-incidence ratio. Flag changes whose uncertainty intervals overlap rather than overstating direction.

**Step 4: Generate findings**

Run: `python -m cancer_explorer.analyse --input data/processed/cancer_observations.parquet --output analysis`  
Expected: global, cancer-type, age, country, sex, risk, projection, and data-quality findings with EN/PL narrative keys.

**Step 5: Run tests and commit**

```bash
python -m pytest tests/test_analyse.py -v
git add src/cancer_explorer/analyse.py tests/test_analyse.py analysis docs/methodology.md
git commit -m "feat: analyse cancer trends across dimensions"
```

### Task 11: Web-data partitions and valid-route index

**Files:**
- Create: `src/cancer_explorer/build_web_data.py`
- Create: `tests/test_web_data.py`
- Create: `data/web/manifest.json`
- Create: `data/web/routes.json`

**Step 1: Write failing web-data tests**

Test deterministic JSON, bounded partition size, valid-route generation, bilingual dimension labels, provenance on every series, and absence of invalid filter combinations.

**Step 2: Verify failure**

Run: `python -m pytest tests/test_web_data.py -v`  
Expected: FAIL.

**Step 3: Implement compact partitions**

Partition first by analysis family and geography, use short stable keys in data arrays, and keep a readable schema in `manifest.json`. Include a fallback starter dataset so the first screen renders before optional partitions load.

**Step 4: Generate and verify assets**

Run: `python -m cancer_explorer.build_web_data --input data/processed/cancer_observations.parquet --output data/web`  
Run: `python -m pytest tests/test_web_data.py -v`  
Expected: PASS; each committed JSON partition remains within the documented size budget.

**Step 5: Commit**

```bash
git add src/cancer_explorer/build_web_data.py tests/test_web_data.py data/web
git commit -m "feat: generate interactive cancer web data"
```

### Task 12: Reproducible analysis notebook

**Files:**
- Create: `notebooks/global_cancer_trends.ipynb`
- Create: `scripts/execute_notebook.py`
- Create: `tests/test_notebook.py`
- Create: `reports/figures/`

**Step 1: Write the failing notebook smoke test**

Verify required section headings, use of package functions rather than duplicated transformations, and successful execution against processed data.

**Step 2: Verify failure**

Run: `python -m pytest tests/test_notebook.py -v`  
Expected: FAIL.

**Step 3: Build the notebook**

Sections: Ask, source inventory, data quality, global burden, cancer types, age, sex, countries, risks, projections, caveats, and export. Save polished figures for documentation.

**Step 4: Execute from a clean kernel**

Run: `python scripts/execute_notebook.py`  
Run: `python -m pytest tests/test_notebook.py -v`  
Expected: PASS with no hidden state dependency.

**Step 5: Commit**

```bash
git add notebooks scripts/execute_notebook.py tests/test_notebook.py reports/figures
git commit -m "docs: add reproducible cancer analysis notebook"
```

### Task 13: Bilingual static site shell and visual system

**Files:**
- Create: `site/index.html`
- Create: `site/assets/css/style.css`
- Create: `site/assets/js/i18n.js`
- Create: `site/assets/js/data-client.js`
- Create: `site/assets/js/app.js`
- Create: `site/tests/i18n.test.js`
- Create: `site/tests/data-client.test.js`

**Step 1: Write failing JavaScript tests**

Use Node's built-in test runner to verify English/Polish key parity, interpolation, language persistence, manifest loading, and unavailable-combination messages.

**Step 2: Verify failure**

Run: `node --test site/tests/*.test.js`  
Expected: FAIL.

**Step 3: Implement the shell**

Reproduce the RM Portfolio theme with a sticky nav, case-study hero, KPI strip, analysis route map, explorer control bar, chart panels, interpretation blocks, source badges, methods section, and footer. Add the EN/PL toggle and accessible mobile navigation.

**Step 4: Verify passing tests**

Run: `node --test site/tests/*.test.js`  
Expected: PASS.

**Step 5: Commit**

```bash
git add site
git commit -m "feat: build bilingual cancer explorer shell"
```

### Task 14: Interactive charts and branching routes

**Files:**
- Create: `site/assets/js/charts.js`
- Create: `site/assets/js/explorer.js`
- Create: `site/assets/js/routes.js`
- Create: `site/tests/explorer.test.js`
- Create: `site/tests/routes.test.js`
- Modify: `site/index.html`
- Modify: `site/assets/css/style.css`

**Step 1: Write failing interaction tests**

Test filter state, compatible option narrowing, URL state serialisation, route-button transitions, data/source labels, age drill-down, country comparison, and modelled/observed/projected styling.

**Step 2: Verify failure**

Run: `node --test site/tests/*.test.js`  
Expected: FAIL.

**Step 3: Implement charts and routes**

Create Chart.js renderers for time series with uncertainty, ranked bars, age profiles, heatmaps, small multiples, slope charts, risk composition, and projections. Every renderer must accept a canonical series object and expose a source detail action.

**Step 4: Run tests and local smoke server**

Run: `node --test site/tests/*.test.js`  
Run: `python -m http.server 8000 --directory site`  
Expected: tests PASS; the site loads at `http://localhost:8000` with no console errors.

**Step 5: Commit**

```bash
git add site
git commit -m "feat: add branching cancer analysis explorer"
```

### Task 15: Narrative, source transparency, and portfolio integration handoff

**Files:**
- Modify: `site/index.html`
- Modify: `README.md`
- Create: `docs/portfolio-integration.md`
- Create: `docs/limitations.md`

**Step 1: Add content assertions**

Extend tests to require an executive summary, interpretation next to every major visual, EN/PL parity, source/version/evidence labels, caveats for ICD changes and modelled data, and no claim that MIR equals survival.

**Step 2: Verify failure before final content**

Run: `python -m pytest -q` and `node --test site/tests/*.test.js`  
Expected: at least one content assertion FAIL.

**Step 3: Add final bilingual narrative and documentation**

Write answer-first findings, explain how to read rates and counts, document integration by copying `site/` into the VPS portfolio, and include the exact homepage card markup as a handoff snippet without modifying the user's VPS.

**Step 4: Verify all content tests pass**

Run: `python -m pytest -q`  
Run: `node --test site/tests/*.test.js`  
Expected: PASS.

**Step 5: Commit**

```bash
git add README.md docs site
git commit -m "docs: complete cancer explorer narrative and handoff"
```

### Task 16: Full verification, GitHub publication, and release handoff

**Files:**
- Modify: any files required by verification
- Create: `docs/verification.md`

**Step 1: Run the complete reproducibility sequence**

Run:

```bash
python scripts/download_sources.py --verify-cache
python scripts/build_dataset.py --countries POL GBR ESP USA --strict
python -m cancer_explorer.analyse --input data/processed/cancer_observations.parquet --output analysis
python -m cancer_explorer.build_web_data --input data/processed/cancer_observations.parquet --output data/web
python scripts/execute_notebook.py
python -m pytest -q
node --test site/tests/*.test.js
```

Expected: all commands succeed; any intentionally manual/restricted source is explicitly listed rather than silently skipped.

**Step 2: Inspect the rendered site**

Check desktop and mobile layouts, both languages, keyboard navigation, every analysis branch, empty states, tooltips, source details, and console output. Record evidence in `docs/verification.md`.

**Step 3: Check repository hygiene**

Run: `git status --short`  
Run: `git ls-files | rg "data/raw|data/staging"`  
Expected: only `.gitkeep` and documentation from raw/staging; no secrets, tokens, or unlicensed bulk files.

**Step 4: Create the public GitHub repository and push**

Run:

```bash
gh auth switch --user robertmaszkiewski
gh repo create robertmaszkiewski/global-cancer-trends-analysis --public --source . --remote origin
git push -u origin main
```

Expected: public repository created under the requested account and `main` pushed.

**Step 5: Tag the initial release after verification**

```bash
git add docs/verification.md
git commit -m "docs: record cancer explorer verification"
git tag -a v1.0.0 -m "Global Cancer Trends Explorer v1.0.0"
git push origin main --tags
```
