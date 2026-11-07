"""A command in a window of its own (``TerminalView`` in a ``TerminalWindow``):
the keys typed reach it, the window's size is its pty's, and closing the
window hangs it up -- a real child on a real pty, as ``test_process.py``'s."""

from __future__ import annotations

import os

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    return Navigator(tmp_path, tmp_path, terminal=FakeTerminal(100, 30))


def windows(a):
    from navigator.widgets.shell.terminal_window import TerminalWindow

    return [w for w in a.shell.desktop.windows() if isinstance(w, TerminalWindow)]


def running(a):
    found = windows(a)
    return bool(found) and found[0].view.busy


def test_the_keys_typed_reach_the_command(app, tmp_path):
    out = tmp_path / "typed.txt"

    def start(a):
        a.shell.run_in_window(f"cat > {out}", zoomed=True, modal=False)

    run_app(app, [start, Until(running, timeout=5),
                  KeyEvent("a", "a"), KeyEvent("b", "b"), KeyEvent("c", "c"), KeyEvent("enter"),
                  KeyEvent("d", ctrl=True),
                  Until(lambda a: not running(a), timeout=5)], timeout=15)
    assert out.read_text() == "abc\n"


def test_the_window_s_size_is_its_pty_s(app, tmp_path):
    out = tmp_path / "size.txt"
    seen = {}

    def start(a):
        a.shell.run_in_window(f"sleep 0.3; stty size > {out}", zoomed=True, modal=False)

    def look(a):
        view = windows(a)[0].view
        seen["view"] = (view.height, view.width)

    run_app(app, [start, Until(running, timeout=5), look, Until(lambda a: out.exists() and out.read_text(), timeout=5)],
            timeout=15)
    lines, columns = (int(n) for n in out.read_text().split())
    assert (lines, columns) == seen["view"]


def test_closing_the_window_hangs_the_command_up(app, monkeypatch):
    from navkit import process as process_module

    monkeypatch.setattr(process_module, "HANG_UP_GRACE", 0.2)
    seen = {}

    def start(a):
        a.shell.run_in_window("sleep 60", zoomed=True, modal=False)

    def close(a):
        window = windows(a)[0]
        seen["pid"] = window.view.process.pid
        window.close()

    def gone(a):
        try:
            os.kill(seen["pid"], 0)
        except ProcessLookupError:
            return True
        # Reaped from the loop (``WNOHANG``): a zombie until then counts as gone.
        try:
            pid, _ = os.waitpid(seen["pid"], os.WNOHANG)
        except ChildProcessError:
            return True
        return pid == seen["pid"]

    run_app(app, [start, Until(running, timeout=5), close, Until(gone, timeout=5)], timeout=15)
    assert seen["pid"] > 0
