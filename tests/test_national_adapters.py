from pathlib import Path

import pandas as pd

from cancer_explorer.adapters.ecis_redecan import parse_ecis_redecan_export
from cancer_explorer.adapters.krn import parse_krn_export
from cancer_explorer.adapters.seer import parse_seer_export
from cancer_explorer.adapters.uk import parse_uk_export


FIXTURES = Path(__file__).parent / "fixtures"


def test_krn_preserves_bilingual_labels_counts_and_asw_rates():
    parsed = parse_krn_export(pd.read_csv(FIXTURES / "krn_sample.csv"))
    lung = parsed.query("cancer_code == 'LUNG'")

    assert set(lung["metric"]) == {"number", "age_specific_rate"}
    assert set(lung["cancer_label_pl"]) == {"Płuco"}
    assert set(lung.loc[lung.metric == "age_specific_rate", "standard_population"]) == {None}


def test_uk_total_and_constituent_nations_are_distinct_geographies():
    parsed = parse_uk_export(pd.read_csv(FIXTURES / "uk_sample.csv"))

    assert set(parsed["geography_code"]) == {"GBR", "GBR-ENG"}
    assert set(parsed["geography_level"]) == {"country", "nation"}
    england = parsed.query("geography_code == 'GBR-ENG'").iloc[0]
    assert england["standard_population"] == "ESP2013"


def test_ecis_registry_is_not_mislabelled_as_national_coverage():
    parsed = parse_ecis_redecan_export(
        pd.read_csv(FIXTURES / "ecis_redecan_sample.csv")
    )
    girona = parsed.query("geography_code == 'ESP-GIRONA'").iloc[0]

    assert girona["geography_level"] == "registry"
    assert girona["coverage_percent"] == 2.0
    assert girona["evidence_type"] == "observed"


def test_redecan_estimate_remains_modelled_and_country_level():
    parsed = parse_ecis_redecan_export(
        pd.read_csv(FIXTURES / "ecis_redecan_sample.csv")
    )
    estimate = parsed.query("source_id == 'redecan'").iloc[0]

    assert estimate["geography_code"] == "ESP"
    assert estimate["evidence_type"] == "modelled"
    assert estimate["quality_flag"] == "national_estimate"


def test_seer_incidence_registry_scope_and_us_mortality_scope_stay_separate():
    parsed = parse_seer_export(pd.read_csv(FIXTURES / "seer_sample.csv"))
    incidence = parsed.query("measure == 'incidence'").iloc[0]
    mortality = parsed.query("measure == 'mortality'").iloc[0]

    assert incidence["geography_level"] == "registry_network"
    assert incidence["geography_code"] == "USA-SEER17"
    assert incidence["coverage_percent"] == 26.5
    assert mortality["geography_level"] == "country"
    assert mortality["geography_code"] == "USA"
