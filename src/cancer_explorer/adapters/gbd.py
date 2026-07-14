"""Adapter for user-exported IHME GBD 2023 result tables."""

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
    "deaths": "mortality",
    "death": "mortality",
    "incidence": "incidence",
    "prevalence": "prevalence",
    "dalys": "DALY",
    "daly": "DALY",
    "ylls": "YLL",
    "yll": "YLL",
    "ylds": "YLD",
    "yld": "YLD",
}


def parse_gbd_export(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert a standard GBD results CSV export to canonical long form."""

    required = {
        "location_name", "year", "sex_name", "age_name", "cause_name",
        "measure_name", "metric_name", "val", "lower", "upper",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"GBD export is missing columns: {sorted(missing)}")

    rows: list[dict[str, object]] = []
    for source in frame.to_dict("records"):
        geo_input = source.get("location_code") or source["location_name"]
        geo_code, geo_name, geo_level = geography_details(geo_input, source["location_name"])
        cancer_code = map_cancer_label(source["cause_name"])
        label_en, label_pl, icd_codes = cancer_labels(cancer_code)
        age_start, age_end, age_label, standardised = parse_age_label(source["age_name"])
        metric_name = str(source["metric_name"]).strip().casefold()
        if metric_name == "number":
            metric = "number"
            standard_population = None
        elif metric_name == "rate" and standardised:
            metric = "age_standardised_rate"
            standard_population = "GBD world standard population"
        elif metric_name == "rate" and age_label == "All ages":
            metric = "crude_rate"
            standard_population = None
        elif metric_name == "rate":
            metric = "age_specific_rate"
            standard_population = None
        elif metric_name in {"percent", "percentage"}:
            metric = "percent"
            standard_population = None
        else:
            raise ValueError(f"Unsupported GBD metric: {source['metric_name']}")
        measure_key = str(source["measure_name"]).strip().casefold()
        if measure_key not in MEASURES:
            raise ValueError(f"Unsupported GBD measure: {source['measure_name']}")
        rows.append(
            {
                "source_id": "gbd_2023",
                "source_version": "GBD 2023",
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
                "sex": sex_label(source["sex_name"]),
                "age_start": age_start,
                "age_end": age_end,
                "age_group_label": age_label,
                "measure": MEASURES[measure_key],
                "metric": metric,
                "standard_population": standard_population,
                "value": numeric(source["val"]),
                "lower_bound": numeric(source["lower"]),
                "upper_bound": numeric(source["upper"]),
                "population": None,
                "coverage_percent": None,
                "quality_flag": "gbd_modelled_estimate",
                "notes": "Modelled IHME estimate from a GBD 2023 user export; uncertainty interval retained.",
                "projection_base_year": None,
            }
        )
    return validate_frame(pd.DataFrame(rows))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = parse_gbd_export(pd.read_csv(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(args.output, index=False)


if __name__ == "__main__":
    main()
