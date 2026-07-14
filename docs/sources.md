# Data sources

The project keeps source identity, version, evidence type, licence, coverage, retrieval date, and file checksum with every dataset. The machine-readable registry is [`config/sources.yml`](../config/sources.yml).

## Evidence layers

- **Observed:** WHO Mortality Database, CI5 Plus, KRN, UK national registrations, ECIS registries, REDECAN registries, and SEER.
- **Modelled:** GBD 2023, WHO Global Health Estimates, GLOBOCAN 2022, and current national estimates where explicitly labelled.
- **Projected:** IARC Cancer Tomorrow, GBD forecasts, ECIS long-term estimates, and supported national projections.

Observed, modelled, and projected values remain separate series. GLOBOCAN editions are not combined into a historical trend because the underlying data and estimation methods change between releases.
