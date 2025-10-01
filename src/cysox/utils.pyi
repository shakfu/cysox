# Type stubs for cysox.utils

def lib_version(major: int, minor: int, patch: int) -> int:
    """Compute a 32-bit integer API version from three 8-bit parts."""
    ...

def lib_version_code() -> int:
    """Get the current libSoX version code."""
    ...

def int_min(bits: int) -> int:
    """Returns the smallest (negative) value storable in a twos-complement signed integer."""
    ...

def int_max(bits: int) -> int:
    """Returns the largest (positive) value storable in a twos-complement signed integer."""
    ...

def uint_max(bits: int) -> int:
    """Returns the largest value storable in an unsigned integer."""
    ...
