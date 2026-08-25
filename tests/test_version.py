"""The declared version must agree everywhere it appears.

`pyproject.toml` and `cysox.__version__` are maintained by hand and nothing
else compares them, so they can drift silently: a release bumps one, the
package reports the other, and the wheel metadata disagrees with what
`cysox --version` prints.
"""

import re
from pathlib import Path

import pytest

import cysox

PROJECT_ROOT = Path(__file__).parent.parent
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
CHANGELOG = PROJECT_ROOT / "CHANGELOG.md"


def _pyproject_version() -> str:
    match = re.search(r'^version\s*=\s*"([^"]+)"', PYPROJECT.read_text(), re.MULTILINE)
    assert match, "no version found in pyproject.toml"
    return match.group(1)


def test_version_is_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", cysox.__version__), cysox.__version__


@pytest.mark.skipif(
    not PYPROJECT.exists(), reason="running against an installed wheel, not a checkout"
)
def test_package_version_matches_pyproject():
    assert cysox.__version__ == _pyproject_version()


@pytest.mark.skipif(
    not CHANGELOG.exists(), reason="running against an installed wheel, not a checkout"
)
def test_changelog_has_an_entry_for_this_version():
    """The current version must be a released heading, not still Unreleased."""
    headings = re.findall(r"^## \[([^\]]+)\]", CHANGELOG.read_text(), re.MULTILINE)
    assert cysox.__version__ in headings, (
        f"CHANGELOG.md has no '## [{cysox.__version__}]' section; found {headings[:5]}"
    )
