"""Reproducible cancer analysis with provenance-preserving comparisons."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd


AGGREGATE_CANCERS = {"ALL", "ALL_EX_NMSC"}


def calculate_change(frame: pd.DataFrame, start_year: int, end_year: int) -> dict[str, object]:
    start = frame.loc[frame["year"].eq(start_year)]
    end = frame.loc[frame["year"].eq(end_year)]
    if len(start) != 1 or len(end) != 1:
        raise ValueError("change requires exactly one like-for-like row at each endpoint")
    start_row, end_row = start.iloc[0], end.iloc[0]
    start_value, end_value = float(start_row["value"]), float(end_row["value"])
    absolute = end_value - start_value
    percent = (absolute / start_value * 100) if start_value else None
    years = end_year - start_year
    cagr = ((end_value / start_value) ** (1 / years) - 1) * 100 if start_value > 0 and end_value >= 0 and years > 0 else None

    bounds = []
    for row in (start_row, end_row):
        lower = row.get("lower_bound")
        upper = row.get("upper_bound")
        bounds.append(None if pd.isna(lower) or pd.isna(upper) else (float(lower), float(upper)))
    if all(bound is not None for bound in bounds):
        (start_lower, start_upper), (end_lower, end_upper) = bounds
        overlap = not (start_upper < end_lower or end_upper < start_lower)
        direction = "uncertain" if overlap else ("increase" if absolute > 0 else "decrease" if absolute < 0 else "stable")
    else:
        direction = "increase" if absolute > 0 else "decrease" if absolute < 0 else "stable"
    return {
        "start_year": int(start_year),
        "end_year": int(end_year),
        "start_value": start_value,
        "end_value": end_value,
        "absolute_change": absolute,
        "percent_change": percent,
        "cagr_percent": cagr,
        "direction": direction,
    }


def rank_cancers(frame: pd.DataFrame, minimum_value: float = 0) -> pd.DataFrame:
    source = frame[~frame["cancer_code"].isin(AGGREGATE_CANCERS)].copy()
    label_columns = [column for column in ["cancer_code", "cancer_label_en", "cancer_label_pl"] if column in source]
    ranked = source.groupby(label_columns, as_index=False, dropna=False)["value"].sum()
    ranked = ranked[ranked["value"].ge(minimum_value)].sort_values(
        ["value", "cancer_code"], ascending=[False, True]
    )
    ranked["rank"] = range(1, len(ranked) + 1)
    return ranked.reset_index(drop=True)


def age_peak(frame: pd.DataFrame) -> dict[str, object]:
    ages = frame[frame["metric"].eq("age_specific_rate")]
    if ages.empty:
        raise ValueError("age peak requires age-specific-rate rows")
    row = ages.loc[ages["value"].idxmax()]
    return {
        "age_start": int(row["age_start"]),
        "age_end": int(row["age_end"]),
        "age_group_label": str(row["age_group_label"]),
        "value": float(row["value"]),
    }


def compare_countries(frame: pd.DataFrame) -> pd.DataFrame:
    dimensions = [
        "source_id", "source_version", "evidence_type", "year", "sex", "age_start",
        "age_end", "measure", "metric", "standard_population", "cancer_code",
    ]
    mixed = [column for column in dimensions if column in frame and frame[column].nunique(dropna=False) != 1]
    if mixed:
        raise ValueError(f"country comparison is not like-for-like; mixed dimensions: {mixed}")
    result = frame.sort_values("value", ascending=False).copy()
    result["rank"] = range(1, len(result) + 1)
    return result.reset_index(drop=True)


def projection_change(frame: pd.DataFrame, target_year: int = 2050) -> dict[str, object]:
    if set(frame["evidence_type"]) != {"projected"}:
        raise ValueError("projection analysis accepts projected records only")
    base_years = frame["projection_base_year"].dropna().astype(int).unique()
    if len(base_years) != 1:
        raise ValueError("projection rows require one common base year")
    result = calculate_change(frame, int(base_years[0]), int(target_year))
    result["scenario"] = "demographic_projection"
    result["projection_base_year"] = int(base_years[0])
    return result


def _current_burden(data: pd.DataFrame) -> pd.DataFrame:
    return data[
        data["source_id"].eq("iarc_globocan_2024")
        & data["year"].eq(2024)
        & data["sex"].eq("both")
        & data["age_start"].eq(0)
        & data["age_end"].isin([74, 125])
    ].copy()


def _build_rankings(current: pd.DataFrame) -> pd.DataFrame:
    source = current[
        current["metric"].eq("number")
        & current["age_group_label"].eq("All ages")
        & current["measure"].isin(["incidence", "mortality"])
    ]
    parts = []
    for (geography_code, measure), group in source.groupby(["geography_code", "measure"]):
        ranked = rank_cancers(group, minimum_value=1)
        ranked.insert(0, "measure", measure)
        ranked.insert(0, "geography_code", geography_code)
        ranked["source_id"] = "iarc_globocan_2024"
        ranked["source_version"] = "GLOBOCAN 2024"
        ranked["year"] = 2024
        parts.append(ranked)
    return pd.concat(parts, ignore_index=True)


def _build_age_peaks(data: pd.DataFrame) -> pd.DataFrame:
    source = data[
        data["source_id"].eq("iarc_globocan_2024")
        & data["sex"].eq("both")
        & data["metric"].eq("age_specific_rate")
        & ~data["cancer_code"].isin(AGGREGATE_CANCERS)
    ]
    rows = []
    group_columns = [
        "geography_code", "geography_name", "cancer_code", "cancer_label_en",
        "cancer_label_pl", "measure",
    ]
    for keys, group in source.groupby(group_columns, dropna=False):
        peak = age_peak(group)
        rows.append(dict(zip(group_columns, keys, strict=True)) | peak)
    result = pd.DataFrame(rows)
    result["source_id"] = "iarc_globocan_2024"
    result["source_version"] = "GLOBOCAN 2024"
    result["year"] = 2024
    return result


def _build_historical_changes(data: pd.DataFrame) -> pd.DataFrame:
    source = data[
        data["source_id"].eq("who_mortality")
        & data["sex"].eq("both")
        & data["age_group_label"].eq("All ages")
        & data["metric"].eq("crude_rate")
        & data["measure"].eq("mortality")
    ]
    rows = []
    group_columns = [
        "geography_code", "geography_name", "cancer_code", "cancer_label_en", "cancer_label_pl"
    ]
    for keys, group in source.groupby(group_columns, dropna=False):
        years = sorted(group["year"].unique())
        if len(years) < 2:
            continue
        for period, start, end in [
            ("full_available", years[0], years[-1]),
            ("latest_decade", years[-1] - 10, years[-1]),
        ]:
            if start not in years:
                continue
            change = calculate_change(group, int(start), int(end))
            rows.append(
                dict(zip(group_columns, keys, strict=True))
                | {"period": period}
                | change
                | {
                    "source_id": "who_mortality",
                    "source_version": "2026-02-23",
                    "evidence_type": "observed",
                    "measure": "mortality",
                    "metric": "crude_rate",
                    "unit": "per 100,000",
                    "caution": "Crude rates reflect age structure; ICD classification breaks may affect long runs.",
                }
            )
    return pd.DataFrame(rows)


def _build_projections(data: pd.DataFrame) -> pd.DataFrame:
    source = data[
        data["source_id"].eq("iarc_cancer_tomorrow")
        & data["sex"].eq("both")
        & data["metric"].eq("number")
    ]
    rows = []
    group_columns = [
        "geography_code", "geography_name", "cancer_code", "cancer_label_en",
        "cancer_label_pl", "measure",
    ]
    for keys, group in source.groupby(group_columns, dropna=False):
        if {2024, 2050} <= set(group["year"]):
            rows.append(
                dict(zip(group_columns, keys, strict=True))
                | projection_change(group, 2050)
                | {
                    "source_id": "iarc_cancer_tomorrow",
                    "source_version": "GLOBOCAN 2024",
                    "evidence_type": "projected",
                    "metric": "number",
                    "caution": "Demographic projection, not an observed forecast; baseline rates are held constant unless explicitly adjusted.",
                }
            )
    return pd.DataFrame(rows)


def _build_sex_gap(data: pd.DataFrame) -> pd.DataFrame:
    source = data[
        data["source_id"].eq("iarc_globocan_2024")
        & data["metric"].eq("age_standardised_rate")
        & data["measure"].isin(["incidence", "mortality"])
        & data["sex"].isin(["male", "female"])
        & ~data["cancer_code"].isin(AGGREGATE_CANCERS)
    ]
    index = [
        "geography_code", "geography_name", "cancer_code", "cancer_label_en",
        "cancer_label_pl", "measure", "year", "standard_population",
    ]
    pivot = source.pivot_table(index=index, columns="sex", values="value", aggfunc="first").reset_index()
    pivot = pivot[pivot.get("male", 0).gt(0) & pivot.get("female", 0).gt(0)].copy()
    pivot["male_minus_female"] = pivot["male"] - pivot["female"]
    pivot["male_female_ratio"] = pivot["male"] / pivot["female"]
    pivot["source_id"] = "iarc_globocan_2024"
    pivot["source_version"] = "GLOBOCAN 2024"
    return pivot


def _format_count(value: float) -> str:
    return f"{value:,.0f}"


def _build_findings(
    data: pd.DataFrame, rankings: pd.DataFrame, projections: pd.DataFrame
) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    for measure, title_en, title_pl in [
        ("incidence", "Most commonly diagnosed cancer worldwide", "Najczęściej rozpoznawany nowotwór na świecie"),
        ("mortality", "Leading cause of cancer death worldwide", "Główna przyczyna zgonów nowotworowych na świecie"),
    ]:
        row = rankings.query(
            "geography_code == 'WORLD' and measure == @measure and rank == 1"
        ).iloc[0]
        findings.append(
            {
                "id": f"world_{measure}_leader",
                "category": "current_burden",
                "title_en": title_en,
                "title_pl": title_pl,
                "narrative_en": f"{row.cancer_label_en} ranks first in GLOBOCAN 2024 with an estimated {_format_count(row.value)} {'new cases' if measure == 'incidence' else 'deaths'}.",
                "narrative_pl": f"{row.cancer_label_pl} zajmuje pierwsze miejsce w GLOBOCAN 2024: szacunkowo {_format_count(row.value)} {'nowych zachorowań' if measure == 'incidence' else 'zgonów'}.",
                "value": float(row.value),
                "filters": {"geography": "WORLD", "year": 2024, "measure": measure, "metric": "number", "sex": "both"},
                "provenance": {"source_id": "iarc_globocan_2024", "source_version": "GLOBOCAN 2024", "evidence_type": "modelled"},
            }
        )
    for geography_code in ["WORLD", "POL", "GBR", "ESP", "USA"]:
        rows = projections.query(
            "geography_code == @geography_code and cancer_code == 'ALL_EX_NMSC' and measure == 'incidence'"
        )
        if rows.empty:
            continue
        row = rows.iloc[0]
        findings.append(
            {
                "id": f"projection_{geography_code.lower()}_all_cancers",
                "category": "projection",
                "title_en": f"Projected cancer burden to 2050 — {row.geography_name}",
                "title_pl": f"Prognozowane obciążenie nowotworami do 2050 — {row.geography_name}",
                "narrative_en": f"With 2024 rates held constant, demographic change raises projected new cases from {_format_count(row.start_value)} to {_format_count(row.end_value)} ({row.percent_change:+.1f}%).",
                "narrative_pl": f"Przy stałych współczynnikach z 2024 r. zmiany demograficzne zwiększają liczbę nowych zachorowań z {_format_count(row.start_value)} do {_format_count(row.end_value)} ({row.percent_change:+.1f}%).",
                "value": float(row.percent_change),
                "filters": {"geography": geography_code, "cancer": "ALL_EX_NMSC", "measure": "incidence", "years": [2024, 2050]},
                "provenance": {"source_id": "iarc_cancer_tomorrow", "source_version": "GLOBOCAN 2024", "evidence_type": "projected"},
            }
        )
    coverage = (
        data[data["source_id"].eq("who_mortality")]
        .groupby("geography_code")["year"]
        .agg(["min", "max"])
        .reset_index()
        .to_dict("records")
    )
    return {
        "generated_from": "data/processed/cancer_observations.parquet",
        "record_count": int(len(data)),
        "findings": findings,
        "observed_mortality_coverage": coverage,
        "cautions": {
            "en": [
                "Observed, modelled, and projected evidence are separate.",
                "GLOBOCAN editions are snapshots, not a historical series.",
                "Crude-rate changes can reflect population ageing as well as disease risk.",
            ],
            "pl": [
                "Dane obserwowane, modelowane i prognozowane są rozdzielone.",
                "Edycje GLOBOCAN są snapshotami, a nie szeregiem historycznym.",
                "Zmiany współczynników surowych mogą wynikać także ze starzenia populacji.",
            ],
        },
    }


def analyse_dataset(input_path: Path, output: Path) -> dict[str, object]:
    data = pd.read_parquet(input_path)
    output.mkdir(parents=True, exist_ok=True)
    summary = output / "summary_tables"
    summary.mkdir(parents=True, exist_ok=True)
    current = _current_burden(data)
    rankings = _build_rankings(current)
    age_peaks = _build_age_peaks(data)
    historical = _build_historical_changes(data)
    projections = _build_projections(data)
    sex_gap = _build_sex_gap(data)
    current.to_csv(summary / "current_burden.csv", index=False)
    rankings.to_csv(summary / "current_rankings.csv", index=False)
    age_peaks.to_csv(summary / "age_peaks.csv", index=False)
    historical.to_csv(summary / "historical_mortality_change.csv", index=False)
    projections.to_csv(summary / "projections_2050.csv", index=False)
    sex_gap.to_csv(summary / "sex_gap.csv", index=False)
    findings = _build_findings(data, rankings, projections)
    (output / "findings.json").write_text(
        json.dumps(findings, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Findings: {len(findings['findings'])}")
    print(f"Current ranking rows: {len(rankings):,}")
    print(f"Age-peak rows: {len(age_peaks):,}")
    print(f"Historical-change rows: {len(historical):,}")
    print(f"Projection rows: {len(projections):,}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/processed/cancer_observations.parquet"))
    parser.add_argument("--output", type=Path, default=Path("analysis"))
    args = parser.parse_args()
    analyse_dataset(args.input, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
