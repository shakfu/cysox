"""Parameter checks shared by the typed effect classes.

These exist so a mistake surfaces as a `ValueError` naming the parameter at
construction time, rather than as a libsox diagnostic on stderr -- or, worse,
as an output file that is quietly wrong.

Only unambiguous constraints are enforced: a filter cutoff cannot be negative,
a tempo factor cannot be zero, a percentage is 0-100. Anything that is merely
unusual (a 40 dB boost, a 500% reverb-sounding value that sox happens to
accept) is left alone -- these classes validate, they do not editorialise.
"""

from typing import Optional


def positive(value: float, name: str) -> float:
    """Require a strictly positive number."""
    if value <= 0:
        raise ValueError(f"{name} must be greater than 0, got {value!r}")
    return value


def non_negative(value: float, name: str) -> float:
    """Require zero or greater."""
    if value < 0:
        raise ValueError(f"{name} must be 0 or greater, got {value!r}")
    return value


def percent(value: float, name: str) -> float:
    """Require a percentage in 0-100."""
    if not 0 <= value <= 100:
        raise ValueError(f"{name} must be between 0 and 100, got {value!r}")
    return value


def in_range(
    value: float, low: float, high: float, name: str, unit: Optional[str] = None
) -> float:
    """Require low <= value <= high."""
    if not low <= value <= high:
        suffix = f" {unit}" if unit else ""
        raise ValueError(
            f"{name} must be between {low}{suffix} and {high}{suffix}, got {value!r}"
        )
    return value


def at_most(value: float, high: float, name: str) -> float:
    """Require value <= high."""
    if value > high:
        raise ValueError(f"{name} must be {high} or less, got {value!r}")
    return value
