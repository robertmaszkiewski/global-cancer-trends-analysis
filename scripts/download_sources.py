"""Download registered open sources or document required manual exports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cancer_explorer.download import download_file, filename_from_url, sha256, source_availability
from cancer_explorer.sources import load_source_registry, write_source_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--discover", action="store_true")
    parser.add_argument("--verify-cache", action="store_true")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    registry = load_source_registry()
    availability = source_availability(registry)
    if args.discover:
        print(json.dumps(availability, indent=2))
        return 0

    selected = args.source or list(registry)
    manual_lines = ["# Manual source exports", ""]
    for source_id in selected:
        source = registry[source_id]
        source_dir = args.raw_dir / source_id
        if availability[source_id]["mode"] == "manual":
            manual_lines.extend(
                [f"## {source.title}", "", f"- Source: {source.url}", f"- Version: {source.version}", f"- Notes: {source.notes}", ""]
            )
            continue
        for source_url in source.download_urls:
            destination = source_dir / filename_from_url(str(source_url))
            if args.verify_cache:
                if not destination.exists():
                    raise SystemExit(f"Missing cached file: {destination}")
                print(f"OK {destination} {sha256(destination)}")
                continue
            downloaded = download_file(str(source_url), destination)
            write_source_manifest(
                source,
                downloaded,
                source_dir / "manifests" / f"{downloaded.name}.json",
            )
            print(f"Downloaded {downloaded}")

    manual_path = args.raw_dir / "MANUAL_DOWNLOADS.md"
    manual_path.write_text("\n".join(manual_lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
