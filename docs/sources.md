# Data sources

The project keeps source identity, version, evidence type, licence, coverage, retrieval date, and file checksum with every dataset. The machine-readable registry is [`config/sources.yml`](../config/sources.yml).

## Evidence layers

- **Observed:** WHO Mortality Database, CI5 Plus, KRN, UK national registrations, ECIS registries, REDECAN registries, and SEER.
- **Modelled:** GBD 2023, WHO Global Health Estimates, GLOBOCAN 2024, and current national estimates where explicitly labelled.
- **Projected:** IARC Cancer Tomorrow, GBD forecasts, ECIS long-term estimates, and supported national projections.

Observed, modelled, and projected values remain separate series. GLOBOCAN editions are not combined into a historical trend because the underlying data and estimation methods change between releases.

## Current acquisition status

| Source | Status | Reproducible handling |
|---|---|---|
| WHO Mortality Database | Acquired | Public raw ZIP files are cached and parsed by country, year, sex, five-year age group, ICD revision, and cancer site. |
| GLOBOCAN 2024 / Cancer Tomorrow | Acquired | The public GCO API is cached for World, Poland, UK, Spain, and USA. Snapshot and projection records are stored separately. |
| GBD 2023 | Manual-access blocker | IHME result export requires acceptance of its data-use agreement. The adapter accepts a user export and retains uncertainty bounds; no values are invented when the export is absent. |
| WHO Global Health Estimates | Fallback adapter ready | Used only for modelled mortality and supported burden measures when a reproducible GBD export is unavailable. Unsupported incidence, prevalence, or survival fields remain absent. |
| CI5 Plus and national sources | Next pipeline stage | Registry and national scope will be retained explicitly so partial-population series are not labelled as national coverage. |

GLOBOCAN 2024 was released on 8 July 2026. It provides a current modelled snapshot for 186 countries or territories and 34 cancer types. Its year identifies the estimation baseline, not one observation in a continuous historical series.
