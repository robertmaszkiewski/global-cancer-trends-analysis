"""Canonical transformations with explicit safeguards against double counting."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from cancer_explorer.schemas import validate_frame


WHO_LIST_PRIORITY = {
    "10M": 0,
    "104": 1,
    "101": 2,
    "09A": 3,
    "09B": 4,
    "08A": 5,
    "08B": 6,
    "07A": 7,
    "07B": 8,
}


def select_preferred_who_lists(frame: pd.DataFrame) -> pd.DataFrame:
    """Choose one cause list per country-year to avoid parallel-list duplicates."""

    source = frame.copy()
    source["_priority"] = source["source_list"].map(WHO_LIST_PRIORITY).fillna(999)
    preferred = source.groupby(["geography_code", "year"])["_priority"].transform("min")
    result = source[source["_priority"] == preferred].drop(columns="_priority")
    list_counts = result.groupby(["geography_code", "year"])["source_list"].nunique()
    if list_counts.gt(1).any():
        raise ValueError("WHO country-year still contains parallel cause lists")
    return result.reset_index(drop=True)


def coalesce_under_five(frame: pd.DataFrame, value_column: str = "value") -> pd.DataFrame:
    """Coalesce 0, 1-4 or single-year infant rows only when they cover 0-4 exactly."""

    under = frame[frame["age_end"].le(4)].sort_values(["age_start", "age_end"])
    rest = frame[frame["age_end"].gt(4)].copy()
    if under.empty:
        return frame.copy()
    cursor = 0
    for row in under[["age_start", "age_end"]].drop_duplicates().itertuples(index=False):
        if int(row.age_start) != cursor:
            raise ValueError("under-five age groups contain a gap or overlap")
        cursor = int(row.age_end) + 1
    if cursor != 5:
        raise ValueError("under-five age groups contain a gap or overlap")
    collapsed = under.iloc[[0]].copy()
    collapsed["age_start"] = 0
    collapsed["age_end"] = 4
    collapsed["age_group_label"] = "0-4"
    collapsed[value_column] = float(under[value_column].sum())
    return pd.concat([collapsed, rest], ignore_index=True)


def reconcile_who_totals(frame: pd.DataFrame, tolerance: float = 0.5) -> pd.DataFrame:
    """Compare allocated ages plus source unallocated deaths with published totals."""

    keys = [
        "geography_code", "year", "source_list", "icd_codes", "sex",
        "cancer_code", "icd_revision",
    ]
    report = (
        frame.groupby(keys, dropna=False)
        .agg(
            allocated=("value", "sum"),
            source_total=("source_total", "first"),
            unallocated=("unallocated_deaths", "first"),
        )
        .reset_index()
    )
    report["difference"] = report["allocated"] + report["unallocated"] - report["source_total"]
    report["status"] = report["difference"].abs().le(tolerance).map({True: "pass", False: "fail"})
    return report


def _coalesce_series_under_five(frame: pd.DataFrame, value_column: str) -> pd.DataFrame:
    dimension_columns = [
        column for column in frame.columns
        if column not in {"age_start", "age_end", "age_group_label", value_column}
    ]
    parts = []
    for _, group in frame.groupby(dimension_columns, dropna=False, sort=False):
        parts.append(coalesce_under_five(group, value_column=value_column))
    return pd.concat(parts, ignore_index=True) if parts else frame.copy()


def _prepare_population(population: pd.DataFrame) -> pd.DataFrame:
    if population.empty:
        return population
    keys = ["geography_code", "geography_name", "year", "sex"]
    age_source = population[
        keys + ["age_start", "age_end", "age_group_label", "population"]
    ].copy()
    age_source = _coalesce_series_under_five(age_source, "population")
    totals = (
        population.groupby(keys, as_index=False)["source_total_population"]
        .first()
        .rename(columns={"source_total_population": "population"})
    )
    totals["age_start"] = 0
    totals["age_end"] = 125
    totals["age_group_label"] = "All ages"
    combined = pd.concat([age_source, totals], ignore_index=True)
    both_keys = ["geography_code", "geography_name", "year", "age_start", "age_end", "age_group_label"]
    eligible = combined.groupby(both_keys)["sex"].nunique().eq(2)
    both = (
        combined.set_index(both_keys)
        .loc[eligible[eligible].index]
        .reset_index()
        .groupby(both_keys, as_index=False)["population"]
        .sum()
    )
    both["sex"] = "both"
    return pd.concat([combined, both], ignore_index=True)


def aggregate_who_mortality(
    frame: pd.DataFrame, population: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Aggregate disjoint WHO causes, harmonise 0-4, and derive safe rates."""

    selected = select_preferred_who_lists(frame)
    cause_group = [
        "source_id", "source_version", "evidence_type", "geography_level",
        "geography_code", "geography_name", "year", "cancer_code",
        "cancer_label_en", "cancer_label_pl", "icd_revision", "source_list",
        "sex", "age_start", "age_end", "age_group_label", "measure", "metric",
        "quality_flag", "notes",
    ]
    aggregated = (
        selected.groupby(cause_group, dropna=False, as_index=False)
        .agg(
            value=("value", "sum"),
            icd_codes=("icd_codes", lambda values: "|".join(sorted(set(map(str, values))))),
            coverage_percent=("coverage_percent", "first"),
        )
    )
    aggregated = _coalesce_series_under_five(aggregated, "value")

    series_dimensions = [
        column for column in aggregated.columns
        if column not in {"age_start", "age_end", "age_group_label", "value"}
    ]
    all_ages = aggregated.groupby(series_dimensions, dropna=False, as_index=False)["value"].sum()
    all_ages["age_start"] = 0
    all_ages["age_end"] = 125
    all_ages["age_group_label"] = "All ages"
    counts = pd.concat([aggregated, all_ages], ignore_index=True)

    both_dimensions = [column for column in counts.columns if column not in {"sex", "value"}]
    eligible_counts = counts.groupby(both_dimensions, dropna=False, group_keys=False).filter(
        lambda group: group["sex"].nunique() == 2
    )
    both = eligible_counts.groupby(
        both_dimensions, dropna=False, as_index=False
    )["value"].sum()
    both["sex"] = "both"
    counts = pd.concat([counts, both], ignore_index=True)

    counts["standard_population"] = None
    counts["lower_bound"] = None
    counts["upper_bound"] = None
    counts["projection_base_year"] = None
    counts["risk_basis"] = None
    counts["population"] = None
    counts["quality_flag"] = "reported_unadjusted_allocated"
    counts["notes"] = (
        "WHO country-reported deaths aggregated from one preferred ICD list; "
        "unallocated ages are excluded from age-specific counts."
    )
    counts = counts.drop(columns=["source_list"])

    if population is not None and not population.empty:
        denominators = _prepare_population(population)
        join_keys = ["geography_code", "year", "sex", "age_start", "age_end"]
        counts = counts.drop(columns="population").merge(
            denominators[join_keys + ["population"]], on=join_keys, how="left", validate="many_to_one"
        )
        rate_rows = counts[counts["population"].gt(0)].copy()
        rate_rows["value"] = rate_rows["value"] / rate_rows["population"] * 100_000
        rate_rows["metric"] = rate_rows["age_group_label"].eq("All ages").map(
            {True: "crude_rate", False: "age_specific_rate"}
        )
        counts = pd.concat([counts, rate_rows], ignore_index=True)

    canonical_columns = [
        "source_id", "source_version", "evidence_type", "geography_level",
        "geography_code", "geography_name", "year", "cancer_code",
        "cancer_label_en", "cancer_label_pl", "icd_revision", "icd_codes",
        "sex", "age_start", "age_end", "age_group_label", "measure", "metric",
        "risk_basis", "standard_population", "value", "lower_bound", "upper_bound",
        "population", "coverage_percent", "quality_flag", "notes", "projection_base_year",
    ]
    return validate_frame(counts[canonical_columns])


def combine_sources(frames: Iterable[pd.DataFrame]) -> pd.DataFrame:
    available = [frame for frame in frames if frame is not None and not frame.empty]
    if not available:
        return pd.DataFrame()
    return validate_frame(pd.concat(available, ignore_index=True, sort=False))
