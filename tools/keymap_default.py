#!/usr/bin/env python3
"""Write ``navigator/assets/keymaps/keybindings_default.ini``: every command
of every key table at the key the code binds, as a set of keys the Key
bindings dialog's *Load* reads -- the way back to the defaults from a file,
and a list of everything that can be bound.

    ./venv/bin/python tools/keymap_default.py          # write it
    ./venv/bin/python tools/keymap_default.py --check  # exit 1 when it is stale

Stale means a command was added, renamed or rebound in the code; the test
suite runs ``--check``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from navigator.lib.config import keybindings  # noqa: E402
from navigator.__main__ import Navigator  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "navigator" / "assets" / "keymaps" / "keybindings_default.ini"

HEADER = (
    "Navigator key bindings: the defaults.",
    "",
    "Every command Navigator lets you bind, at the key it has out of the box:",
    "Ctrl+S saves, Ctrl+F finds, Ctrl+Z undoes and Ctrl+X/C/V are the clipboard",
    "in the editor; the panels, viewer and dialogs keep DOS Navigator's keys.",
    "A command with nothing after the '=' has no key by default (the editor's",
    "WordStar commands: keybindings_wordstar.ini binds them).",
    "",
    "Load it from Options > Configuration > Key bindings > Load to go back to",
    "the defaults, as Reset does. Written by tools/keymap_default.py.",
)


def text() -> str:
    return keybindings.render(keybindings.sections(Navigator), {}, HEADER)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 when the file is stale")
    args = parser.parse_args()
    wanted = text()
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != wanted:
            print(f"{OUT} is stale: run tools/keymap_default.py", file=sys.stderr)
            return 1
        return 0
    OUT.write_text(wanted, encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
