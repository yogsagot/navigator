"""Map a PEP 440 version onto the Debian and RPM version strings.

Python, Debian and RPM all order versions, and they do not agree, so a release
that is a pre-release in one has to be *written* differently in the others or
it sorts on the wrong side of the final release.  Getting this wrong is quiet:
the package builds, installs, and then strands everybody who took the
pre-release, because ``apt`` sees no upgrade to offer them.

Debian's rule is that ``~`` sorts before everything, including the end of the
string, so a suffix that must precede the release gets one.  Two suffixes that
must sort *among themselves* need more care, and that is the trap:

    1.0.0.dev5   ->  1.0.0~~dev5      not 1.0.0~dev5
    1.0.0a1      ->  1.0.0~a1
    1.0.0rc1     ->  1.0.0~rc1
    1.0.0        ->  1.0.0
    1.0.0.post1  ->  1.0.0.post1

PEP 440 orders ``dev`` before ``a``, but ``~dev5`` sorts *after* ``~a1`` --
they are compared past the tilde, where ``a`` < ``d``.  The second tilde puts
``dev`` back where it belongs, because nothing sorts before ``~``.  ``.post``
needs no tilde at all: end-of-string already sorts before ``.``.

RPM has understood ``~`` the same way since 4.10, so one mapped string serves
both formats -- which is what lets a single nfpm config build the pair.  RPM's
one extra rule is that ``-`` may not appear in a version, being its own
Version/Release separator; the mapping never emits one.
"""

from __future__ import annotations

import argparse
import sys

from packaging.version import InvalidVersion, Version


def to_native(version: str) -> str:
    """Rewrite a PEP 440 version so Debian and RPM order it as Python does."""
    parsed = Version(version)

    # `release' is the numeric part every version has: 1.0.0 -> (1, 0, 0).
    out = ".".join(str(n) for n in parsed.release)
    if parsed.epoch:
        # An epoch is a Debian and RPM concept too, but it is spelled in the
        # package metadata rather than here, and nfpm has its own field.
        raise ValueError(f"epochs are set in nfpm.yaml, not in the version: {version}")

    # Order matters: dev sorts before pre-release, which sorts before the
    # release itself.  Both get a tilde; dev gets two so that it also sorts
    # before the pre-release's tilde.
    if parsed.dev is not None:
        out += f"~~dev{parsed.dev}"
    if parsed.pre is not None:
        letters, number = parsed.pre
        out += f"~{letters}{number}"
    # A post-release follows the release, and `.' already sorts after the end
    # of the string in both schemes, so it is written plainly.
    if parsed.post is not None:
        out += f".post{parsed.post}"
    if parsed.local is not None:
        # `+' is legal in both, and both treat it as an ordinary separator.
        out += f"+{parsed.local}"
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="native_version.py", description=__doc__.splitlines()[0],
    )
    parser.add_argument("version", help="a PEP 440 version, e.g. 1.0.0rc1")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        print(to_native(args.version))
    except (InvalidVersion, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
