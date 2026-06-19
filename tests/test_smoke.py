import anchor


def test_version_present():
    assert isinstance(anchor.__version__, str)
    assert anchor.__version__.count(".") >= 2
