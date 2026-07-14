"""Measure and metric compatibility for pipeline and browser filters."""

COMPATIBLE_METRICS: dict[str, tuple[str, ...]] = {
    "incidence": ("number", "crude_rate", "age_specific_rate", "age_standardised_rate"),
    "mortality": ("number", "crude_rate", "age_specific_rate", "age_standardised_rate"),
    "prevalence": ("number", "crude_rate", "age_specific_rate", "age_standardised_rate", "percent"),
    "DALY": ("number", "crude_rate", "age_specific_rate", "age_standardised_rate"),
    "YLL": ("number", "crude_rate", "age_specific_rate", "age_standardised_rate"),
    "YLD": ("number", "crude_rate", "age_specific_rate", "age_standardised_rate"),
    "survival": ("percent", "probability"),
    "lifetime_risk": ("percent", "probability"),
    "attributable_burden": ("number", "age_standardised_rate", "percent"),
}


def is_valid_combination(measure: str, metric: str) -> bool:
    return metric in COMPATIBLE_METRICS.get(measure, ())


def valid_routes(measure: str) -> list[str]:
    return list(COMPATIBLE_METRICS.get(measure, ()))
