"""Show exactly what the terminal sends while it is in Navigator's modes.

    ./venv/bin/python tools/keyprobe.py [--legacy] [--no-mouse]

Raw mode, SGR mouse tracking, bracketed paste and the kitty keyboard flags
Navigator pushes -- the same escapes :class:`navkit.terminal.Terminal` writes --
and then every read is printed as bytes and as what ``InputParser`` makes of
it.  Press ``q`` twice in a row to quit.

It exists for the questions only a real terminal can answer: whether a key the
terminal binds for itself (Ctrl+Shift+V, Shift+Insert) reaches the application
as a paste or as a key, and what changes when the kitty flags are not pushed
(``--legacy``) or the mouse is not tracked (``--no-mouse``).
"""

from __future__ import annotations

import argparse
import os
import select
import sys
import termios
import tty
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from navkit.terminal import (  # noqa: E402
    InputParser,
    KEYBOARD_OFF,
    KEYBOARD_ON,
    MOUSE_OFF,
    MOUSE_ON,
    PASTE_OFF,
    PASTE_ON,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--legacy", action="store_true", help="do not push the kitty keyboard flags")
    parser.add_argument("--no-mouse", action="store_true", help="do not turn mouse tracking on")
    args = parser.parse_args()

    on = PASTE_ON + ("" if args.no_mouse else MOUSE_ON) + ("" if args.legacy else KEYBOARD_ON)
    off = ("" if args.legacy else KEYBOARD_OFF) + ("" if args.no_mouse else MOUSE_OFF) + PASTE_OFF
    fd = sys.stdin.fileno()
    saved = termios.tcgetattr(fd)
    decoder = InputParser()
    quits = 0
    try:
        tty.setraw(fd)
        os.write(1, on.encode())
        os.write(1, b"Navigator's modes are on.  Press keys, paste, click; q twice quits.\r\n")
        while True:
            select.select([fd], [], [])
            data = os.read(fd, 4096)
            events = decoder.feed(data)
            names = ", ".join(repr(e) for e in events) or "(nothing yet)"
            os.write(1, f"{data!r}\r\n    -> {names}\r\n".encode())
            quits = quits + 1 if data == b"q" else 0
            if quits >= 2:
                break
    finally:
        os.write(1, off.encode())
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
