"""UK and constituent-nation cancer statistics adapter."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from cancer_explorer.adapters.common import cancer_labels, map_cancer_label, numeric, parse_age_label, sex_label
from cancer_explorer.schemas import validate_frame


MEASURES = {"incidence": "incidence", "mortality": "mortality", "prevalence": "prevalence", "survival": "survival"}


def parse_uk_export(frame: pd.DataFrame) -> pd.DataFrame:
    required = {
        "geography_scope", "geography_code", "geography_name", "year", "sex",
        "age_group", "cancer", "measure", "metric", "value", "evidence_type",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"UK export is missing columns: {sorted(missing)}")
    rows: list[dict[str, object]] = []
    for source in frame.to_dict("records"):
        code = map_cancer_label(source["cancer"])
        label_en, label_pl, icd_codes = cancer_labels(code)
        age_start, age_end, age_label, standardised = parse_age_label(source["age_group"])
        measure_key = str(source["measure"]).strip().casefold()
        if measure_key not in MEASURES:
            raise ValueError(f"Unsupported UK measure: {source['measure']}")
        metric_key = str(source["metric"]).strip().casefold()
        if metric_key == "number":
            metric, standard = "number", None
        elif metric_key in {"percent", "percentage"}:
            metric, standard = "percent", None
        elif metric_key == "rate" and standardised:
            metric = "age_standardised_rate"
            standard = str(source.get("standard_population") or "ESP2013")
        elif metric_key == "rate" and age_label == "All ages":
            metric, standard = "crude_rate", None
        elif metric_key == "rate":
            metric, standard = "age_specific_rate", None
        else:
            raise ValueError(f"Unsupported UK metric: {source['metric']}")
        rows.append(
            {
                "source_id": "uk_cancer",
                "source_version": "latest releases through incidence 2022 and mortality 2024",
                "evidence_type": str(source["evidence_type"]).strip().casefold(),
                "geography_level": str(source["geography_scope"]).strip().casefold(),
                "geography_code": str(source["geography_code"]),
                "geography_name": str(source["geography_name"]),
                "year": int(source["year"]),
                "cancer_code": code,
                "cancer_label_en": label_en,
                "cancer_label_pl": label_pl,
                "icd_revision": "ICD-10",
                "icd_codes": icd_codes,
                "sex": sex_label(source["sex"]),
                "age_start": age_start,
                "age_end": age_end,
                "age_group_label": age_label,
                "measure": MEASURES[measure_key],
                "metric": metric,
                "standard_population": standard,
                "value": numeric(source["value"]),
                "lower_bound": numeric(source.get("lower_bound")),
                "upper_bound": numeric(source.get("upper_bound")),
                "population": numeric(source.get("population")),
                "coverage_percent": numeric(source.get("coverage_percent")),
                "quality_flag": "uk_official_release",
                "notes": "UK and constituent-nation scopes are intentionally separate; release year varies by measure.",
                "projection_base_year": numeric(source.get("projection_base_year")),
            }
        )
    return validate_frame(pd.DataFrame(rows))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = parse_uk_export(pd.read_csv(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(args.output, index=False)


if __name__ == "__main__":
    main()
