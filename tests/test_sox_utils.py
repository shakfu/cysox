from cysox import utils


def test_utls_lib_version():
    assert utils.lib_version(14, 4, 2) == 918530


def test_utls_lib_version_code():
    assert utils.lib_version_code() == 918530


def test_utils_int_max():
    assert utils.int_max(8) == 127


def test_utils_int_min():
    assert utils.int_min(2) == 2


def test_utils_uint_max():
    assert utils.uint_max(10) == 1023
