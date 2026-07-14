import pandas as pd
import pytest

from cancer_explorer.transform import (
    aggregate_who_mortality,
    coalesce_under_five,
    combine_sources,
    reconcile_who_totals,
    select_preferred_who_lists,
)


def who_rows():
    rows = []
    for source_list, revision in [("08A", "ICD-8"), ("104", "ICD-10")]:
        for sex, values in [("male", [2, 3]), ("female", [1, 4])]:
            for cause, multiplier in [("C33", 1), ("C34", 2)]:
                allocated = sum(values) * multiplier
                for (age_start, age_end, label), value in zip(
                    [(0, 0, "0"), (1, 4, "1-4")], values, strict=True
                ):
                    rows.append(
                        {
                            "source_id": "who_mortality",
                            "source_version": "2026-02-23",
                            "evidence_type": "observed",
                            "geography_level": "country",
                            "geography_code": "POL",
                            "geography_name": "Poland",
                            "year": 2020,
                            "cancer_code": "LUNG",
                            "cancer_label_en": "Trachea, bronchus and lung",
                            "cancer_label_pl": "Tchawica, oskrzela i płuco",
                            "icd_revision": revision,
                            "icd_codes": cause,
                            "source_list": source_list,
                            "sex": sex,
                            "age_start": age_start,
                            "age_end": age_end,
                            "age_group_label": label,
                            "measure": "mortality",
                            "metric": "number",
                            "value": value * multiplier,
                            "source_total": allocated + 1,
                            "unallocated_deaths": 1,
                            "coverage_percent": 99.0,
                            "quality_flag": "reported_unadjusted",
                            "notes": "test",
                        }
                    )
    return pd.DataFrame(rows)


def test_preferred_who_list_prevents_double_counting_parallel_icd_lists():
    selected = select_preferred_who_lists(who_rows())

    assert set(selected["source_list"]) == {"104"}


def test_under_five_aggregation_requires_complete_non_overlapping_coverage():
    complete = pd.DataFrame(
        {"age_start": [0, 1], "age_end": [0, 4], "value": [2, 3]}
    )
    assert coalesce_under_five(complete)["value"].sum() == 5

    incomplete = pd.DataFrame(
        {"age_start": [0, 2], "age_end": [0, 4], "value": [2, 3]}
    )
    with pytest.raises(ValueError, match="gap or overlap"):
        coalesce_under_five(incomplete)


def test_who_cause_rows_are_aggregated_to_cancer_age_and_both_sexes():
    result = aggregate_who_mortality(who_rows())
    under_five = result.query("age_start == 0 and age_end == 4 and metric == 'number'")

    assert set(under_five["sex"]) == {"male", "female", "both"}
    assert under_five.query("sex == 'male'")["value"].iloc[0] == 15
    assert under_five.query("sex == 'female'")["value"].iloc[0] == 15
    assert under_five.query("sex == 'both'")["value"].iloc[0] == 30


def test_who_allocated_plus_unallocated_reconciles_to_published_total():
    reconciliation = reconcile_who_totals(
        select_preferred_who_lists(who_rows()), tolerance=0.01
    )

    assert set(reconciliation["status"]) == {"pass"}


def test_combining_sources_preserves_overlapping_observed_and_modelled_rows():
    observed = aggregate_who_mortality(who_rows()).head(1)
    modelled = observed.copy()
    modelled["source_id"] = "iarc_globocan_2024"
    modelled["source_version"] = "GLOBOCAN 2024"
    modelled["evidence_type"] = "modelled"

    combined = combine_sources([observed, modelled])

    assert len(combined) == 2
    assert set(combined["evidence_type"]) == {"observed", "modelled"}
