"""Build a self-contained static cancer explorer for VPS deployment."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


SOURCE_DATA_MARKER = 'window.CANCER_DATA_BASE = "../data/web"'
PACKAGED_DATA_MARKER = 'window.CANCER_DATA_BASE = "./data"'


def _verify_inputs(site: Path, data: Path) -> None:
    required = [
        site / "index.html",
        site / "assets" / "js" / "app.js",
        data / "manifest.json",
        data / "routes.json",
        data / "starter.json",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Cannot package incomplete site: " + ", ".join(str(path) for path in missing))


def _verify_routes(data: Path) -> int:
    route_index = json.loads((data / "routes.json").read_text(encoding="utf-8"))
    routes = route_index.get("routes", [])
    missing = [route["file"] for route in routes if not (data / route["file"]).exists()]
    if missing:
        raise FileNotFoundError(f"Route index points to {len(missing)} missing partition(s)")
    return len(routes)


def package_site(project_root: Path, output: Path) -> Path:
    """Copy the site and lazy data routes into one deployment directory."""

    project_root = Path(project_root).resolve()
    output = Path(output).resolve()
    site = project_root / "site"
    data = project_root / "data" / "web"
    _verify_inputs(site, data)
    route_count = _verify_routes(data)

    if output == project_root or output in project_root.parents:
        raise ValueError("Output must not replace the project or one of its parents")

    staging = output.with_name(f".{output.name}.staging")
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(site, staging)
    shutil.copytree(data, staging / "data")

    index = staging / "index.html"
    html = index.read_text(encoding="utf-8")
    if SOURCE_DATA_MARKER not in html:
        raise ValueError("Site data-base marker is missing; packaging would produce a broken explorer")
    index.write_text(html.replace(SOURCE_DATA_MARKER, PACKAGED_DATA_MARKER), encoding="utf-8")

    file_count = sum(1 for path in staging.rglob("*") if path.is_file())
    total_bytes = sum(path.stat().st_size for path in staging.rglob("*") if path.is_file())
    (staging / "PACKAGE.json").write_text(
        json.dumps(
            {
                "format": "self-contained-static-site",
                "routes": route_count,
                "files": file_count,
                "bytes": total_bytes,
                "entrypoint": "index.html",
                "data_base": "./data",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (staging / ".nojekyll").touch()

    if output.exists():
        shutil.rmtree(output)
    staging.replace(output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.project_root.resolve()
    output = args.output.resolve() if args.output else root / "dist" / "cancer-explorer"
    packaged = package_site(root, output)
    print(packaged)


if __name__ == "__main__":
    main()
