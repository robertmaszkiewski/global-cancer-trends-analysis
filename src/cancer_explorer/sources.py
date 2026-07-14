"""Source registry and file provenance helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import AnyHttpUrl, BaseModel, Field


class SourceDefinition(BaseModel):
    """Auditable metadata for one upstream dataset."""

    id: str
    publisher: str
    title: str
    url: AnyHttpUrl
    version: str
    retrieved_at: date
    evidence_type: list[Literal["observed", "modelled", "projected"]]
    licence: str
    geographies: list[str] = Field(min_length=1)
    notes: str
    download_urls: list[AnyHttpUrl] = Field(default_factory=list)
    manual: bool = False


DEFAULT_REGISTRY = Path(__file__).resolve().parents[2] / "config" / "sources.yml"


def load_source_registry(path: Path | str = DEFAULT_REGISTRY) -> dict[str, SourceDefinition]:
    """Load and validate the source registry, keyed by stable source id."""

    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    sources = [SourceDefinition.model_validate(item) for item in payload["sources"]]
    registry = {source.id: source for source in sources}
    if len(registry) != len(sources):
        raise ValueError("Source ids must be unique")
    return registry


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_source_manifest(
    source: SourceDefinition, raw_file: Path | str, output: Path | str
) -> dict[str, object]:
    """Write machine-readable provenance for a downloaded source file."""

    raw_path = Path(raw_file)
    output_path = Path(output)
    result: dict[str, object] = {
        "source": source.model_dump(mode="json"),
        "filename": raw_path.name,
        "bytes": raw_path.stat().st_size,
        "sha256": _sha256(raw_path),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result
