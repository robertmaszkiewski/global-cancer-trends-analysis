import math

import pandas as pd
import pytest

from cancer_explorer.analyse import (
    age_peak,
    calculate_change,
    compare_countries,
    projection_change,
    rank_cancers,
)


def test_change_reports_absolute_relative_and_compound_annual_change():
    frame = pd.DataFrame(
        {"year": [2000, 2010], "value": [100.0, 200.0], "lower_bound": [None, None], "upper_bound": [None, None]}
    )

    result = calculate_change(frame, 2000, 2010)

    assert result["absolute_change"] == 100
    assert result["percent_change"] == 100
    assert math.isclose(result["cagr_percent"], 7.177346, rel_tol=1e-5)
    assert result["direction"] == "increase"


def test_change_is_uncertain_when_intervals_overlap():
    frame = pd.DataFrame(
        {
            "year": [2020, 2021],
            "value": [100.0, 105.0],
            "lower_bound": [90.0, 95.0],
            "upper_bound": [110.0, 115.0],
        }
    )

    assert calculate_change(frame, 2020, 2021)["direction"] == "uncertain"


def test_cancer_ranking_excludes_aggregate_categories_and_low_volume_noise():
    frame = pd.DataFrame(
        {
            "cancer_code": ["ALL", "LUNG", "BREAST", "RARE"],
            "cancer_label_en": ["All cancers", "Lung", "Breast", "Rare"],
            "value": [1000, 300, 250, 2],
        }
    )

    ranked = rank_cancers(frame, minimum_value=10)

    assert list(ranked["cancer_code"]) == ["LUNG", "BREAST"]
    assert list(ranked["rank"]) == [1, 2]


def test_age_peak_uses_age_specific_rows_not_all_age_totals():
    frame = pd.DataFrame(
        {
            "metric": ["number", "age_specific_rate", "age_specific_rate"],
            "age_start": [0, 50, 65],
            "age_end": [125, 54, 69],
            "age_group_label": ["All ages", "50-54", "65-69"],
            "value": [10_000, 45.0, 120.0],
        }
    )

    peak = age_peak(frame)

    assert peak["age_group_label"] == "65-69"
    assert peak["value"] == 120


def test_country_comparison_requires_like_for_like_metrics_and_standards():
    frame = pd.DataFrame(
        {
            "geography_code": ["POL", "ESP"],
            "value": [100, 120],
            "source_id": ["iarc_globocan_2024"] * 2,
            "source_version": ["GLOBOCAN 2024"] * 2,
            "evidence_type": ["modelled"] * 2,
            "year": [2024] * 2,
            "sex": ["both"] * 2,
            "age_start": [0] * 2,
            "age_end": [125] * 2,
            "measure": ["incidence"] * 2,
            "metric": ["age_standardised_rate", "crude_rate"],
            "standard_population": ["World", None],
            "cancer_code": ["LUNG"] * 2,
        }
    )

    with pytest.raises(ValueError, match="like-for-like"):
        compare_countries(frame)


def test_projection_change_rejects_observed_rows_and_labels_demographic_scenario():
    projected = pd.DataFrame(
        {
            "year": [2024, 2050],
            "value": [100, 150],
            "evidence_type": ["projected", "projected"],
            "projection_base_year": [2024, 2024],
        }
    )
    result = projection_change(projected, 2050)

    assert result["percent_change"] == 50
    assert result["scenario"] == "demographic_projection"

    observed = projected.assign(evidence_type="observed")
    with pytest.raises(ValueError, match="projected"):
        projection_change(observed, 2050)
