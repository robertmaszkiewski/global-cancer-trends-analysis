from pathlib import Path

from cancer_explorer.package_site import package_site


def test_package_site_creates_self_contained_static_folder(tmp_path):
    project = tmp_path / "project"
    site = project / "site"
    web_data = project / "data" / "web"
    (site / "assets" / "js").mkdir(parents=True)
    (web_data / "partitions").mkdir(parents=True)
    (site / "index.html").write_text(
        '<script>window.CANCER_DATA_BASE = "../data/web";</script>', encoding="utf-8"
    )
    (site / "assets" / "js" / "app.js").write_text("export {};", encoding="utf-8")
    (web_data / "manifest.json").write_text('{"version":1}', encoding="utf-8")
    (web_data / "routes.json").write_text(
        '{"version":1,"routes":[{"file":"partitions/sample.json"}]}', encoding="utf-8"
    )
    (web_data / "starter.json").write_text('{"summary":{"records":0}}', encoding="utf-8")
    (web_data / "partitions" / "sample.json").write_text('{"rows":[]}', encoding="utf-8")

    output = package_site(project, tmp_path / "dist")

    assert (output / "index.html").exists()
    assert (output / "data" / "manifest.json").exists()
    assert (output / "data" / "partitions" / "sample.json").exists()
    assert 'window.CANCER_DATA_BASE = "./data"' in (output / "index.html").read_text(encoding="utf-8")


def test_package_site_refuses_incomplete_source(tmp_path):
    project = tmp_path / "project"
    project.mkdir()

    try:
        package_site(project, tmp_path / "dist")
    except FileNotFoundError as error:
        assert "site" in str(error)
    else:
        raise AssertionError("Incomplete source should not be packaged")
