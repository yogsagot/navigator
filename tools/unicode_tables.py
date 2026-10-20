#!/usr/bin/env python3
"""Write the two tables behind the character table, ``navigator/assets/unicode/``.

    ./venv/bin/python tools/unicode_tables.py          # download and write them
    ./venv/bin/python tools/unicode_tables.py --check  # exit 1 when they are stale

Python's :mod:`unicodedata` names every character and gives its general
category, but it has no blocks -- *Box Drawing*, *Arrows* -- and it knows
nothing of the Private Use Area, where a Nerd Font keeps its icons.  So:

- ``Blocks.txt``, the Unicode Character Database's own file, verbatim, for
  :data:`UNICODE` -- pinned, not the running :mod:`unicodedata`'s version,
  because one file ships to every Python Navigator runs on and each has its
  own (3.12 has 15.0, 3.13 15.1, 3.14 16.0, 3.15 17.0).  It is the newest of
  them; on an older Python a block with nothing assigned yet is left out of
  the table (``unicode_table.block_categories``).
- ``nerdfont.txt``, from the nerd-fonts project's ``glyphnames.json`` at
  :data:`NERD_FONTS`: one line a codepoint, ``code<TAB>names``, the names its
  sets give it (``fa-folder``, ``custom-folder``), space-separated.

``--check`` needs no network: it says whether ``Blocks.txt`` is for
:data:`UNICODE` and that is no older than the :mod:`unicodedata` installed --
a Python newer than the pin knows characters no block names -- and whether
``nerdfont.txt`` is for :data:`NERD_FONTS`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import urllib.request
from collections import defaultdict
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "navigator" / "assets" / "unicode"

#: The nerd-fonts release whose glyph names are shipped.  Version 3 moved
#: Material Design out of the BMP, so names from 2.x would be wrong.
NERD_FONTS = "v3.4.0"

#: The Unicode version whose ``Blocks.txt`` is shipped: the newest any
#: supported Python's :mod:`unicodedata` is built from.  Raised when a new
#: Python is, which ``--check`` says.
UNICODE = "17.0.0"

BLOCKS_URL = "https://www.unicode.org/Public/{version}/ucd/Blocks.txt"
NERD_URL = "https://raw.githubusercontent.com/ryanoasis/nerd-fonts/{tag}/glyphnames.json"


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def nerd_table(names: dict) -> str:
    """``glyphnames.json`` as ``nerdfont.txt``'s lines."""
    by_code: dict[int, list[str]] = defaultdict(list)
    for name, entry in names.items():
        if name == "METADATA":
            continue
        by_code[int(entry["code"], 16)].append(name)
    lines = [f"# nerd-fonts {NERD_FONTS} glyphnames.json: code, then its names"]
    lines += [f"{code:x}\t{' '.join(sorted(by_code[code]))}" for code in sorted(by_code)]
    return "\n".join(lines) + "\n"


def blocks_version(text: str) -> str | None:
    found = re.match(r"# Blocks-(\d+\.\d+\.\d+)\.txt", text)
    return found.group(1) if found else None


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def check() -> int:
    stale = []
    blocks = ASSETS / "Blocks.txt"
    if not blocks.exists() or blocks_version(blocks.read_text(encoding="utf-8")) != UNICODE:
        stale.append(f"{blocks} is not for Unicode {UNICODE}")
    if _version(unicodedata.unidata_version) > _version(UNICODE):
        stale.append(f"this Python's unicodedata is Unicode {unicodedata.unidata_version}, "
                     f"newer than UNICODE ({UNICODE}): raise it")
    nerd = ASSETS / "nerdfont.txt"
    if not nerd.exists() or not nerd.read_text(encoding="utf-8").startswith(f"# nerd-fonts {NERD_FONTS} "):
        stale.append(f"{nerd} is not for nerd-fonts {NERD_FONTS}")
    for line in stale:
        print(line, file=sys.stderr)
    return 1 if stale else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="exit 1 when the tables are stale")
    args = parser.parse_args()
    if args.check:
        return check()
    ASSETS.mkdir(parents=True, exist_ok=True)
    blocks = fetch(BLOCKS_URL.format(version=UNICODE))
    (ASSETS / "Blocks.txt").write_bytes(blocks)
    names = json.loads(fetch(NERD_URL.format(tag=NERD_FONTS)))
    (ASSETS / "nerdfont.txt").write_text(nerd_table(names), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
