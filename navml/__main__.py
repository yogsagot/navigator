"""``python -m navml`` -- the markup toolchain's one command.

Argument parsing and printing, and nothing else: what a build *is* lives in
:mod:`navml.build`, so that the same work is reachable from a test without
going through a process.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from navml.build import build
from navml.errors import MarkupError

#: 0 clean, 1 a document whose generated half is out of date, 2 a document that
#: could not be compiled at all -- the three a build can honestly report.
OK, STALE, BROKEN = 0, 1, 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m navml",
        description="Generate the Python half of a .nml component.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    builder = commands.add_parser(
        "build", help="regenerate <stem>_nml.py and <stem>.pyi"
    )
    builder.add_argument(
        "paths",
        nargs="*",
        help="documents or directories; the installed navml package by default",
    )
    builder.add_argument(
        "--check",
        action="store_true",
        help="report markup that no longer matches its generated half",
    )
    builder.add_argument(
        "-v", "--verbose", action="store_true", help="name every file"
    )
    arguments = parser.parse_args(argv)

    try:
        report = build(arguments.paths, check_only=arguments.check)
    except MarkupError as error:
        print(error, file=sys.stderr)
        return BROKEN

    if arguments.check:
        for artefact in report.stale:
            print(
                f"{artefact.path.name}: stale from line {artefact.differs}, "
                f"regenerate with python -m navml build",
                file=sys.stderr,
            )
        if report.stale:
            return STALE
        print(f"{len(report.documents)} documents, all up to date")
        return OK

    for path in report.written:
        print(f"wrote {path}")
    if arguments.verbose:
        for path in report.unchanged:
            print(f"unchanged {path}")
    print(
        f"{len(report.documents)} documents, "
        f"{len(report.written)} files written"
    )
    return OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
