"""Generate compact deterministic partitions for the static cancer explorer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from cancer_explorer.mappings import CONFIG_DIR, load_cancer_taxonomy
from cancer_explorer.validate import build_coverage_table


MAX_PARTITION_BYTES = 350_000


def _clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(item) for item in value]
    if pd.isna(value) if not isinstance(value, (str, bytes)) else False:
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def deterministic_json(payload: Any) -> str:
    return json.dumps(
        _clean(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _write_json(path: Path, payload: Any, enforce_budget: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = deterministic_json(payload).encode("utf-8")
    if enforce_budget and len(encoded) > MAX_PARTITION_BYTES:
        raise ValueError(
            f"web partition {path.as_posix()} is {len(encoded):,} bytes; budget is {MAX_PARTITION_BYTES:,}"
        )
    path.write_bytes(encoded)


def _dimension_labels(frame: pd.DataFrame) -> dict[str, Any]:
    taxonomy = load_cancer_taxonomy().fillna("")
    cancers = {
        row.cancer_code: {"en": row.label_en, "pl": row.label_pl, "icd10": row.icd10_codes}
        for row in taxonomy.itertuples(index=False)
        if row.cancer_code in set(frame["cancer_code"])
    }
    geographies_frame = pd.read_csv(CONFIG_DIR / "geographies.csv", dtype=str)
    geographies = {
        row.geography_code: {"en": row.geography_name_en, "pl": row.geography_name_pl}
        for row in geographies_frame.itertuples(index=False)
        if row.geography_code in set(frame["geography_code"])
    }
    # Preserve registry/nation labels if national adapters are added later.
    for row in frame[["geography_code", "geography_name"]].drop_duplicates().itertuples(index=False):
        geographies.setdefault(row.geography_code, {"en": row.geography_name, "pl": row.geography_name})
    measures = {
        "incidence": {"en": "Incidence", "pl": "Zachorowalność"},
        "mortality": {"en": "Mortality", "pl": "Umieralność"},
        "prevalence": {"en": "Prevalence", "pl": "Chorobowość"},
        "DALY": {"en": "DALYs", "pl": "DALY"},
        "YLL": {"en": "Years of life lost", "pl": "Utracone lata życia"},
        "YLD": {"en": "Years lived with disability", "pl": "Lata życia z niepełnosprawnością"},
        "survival": {"en": "Survival", "pl": "Przeżywalność"},
        "lifetime_risk": {"en": "Cumulative risk to age 74", "pl": "Ryzyko skumulowane do 74 lat"},
    }
    metrics = {
        "number": {"en": "Number", "pl": "Liczba"},
        "crude_rate": {"en": "Crude rate per 100,000", "pl": "Współczynnik surowy na 100 000"},
        "age_specific_rate": {"en": "Age-specific rate per 100,000", "pl": "Współczynnik dla wieku na 100 000"},
        "age_standardised_rate": {"en": "Age-standardised rate per 100,000", "pl": "Współczynnik standaryzowany na 100 000"},
        "percent": {"en": "Percent", "pl": "Procent"},
        "probability": {"en": "Probability", "pl": "Prawdopodobieństwo"},
    }
    sexes = {
        "both": {"en": "Both sexes", "pl": "Obie płcie"},
        "male": {"en": "Male", "pl": "Mężczyźni"},
        "female": {"en": "Female", "pl": "Kobiety"},
    }
    evidence = {
        "observed": {"en": "Observed", "pl": "Obserwowane"},
        "modelled": {"en": "Modelled", "pl": "Modelowane"},
        "projected": {"en": "Projected", "pl": "Prognozowane"},
    }
    ages = {}
    polish_age = {"All ages": "Wszystkie grupy wieku", "Age-standardised": "Standaryzowane wg wieku"}
    for label in sorted(frame["age_group_label"].dropna().astype(str).unique()):
        ages[label] = {"en": label, "pl": polish_age.get(label, label.replace("+", "+"))}
    return {
        "cancers": cancers,
        "geographies": geographies,
        "measures": {key: value for key, value in measures.items() if key in set(frame["measure"])},
        "metrics": {key: value for key, value in metrics.items() if key in set(frame["metric"])},
        "sexes": {key: value for key, value in sexes.items() if key in set(frame["sex"])},
        "evidence": {key: value for key, value in evidence.items() if key in set(frame["evidence_type"])},
        "ages": ages,
    }


def _provenance(group: pd.DataFrame) -> dict[str, Any]:
    return {
        "source_id": str(group["source_id"].iloc[0]),
        "source_version": str(group["source_version"].iloc[0]),
        "evidence_type": str(group["evidence_type"].iloc[0]),
        "quality_flags": sorted(group["quality_flag"].dropna().astype(str).unique()),
    }


def _rows(frame: pd.DataFrame, columns: list[str]) -> list[list[Any]]:
    ordered = frame.sort_values(
        [column for column in ["year", "cancer_code", "sex", "age_start", "age_end", "metric"] if column in frame]
    )
    return [[_clean(value) for value in row] for row in ordered[columns].itertuples(index=False, name=None)]


def _starter(frame: pd.DataFrame) -> dict[str, Any]:
    current = frame[
        frame["source_id"].eq("iarc_globocan_2024")
        & frame["year"].eq(2024)
        & frame["sex"].eq("both")
        & frame["age_group_label"].eq("All ages")
        & frame["metric"].eq("number")
    ][
        ["geography_code", "cancer_code", "measure", "value", "source_id", "source_version", "evidence_type"]
    ].copy()
    current = current.sort_values(["geography_code", "measure", "value"], ascending=[True, True, False])
    current = current.groupby(["geography_code", "measure"], as_index=False, group_keys=False).head(8)
    coverage = build_coverage_table(frame).to_dict("records")
    return {
        "summary": {
            "records": int(len(frame)),
            "first_year": int(frame["year"].min()),
            "last_year": int(frame["year"].max()),
            "geographies": int(frame["geography_code"].nunique()),
            "cancers": int(frame["cancer_code"].nunique()),
        },
        "current": current.to_dict("records"),
        "coverage": coverage,
    }


def build_web_data(frame: pd.DataFrame, output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    routes: list[dict[str, Any]] = []

    current = frame[frame["source_id"].eq("iarc_globocan_2024")]
    current_columns = [
        "year", "cancer_code", "sex", "age_start", "age_end", "age_group_label",
        "metric", "value", "population", "risk_basis", "standard_population",
    ]
    for (geography, measure), group in current.groupby(["geography_code", "measure"]):
        relative = f"partitions/current/{geography}/{measure}.json"
        payload = {
            "family": "current",
            "geography": geography,
            "measure": measure,
            "schema": current_columns,
            "rows": _rows(group, current_columns),
            "provenance": _provenance(group),
        }
        _write_json(output / relative, payload, enforce_budget=True)
        routes.append({"family": "current", "geography": geography, "measure": measure, "file": relative, "rows": len(group)})

    history = frame[frame["source_id"].eq("who_mortality")]
    history_columns = [
        "year", "sex", "age_start", "age_end", "age_group_label", "metric", "value",
        "population", "icd_revision", "icd_codes",
    ]
    for (geography, cancer, metric), group in history.groupby(
        ["geography_code", "cancer_code", "metric"]
    ):
        relative = f"partitions/history/{geography}/{cancer}/{metric}.json"
        payload = {
            "family": "history",
            "geography": geography,
            "cancer": cancer,
            "measure": "mortality",
            "schema": history_columns,
            "rows": _rows(group, history_columns),
            "provenance": _provenance(group),
        }
        _write_json(output / relative, payload, enforce_budget=True)
        routes.append(
            {
                "family": "history",
                "geography": geography,
                "cancer": cancer,
                "measure": "mortality",
                "metric": metric,
                "file": relative,
                "rows": len(group),
            }
        )

    projection = frame[frame["source_id"].eq("iarc_cancer_tomorrow")]
    projection_columns = ["year", "cancer_code", "sex", "value", "population", "projection_base_year"]
    for (geography, measure), group in projection.groupby(["geography_code", "measure"]):
        relative = f"partitions/projection/{geography}/{measure}.json"
        payload = {
            "family": "projection",
            "geography": geography,
            "measure": measure,
            "schema": projection_columns,
            "rows": _rows(group, projection_columns),
            "provenance": _provenance(group),
        }
        _write_json(output / relative, payload, enforce_budget=True)
        routes.append({"family": "projection", "geography": geography, "measure": measure, "file": relative, "rows": len(group)})

    manifest = {
        "version": 1,
        "generated_on": "2026-07-14",
        "partition_budget_bytes": MAX_PARTITION_BYTES,
        "partition_schema": {
            "rows": "Array rows follow the ordered schema field list stored in each partition.",
            "provenance": "Every partition names source_id, source_version, evidence_type, and quality flags.",
        },
        "dimensions": _dimension_labels(frame),
    }
    route_index = {"version": 1, "routes": sorted(routes, key=lambda item: item["file"])}
    _write_json(output / "manifest.json", manifest)
    _write_json(output / "routes.json", route_index)
    _write_json(output / "starter.json", _starter(frame))
    return {"manifest": manifest, "routes": route_index}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/processed/cancer_observations.parquet"))
    parser.add_argument("--output", type=Path, default=Path("data/web"))
    args = parser.parse_args()
    result = build_web_data(pd.read_parquet(args.input), args.output)
    print(f"Web routes: {len(result['routes']['routes']):,}")
    print(f"Maximum partition budget: {MAX_PARTITION_BYTES:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
