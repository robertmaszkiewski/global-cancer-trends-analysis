"""Shared, source-preserving normalisation helpers for burden adapters."""

from __future__ import annotations

import re
from functools import lru_cache

import pandas as pd

from cancer_explorer.mappings import load_cancer_taxonomy, normalize_geography, normalize_sex


@lru_cache(maxsize=1)
def taxonomy_records() -> dict[str, dict[str, object]]:
    frame = load_cancer_taxonomy().fillna("")
    return {row.cancer_code: row._asdict() for row in frame.itertuples(index=False)}


@lru_cache(maxsize=1)
def cancer_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}
    for code, row in taxonomy_records().items():
        aliases[str(row["label_en"]).casefold()] = code
    aliases.update(
        {
            "tracheal bronchus and lung cancer": "LUNG",
            "trachea bronchus lung cancers": "LUNG",
            "lung": "LUNG",
            "lung cancer": "LUNG",
            "breast": "BREAST",
            "breast cancer": "BREAST",
            "colon and rectum cancer": "COLORECTUM",
            "colon and rectal cancer": "COLORECTUM",
            "colorectal cancer": "COLORECTUM",
            "liver cancer": "LIVER",
            "non-hodgkin lymphoma": "NHL",
            "leukemia": "LEUKAEMIA",
            "all cancers excl. non-melanoma skin cancer": "ALL_EX_NMSC",
            "all cancers excluding non-melanoma skin cancer": "ALL_EX_NMSC",
        }
    )
    return aliases


def map_cancer_label(label: object) -> str:
    cleaned = re.sub(r"\s+", " ", str(label).strip()).casefold()
    if cleaned in cancer_aliases():
        return cancer_aliases()[cleaned]
    for alias, code in cancer_aliases().items():
        if cleaned == f"{alias} cancer" or cleaned.rstrip("s") == alias.rstrip("s"):
            return code
    raise ValueError(f"Unknown cancer label: {label}")


def cancer_labels(code: str) -> tuple[str, str, str]:
    row = taxonomy_records()[code]
    return str(row["label_en"]), str(row["label_pl"]), str(row["icd10_codes"])


def parse_age_label(label: object) -> tuple[int, int, str, bool]:
    text = str(label).strip()
    folded = text.casefold().replace("–", "-")
    if folded in {"all ages", "all age", "all", "0-125"}:
        return 0, 125, "All ages", False
    if folded in {"age-standardized", "age-standardised", "age standardized", "age standardised"}:
        return 0, 125, "Age-standardised", True
    match = re.fullmatch(r"(\d+)\s*-\s*(\d+)", folded)
    if match:
        start, end = map(int, match.groups())
        return start, end, f"{start}-{end}", False
    match = re.fullmatch(r"(\d+)\+", folded)
    if match:
        start = int(match.group(1))
        return start, 125, f"{start}+", False
    raise ValueError(f"Unknown age group: {label}")


def geography_details(code_or_name: object, fallback_name: object | None = None) -> tuple[str, str, str]:
    code = normalize_geography(code_or_name)
    names = {
        "WORLD": ("World", "global"),
        "POL": ("Poland", "country"),
        "GBR": ("United Kingdom", "country"),
        "ESP": ("Spain", "country"),
        "USA": ("United States", "country"),
    }
    name, level = names[code]
    return code, name if name else str(fallback_name), level


def numeric(value: object) -> float | None:
    parsed = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return None if pd.isna(parsed) else float(parsed)


def sex_label(value: object) -> str:
    return normalize_sex(value)
