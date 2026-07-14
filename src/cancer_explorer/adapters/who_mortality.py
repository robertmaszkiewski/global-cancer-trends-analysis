"""WHO Mortality Database adapter with list- and age-format awareness."""

from __future__ import annotations

import argparse
import zipfile
from functools import lru_cache
from pathlib import Path

import pandas as pd

from cancer_explorer.mappings import (
    CONFIG_DIR,
    UnknownMappingError,
    load_cancer_taxonomy,
    map_icd_code,
    normalize_geography,
    normalize_sex,
)


# Column placement follows WHO Mortality Database Annex 1. Combined age bands are
# stored in the first standard slot they cover; unused slots remain blank.
AGE_LAYOUTS: dict[str, dict[str, tuple[int, int, str]]] = {
    "00": {
        **{f"Deaths{index + 2}": (age, age, str(age)) for index, age in enumerate(range(5))},
        **{
            f"Deaths{index + 7}": (age, age + 4, f"{age}-{age + 4}")
            for index, age in enumerate(range(5, 100, 5))
        },
    },
    "01": {
        **{f"Deaths{index + 2}": (age, age, str(age)) for index, age in enumerate(range(5))},
        **{
            f"Deaths{index + 7}": (age, 125 if age == 85 else age + 4, "85+" if age == 85 else f"{age}-{age + 4}")
            for index, age in enumerate(range(5, 90, 5))
        },
    },
    "02": {
        "Deaths2": (0, 0, "0"),
        "Deaths3": (1, 4, "1-4"),
        **{
            f"Deaths{index + 7}": (age, 125 if age == 85 else age + 4, "85+" if age == 85 else f"{age}-{age + 4}")
            for index, age in enumerate(range(5, 90, 5))
        },
    },
    "03": {
        **{f"Deaths{index + 2}": (age, age, str(age)) for index, age in enumerate(range(5))},
        **{
            f"Deaths{index + 7}": (age, 125 if age == 75 else age + 4, "75+" if age == 75 else f"{age}-{age + 4}")
            for index, age in enumerate(range(5, 80, 5))
        },
    },
    "04": {
        "Deaths2": (0, 0, "0"),
        "Deaths3": (1, 4, "1-4"),
        **{
            f"Deaths{index + 7}": (age, 125 if age == 75 else age + 4, "75+" if age == 75 else f"{age}-{age + 4}")
            for index, age in enumerate(range(5, 80, 5))
        },
    },
    "05": {
        "Deaths2": (0, 0, "0"), "Deaths3": (1, 4, "1-4"),
        **{f"Deaths{index + 7}": (age, 125 if age == 70 else age + 4, "70+" if age == 70 else f"{age}-{age + 4}") for index, age in enumerate(range(5, 75, 5))},
    },
    "06": {
        "Deaths2": (0, 0, "0"), "Deaths3": (1, 4, "1-4"),
        **{f"Deaths{index + 7}": (age, 125 if age == 65 else age + 4, "65+" if age == 65 else f"{age}-{age + 4}") for index, age in enumerate(range(5, 70, 5))},
    },
    "07": {
        "Deaths2": (0, 0, "0"), "Deaths3": (1, 4, "1-4"),
        "Deaths7": (5, 14, "5-14"), "Deaths9": (15, 24, "15-24"),
        "Deaths11": (25, 34, "25-34"), "Deaths13": (35, 44, "35-44"),
        "Deaths15": (45, 54, "45-54"), "Deaths17": (55, 64, "55-64"),
        "Deaths19": (65, 74, "65-74"), "Deaths21": (75, 125, "75+"),
    },
    "08": {
        "Deaths2": (0, 0, "0"), "Deaths3": (1, 4, "1-4"),
        "Deaths7": (5, 14, "5-14"), "Deaths9": (15, 24, "15-24"),
        "Deaths11": (25, 34, "25-34"), "Deaths13": (35, 44, "35-44"),
        "Deaths15": (45, 54, "45-54"), "Deaths17": (55, 64, "55-64"),
        "Deaths19": (65, 125, "65+"),
    },
}


@lru_cache(maxsize=1)
def _list_mappings() -> dict[tuple[str, str], str]:
    frame = pd.read_csv(CONFIG_DIR / "who_list_mappings.csv", dtype=str)
    return {
        (row.list_code.upper(), row.cause_code.upper()): row.cancer_code
        for row in frame.itertuples(index=False)
    }


@lru_cache(maxsize=1)
def _taxonomy_labels() -> dict[str, tuple[str, str]]:
    taxonomy = load_cancer_taxonomy()
    return {
        row.cancer_code: (row.label_en, row.label_pl)
        for row in taxonomy.itertuples(index=False)
    }


def decode_who_cause(list_code: str, cause: str) -> str:
    list_code = str(list_code).strip().upper()
    cause = str(cause).strip().upper()
    mapped = _list_mappings().get((list_code, cause))
    if mapped:
        return mapped
    if list_code in {"104", "10M"} and cause.startswith("C"):
        return map_icd_code("ICD-10", cause[:3])
    raise UnknownMappingError(f"Unmapped WHO list/cause: {list_code}/{cause}")


def _national_rows(frame: pd.DataFrame) -> pd.DataFrame:
    admin = frame["Admin1"].fillna("").astype(str).str.strip()
    subdiv = frame["SubDiv"].fillna("").astype(str).str.strip()
    return frame[(admin == "") & (subdiv == "")].copy()


def parse_who_frame(
    frame: pd.DataFrame, country_lookup: dict[int, tuple[str, str]]
) -> pd.DataFrame:
    """Parse selected WHO mortality rows into source-preserving age records."""

    source = _national_rows(frame)
    source["Country"] = pd.to_numeric(source["Country"], errors="coerce").astype("Int64")
    source = source[source["Country"].isin(country_lookup)].copy()
    decoded: list[str | None] = []
    for list_code, cause in zip(source["List"], source["Cause"], strict=True):
        try:
            decoded.append(decode_who_cause(str(list_code), str(cause)))
        except UnknownMappingError:
            decoded.append(None)
    source["cancer_code"] = decoded
    source = source[source["cancer_code"].notna()].copy()

    records: list[dict[str, object]] = []
    labels = _taxonomy_labels()
    for row in source.itertuples(index=False):
        row_data = row._asdict()
        age_layout = AGE_LAYOUTS.get(str(row_data["Frmat"]).zfill(2))
        if not age_layout:
            continue
        country_code, country_name = country_lookup[int(row_data["Country"])]
        source_total = float(row_data["Deaths1"] or 0)
        unallocated = float(row_data.get("Deaths26") or 0)
        cancer_code = str(row_data["cancer_code"])
        label_en, label_pl = labels[cancer_code]
        for column, (age_start, age_end, age_label) in age_layout.items():
            raw_value = row_data.get(column)
            if pd.isna(raw_value):
                continue
            value = float(raw_value)
            records.append(
                {
                    "source_id": "who_mortality",
                    "source_version": "2026-02-23",
                    "evidence_type": "observed",
                    "geography_level": "country",
                    "geography_code": country_code,
                    "geography_name": country_name,
                    "year": int(row_data["Year"]),
                    "cancer_code": cancer_code,
                    "cancer_label_en": label_en,
                    "cancer_label_pl": label_pl,
                    "icd_revision": _revision_for_list(str(row_data["List"])),
                    "icd_codes": str(row_data["Cause"]),
                    "source_list": str(row_data["List"]),
                    "sex": normalize_sex(str(row_data["Sex"])),
                    "age_start": age_start,
                    "age_end": age_end,
                    "age_group_label": age_label,
                    "measure": "mortality",
                    "metric": "number",
                    "value": value,
                    "source_total": source_total,
                    "unallocated_deaths": unallocated,
                    "coverage_percent": None,
                    "quality_flag": "reported_unadjusted",
                    "notes": "WHO country-reported deaths; no completeness adjustment",
                }
            )
    result = pd.DataFrame.from_records(records)
    if result.empty:
        return result
    duplicate_key = [
        "source_id", "geography_code", "year", "source_list", "icd_codes",
        "sex", "age_start", "age_end",
    ]
    if result.duplicated(duplicate_key).any():
        raise ValueError("duplicate WHO mortality keys")
    return result


def _revision_for_list(list_code: str) -> str:
    list_code = list_code.upper()
    if list_code.startswith("07"):
        return "ICD-7"
    if list_code.startswith("08"):
        return "ICD-8"
    if list_code.startswith("09"):
        return "ICD-9"
    return "ICD-10"


def filter_complete_country_years(
    frame: pd.DataFrame, quality: pd.DataFrame, minimum: float = 65
) -> pd.DataFrame:
    merged = frame.merge(quality, on=["geography_code", "year"], how="left", suffixes=("", "_quality"))
    coverage_column = "coverage_percent_quality" if "coverage_percent_quality" in merged else "coverage_percent"
    result = merged[merged[coverage_column].ge(minimum)].copy()
    if coverage_column != "coverage_percent":
        result["coverage_percent"] = result[coverage_column]
        result = result.drop(columns=[coverage_column])
    return result


def _read_country_lookup(raw_dir: Path, requested: set[str]) -> dict[int, tuple[str, str]]:
    country_zip = raw_dir / "mort_country_codes.zip"
    countries = pd.read_csv(country_zip, compression="zip")
    lookup: dict[int, tuple[str, str]] = {}
    for row in countries.itertuples(index=False):
        try:
            code = normalize_geography(row.name)
        except UnknownMappingError:
            continue
        if code in requested:
            lookup[int(row.country)] = (code, str(row.name))
    return lookup


def build_who_mortality(raw_dir: Path, output: Path, countries: set[str]) -> pd.DataFrame:
    lookup = _read_country_lookup(raw_dir, countries)
    parsed_parts: list[pd.DataFrame] = []
    dtype = {"Admin1": str, "SubDiv": str, "List": str, "Cause": str, "Frmat": str}
    for archive in sorted(raw_dir.glob("morticd*.zip")):
        if archive.name == "morticd10_add.zip":
            continue
        with zipfile.ZipFile(archive) as zipped:
            member = zipped.namelist()[0]
            with zipped.open(member) as handle:
                for chunk in pd.read_csv(handle, dtype=dtype, chunksize=100_000, low_memory=False):
                    selected = chunk[pd.to_numeric(chunk["Country"], errors="coerce").isin(lookup)]
                    if selected.empty:
                        continue
                    parsed = parse_who_frame(selected, lookup)
                    if not parsed.empty:
                        parsed_parts.append(parsed)
    result = pd.concat(parsed_parts, ignore_index=True) if parsed_parts else pd.DataFrame()
    output.mkdir(parents=True, exist_ok=True)
    if not result.empty:
        for geography, partition in result.groupby("geography_code"):
            partition.to_parquet(output / f"{geography}.parquet", index=False)
        coverage = (
            result.groupby(["geography_code", "cancer_code"])
            .agg(first_year=("year", "min"), last_year=("year", "max"), rows=("value", "size"))
            .reset_index()
        )
        coverage.to_csv(output / "coverage.csv", index=False)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/who_mortality"))
    parser.add_argument("--countries", nargs="+", default=["POL", "GBR", "ESP", "USA"])
    parser.add_argument("--output", type=Path, default=Path("data/staging/who_mortality"))
    args = parser.parse_args()
    result = build_who_mortality(args.raw_dir, args.output, set(args.countries))
    print(f"Parsed {len(result):,} WHO mortality age records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
