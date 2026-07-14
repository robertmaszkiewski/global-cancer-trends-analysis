import pandas as pd
import pytest
from pydantic import ValidationError

from cancer_explorer.schemas import CancerRecord, canonical_series_key, validate_frame


def valid_record(**overrides):
    record = {
        "source_id": "gbd_2023",
        "source_version": "GBD 2023",
        "evidence_type": "modelled",
        "geography_level": "country",
        "geography_code": "POL",
        "geography_name": "Poland",
        "year": 2023,
        "cancer_code": "C00-C97_EX_NMSC",
        "cancer_label_en": "All cancers excluding NMSC",
        "cancer_label_pl": "Wszystkie nowotwory bez NMSC",
        "icd_revision": "ICD-10",
        "icd_codes": "C00-C97 excluding C44",
        "sex": "both",
        "age_start": 0,
        "age_end": 125,
        "age_group_label": "All ages",
        "measure": "incidence",
        "metric": "age_standardised_rate",
        "risk_basis": None,
        "standard_population": "GBD world population standard",
        "value": 250.0,
        "lower_bound": 230.0,
        "upper_bound": 270.0,
        "population": 36_700_000,
        "coverage_percent": None,
        "quality_flag": "modelled_with_uncertainty",
        "notes": "",
        "projection_base_year": None,
    }
    record.update(overrides)
    return record


def test_valid_record_accepts_uncertainty_bounds():
    row = CancerRecord.model_validate(valid_record())

    assert row.lower_bound <= row.value <= row.upper_bound


def test_negative_values_are_rejected():
    with pytest.raises(ValidationError):
        CancerRecord.model_validate(valid_record(value=-1))


def test_age_standardised_rate_requires_named_standard():
    with pytest.raises(ValidationError):
        CancerRecord.model_validate(valid_record(standard_population=None))


def test_projected_record_requires_base_year():
    with pytest.raises(ValidationError):
        CancerRecord.model_validate(
            valid_record(evidence_type="projected", year=2050, projection_base_year=None)
        )


def test_lifetime_risk_requires_an_outcome_basis():
    with pytest.raises(ValidationError):
        CancerRecord.model_validate(
            valid_record(
                measure="lifetime_risk",
                metric="percent",
                standard_population=None,
                risk_basis=None,
            )
        )


def test_observed_and_modelled_rows_have_different_series_keys():
    observed = valid_record(evidence_type="observed", lower_bound=None, upper_bound=None)
    modelled = valid_record()

    key = canonical_series_key()

    assert "evidence_type" in key
    assert tuple(observed[field] for field in key) != tuple(
        modelled[field] for field in key
    )


def test_frame_rejects_duplicate_canonical_keys():
    frame = pd.DataFrame([valid_record(), valid_record()])

    with pytest.raises(ValueError, match="duplicate canonical keys"):
        validate_frame(frame)
