import hashlib
import io
import zipfile
from pathlib import Path

import pytest

from cancer_explorer.download import DownloadError, download_file, source_availability
from cancer_explorer.sources import load_source_registry


class FakeResponse:
    def __init__(self, content: bytes, content_type: str = "application/zip"):
        self.content = content
        self.headers = {
            "content-type": content_type,
            "content-length": str(len(content)),
        }

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size=1024):
        for start in range(0, len(self.content), chunk_size):
            yield self.content[start : start + chunk_size]


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def get(self, *args, **kwargs):
        self.calls += 1
        return self.response


def zip_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("sample.csv", "country,value\nPOL,1\n")
    return buffer.getvalue()


def test_download_is_atomic_and_validates_zip(tmp_path: Path):
    destination = tmp_path / "source.zip"
    session = FakeSession(FakeResponse(zip_bytes()))

    result = download_file("https://example.test/source.zip", destination, session=session)

    assert result == destination
    assert zipfile.is_zipfile(destination)
    assert not destination.with_suffix(".zip.part").exists()


def test_valid_cached_file_avoids_network(tmp_path: Path):
    destination = tmp_path / "source.zip"
    payload = zip_bytes()
    destination.write_bytes(payload)
    session = FakeSession(FakeResponse(b"should not be used"))

    result = download_file(
        "https://example.test/source.zip",
        destination,
        expected_sha256=hashlib.sha256(payload).hexdigest(),
        session=session,
    )

    assert result == destination
    assert session.calls == 0


def test_html_error_page_is_not_saved_as_data(tmp_path: Path):
    destination = tmp_path / "source.zip"
    session = FakeSession(FakeResponse(b"<html>error</html>", "text/html"))

    with pytest.raises(DownloadError):
        download_file("https://example.test/source.zip", destination, session=session)

    assert not destination.exists()


def test_corrupt_zip_is_rejected_before_atomic_replace(tmp_path: Path):
    destination = tmp_path / "source.zip"
    session = FakeSession(FakeResponse(b"not a zip archive"))

    with pytest.raises(DownloadError):
        download_file("https://example.test/source.zip", destination, session=session)

    assert not destination.exists()


def test_source_discovery_distinguishes_automatic_and_manual_sources():
    availability = source_availability(load_source_registry())

    assert availability["who_mortality"]["mode"] == "automatic"
    assert availability["gbd_2023"]["mode"] == "manual"
