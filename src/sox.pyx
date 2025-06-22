cimport sox


def version() -> str:
    """Returns version number string of libSoX, for example, 14.4.0."""
    return (<const char*>sox_version()).decode()


