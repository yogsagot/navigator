"""Navigator on a real pseudo-terminal: what no fake terminal can show.

``nav --language he`` is run on a pty of a set size, and its own bytes are
read back: the alternate screen and ``CSI 8 l`` (the terminal told to
reorder nothing) before the first clear, a mirrored menu bar, and on the way
out ``CSI 8 h`` handing the terminal its bidi back.

Opt-in, being a real process with a real tty: ``NAVIGATOR_PTY_TESTS=1
./venv/bin/python -m pytest tests/test_pty_end_to_end.py``.  Linux and macOS
only (``pty.fork``).
"""

from __future__ import annotations

import fcntl
import os
import pty
import select
import signal
import struct
import sys
import termios
import time
from pathlib import Path

import pyte
import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("NAVIGATOR_PTY_TESTS") != "1",
    reason="a real pty and process: set NAVIGATOR_PTY_TESTS=1 to run",
)

ROOT = Path(__file__).resolve().parent.parent
COLUMNS, LINES = 100, 30
ALT_SCREEN_ON, CLEAR = b"\x1b[?1049h", b"\x1b[2J"
BIDI_EXPLICIT, BIDI_IMPLICIT = b"\x1b[8l", b"\x1b[8h"
#: The Hebrew catalogue's File menu.  The mirrored frame sends it laid out
#: for the screen, so its cells hold it in painted (reversed) order.
FILE_MENU = "קובץ"


class Session:
    """A child running Navigator on a pty, and everything it has written."""

    def __init__(self, argv: list[str], env: dict[str, str]) -> None:
        self.pid, self.fd = pty.fork()
        if self.pid == 0:  # the child: the pty is its tty now
            os.chdir(ROOT)
            os.execvpe(argv[0], argv, env)
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, struct.pack("HHHH", LINES, COLUMNS, 0, 0))
        self.output = b""

    def read_until(self, wanted, timeout: float = 15.0) -> bool:
        """Read until *wanted* (bytes, or a test of the output) holds, or time out."""
        test = wanted if callable(wanted) else (lambda out: wanted in out)
        deadline = time.monotonic() + timeout
        while not test(self.output):
            left = deadline - time.monotonic()
            if left <= 0:
                return False
            ready, _, _ = select.select([self.fd], [], [], min(left, 0.2))
            if ready:
                try:
                    chunk = os.read(self.fd, 65536)
                except OSError:  # the child is gone and the pty with it
                    return test(self.output)
                if not chunk:
                    return test(self.output)
                self.output += chunk
        return True

    def screen(self) -> list[str]:
        """What a terminal shows of the output so far, row by row (pyte, which
        reorders nothing: the cells as Navigator laid them out)."""
        screen = pyte.Screen(COLUMNS, LINES)
        pyte.ByteStream(screen).feed(self.output)
        return screen.display

    def send(self, data: bytes) -> None:
        os.write(self.fd, data)

    def wait(self, timeout: float = 10.0) -> int | None:
        """The child's exit status, reading what it still writes meanwhile."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
            if pid:
                self.read_until(lambda out: False, timeout=0.3)
                return os.waitstatus_to_exitcode(status)
            self.read_until(lambda out: False, timeout=0.2)
        return None

    def close(self) -> None:
        try:
            os.kill(self.pid, signal.SIGKILL)
            os.waitpid(self.pid, 0)
        except (ProcessLookupError, ChildProcessError):
            pass
        os.close(self.fd)


@pytest.fixture
def hebrew(tmp_path):
    """``nav --language he`` on a pty, over a directory of its own."""
    place = tmp_path / "files"
    place.mkdir()
    (place / "שלום.txt").write_text("x")
    (place / "plain.txt").write_text("y")
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith(("NAVKIT_", "KITTY_", "KONSOLE_", "TMUX", "STY", "MLTERM"))
    }
    env.update(TERM="xterm-256color", LANG="C.UTF-8", HOME=str(tmp_path), SHELL="/bin/sh",
               XDG_STATE_HOME=str(tmp_path / "state"), XDG_CONFIG_HOME=str(tmp_path / "config"))
    argv = [
        sys.executable, "-m", "navigator", "--language", "he",
        "--database", str(tmp_path / "nav.db"), "--config", str(tmp_path / "navigator.ini"),
        "--on-error", "crash", str(place), str(place),
    ]
    session = Session(argv, env)
    yield session
    session.close()


def test_hebrew_runs_mirrored_with_the_terminal_s_bidi_off_and_back(hebrew):
    painted = FILE_MENU[::-1]
    assert hebrew.read_until(lambda out: painted in hebrew.screen()[0]), "\n".join(hebrew.screen())
    out = hebrew.output
    # The terminal told to reorder nothing before anything is drawn: VTE keeps
    # the mode per line from when the line is made.
    assert out.index(ALT_SCREEN_ON) < out.index(BIDI_EXPLICIT) < out.index(CLEAR)
    # Mirrored: the menu's ≡ is the top row's last cell, the File menu just
    # left of it, where an unmirrored screen has them first.
    top = hebrew.screen()[0].rstrip()
    assert top.endswith("≡") and top.index(painted) > COLUMNS // 2, top

    hebrew.send(b"\x1bx")  # Alt+X: DN's quit, which asks first
    time.sleep(0.5)
    hebrew.send(b"\r")     # the dialog's default button: yes, quit
    assert hebrew.wait() == 0, hebrew.output[-2000:]
    tail = hebrew.output[hebrew.output.rindex(BIDI_EXPLICIT):]
    assert BIDI_IMPLICIT in tail  # the terminal's own bidi given back
