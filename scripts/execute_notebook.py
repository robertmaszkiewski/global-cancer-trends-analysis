"""Execute the cancer analysis notebook from a clean kernel and save outputs."""

from __future__ import annotations

import re
from pathlib import Path

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).parents[1]
NOTEBOOK = ROOT / "notebooks" / "global_cancer_trends.ipynb"


def normalise_execution_artifact(notebook):
    """Remove timestamps and machine-specific warnings from an executed notebook."""

    for cell in notebook.cells:
        cell.metadata.pop("execution", None)
        if cell.cell_type != "code":
            continue
        cleaned_outputs = []
        for output in cell.get("outputs", []):
            if output.output_type == "stream":
                text = "".join(output.get("text", []))
                if "FigureCanvasAgg is non-interactive" in text:
                    continue
                output["text"] = re.sub(
                    r"[A-Za-z]:\\[^\n]*?\\Temp\\ipykernel_\d+\\",
                    "<ipykernel>/",
                    text,
                )
            cleaned_outputs.append(output)
        cell["outputs"] = cleaned_outputs
    return notebook


def main() -> int:
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=240,
        kernel_name="python3",
        resources={"metadata": {"path": str(ROOT)}},
        allow_errors=False,
    )
    executed = normalise_execution_artifact(client.execute(cwd=str(ROOT)))
    nbformat.write(executed, NOTEBOOK)
    print(f"Executed {NOTEBOOK.relative_to(ROOT)} with {len(executed.cells)} cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
