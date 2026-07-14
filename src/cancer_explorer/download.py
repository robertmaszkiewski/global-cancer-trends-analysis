"""Safe and reproducible upstream file downloads."""

from __future__ import annotations

import hashlib
import html
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests

from cancer_explorer.sources import SourceDefinition


class DownloadError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_file(path: Path, content_type: str = "") -> None:
    if not path.exists() or path.stat().st_size == 0:
        raise DownloadError(f"Downloaded file is empty: {path.name}")
    prefix = path.read_bytes()[:128].lstrip().lower()
    if "html" in content_type.casefold() or prefix.startswith((b"<html", b"<!doctype html")):
        raise DownloadError(f"Upstream returned HTML instead of data: {path.name}")
    if path.name.casefold().endswith((".zip", ".zip.part")) and not zipfile.is_zipfile(path):
        raise DownloadError(f"Invalid ZIP archive: {path.name}")


def download_file(
    url: str,
    destination: Path | str,
    *,
    expected_sha256: str | None = None,
    session=None,
    retries: int = 3,
    timeout: int = 90,
) -> Path:
    """Download atomically and refuse error pages or corrupt archives."""

    destination = Path(destination)
    if destination.exists():
        try:
            _validate_file(destination)
            if expected_sha256 is None or sha256(destination) == expected_sha256:
                return destination
        except DownloadError:
            pass

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    client = session or requests.Session()
    last_error: Exception | None = None

    for _ in range(retries):
        try:
            response = client.get(url, stream=True, timeout=timeout)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            with temporary.open("wb") as handle:
                for block in response.iter_content(chunk_size=1024 * 1024):
                    if block:
                        handle.write(block)
            expected_length = response.headers.get("content-length")
            if expected_length and temporary.stat().st_size != int(expected_length):
                raise DownloadError(
                    f"Content length mismatch for {destination.name}: "
                    f"expected {expected_length}, received {temporary.stat().st_size}"
                )
            _validate_file(temporary, content_type)
            if expected_sha256 and sha256(temporary) != expected_sha256:
                raise DownloadError(f"Checksum mismatch for {destination.name}")
            temporary.replace(destination)
            return destination
        except Exception as exc:  # retries cover transport and validation failures
            last_error = exc
            temporary.unlink(missing_ok=True)

    raise DownloadError(f"Failed to download {url}: {last_error}") from last_error


def source_availability(
    registry: dict[str, SourceDefinition],
) -> dict[str, dict[str, object]]:
    return {
        source_id: {
            "mode": "automatic" if source.download_urls and not source.manual else "manual",
            "files": len(source.download_urls),
            "reason": "registered direct downloads"
            if source.download_urls and not source.manual
            else "interactive export, authentication, or manual licence step",
        }
        for source_id, source in registry.items()
    }


def filename_from_url(url: str) -> str:
    return unquote(Path(urlparse(html.unescape(url)).path).name)
