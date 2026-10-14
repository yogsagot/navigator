"""The terminal's title: ``user@host ~/dir — Navigator``, following the active panel."""

from __future__ import annotations

import io

import pytest

from conftest import FakeTerminal, run_app
from navkit.capabilities import TerminalInfo
from navkit.events import KeyEvent
from navkit.terminal import TITLE_POP, TITLE_PUSH, Terminal

from navigator.lib.system import title


@pytest.fixture
def host(monkeypatch, tmp_path):
    monkeypatch.setattr("getpass.getuser", lambda: "juris")
    monkeypatch.setattr("socket.gethostname", lambda: "server.example.com")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    title.user_host.cache_clear()
    yield tmp_path
    title.user_host.cache_clear()


def test_the_title_names_user_short_host_and_directory(host):
    assert title.window_title(host / "home" / "src") == "juris@server ~/src — Navigator"
    assert title.window_title(host / "home") == "juris@server ~ — Navigator"
    assert title.window_title(host / "homely") == f"juris@server {host}/homely — Navigator"
    assert title.window_title(None) == "juris@server — Navigator"


def test_the_shells_title_is_pushed_once_and_popped_at_the_end():
    out = io.StringIO()
    terminal = Terminal(input_stream=io.StringIO(), output_stream=out, info=TerminalInfo())
    terminal.start()
    terminal.set_title("one")
    terminal.set_title("one")
    terminal.set_title("two")
    terminal.flush()
    written = out.getvalue()
    assert written.count(TITLE_PUSH) == 1
    assert written.count("\x1b]0;one\x07") == 1 and "\x1b]0;two\x07" in written
    assert written.index(TITLE_PUSH) < written.index("\x1b]0;one")
    terminal.stop()
    assert out.getvalue().endswith(TITLE_POP)


def test_nothing_is_popped_when_nothing_was_pushed():
    out = io.StringIO()
    terminal = Terminal(input_stream=io.StringIO(), output_stream=out, info=TerminalInfo())
    terminal.start()
    terminal.stop()
    assert TITLE_POP not in out.getvalue()


@pytest.fixture
def nav(host, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr("navigator.widgets.shell.console.Console.start", lambda self, argv=None: None)
    (host / "left" / "inner").mkdir(parents=True)
    (host / "right").mkdir()
    return host


def test_the_title_follows_the_active_panel(nav):
    from navigator.__main__ import Navigator

    terminal = FakeTerminal(80, 24)
    app = Navigator(nav / "left", nav / "right", terminal=terminal)
    seen = []
    run_app(app, [
        lambda a: seen.append(terminal.title),
        KeyEvent("tab"), lambda a: None,
        lambda a: seen.append(terminal.title),
        lambda a: a.manager.active_panel.__setattr__("path", nav / "left" / "inner"),
        lambda a: None,
        lambda a: seen.append(terminal.title),
    ])
    assert seen == [
        f"juris@server {nav}/left — Navigator",
        f"juris@server {nav}/right — Navigator",
        f"juris@server {nav}/left/inner — Navigator",
    ]
