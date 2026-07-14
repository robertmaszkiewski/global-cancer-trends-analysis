"""Canonical long-form schema for every cancer observation."""

from __future__ import annotations

from typing import Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

EvidenceType = Literal["observed", "modelled", "projected"]
Sex = Literal["both", "female", "male"]
Measure = Literal[
    "incidence",
    "mortality",
    "prevalence",
    "DALY",
    "YLL",
    "YLD",
    "survival",
    "lifetime_risk",
    "attributable_burden",
]
Metric = Literal[
    "number",
    "crude_rate",
    "age_specific_rate",
    "age_standardised_rate",
    "percent",
    "probability",
]
RiskBasis = Literal["incidence", "mortality"]


class CancerRecord(BaseModel):
    """One source-preserving cancer measure at a precise analytical grain."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    source_version: str
    evidence_type: EvidenceType
    geography_level: str
    geography_code: str
    geography_name: str
    year: int = Field(ge=1900, le=2100)
    cancer_code: str
    cancer_label_en: str
    cancer_label_pl: str
    icd_revision: str | None = None
    icd_codes: str | None = None
    sex: Sex
    age_start: int = Field(ge=0, le=125)
    age_end: int = Field(ge=0, le=125)
    age_group_label: str
    measure: Measure
    metric: Metric
    risk_basis: RiskBasis | None = None
    standard_population: str | None = None
    value: float = Field(ge=0)
    lower_bound: float | None = Field(default=None, ge=0)
    upper_bound: float | None = Field(default=None, ge=0)
    population: float | None = Field(default=None, ge=0)
    coverage_percent: float | None = Field(default=None, ge=0, le=100)
    quality_flag: str
    notes: str = ""
    projection_base_year: int | None = Field(default=None, ge=1900, le=2100)

    @model_validator(mode="after")
    def validate_cross_field_rules(self) -> "CancerRecord":
        if self.age_end < self.age_start:
            raise ValueError("age_end must be greater than or equal to age_start")
        if (self.lower_bound is None) != (self.upper_bound is None):
            raise ValueError("uncertainty bounds must be supplied together")
        if self.lower_bound is not None and not (
            self.lower_bound <= self.value <= self.upper_bound
        ):
            raise ValueError("value must fall within uncertainty bounds")
        if self.metric == "age_standardised_rate" and not self.standard_population:
            raise ValueError("age-standardised rates require a standard population")
        if self.measure == "lifetime_risk" and self.risk_basis is None:
            raise ValueError("lifetime risk requires an incidence or mortality basis")
        if self.evidence_type == "projected" and self.projection_base_year is None:
            raise ValueError("projected records require projection_base_year")
        return self


def canonical_series_key() -> tuple[str, ...]:
    """Columns that uniquely identify one canonical observation."""

    return (
        "source_id",
        "source_version",
        "evidence_type",
        "geography_level",
        "geography_code",
        "year",
        "cancer_code",
        "sex",
        "age_start",
        "age_end",
        "measure",
        "metric",
        "risk_basis",
        "standard_population",
        "projection_base_year",
    )


def validate_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate records and fail on mixed or duplicated analytical grain."""

    # Pandas promotes optional numeric/string fields containing ``None`` to
    # floating NaN. Convert missing values back to Python ``None`` before
    # passing records across the strict Pydantic boundary.
    records = frame.astype(object).where(pd.notna(frame), None).to_dict("records")
    validated = [CancerRecord.model_validate(row).model_dump() for row in records]
    result = pd.DataFrame(validated)
    duplicates = result.duplicated(subset=list(canonical_series_key()), keep=False)
    if duplicates.any():
        examples = result.loc[duplicates, list(canonical_series_key())].head(5)
        raise ValueError(f"duplicate canonical keys:\n{examples.to_string(index=False)}")
    return result
