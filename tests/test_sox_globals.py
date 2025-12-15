from cysox import sox


# Test Globals class


def test_globals():
    """Test get_globals function"""
    g = sox.Globals()
    assert isinstance(g, sox.Globals)
    assert g.verbosity == 2
    assert g.repeatable == 0
    assert g.bufsiz == 8192
