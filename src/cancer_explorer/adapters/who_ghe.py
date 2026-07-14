"""Explicit fallback adapter for WHO Global Health Estimates exports."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from cancer_explorer.adapters.common import (
    cancer_labels,
    geography_details,
    map_cancer_label,
    numeric,
    parse_age_label,
    sex_label,
)
from cancer_explorer.schemas import validate_frame


MEASURES = {
    "mortality": "mortality",
    "deaths": "mortality",
    "daly": "DALY",
    "dalys": "DALY",
    "yll": "YLL",
    "ylls": "YLL",
    "yld": "YLD",
    "ylds": "YLD",
}


def parse_who_ghe_export(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"location_name", "year", "sex", "age_group", "cause", "measure", "metric", "value"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"WHO GHE export is missing columns: {sorted(missing)}")
    rows: list[dict[str, object]] = []
    for source in frame.to_dict("records"):
        geo_input = source.get("location_code") or source["location_name"]
        geo_code, geo_name, geo_level = geography_details(geo_input, source["location_name"])
        cancer_code = map_cancer_label(source["cause"])
        label_en, label_pl, icd_codes = cancer_labels(cancer_code)
        age_start, age_end, age_label, standardised = parse_age_label(source["age_group"])
        measure_key = str(source["measure"]).strip().casefold()
        if measure_key not in MEASURES:
            raise ValueError(f"WHO GHE fallback does not support measure: {source['measure']}")
        metric_key = str(source["metric"]).strip().casefold()
        if metric_key == "number":
            metric, standard_population = "number", None
        elif metric_key == "rate" and standardised:
            metric, standard_population = "age_standardised_rate", "WHO standard population"
        elif metric_key == "rate" and age_label == "All ages":
            metric, standard_population = "crude_rate", None
        elif metric_key == "rate":
            metric, standard_population = "age_specific_rate", None
        else:
            raise ValueError(f"Unsupported WHO GHE metric: {source['metric']}")
        rows.append(
            {
                "source_id": "who_ghe",
                "source_version": "WHO GHE latest available 2026-07-14",
                "evidence_type": "modelled",
                "geography_level": geo_level,
                "geography_code": geo_code,
                "geography_name": geo_name,
                "year": int(source["year"]),
                "cancer_code": cancer_code,
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
                "standard_population": standard_population,
                "value": numeric(source["value"]),
                "lower_bound": numeric(source.get("lower")),
                "upper_bound": numeric(source.get("upper")),
                "population": numeric(source.get("population")),
                "coverage_percent": None,
                "quality_flag": "fallback_who_ghe",
                "notes": "Modelled WHO GHE fallback used when a reproducible GBD export is unavailable.",
                "projection_base_year": None,
            }
        )
    return validate_frame(pd.DataFrame(rows))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = parse_who_ghe_export(pd.read_csv(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(args.output, index=False)


if __name__ == "__main__":
    main()
