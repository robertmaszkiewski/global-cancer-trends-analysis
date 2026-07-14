from pathlib import Path

import pandas as pd
import pytest

from cancer_explorer.adapters.who_mortality import (
    filter_complete_country_years,
    parse_who_frame,
    parse_who_population,
)


FIXTURE = Path(__file__).parent / "fixtures" / "who_mortality_sample.csv"


def parsed_sample():
    frame = pd.read_csv(
        FIXTURE,
        dtype={"Admin1": str, "SubDiv": str, "List": str, "Cause": str, "Frmat": str},
    )
    return parse_who_frame(frame, {4270: ("POL", "Poland")})


def test_detailed_and_condensed_lists_map_to_cancer_types():
    parsed = parsed_sample()

    assert {"LUNG", "BREAST"} <= set(parsed["cancer_code"])


def test_who_rows_are_always_observed():
    assert set(parsed_sample()["evidence_type"]) == {"observed"}


def test_parser_preserves_age_granularity_and_total():
    parsed = parsed_sample()
    lung = parsed.query("cancer_code == 'LUNG'")

    assert lung["source_total"].iloc[0] == 130
    assert lung["value"].sum() == 115
    assert lung["unallocated_deaths"].iloc[0] == 15
    assert {65, 70, 75, 80, 85} <= set(lung["age_start"])


def test_country_subdivisions_are_excluded_from_national_series():
    frame = pd.read_csv(
        FIXTURE,
        dtype={"Admin1": str, "SubDiv": str, "List": str, "Cause": str, "Frmat": str},
    )
    frame.loc[0, "Admin1"] = "901"

    parsed = parse_who_frame(frame, {4270: ("POL", "Poland")})

    assert not ((parsed["cancer_code"] == "LUNG") & (parsed["year"] == 2021)).any()


def test_country_years_below_completeness_threshold_are_removed():
    parsed = parsed_sample()
    quality = pd.DataFrame(
        [
            {"geography_code": "POL", "year": 2021, "coverage_percent": 64.9},
        ]
    )

    result = filter_complete_country_years(parsed, quality, minimum=65)

    assert result.empty


def test_duplicate_age_keys_are_rejected():
    frame = pd.read_csv(
        FIXTURE,
        dtype={"Admin1": str, "SubDiv": str, "List": str, "Cause": str, "Frmat": str},
    )
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="duplicate WHO mortality keys"):
        parse_who_frame(frame, {4270: ("POL", "Poland")})


def test_population_denominators_follow_the_same_age_layouts():
    frame = pd.DataFrame(
        [
            {
                "Country": 4270,
                "Admin1": None,
                "SubDiv": None,
                "Year": 2021,
                "Sex": 1,
                "Frmat": "02",
                "Pop1": 1_000,
                "Pop2": 10,
                "Pop3": 40,
                "Pop7": 100,
            }
        ]
    )

    parsed = parse_who_population(frame, {4270: ("POL", "Poland")})

    assert parsed["source_total_population"].eq(1_000).all()
    assert set(parsed["age_group_label"]) == {"0", "1-4", "5-9"}
    assert parsed["population"].sum() == 150
