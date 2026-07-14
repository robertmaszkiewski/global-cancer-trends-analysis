from cancer_explorer.compatibility import is_valid_combination, valid_routes


def test_survival_only_accepts_percent_or_probability():
    assert is_valid_combination("survival", "percent")
    assert not is_valid_combination("survival", "number")


def test_daly_does_not_accept_probability():
    assert is_valid_combination("DALY", "number")
    assert is_valid_combination("DALY", "age_standardised_rate")
    assert not is_valid_combination("DALY", "probability")


def test_valid_routes_explain_supported_metrics():
    routes = valid_routes("incidence")

    assert "number" in routes
    assert "age_specific_rate" in routes
    assert "probability" not in routes
