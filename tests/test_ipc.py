from anchor.ipc import get_or_create_cookie, socket_address, state_dir


def test_cookie_is_stable_and_long(tmp_path):
    c1 = get_or_create_cookie(str(tmp_path))
    c2 = get_or_create_cookie(str(tmp_path))
    assert c1 == c2 and len(c1) >= 64


def test_state_dir_created(tmp_path):
    import os
    d = state_dir(str(tmp_path))
    assert os.path.isdir(d)


def test_socket_address_is_per_home(tmp_path):
    a = socket_address(str(tmp_path))
    b = socket_address(str(tmp_path / "other"))
    assert a != b
