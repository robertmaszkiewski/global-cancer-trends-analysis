# Data quality report

Validated canonical records: **386,916**
Validation issue types at error severity: **0**

## Coverage by evidence source

| source_id | source_version | evidence_type | first_year | last_year | rows | geographies | cancers | sexes | age_groups | measures | metrics |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| iarc_cancer_tomorrow | GLOBOCAN 2024 | projected | 2024 | 2050 | 7350 | 5 | 38 | 3 | 1 | 2 | 1 |
| iarc_globocan_2024 | GLOBOCAN 2024 | modelled | 2024 | 2024 | 40800 | 5 | 37 | 3 | 20 | 3 | 5 |
| who_mortality | 2026-02-23 | observed | 1968 | 2024 | 338766 | 4 | 36 | 3 | 22 | 1 | 3 |

## Validation results

No validation errors were detected.

## Interpretation safeguards

- Observed, modelled, and projected records remain separate evidence layers.
- GLOBOCAN releases are independent snapshots and are not treated as a historical trend.
- WHO mortality counts use one preferred ICD list per country-year to avoid double counting.
- Registry-network coverage is not relabelled as whole-country coverage.
- Rates with different standard populations are not treated as directly interchangeable.
