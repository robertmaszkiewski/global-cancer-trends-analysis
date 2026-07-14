# Global Cancer Trends Explorer — Design

**Date:** 2026-07-14  
**Status:** Approved  
**Repository:** `robertmaszkiewski/global-cancer-trends-analysis`

## Purpose

Build a reproducible, portfolio-quality cancer analysis and a standalone bilingual EN/PL web page that can later be mounted as a new case-study tab on `rmportfolio.co.uk`.

The product is not a linear report with a few headline charts. It is a high-detail cancer data explorer whose users can branch repeatedly by geography, year, cancer type, age, sex, measure, metric, and evidence type. The project must preserve the highest useful granularity available from each source while preventing invalid comparisons between observed, modelled, and projected estimates.

## Audience and success criteria

The primary audience is data-analysis recruiters and portfolio visitors. A secondary audience is anyone who wants to explore how cancer burden differs by age, cancer site, sex, geography, and time.

The project succeeds when:

- a user can begin with a global result and drill into Poland, the United Kingdom, Spain, or the United States;
- a user can select all cancers or a specific cancer type and continue into age- and sex-specific views;
- counts, crude rates, age-specific rates, and age-standardised rates are clearly distinguished;
- observed registry data, modelled estimates, and projections are never silently joined into one series;
- every displayed value retains source and methodology metadata;
- the full pipeline can be rerun from documented source downloads to compact web-ready assets;
- the static web page works without a backend and visually matches the existing RM Portfolio style;
- all interface and explanatory copy is available in English and Polish.

## Product direction

Use the visual language of `rmportfolio`: white and pale-grey surfaces, navy text, green data accent, rounded cards, restrained shadows, sticky navigation, Chart.js charts, and a clear Ask–Prepare–Process–Analyse–Share narrative.

The distinctive idea is an **analysis route map**. Each major chart exposes logical next routes, such as “break down by age”, “compare countries”, “open cancer type”, or “inspect source quality”. The page should feel like a research instrument while remaining understandable to a non-specialist.

## Evidence architecture

No single cancer dataset supports the requested historical depth, worldwide coverage, cancer-site detail, age detail, survival outcomes, and risk attribution. The explorer therefore uses evidence layers.

### Layer 1 — comparable global panel

Use Global Burden of Disease results for consistent global, regional, and country comparisons from 1990 through 2023 where downloadable data and licence terms permit. Preserve values and uncertainty bounds for incidence, deaths, prevalence, DALYs, YLLs, and YLDs by cancer cause, age, sex, year, and geography.

If the current GBD result export cannot be obtained reproducibly, the pipeline must record the blocker and use WHO Global Health Estimates for comparable mortality/burden time series. It must not fabricate unavailable incidence detail.

### Layer 2 — longest observed mortality history

Use the WHO Mortality Database raw files for country-reported deaths from 1950 onward. Load ICD-7, ICD-8, ICD-9, and ICD-10 files, mapping codes to a documented common cancer taxonomy. Keep country, year, sex, age, ICD revision, cause code, deaths, population, completeness, and usability metadata.

Only publish a country-year when source quality passes the selected rule. Gaps remain gaps. ICD changes are displayed as methodological breaks where they may affect trends.

### Layer 3 — detailed incidence time trends

Use IARC CI5 Plus / Cancer Over Time for annual incidence in selected cancer registries and populations, by cancer site, year, sex, and age, for the longest available period. Registry-level data must not be presented as whole-country incidence unless the source explicitly supports national coverage.

### Layer 4 — current global snapshot and projections

Use the newly released IARC GLOBOCAN 2024 snapshot for incidence and mortality across 186 countries or territories and 34 cancer types. Use Cancer Tomorrow projections from the 2024 baseline through 2050. Preserve five-year age groups, sex, cancer site, count, age-specific rate, crude rate, age-standardised rate, and cumulative risk wherever supplied.

GLOBOCAN releases from different years must not be treated as a historical series because source coverage and estimation methods change between releases.

### Layer 5 — country validation and deeper outcomes

- Poland: Polish National Cancer Registry (KRN), with long-run incidence and mortality tables and the latest annual report.
- United Kingdom: national cancer registrations and mortality series exposed through ONS and Cancer Research UK; survival and stage only where definitions are consistent.
- Spain: REDECAN and ECIS, with registry coverage metadata and INE mortality where applicable.
- United States: SEER incidence, survival, prevalence, stage, and lifetime-risk exports plus national mortality data.

Country-specific series validate headline findings and add outcome measures that are not globally comparable. The interface must label them as national deep dives rather than merge them into the global comparison layer.

### Layer 6 — attributable risks

Use GBD risk attribution and/or IARC attributable-fraction datasets for tobacco, alcohol, high body-mass index, infections, ultraviolet radiation, air pollution, occupational exposure, diet, and other supported factors. Only show risk–cancer–geography combinations explicitly supplied by a source. Association and attribution must not be described as individual-level causation.

## Normalised analytical model

The canonical long-form fact table will contain:

- `source_id`
- `source_version`
- `evidence_type` (`observed`, `modelled`, `projected`)
- `geography_level`
- `geography_code`
- `geography_name`
- `year`
- `cancer_code`
- `cancer_label_en`
- `cancer_label_pl`
- `icd_revision`
- `icd_codes`
- `sex`
- `age_start`
- `age_end`
- `age_group_label`
- `measure` (`incidence`, `mortality`, `prevalence`, `DALY`, `YLL`, `YLD`, `survival`, `lifetime_risk`)
- `metric` (`number`, `crude_rate`, `age_specific_rate`, `age_standardised_rate`, `percent`, `probability`)
- `standard_population`
- `value`
- `lower_bound`
- `upper_bound`
- `population`
- `coverage_percent`
- `quality_flag`
- `notes`

Separate dimension tables define geographies, cancer taxonomy, age groups, sources, and metric compatibility.

## Granularity

Preserve five-year age groups wherever available: `0–4`, `5–9`, through `80–84`, and `85+`. Derive additional audience-friendly groupings such as children, adolescents and young adults, `20–39`, `40–64`, and `65+` only from complete constituent groups.

Preserve the source cancer taxonomy and map it to a common set including all cancers and the major individual sites: lung, breast, colorectum, prostate, stomach, liver, cervix uteri, pancreas, bladder, kidney, thyroid, melanoma, brain/CNS, leukaemia, non-Hodgkin lymphoma, multiple myeloma, ovary, corpus uteri, testis, oesophagus, oral cavity, larynx, gallbladder, nasopharynx, and other supported sites.

Never aggregate incompatible definitions of “all cancers”, especially where non-melanoma skin cancer is included in one source and excluded in another.

## Analysis branches

1. **Global burden:** counts and rates over time, with population growth and ageing separated from rate change where the data supports decomposition.
2. **Cancer type explorer:** incidence, mortality, prevalence, burden, and trend for each supported cancer site.
3. **Age explorer:** age-specific curves, cancer mix within an age group, median/peak age patterns, and changes in younger versus older populations.
4. **Country comparison:** world, Poland, UK, Spain, and USA using like-for-like age-standardised metrics.
5. **Sex differences:** male/female gaps by cancer, age, country, and time.
6. **Rising and falling cancers:** absolute and relative changes, with a minimum-volume rule to avoid ranking noise.
7. **Survival and outcomes:** national deep dives only, with source-specific definitions and periods.
8. **Risk factors:** attributable burden by factor and cancer, plus careful interpretation.
9. **Future burden:** projections to 2050, separating demographic projection from assumed risk change when the source permits.
10. **Data quality:** completeness, registry coverage, uncertainty intervals, ICD breaks, and missing combinations.

## Web experience

The site is a standalone static application under `site/`.

### Navigation

- Overview
- Explore
- Age
- Cancer types
- Countries
- Risk factors
- Future
- Methods
- EN/PL language switch

### Explorer controls

Sticky filters select geography, cancer type, age group, sex, measure, metric, year range, and evidence type. Invalid filter combinations are disabled with an explanation instead of returning a misleading blank chart.

### Visuals

- KPI cards for the active selection;
- time-series charts with uncertainty bands;
- age-profile lines and age-by-cancer heatmaps;
- ranked bars for cancer mix and rates;
- small multiples for country comparisons;
- slope/change charts for rising and falling cancers;
- composition charts for attributable risks;
- projection fan or scenario charts through 2050;
- data-quality badges and source details adjacent to each visual.

Every visual receives a plain-language interpretation and route buttons for deeper analysis. Tooltips include exact values, units, source, and evidence type.

## Data flow

1. Download or verify immutable raw source files and record URL, retrieval date, version, licence, size, and checksum.
2. Parse each source into a source-specific staging table without losing original columns.
3. Validate codes, units, duplicates, missing values, and coverage.
4. Map geography, cancer, sex, age, measure, and metric dimensions.
5. Write the canonical Parquet/CSV analytical tables.
6. Run reconciliation checks against published source totals.
7. Produce analysis outputs, findings, and static figures for documentation.
8. Generate partitioned, compact JSON files for the browser.
9. Run web-data schema checks and render the standalone site.

The browser never loads raw million-row mortality files. It loads small pre-aggregated partitions and an index describing available filter combinations.

## Error handling and honesty rules

- Downloads fail with a source-specific message and do not silently use invented or stale data.
- Cached raw files are allowed only when checksum and version metadata match.
- Duplicate keys, impossible ages, negative values, unknown codes, and unit mismatches fail validation.
- Suppressed or missing values remain missing.
- The site displays “not available for this combination” and suggests valid routes.
- Observed, modelled, and projected series use different line styles and visible labels.
- Uncertainty bounds are retained and shown where supplied.
- Mortality-to-incidence ratio is never labelled as survival.
- Correlation and attributable burden are not presented as proof of individual causation.

## Testing and quality assurance

- Unit tests for ICD and cancer taxonomy mappings.
- Unit tests for age aggregation and metric conversions.
- Schema and uniqueness tests for every processed table.
- Reconciliation tests against published global and country totals.
- Snapshot tests for generated web-data manifests.
- JavaScript tests for filters, translations, and invalid combinations.
- Accessibility checks for keyboard navigation, contrast, labels, and reduced motion.
- Responsive checks at mobile, tablet, and desktop widths.
- Visual inspection of every chart in English and Polish.
- A documented data-quality report listing coverage, gaps, and unresolved limitations.

## Repository layout

```text
global-cancer-trends-analysis/
├── README.md
├── pyproject.toml
├── data/
│   ├── raw/                 # downloaded locally; large files ignored
│   ├── staging/             # source-shaped intermediate tables
│   ├── processed/           # canonical analysis tables
│   └── web/                 # compact JSON partitions committed for the site
├── docs/
│   ├── sources.md
│   ├── methodology.md
│   ├── data-quality.md
│   └── plans/
├── notebooks/
│   └── global_cancer_trends.ipynb
├── src/cancer_explorer/
│   ├── download.py
│   ├── schemas.py
│   ├── mappings.py
│   ├── transform.py
│   ├── validate.py
│   ├── analyse.py
│   └── build_web_data.py
├── tests/
├── reports/figures/
└── site/
    ├── index.html
    └── assets/
        ├── css/style.css
        └── js/
            ├── app.js
            ├── charts.js
            └── i18n.js
```

## Delivery

The repository will be public on GitHub. The `site/` directory will be self-contained so it can be copied into the VPS portfolio or linked as a separate case study. The README will document local viewing, full reproduction, data-source licences, limitations, and integration steps for RM Portfolio.
