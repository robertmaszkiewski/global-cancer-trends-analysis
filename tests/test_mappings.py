import pandas as pd
import pytest

from cancer_explorer.mappings import (
    IncompleteAggregationError,
    UnknownMappingError,
    aggregate_age,
    load_cancer_taxonomy,
    map_icd_code,
    normalize_geography,
    normalize_sex,
)


def test_all_cancers_with_and_without_nmsc_are_distinct():
    taxonomy = load_cancer_taxonomy().set_index("cancer_code")

    assert taxonomy.loc["ALL", "includes_nmsc"]
    assert not taxonomy.loc["ALL_EX_NMSC", "includes_nmsc"]


@pytest.mark.parametrize(
    ("revision", "source_code", "expected"),
    [
        ("ICD-10", "C34", "LUNG"),
        ("ICD-10", "C50", "BREAST"),
        ("ICD-9", "162", "LUNG"),
        ("ICD-8", "174", "BREAST"),
        ("ICD-7", "151", "STOMACH"),
    ],
)
def test_icd_revisions_map_to_common_cancer_types(revision, source_code, expected):
    assert map_icd_code(revision, source_code) == expected


def test_unknown_icd_code_is_rejected_for_review():
    with pytest.raises(UnknownMappingError):
        map_icd_code("ICD-10", "Z99")


@pytest.mark.parametrize(
    ("source", "expected"),
    [("1", "male"), ("Males", "male"), ("2", "female"), ("Both sexes", "both")],
)
def test_sex_labels_are_normalised(source, expected):
    assert normalize_sex(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [("Poland", "POL"), ("United Kingdom", "GBR"), ("UK", "GBR"), ("840", "USA")],
)
def test_geography_aliases_are_normalised(source, expected):
    assert normalize_geography(source) == expected


def age_rows():
    return pd.DataFrame(
        {
            "age_start": [65, 70, 75, 80, 85],
            "age_end": [69, 74, 79, 84, 125],
            "value": [10, 20, 30, 40, 50],
        }
    )


def test_age_65_plus_sums_complete_constituent_groups():
    result = aggregate_age(age_rows(), "65+")

    assert result == 150


def test_age_65_plus_requires_all_constituent_groups():
    incomplete = age_rows().query("age_start != 75")

    with pytest.raises(IncompleteAggregationError):
        aggregate_age(incomplete, "65+")
