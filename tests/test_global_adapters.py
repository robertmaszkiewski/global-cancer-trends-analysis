from pathlib import Path

import pandas as pd
import pytest

from cancer_explorer.adapters.gbd import parse_gbd_export
from cancer_explorer.adapters.iarc import (
    parse_iarc_export,
    reject_cross_release_trend,
)
from cancer_explorer.adapters.who_ghe import parse_who_ghe_export


FIXTURES = Path(__file__).parent / "fixtures"


def test_gbd_preserves_uncertainty_and_marks_estimates_modelled():
    parsed = parse_gbd_export(pd.read_csv(FIXTURES / "gbd_sample.csv"))
    lung = parsed.query("cancer_code == 'LUNG'").iloc[0]

    assert lung["evidence_type"] == "modelled"
    assert (lung["lower_bound"], lung["value"], lung["upper_bound"]) == (
        3000,
        3200,
        3400,
    )
    assert lung["age_group_label"] == "50-54"


def test_gbd_keeps_age_standardisation_and_burden_measures_explicit():
    parsed = parse_gbd_export(pd.read_csv(FIXTURES / "gbd_sample.csv"))
    breast = parsed.query("cancer_code == 'BREAST'").iloc[0]
    daly = parsed.query("measure == 'DALY'").iloc[0]

    assert breast["metric"] == "age_standardised_rate"
    assert breast["standard_population"] == "GBD world standard population"
    assert daly["cancer_code"] == "COLORECTUM"


def test_who_ghe_is_an_explicit_modelled_fallback():
    parsed = parse_who_ghe_export(pd.read_csv(FIXTURES / "who_ghe_sample.csv"))

    assert set(parsed["evidence_type"]) == {"modelled"}
    assert set(parsed["quality_flag"]) == {"fallback_who_ghe"}
    assert parsed["notes"].str.contains("fallback", case=False).all()
    assert not parsed["measure"].isin({"incidence", "prevalence", "survival"}).any()


def test_iarc_parses_age_sex_type_and_rates_without_losing_counts():
    parsed = parse_iarc_export(pd.read_csv(FIXTURES / "iarc_sample.csv"))
    age_rows = parsed.query("cancer_code == 'LUNG'")

    assert set(age_rows["sex"]) == {"female"}
    assert set(age_rows["measure"]) == {"incidence"}
    assert set(age_rows["age_group_label"]) == {"50-54"}
    assert set(age_rows["metric"]) == {"number", "age_specific_rate"}
    assert set(age_rows["source_version"]) == {"GLOBOCAN 2024"}


def test_iarc_projection_is_separate_and_has_a_base_year():
    parsed = parse_iarc_export(pd.read_csv(FIXTURES / "iarc_sample.csv"))
    projection = parsed.query("evidence_type == 'projected'").iloc[0]

    assert projection["year"] == 2050
    assert projection["projection_base_year"] == 2024
    assert projection["source_id"] == "iarc_cancer_tomorrow"
    assert projection["metric"] == "number"


def test_iarc_lifetime_risk_retains_incidence_or_mortality_basis():
    frame = pd.read_csv(FIXTURES / "iarc_sample.csv")
    all_age = frame.query("record_kind == 'snapshot' and age_index != age_index").copy()
    incidence = all_age.iloc[[0]].copy()
    incidence["type"] = 0
    incidence["cum_risk_74"] = 7.1
    combined = pd.concat([all_age, incidence], ignore_index=True)

    parsed = parse_iarc_export(combined)
    risk = parsed.query("measure == 'lifetime_risk'")

    assert set(risk["risk_basis"]) == {"incidence", "mortality"}


def test_separate_globocan_releases_cannot_be_presented_as_a_time_trend():
    frame = pd.DataFrame(
        {
            "source_version": ["GLOBOCAN 2022 v1.1", "GLOBOCAN 2024"],
            "year": [2022, 2024],
            "cancer_code": ["LUNG", "LUNG"],
        }
    )

    with pytest.raises(ValueError, match="independent snapshots"):
        reject_cross_release_trend(frame)
