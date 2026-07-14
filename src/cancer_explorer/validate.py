"""Machine-readable validation and human-readable coverage reporting."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from cancer_explorer.schemas import canonical_series_key


ISSUE_COLUMNS = ["severity", "code", "count", "detail"]


def _markdown_table(frame: pd.DataFrame) -> str:
    """Render a compact Markdown table without an optional tabulate dependency."""

    if frame.empty:
        return "_No rows._"
    columns = list(frame.columns)

    def cell(value: object) -> str:
        if pd.isna(value):
            return ""
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = [
        "| " + " | ".join(map(str, columns)) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    lines.extend(
        "| " + " | ".join(cell(value) for value in row) + " |"
        for row in frame.itertuples(index=False, name=None)
    )
    return "\n".join(lines)


def validate_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    issues: list[dict[str, object]] = []

    def add(code: str, mask: pd.Series, detail: str, severity: str = "error") -> None:
        count = int(mask.fillna(False).sum())
        if count:
            issues.append({"severity": severity, "code": code, "count": count, "detail": detail})

    required = {
        "source_id", "source_version", "evidence_type", "geography_code", "year",
        "cancer_code", "sex", "age_start", "age_end", "measure", "metric", "value",
    }
    missing_columns = required - set(frame.columns)
    if missing_columns:
        issues.append(
            {
                "severity": "error",
                "code": "missing_columns",
                "count": len(missing_columns),
                "detail": ", ".join(sorted(missing_columns)),
            }
        )
        return pd.DataFrame(issues, columns=ISSUE_COLUMNS)

    add("negative_value", frame["value"].lt(0), "Canonical values must be non-negative.")
    bounds_present = frame.get("lower_bound", pd.Series(index=frame.index, dtype=float)).notna() | frame.get(
        "upper_bound", pd.Series(index=frame.index, dtype=float)
    ).notna()
    lower = pd.to_numeric(frame.get("lower_bound"), errors="coerce")
    upper = pd.to_numeric(frame.get("upper_bound"), errors="coerce")
    value = pd.to_numeric(frame["value"], errors="coerce")
    add(
        "uncertainty_order",
        bounds_present & (~(lower.le(value) & value.le(upper))),
        "Uncertainty intervals must satisfy lower <= value <= upper.",
    )
    add("invalid_age_range", frame["age_end"].lt(frame["age_start"]), "age_end must be >= age_start.")
    key = [column for column in canonical_series_key() if column in frame]
    add(
        "duplicate_canonical_key",
        frame.duplicated(key, keep=False),
        "Two rows occupy the same source-preserving analytical grain.",
    )
    if {"ALL", "ALL_EX_NMSC"} <= set(frame["cancer_code"]):
        definitions = frame[frame["cancer_code"].isin(["ALL", "ALL_EX_NMSC"])].copy()
        definition_key = [
            column for column in ["source_id", "source_version", "icd_codes"]
            if column in definitions
        ]
        distinct_definitions = definitions[definition_key + ["cancer_code"]].drop_duplicates()
        collisions = distinct_definitions.groupby(definition_key, dropna=False)["cancer_code"].nunique().gt(1)
        collision_count = int(collisions.sum())
        if collision_count:
            issues.append(
                {
                    "severity": "error",
                    "code": "nmsc_definition_collision",
                    "count": collision_count,
                    "detail": "All cancers and all cancers excluding NMSC must not share an identical definition.",
                }
            )
    if "standard_population" in frame:
        add(
            "missing_standard_population",
            frame["metric"].eq("age_standardised_rate") & frame["standard_population"].isna(),
            "Age-standardised rates require a named standard population.",
        )
    if "projection_base_year" in frame:
        add(
            "missing_projection_base",
            frame["evidence_type"].eq("projected") & frame["projection_base_year"].isna(),
            "Projected values require their baseline year.",
        )
        projected = frame[
            frame["evidence_type"].eq("projected")
            & frame["projection_base_year"].notna()
            & frame["year"].eq(frame["projection_base_year"])
            & frame["metric"].eq("number")
            & frame["age_start"].eq(0)
            & frame["age_end"].eq(125)
            & ~frame["cancer_code"].isin(["OTHER", "UNSPECIFIED"])
        ]
        modelled = frame[
            frame["evidence_type"].eq("modelled")
            & frame["metric"].eq("number")
            & frame["age_start"].eq(0)
            & frame["age_end"].eq(125)
            & ~frame["cancer_code"].isin(["OTHER", "UNSPECIFIED"])
        ]
        comparison_keys = [
            "geography_code", "year", "cancer_code", "sex", "measure", "metric",
            "age_start", "age_end",
        ]
        if not projected.empty and not modelled.empty:
            comparison = projected.merge(
                modelled[comparison_keys + ["value"]],
                on=comparison_keys,
                how="inner",
                suffixes=("_projected", "_snapshot"),
            )
            mismatch = (
                (comparison["value_projected"] - comparison["value_snapshot"]).abs()
                / comparison["value_snapshot"].replace(0, pd.NA)
            ).gt(0.005)
            if mismatch.any():
                issues.append(
                    {
                        "severity": "error",
                        "code": "projection_baseline_mismatch",
                        "count": int(mismatch.sum()),
                        "detail": "Projection base counts must reconcile with the matching modelled snapshot within 0.5%.",
                    }
                )
    return pd.DataFrame(issues, columns=ISSUE_COLUMNS)


def build_coverage_table(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby(["source_id", "source_version", "evidence_type"], dropna=False)
        .agg(
            first_year=("year", "min"),
            last_year=("year", "max"),
            rows=("value", "size"),
            geographies=("geography_code", "nunique"),
            cancers=("cancer_code", "nunique"),
            sexes=("sex", "nunique"),
            age_groups=("age_group_label", "nunique"),
            measures=("measure", "nunique"),
            metrics=("metric", "nunique"),
        )
        .reset_index()
    )


def write_quality_report(frame: pd.DataFrame, issues: pd.DataFrame, output: Path) -> None:
    coverage = build_coverage_table(frame)
    errors = int((issues["severity"] == "error").sum()) if not issues.empty else 0
    lines = [
        "# Data quality report",
        "",
        f"Validated canonical records: **{len(frame):,}**",
        f"Validation issue types at error severity: **{errors}**",
        "",
        "## Coverage by evidence source",
        "",
        _markdown_table(coverage),
        "",
        "## Validation results",
        "",
        "No validation errors were detected." if issues.empty else _markdown_table(issues),
        "",
        "## Interpretation safeguards",
        "",
        "- Observed, modelled, and projected records remain separate evidence layers.",
        "- GLOBOCAN releases are independent snapshots and are not treated as a historical trend.",
        "- WHO mortality counts use one preferred ICD list per country-year to avoid double counting.",
        "- Registry-network coverage is not relabelled as whole-country coverage.",
        "- Rates with different standard populations are not treated as directly interchangeable.",
        "",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
