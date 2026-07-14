import hashlib
import json
from pathlib import Path

import pytest

from cancer_explorer.sources import load_source_registry, write_source_manifest


@pytest.fixture()
def source_registry():
    return load_source_registry()


def test_required_sources_are_registered(source_registry):
    required = {
        "who_mortality",
        "who_ghe",
        "gbd_2023",
        "iarc_globocan_2024",
        "iarc_cancer_tomorrow",
        "iarc_ci5plus",
        "ecis",
        "krn",
        "uk_cancer",
        "redecan",
        "seer",
    }

    assert required <= set(source_registry)


def test_every_source_has_complete_provenance(source_registry):
    required_fields = {
        "id",
        "publisher",
        "title",
        "url",
        "version",
        "retrieved_at",
        "evidence_type",
        "licence",
        "geographies",
        "notes",
    }

    for source in source_registry.values():
        assert required_fields <= set(source.model_dump())
        assert source.id
        assert str(source.url).startswith("https://")


def test_manifest_records_checksum_and_size(tmp_path: Path, source_registry):
    raw_file = tmp_path / "sample.csv"
    raw_file.write_bytes(b"country,value\nPOL,1\n")
    output = tmp_path / "manifest.json"

    result = write_source_manifest(
        source_registry["who_mortality"], raw_file, output
    )

    assert result["sha256"] == hashlib.sha256(raw_file.read_bytes()).hexdigest()
    assert result["bytes"] == raw_file.stat().st_size
    assert json.loads(output.read_text(encoding="utf-8")) == result
