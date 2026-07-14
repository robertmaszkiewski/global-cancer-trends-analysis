"""Reference-data mappings that preserve analytical meaning across sources."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


class UnknownMappingError(ValueError):
    pass


class IncompleteAggregationError(ValueError):
    pass


CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


def load_cancer_taxonomy() -> pd.DataFrame:
    frame = pd.read_csv(CONFIG_DIR / "cancer_taxonomy.csv")
    frame["includes_nmsc"] = frame["includes_nmsc"].astype(bool)
    return frame


def _numeric_icd_code(revision: str, source_code: str) -> int:
    code = str(source_code).upper().strip()
    if revision == "ICD-10":
        match = re.fullmatch(r"C(\d{2})(?:\.\d+)?", code)
    else:
        match = re.fullmatch(r"(\d{3})(?:\.\d+)?", code)
    if not match:
        raise UnknownMappingError(f"Unknown {revision} code: {source_code}")
    return int(match.group(1))


def map_icd_code(revision: str, source_code: str) -> str:
    revision = revision.upper().replace("ICD10", "ICD-10").replace("ICD9", "ICD-9")
    numeric = _numeric_icd_code(revision, source_code)
    mappings = pd.read_csv(CONFIG_DIR / "icd_mappings.csv")
    matched = mappings[
        (mappings["revision"] == revision)
        & (mappings["code_start"] <= numeric)
        & (mappings["code_end"] >= numeric)
    ]
    if matched.empty:
        raise UnknownMappingError(f"Unmapped {revision} code: {source_code}")
    return str(matched.iloc[0]["cancer_code"])


def normalize_geography(source: str) -> str:
    needle = str(source).strip().casefold()
    geographies = pd.read_csv(CONFIG_DIR / "geographies.csv", dtype=str)
    for row in geographies.to_dict("records"):
        aliases = {item.strip().casefold() for item in row["aliases"].split("|")}
        aliases.add(row["geography_code"].casefold())
        if needle in aliases:
            return row["geography_code"]
    raise UnknownMappingError(f"Unknown geography: {source}")


def normalize_sex(source: str) -> str:
    value = str(source).strip().casefold()
    aliases = {
        "both": {"0", "both", "both sexes", "persons", "all"},
        "male": {"1", "male", "males", "men", "m"},
        "female": {"2", "female", "females", "women", "f"},
    }
    for canonical, values in aliases.items():
        if value in values:
            return canonical
    raise UnknownMappingError(f"Unknown sex label: {source}")


def aggregate_age(frame: pd.DataFrame, label: str, value_col: str = "value") -> float:
    groups = pd.read_csv(CONFIG_DIR / "age_groups.csv", dtype={"label": str})
    selected = groups[groups["label"] == label]
    if selected.empty:
        raise UnknownMappingError(f"Unknown age aggregation: {label}")
    expected = {int(value) for value in selected.iloc[0]["constituent_starts"].split("|")}
    actual = set(frame["age_start"].astype(int))
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise IncompleteAggregationError(
            f"{label} requires complete five-year groups; missing={missing}, extra={extra}"
        )
    if frame[value_col].isna().any():
        raise IncompleteAggregationError(f"{label} contains missing values")
    return float(frame[value_col].sum())
