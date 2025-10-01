# Version utility functions


def lib_version(major: int, minor: int, patch: int) -> int:
    """Compute a 32-bit integer API version from three 8-bit parts."""
    return ((major) << 16) + ((minor) << 8) + (patch)


def lib_version_code() -> int:
    """Get the current libSoX version code."""
    return lib_version(14, 4, 2)


def int_min(bits: int) -> int:
    """Returns the smallest (negative) value storable in a twos-complement signed
    integer with the specified number of bits, cast to an unsigned integer.

    for example, SOX_INT_MIN(8) = 0x80, SOX_INT_MIN(16) = 0x8000, etc.
    @param bits Size of value for which to calculate minimum.
    @returns the smallest (negative) value storable in a twos-complement signed
    integer with the specified number of bits, cast to an unsigned integer.
    """
    return 1 << ((bits) - 1)


def int_max(bits: int) -> int:
    """Returns the largest (positive) value storable in a twos-complement signed
    integer with the specified number of bits, cast to an unsigned integer.

    for example, SOX_INT_MAX(8) = 0x7F, SOX_INT_MAX(16) = 0x7FFF, etc.
    @param bits Size of value for which to calculate maximum.
    @returns the largest (positive) value storable in a twos-complement signed
    integer with the specified number of bits, cast to an unsigned integer.
    """
    return (-1 + 2**32) >> (33 - (bits))


def uint_max(bits: int) -> int:
    """Returns the largest value storable in an unsigned integer with the specified
    number of bits;

    for example, SOX_UINT_MAX(8) = 0xFF, SOX_UINT_MAX(16) = 0xFFFF, etc.
    @param bits Size of value for which to calculate maximum.
    @returns the largest value storable in an unsigned integer with the specified
    number of bits.
    """
    return int_min(bits) | int_max(bits)
