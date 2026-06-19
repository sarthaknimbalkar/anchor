from anchor.matcher import normalize_path, glob_matches


def test_normalize_forward_slashes_and_absolute():
    out = normalize_path("sub/../.env", cwd="/home/proj")
    assert out == "/home/proj/.env"


def test_glob_doublestar_crosses_slashes():
    assert glob_matches("**/.env", "/home/proj/.env", case_insensitive=False)
    assert glob_matches("/etc/signalminer/**", "/etc/signalminer/app.env", case_insensitive=False)


def test_glob_case_insensitive_toggle():
    assert glob_matches("**/.ENV", "/p/.env", case_insensitive=True)
    assert not glob_matches("**/.ENV", "/p/.env", case_insensitive=False)
