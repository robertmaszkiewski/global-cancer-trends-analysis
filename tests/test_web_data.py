import json
from pathlib import Path

import pandas as pd

from cancer_explorer.build_web_data import (
    MAX_PARTITION_BYTES,
    build_web_data,
    deterministic_json,
)


def sample_frame():
    base = {
        "source_version": "GLOBOCAN 2024",
        "geography_level": "country",
        "geography_code": "POL",
        "geography_name": "Poland",
        "cancer_code": "LUNG",
        "cancer_label_en": "Trachea, bronchus and lung",
        "cancer_label_pl": "Tchawica, oskrzela i płuco",
        "icd_revision": "ICD-10",
        "icd_codes": "C33-C34",
        "age_group_label": "All ages",
        "risk_basis": None,
        "standard_population": None,
        "lower_bound": None,
        "upper_bound": None,
        "population": 38_000_000,
        "coverage_percent": None,
        "quality_flag": "test",
        "notes": "test",
        "projection_base_year": None,
    }
    return pd.DataFrame(
        [
            base | {"source_id": "iarc_globocan_2024", "evidence_type": "modelled", "year": 2024, "sex": "both", "age_start": 0, "age_end": 125, "measure": "incidence", "metric": "number", "value": 200_000},
            base | {"source_id": "iarc_globocan_2024", "evidence_type": "modelled", "year": 2024, "sex": "female", "age_start": 50, "age_end": 54, "age_group_label": "50-54", "measure": "incidence", "metric": "age_specific_rate", "value": 45.0},
            base | {"source_id": "who_mortality", "source_version": "2026-02-23", "evidence_type": "observed", "year": 2020, "sex": "both", "age_start": 0, "age_end": 125, "measure": "mortality", "metric": "crude_rate", "value": 40.0},
            base | {"source_id": "iarc_cancer_tomorrow", "evidence_type": "projected", "year": 2050, "sex": "both", "age_start": 0, "age_end": 125, "measure": "incidence", "metric": "number", "value": 250_000, "projection_base_year": 2024},
        ]
    )


def test_json_serialisation_is_deterministic():
    left = deterministic_json({"b": 2, "a": [3, 1]})
    right = deterministic_json({"a": [3, 1], "b": 2})

    assert left == right
    assert left.startswith('{"a"')


def test_generated_routes_point_only_to_real_partitions(tmp_path):
    build_web_data(sample_frame(), tmp_path)
    routes = json.loads((tmp_path / "routes.json").read_text(encoding="utf-8"))

    assert routes["routes"]
    assert all((tmp_path / route["file"]).exists() for route in routes["routes"])
    assert not any(route.get("measure") == "survival" for route in routes["routes"])


def test_manifest_has_bilingual_dimension_labels_and_schema(tmp_path):
    build_web_data(sample_frame(), tmp_path)
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["dimensions"]["cancers"]["LUNG"]["en"]
    assert manifest["dimensions"]["cancers"]["LUNG"]["pl"]
    assert manifest["dimensions"]["measures"]["incidence"] == {
        "en": "Incidence",
        "pl": "Zachorowalność",
    }
    assert manifest["partition_schema"]["rows"]


def test_each_partition_has_provenance_and_stays_within_budget(tmp_path):
    build_web_data(sample_frame(), tmp_path)
    routes = json.loads((tmp_path / "routes.json").read_text(encoding="utf-8"))

    for route in routes["routes"]:
        path = tmp_path / route["file"]
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["provenance"]["source_id"]
        assert payload["provenance"]["source_version"]
        assert payload["provenance"]["evidence_type"]
        assert path.stat().st_size <= MAX_PARTITION_BYTES


def test_starter_dataset_is_present_for_first_render(tmp_path):
    build_web_data(sample_frame(), tmp_path)
    starter = json.loads((tmp_path / "starter.json").read_text(encoding="utf-8"))

    assert starter["summary"]["records"] == 4
    assert starter["current"]
