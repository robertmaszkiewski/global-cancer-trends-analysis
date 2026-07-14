"""Execute the cancer analysis notebook from a clean kernel and save outputs."""

from __future__ import annotations

from pathlib import Path

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).parents[1]
NOTEBOOK = ROOT / "notebooks" / "global_cancer_trends.ipynb"


def main() -> int:
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=240,
        kernel_name="python3",
        resources={"metadata": {"path": str(ROOT)}},
        allow_errors=False,
    )
    executed = client.execute(cwd=str(ROOT))
    nbformat.write(executed, NOTEBOOK)
    print(f"Executed {NOTEBOOK.relative_to(ROOT)} with {len(executed.cells)} cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
