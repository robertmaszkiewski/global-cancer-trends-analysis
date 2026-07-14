"""Build the validated canonical dataset from acquired staging tables."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from cancer_explorer.adapters.who_mortality import build_who_population
from cancer_explorer.transform import aggregate_who_mortality, combine_sources, reconcile_who_totals, select_preferred_who_lists
from cancer_explorer.validate import build_coverage_table, validate_dataset, write_quality_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--countries", nargs="+", default=["POL", "GBR", "ESP", "USA"])
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/who_mortality"))
    parser.add_argument("--staging-dir", type=Path, default=Path("data/staging"))
    parser.add_argument("--output", type=Path, default=Path("data/processed"))
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    who_parts = [
        pd.read_parquet(args.staging_dir / "who_mortality" / f"{country}.parquet")
        for country in args.countries
    ]
    who_raw = pd.concat(who_parts, ignore_index=True)
    population = build_who_population(args.raw_dir, set(args.countries))
    reconciliation = reconcile_who_totals(select_preferred_who_lists(who_raw))
    who = aggregate_who_mortality(who_raw, population=population)

    iarc_dir = args.staging_dir / "iarc"
    iarc = [pd.read_parquet(path) for path in sorted(iarc_dir.glob("*.parquet"))]
    canonical = combine_sources([who, *iarc])
    issues = validate_dataset(canonical)
    failed_reconciliation = reconciliation[reconciliation["status"] == "fail"]
    if not failed_reconciliation.empty:
        issues = pd.concat(
            [
                issues,
                pd.DataFrame(
                    [
                        {
                            "severity": "error",
                            "code": "who_total_reconciliation",
                            "count": len(failed_reconciliation),
                            "detail": "Allocated ages plus unallocated deaths do not match source totals.",
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    args.output.mkdir(parents=True, exist_ok=True)
    canonical.to_parquet(args.output / "cancer_observations.parquet", index=False)
    build_coverage_table(canonical).to_csv(args.output / "coverage.csv", index=False)
    issues.to_csv(args.output / "validation.csv", index=False)
    reconciliation.to_csv(args.output / "who_reconciliation.csv", index=False)
    canonical[
        ["cancer_code", "cancer_label_en", "cancer_label_pl", "icd_codes"]
    ].drop_duplicates().sort_values("cancer_code").to_csv(args.output / "cancers.csv", index=False)
    write_quality_report(canonical, issues, Path("docs/data-quality.md"))

    print(f"Canonical records: {len(canonical):,}")
    print(f"WHO observed records: {len(who):,}")
    print(f"IARC snapshot/projection records: {sum(map(len, iarc)):,}")
    print(f"Validation issue rows: {len(issues):,}")
    print(f"WHO reconciliation failures: {len(failed_reconciliation):,}")
    if args.strict and (not issues.empty or not failed_reconciliation.empty):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
