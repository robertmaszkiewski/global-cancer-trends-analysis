from pathlib import Path

import nbformat


ROOT = Path(__file__).parents[1]
NOTEBOOK = ROOT / "notebooks" / "global_cancer_trends.ipynb"


def load_notebook():
    return nbformat.read(NOTEBOOK, as_version=4)


def test_notebook_contains_required_analysis_sections():
    markdown = "\n".join(
        "".join(cell.source) for cell in load_notebook().cells if cell.cell_type == "markdown"
    )
    required = [
        "Ask", "Source inventory", "Data quality", "Global burden", "Cancer types",
        "Age", "Sex", "Countries", "Risks", "Projections", "Caveats", "Export",
    ]

    assert all(section in markdown for section in required)


def test_notebook_uses_package_analysis_functions():
    code = "\n".join(
        "".join(cell.source) for cell in load_notebook().cells if cell.cell_type == "code"
    )

    assert "from cancer_explorer.analyse import" in code
    assert "rank_cancers(" in code
    assert "projection_change(" in code


def test_notebook_has_been_executed_without_cell_errors():
    notebook = load_notebook()
    code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]

    assert code_cells
    assert all(cell.execution_count is not None for cell in code_cells)
    assert not any(
        output.output_type == "error"
        for cell in code_cells
        for output in cell.get("outputs", [])
    )


def test_notebook_execution_artifact_is_deterministic():
    notebook = load_notebook()
    code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]

    assert all("execution" not in cell.metadata for cell in code_cells)
    assert not any(
        "AppData\\Local\\Temp\\ipykernel_" in "".join(output.get("text", []))
        for cell in code_cells
        for output in cell.get("outputs", [])
        if output.output_type == "stream"
    )


def test_notebook_exports_documentation_figures():
    figures = ROOT / "reports" / "figures"
    required = [
        "global_top_cancers.png",
        "historical_lung_mortality.png",
        "age_profile_lung.png",
        "projections_2050.png",
    ]

    assert all((figures / name).stat().st_size > 10_000 for name in required)
