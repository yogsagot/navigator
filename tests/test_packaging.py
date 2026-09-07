"""The PEP 440 -> Debian/RPM version mapping.

This is tested against ``dpkg`` itself rather than against a table of expected
strings, because the property that matters is not what the mapping writes but
whether the package manager *orders* the result the way Python does.  A
mapping that looks right and sorts wrong is the failure mode -- it builds,
installs, and then silently offers no upgrade to whoever took the
pre-release.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

_SOURCE = Path(__file__).resolve().parent.parent / "packaging/linux/native_version.py"
_spec = importlib.util.spec_from_file_location("native_version", _SOURCE)
native_version = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(native_version)

to_native = native_version.to_native

#: PEP 440's own ordering, weakest first.  Everything below asserts that the
#: mapping preserves it.
ASCENDING = [
    "1.0.0.dev5",
    "1.0.0a1",
    "1.0.0b2",
    "1.0.0rc1",
    "1.0.0",
    "1.0.0.post1",
    "1.0.1",
]

needs_dpkg = pytest.mark.skipif(
    shutil.which("dpkg") is None, reason="dpkg is what does the comparing"
)


def compare(left: str, op: str, right: str) -> bool:
    return subprocess.run(
        ["dpkg", "--compare-versions", left, op, right], check=False
    ).returncode == 0


@pytest.mark.parametrize(
    "version,expected",
    [
        ("0.0.1", "0.0.1"),
        ("1.0.0", "1.0.0"),
        ("1.0.0a1", "1.0.0~a1"),
        ("1.0.0rc1", "1.0.0~rc1"),
        ("1.0.0.dev5", "1.0.0~~dev5"),
        ("1.0.0.post1", "1.0.0.post1"),
        ("1.0.0+g57ccd03", "1.0.0+g57ccd03"),
    ],
)
def test_the_mapping(version, expected):
    assert to_native(version) == expected


def test_no_hyphen_ever_appears():
    """RPM reads ``-`` as its Version/Release separator, so it cannot occur."""
    assert all("-" not in to_native(v) for v in ASCENDING)


@needs_dpkg
@pytest.mark.parametrize("index", range(len(ASCENDING) - 1))
def test_the_mapping_preserves_pep440_order(index):
    lower, higher = ASCENDING[index], ASCENDING[index + 1]
    assert compare(f"{to_native(lower)}-1", "lt", f"{to_native(higher)}-1"), (
        f"{lower} -> {to_native(lower)} does not sort below "
        f"{higher} -> {to_native(higher)}"
    )


@needs_dpkg
def test_a_single_tilde_would_get_dev_backwards():
    """Why ``.devN`` gets two tildes and not one.

    Past the tilde the comparison is ordinary, and ``a`` < ``d`` -- so the
    obvious ``1.0.0~dev5`` sorts *after* ``1.0.0~a1`` and inverts PEP 440.
    Nothing sorts before a second ``~``, which is what puts it back.
    """
    assert not compare("1.0.0~dev5-1", "lt", "1.0.0~a1-1")
    assert compare(to_native("1.0.0.dev5") + "-1", "lt", to_native("1.0.0a1") + "-1")


@needs_dpkg
def test_a_prerelease_sorts_below_its_release():
    """The one that strands users if it is wrong."""
    for pre in ("1.0.0.dev5", "1.0.0a1", "1.0.0b2", "1.0.0rc1"):
        assert compare(f"{to_native(pre)}-1", "lt", "1.0.0-1"), pre


def test_an_epoch_is_refused_rather_than_dropped():
    """Silently losing it would make the package sort below its predecessor."""
    with pytest.raises(ValueError):
        to_native("1!2.0.0")
