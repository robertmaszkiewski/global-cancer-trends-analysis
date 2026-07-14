# Global Cancer Trends Explorer

A reproducible, high-granularity cancer epidemiology project with a standalone bilingual **English / Polish** interactive site. It combines global estimates with detailed views for Poland, the United Kingdom, Spain and the United States, while keeping observed, modelled and projected evidence visibly separate.

> **386,916 canonical observations · 42 cancer categories · 5 geographies · 1968–2050 · 457 lazy data routes**

## What can be explored

The site provides six analytical branches:

1. **Current ranking** — most common cancers by incidence or mortality, count or rate.
2. **Age profile** — five-year age-specific rates for any compatible cancer, geography, sex and measure.
3. **Historical trend** — observed WHO mortality records with ICD revision metadata.
4. **Sex comparison** — female and male values without treating sex-specific cancers as missing errors.
5. **Country comparison** — like-for-like views for the world, Poland, UK, Spain and USA.
6. **Projection to 2050** — IARC demographic scenarios by cancer, sex, geography and outcome.

Every chart includes a source/version badge, evidence status, an interpretation boundary, an accessible table, a shareable URL and filtered CSV export.

## Data coverage

| Layer | Source | Geography | Period | Detail | Records |
|---|---|---|---:|---|---:|
| Observed mortality | WHO Mortality Database | POL, GBR, ESP, USA | 1968–2024* | cancer × 5-year age × sex × year | 338,766 |
| Current burden | IARC GLOBOCAN 2024 | World + 4 countries | 2024 | incidence, mortality, risk × cancer × age × sex | 40,800 |
| Projection | IARC Cancer Tomorrow | World + 4 countries | 2024–2050 | incidence/mortality × cancer × sex | 7,350 |

\* Latest year differs by reporting country. The interface shows only source-available years.

The source registry also documents adapters for GBD 2023, WHO Global Health Estimates, KRN, UK cancer releases, ECIS/REDECAN and SEER. Data that require a manual licence/export are **not** presented as acquired observations.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest -q
cd site
npm test
cd ..
python -m http.server 8765
```

Open `http://127.0.0.1:8765/site/`. The server must start at the repository root because the development page reads `data/web` lazily.

## Reproduce the analysis

```powershell
python scripts/download_sources.py
python scripts/build_dataset.py
python -m cancer_explorer.analyse
python -m cancer_explorer.build_web_data
python scripts/execute_notebook.py
```

Raw downloads are intentionally ignored by Git. The canonical Parquet dataset, validation outputs, analytical tables, web partitions and executed notebook are versioned for reproducibility.

## Build the standalone VPS folder

```powershell
python scripts/package_site.py
```

This creates `dist/cancer-explorer/`: one static folder containing the page, assets and all 457 data routes. It has no runtime backend, database, cookies or tracking. See [`docs/portfolio-integration.md`](docs/portfolio-integration.md) for the exact portfolio card and VPS steps.

## Evidence rules

- **Observed** — country-reported deaths in the WHO Mortality Database.
- **Modelled** — IARC estimates built for internally consistent 2024 comparison.
- **Projected** — future counts under population change with baseline rates held constant.
- Counts describe service volume; crude and age-standardised rates answer different comparison questions.
- GLOBOCAN editions are independent snapshots and are not joined into a false time series.
- Mortality-to-incidence ratios are not used as survival estimates or health-system rankings.
- Missing data remain missing; the pipeline does not manufacture national coverage.

Read [`docs/methodology.md`](docs/methodology.md), [`docs/data-quality.md`](docs/data-quality.md), [`docs/limitations.md`](docs/limitations.md) and [`docs/sources.md`](docs/sources.md) before interpreting results.

## Repository map

```text
analysis/          bilingual findings and reproducible summary tables
config/            source registry, geography, age, ICD and cancer mappings
data/processed/    canonical Parquet dataset and validation outputs
data/web/          compact manifest, route index and 457 lazy partitions
docs/              methodology, quality, sources, limitations and VPS handoff
notebooks/         executed end-to-end analytical notebook
reports/figures/   publication-ready analytical figures
site/              bilingual static case-study page and JavaScript tests
src/               acquisition, adapters, transformation, validation and analysis
tests/             Python unit, contract, reconciliation and packaging tests
```

## Polish summary / Podsumowanie po polsku

Projekt zawiera kompletny, odtwarzalny proces: pobranie danych, czyszczenie, mapowanie ICD, walidację, analizę, podział na lekkie pliki dla przeglądarki oraz osobną dwujęzyczną podstronę w stylu `rmportfolio.co.uk`. Można analizować rodzaj raka, wiek, płeć, kraj, rok, zachorowalność, umieralność, liczbę, współczynnik oraz prognozę do 2050 r. Dane obserwowane WHO, modelowane IARC i prognozowane IARC są wyraźnie oznaczone i nigdy nie są po cichu łączone.

Do wdrożenia na VPS użyj `python scripts/package_site.py`, a następnie przekaż katalog `dist/cancer-explorer/` zgodnie z instrukcją w [`docs/portfolio-integration.md`](docs/portfolio-integration.md).

## Primary sources

- [WHO Mortality Database](https://www.who.int/data/data-collection-tools/who-mortality-database)
- [IARC Global Cancer Observatory](https://gco.iarc.who.int/)
- [IARC Cancer Tomorrow](https://gco.iarc.who.int/tomorrow/)

This is descriptive public-health analysis, not medical advice, individual risk prediction or a causal model.
