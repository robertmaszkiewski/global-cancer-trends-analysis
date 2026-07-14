"""US SEER incidence and national mortality export adapter."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from cancer_explorer.adapters.common import cancer_labels, map_cancer_label, numeric, parse_age_label, sex_label
from cancer_explorer.schemas import validate_frame


def parse_seer_export(frame: pd.DataFrame) -> pd.DataFrame:
    required = {
        "dataset_scope", "geography_code", "geography_name", "year", "sex",
        "age_group", "cancer", "measure", "metric", "value",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"SEER export is missing columns: {sorted(missing)}")
    rows: list[dict[str, object]] = []
    for source in frame.to_dict("records"):
        measure = str(source["measure"]).strip().casefold()
        if measure not in {"incidence", "mortality", "prevalence", "survival", "lifetime_risk"}:
            raise ValueError(f"Unsupported SEER measure: {source['measure']}")
        code = map_cancer_label(source["cancer"])
        label_en, label_pl, icd_codes = cancer_labels(code)
        age_start, age_end, age_label, standardised = parse_age_label(source["age_group"])
        metric_key = str(source["metric"]).strip().casefold()
        if metric_key == "number":
            metric, standard = "number", None
        elif metric_key in {"percent", "percentage"}:
            metric, standard = "percent", None
        elif metric_key == "rate" and standardised:
            metric = "age_standardised_rate"
            standard = str(source.get("standard_population") or "US 2000 standard population")
        elif metric_key == "rate" and age_label == "All ages":
            metric, standard = "crude_rate", None
        elif metric_key == "rate":
            metric, standard = "age_specific_rate", None
        else:
            raise ValueError(f"Unsupported SEER metric: {source['metric']}")
        scope = str(source["dataset_scope"]).strip().casefold()
        geography_level = "registry_network" if scope == "registry" else "country"
        rows.append(
            {
                "source_id": "seer",
                "source_version": "SEER incidence 1975-2023 release",
                "evidence_type": "observed",
                "geography_level": geography_level,
                "geography_code": str(source["geography_code"]),
                "geography_name": str(source["geography_name"]),
                "year": int(source["year"]),
                "cancer_code": code,
                "cancer_label_en": label_en,
                "cancer_label_pl": label_pl,
                "icd_revision": "ICD-O/ICD-10",
                "icd_codes": icd_codes,
                "sex": sex_label(source["sex"]),
                "age_start": age_start,
                "age_end": age_end,
                "age_group_label": age_label,
                "measure": measure,
                "metric": metric,
                "standard_population": standard,
                "value": numeric(source["value"]),
                "lower_bound": numeric(source.get("lower_bound")),
                "upper_bound": numeric(source.get("upper_bound")),
                "population": numeric(source.get("population")),
                "coverage_percent": numeric(source.get("coverage_percent")),
                "quality_flag": "seer_registry_observed" if scope == "registry" else "us_national_observed",
                "notes": "SEER incidence registry coverage is not equivalent to national US mortality coverage.",
                "projection_base_year": None,
                "risk_basis": str(source.get("risk_basis")).casefold() if measure == "lifetime_risk" else None,
            }
        )
    return validate_frame(pd.DataFrame(rows))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = parse_seer_export(pd.read_csv(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(args.output, index=False)


if __name__ == "__main__":
    main()
