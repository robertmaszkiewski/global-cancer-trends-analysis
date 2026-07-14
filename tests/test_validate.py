import pandas as pd

from cancer_explorer.validate import build_coverage_table, validate_dataset


def valid_row(**overrides):
    row = {
        "source_id": "iarc_globocan_2024",
        "source_version": "GLOBOCAN 2024",
        "evidence_type": "modelled",
        "geography_level": "country",
        "geography_code": "POL",
        "geography_name": "Poland",
        "year": 2024,
        "cancer_code": "LUNG",
        "cancer_label_en": "Trachea, bronchus and lung",
        "cancer_label_pl": "Tchawica, oskrzela i płuco",
        "icd_revision": "ICD-10",
        "icd_codes": "C33-C34",
        "sex": "both",
        "age_start": 0,
        "age_end": 125,
        "age_group_label": "All ages",
        "measure": "incidence",
        "metric": "age_standardised_rate",
        "risk_basis": None,
        "standard_population": "World standard population",
        "value": 50.0,
        "lower_bound": 45.0,
        "upper_bound": 55.0,
        "population": 36_000_000,
        "coverage_percent": None,
        "quality_flag": "modelled",
        "notes": "test",
        "projection_base_year": None,
    }
    row.update(overrides)
    return row


def test_validation_detects_negative_values_and_bad_uncertainty_order():
    frame = pd.DataFrame(
        [valid_row(value=-1), valid_row(value=60, lower_bound=65, upper_bound=55, cancer_code="BREAST")]
    )
    issues = validate_dataset(frame)

    assert {"negative_value", "uncertainty_order"} <= set(issues["code"])


def test_validation_detects_duplicate_canonical_keys():
    frame = pd.DataFrame([valid_row(), valid_row()])
    issues = validate_dataset(frame)

    duplicate = issues.query("code == 'duplicate_canonical_key'").iloc[0]
    assert duplicate["severity"] == "error"
    assert duplicate["count"] == 2


def test_all_cancers_with_and_without_nmsc_must_keep_distinct_definitions():
    frame = pd.DataFrame(
        [
            valid_row(cancer_code="ALL", icd_codes="C00-C97"),
            valid_row(cancer_code="ALL_EX_NMSC", icd_codes="C00-C97"),
        ]
    )
    issues = validate_dataset(frame)

    assert "nmsc_definition_collision" in set(issues["code"])


def test_coverage_table_reports_each_source_dimension_and_year_range():
    frame = pd.DataFrame(
        [
            valid_row(year=2022),
            valid_row(year=2024, geography_code="ESP", geography_name="Spain"),
        ]
    )
    coverage = build_coverage_table(frame)

    assert coverage["first_year"].iloc[0] == 2022
    assert coverage["last_year"].iloc[0] == 2024
    assert coverage["geographies"].iloc[0] == 2
    assert coverage["cancers"].iloc[0] == 1


def test_projection_baseline_must_match_the_modelled_snapshot():
    snapshot = valid_row(metric="number", standard_population=None, value=100)
    projection = valid_row(
        source_id="iarc_cancer_tomorrow",
        evidence_type="projected",
        metric="number",
        standard_population=None,
        value=200,
        projection_base_year=2024,
    )
    issues = validate_dataset(pd.DataFrame([snapshot, projection]))

    assert "projection_baseline_mismatch" in set(issues["code"])
