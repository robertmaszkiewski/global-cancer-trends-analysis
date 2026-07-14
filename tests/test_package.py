def test_package_exposes_version():
    import cancer_explorer

    assert cancer_explorer.__version__ == "0.1.0"
