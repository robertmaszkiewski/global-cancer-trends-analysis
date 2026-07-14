"""Polish National Cancer Registry (KRN) table adapter."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from cancer_explorer.adapters.common import cancer_labels, map_cancer_label, numeric, parse_age_label, sex_label
from cancer_explorer.schemas import validate_frame


MEASURES = {"incidence": "incidence", "mortality": "mortality", "deaths": "mortality"}


def parse_krn_export(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"year", "sex", "age_group", "cancer_label_en", "measure", "count", "asw_rate"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"KRN export is missing columns: {sorted(missing)}")
    rows: list[dict[str, object]] = []
    for source in frame.to_dict("records"):
        code = map_cancer_label(source["cancer_label_en"])
        label_en, label_pl, taxonomy_icd = cancer_labels(code)
        label_pl = str(source.get("cancer_label_pl") or label_pl)
        age_start, age_end, age_label, standardised = parse_age_label(source["age_group"])
        measure_key = str(source["measure"]).strip().casefold()
        if measure_key not in MEASURES:
            raise ValueError(f"Unsupported KRN measure: {source['measure']}")
        base = {
            "source_id": "krn",
            "source_version": "KRN 2023 report published 2026",
            "evidence_type": "observed",
            "geography_level": "country",
            "geography_code": "POL",
            "geography_name": "Poland",
            "year": int(source["year"]),
            "cancer_code": code,
            "cancer_label_en": label_en,
            "cancer_label_pl": label_pl,
            "icd_revision": "ICD-10",
            "icd_codes": str(source.get("icd10") or taxonomy_icd),
            "sex": sex_label(source["sex"]),
            "age_start": age_start,
            "age_end": age_end,
            "age_group_label": age_label,
            "measure": MEASURES[measure_key],
            "lower_bound": None,
            "upper_bound": None,
            "population": numeric(source.get("population")),
            "coverage_percent": numeric(source.get("coverage_percent")),
            "quality_flag": "national_registry_observed",
            "notes": "KRN national registry publication; rate standard and coverage follow the source table.",
            "projection_base_year": None,
        }
        count = numeric(source.get("count"))
        if count is not None:
            rows.append({**base, "metric": "number", "standard_population": None, "value": count})
        rate = numeric(source.get("asw_rate"))
        if rate is not None:
            metric = "age_standardised_rate" if standardised else "age_specific_rate"
            rows.append(
                {
                    **base,
                    "metric": metric,
                    "standard_population": "World standard population (Segi/Doll)" if standardised else None,
                    "value": rate,
                }
            )
    return validate_frame(pd.DataFrame(rows))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = parse_krn_export(pd.read_csv(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(args.output, index=False)


if __name__ == "__main__":
    main()
