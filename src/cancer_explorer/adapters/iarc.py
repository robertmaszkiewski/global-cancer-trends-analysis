"""IARC GLOBOCAN 2024 snapshot and Cancer Tomorrow projection adapter."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from cancer_explorer.adapters.common import (
    cancer_labels,
    geography_details,
    map_cancer_label,
    numeric,
    sex_label,
)
from cancer_explorer.schemas import validate_frame


API_ROOT = "https://gco.iarc.who.int/gateway_prod/api/globocan/v3/2024"
POPULATION_CODES = {"WORLD": 900, "POL": 616, "GBR": 826, "ESP": 724, "USA": 840}
AGE_GROUPS = {
    index: (start, 125 if start == 85 else start + 4, "85+" if start == 85 else f"{start}-{start + 4}")
    for index, start in enumerate(range(0, 90, 5))
}
TYPE_TO_MEASURE = {0: "incidence", 1: "mortality", 2: "prevalence"}


def reject_cross_release_trend(frame: pd.DataFrame) -> None:
    """Reject the common error of treating independent GLOBOCAN releases as years."""

    versions = set(frame["source_version"].dropna().astype(str))
    if len(versions) > 1:
        raise ValueError(
            "GLOBOCAN releases are independent snapshots and cannot be combined as a time trend"
        )


def _base_record(source: dict[str, Any], cancer_code: str, projection: bool) -> dict[str, Any]:
    release_year = int(source["release_year"])
    numeric_country = int(source["country_code"])
    geo_alias = next((code for code, value in POPULATION_CODES.items() if value == numeric_country), numeric_country)
    geo_code, geo_name, geo_level = geography_details(geo_alias, source.get("country_name"))
    label_en, label_pl, icd_codes = cancer_labels(cancer_code)
    return {
        "source_id": "iarc_cancer_tomorrow" if projection else "iarc_globocan_2024",
        "source_version": f"GLOBOCAN {release_year}",
        "evidence_type": "projected" if projection else "modelled",
        "geography_level": geo_level,
        "geography_code": geo_code,
        "geography_name": geo_name,
        "cancer_code": cancer_code,
        "cancer_label_en": label_en,
        "cancer_label_pl": label_pl,
        "icd_revision": "ICD-10",
        "icd_codes": icd_codes,
        "sex": sex_label(source["sex"]),
        "measure": TYPE_TO_MEASURE[int(source["type"])],
        "lower_bound": None,
        "upper_bound": None,
        "coverage_percent": None,
    }


def parse_iarc_export(frame: pd.DataFrame) -> pd.DataFrame:
    """Parse flattened Cancer Today/Tomorrow API rows into canonical metrics."""

    rows: list[dict[str, Any]] = []
    for source in frame.to_dict("records"):
        projection = str(source["record_kind"]).strip().casefold() == "projection"
        cancer_code = map_cancer_label(source["cancer_label"])
        base = _base_record(source, cancer_code, projection)
        if projection:
            rows.append(
                {
                    **base,
                    "year": int(source["year"]),
                    "age_start": 0,
                    "age_end": 125,
                    "age_group_label": "All ages",
                    "metric": "number",
                    "standard_population": None,
                    "value": numeric(source["cases_pred"]),
                    "population": numeric(source.get("pop")),
                    "quality_flag": "demographic_projection_constant_rates",
                    "notes": f"Demographic projection from the {int(source['release_year'])} GLOBOCAN baseline; not an observed future count.",
                    "projection_base_year": int(source["release_year"]),
                }
            )
            continue

        age_index = numeric(source.get("age_index"))
        if age_index is None:
            age_start, age_end, age_label = 0, 125, "All ages"
            metrics = [
                ("number", None, numeric(source.get("total"))),
                ("crude_rate", None, numeric(source.get("crude_rate"))),
                ("age_standardised_rate", "World standard population", numeric(source.get("asr"))),
            ]
        else:
            age_start, age_end, age_label = AGE_GROUPS[int(age_index)]
            metrics = [
                ("number", None, numeric(source.get("total"))),
                ("age_specific_rate", None, numeric(source.get("crude_rate"))),
            ]
        for metric, standard_population, value in metrics:
            if value is None:
                continue
            rows.append(
                {
                    **base,
                    "year": int(source["release_year"]),
                    "age_start": age_start,
                    "age_end": age_end,
                    "age_group_label": age_label,
                    "metric": metric,
                    "standard_population": standard_population,
                    "value": value,
                    "population": numeric(source.get("total_pop")),
                    "quality_flag": "iarc_modelled_snapshot",
                    "notes": "Independent GLOBOCAN modelled snapshot; do not interpret releases as an observed time trend.",
                    "projection_base_year": None,
                }
            )
        risk = numeric(source.get("cum_risk_74"))
        if age_index is None and risk is not None:
            rows.append(
                {
                    **base,
                    "year": int(source["release_year"]),
                    "age_start": 0,
                    "age_end": 74,
                    "age_group_label": "0-74",
                    "measure": "lifetime_risk",
                    "metric": "percent",
                    "risk_basis": base["measure"],
                    "standard_population": None,
                    "value": risk,
                    "population": numeric(source.get("total_pop")),
                    "quality_flag": "iarc_modelled_snapshot",
                    "notes": f"Cumulative risk to age 74 for {base['measure']}; GLOBOCAN modelled snapshot.",
                    "projection_base_year": None,
                }
            )
    return validate_frame(pd.DataFrame(rows))


class IARCClient:
    """Small cached client limited to the five project geographies."""

    def __init__(self, cache_dir: Path, delay_seconds: float = 0.08):
        self.cache_dir = cache_dir
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "global-cancer-trends-analysis/1.0 (source-attributed research)"})

    def get_json(self, relative_url: str) -> Any:
        key = relative_url.strip("/").replace("/", "__").replace("?", "_").replace("&", "_").replace("=", "-")
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        response = self.session.get(f"{API_ROOT}/{relative_url.lstrip('/')}", timeout=60)
        response.raise_for_status()
        payload = response.json()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        time.sleep(self.delay_seconds)
        return payload

    def cancer_dictionary(self) -> dict[int, str]:
        payload = self.get_json("meta/cancers/all/")
        return {int(row["cancer"]): str(row["label"]) for row in payload}

    def snapshot_rows(self, geography_codes: list[str]) -> pd.DataFrame:
        cancers = self.cancer_dictionary()
        flattened: list[dict[str, Any]] = []
        for geography_code in geography_codes:
            population = POPULATION_CODES[geography_code]
            country_name = geography_details(geography_code)[1]
            for age_index in [None, *AGE_GROUPS.keys()]:
                age_query = "0_17" if age_index is None else f"{age_index}_{age_index}"
                payload = self.get_json(
                    f"data/rate/0_1/0_1_2/{population}/all/?ages_group={age_query}&group_CRC=1&include_nmsc=1&include_nmsc_other=1"
                )
                for row in payload.get("dataset", []):
                    flattened.append(
                        {
                            **row,
                            "record_kind": "snapshot",
                            "release_year": 2024,
                            "country_name": country_name,
                            "cancer_label": cancers[int(row["cancer_code"])],
                            "age_index": age_index,
                        }
                    )
        return pd.DataFrame(flattened)

    def projection_rows(self, geography_codes: list[str]) -> pd.DataFrame:
        cancers = self.cancer_dictionary()
        cancer_path = "_".join(str(code) for code in cancers)
        flattened: list[dict[str, Any]] = []
        for geography_code in geography_codes:
            population = POPULATION_CODES[geography_code]
            payload = self.get_json(f"data/prediction/0_1/0_1_2/{population}/{cancer_path}/")
            for row in payload.get("dataset", []):
                flattened.append(
                    {
                        **row,
                        "record_kind": "projection",
                        "release_year": 2024,
                        "country_code": row["id"],
                        "country_name": row.get("id_label", geography_details(geography_code)[1]),
                        "cancer_code": row["cancer"],
                        "cancer_label": row.get("cancer_label", cancers[int(row["cancer"])]),
                        "cases_pred": row["cases_pred"],
                    }
                )
        return pd.DataFrame(flattened)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path("data/raw/iarc_api"))
    parser.add_argument("--geographies", nargs="+", default=list(POPULATION_CODES))
    args = parser.parse_args()
    unknown = set(args.geographies) - set(POPULATION_CODES)
    if unknown:
        raise SystemExit(f"Unsupported IARC geographies: {sorted(unknown)}")
    client = IARCClient(args.cache)
    snapshot = parse_iarc_export(client.snapshot_rows(args.geographies))
    projections = parse_iarc_export(client.projection_rows(args.geographies))
    args.output.mkdir(parents=True, exist_ok=True)
    snapshot.to_parquet(args.output / "globocan_2024.parquet", index=False)
    projections.to_parquet(args.output / "cancer_tomorrow_2024_2050.parquet", index=False)
    print(f"IARC snapshot records: {len(snapshot):,}")
    print(f"IARC projection records: {len(projections):,}")


if __name__ == "__main__":
    main()
