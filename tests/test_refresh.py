"""≡ > Refresh display: ``cmRefresh``, the whole screen sent again."""

from __future__ import annotations

from conftest import FakeTerminal, run_app

from navigator.__main__ import Navigator
from navigator.commands import Refresh


def test_refresh_sends_every_cell_again_where_a_frame_would_send_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = {}

    def before(a):
        seen["first"] = len(a.terminal.frames[0])
        seen["count"] = len(a.terminal.frames)

    run_app(app, [lambda a: None, before, lambda a: a.invalidate(), lambda a: None,
                  lambda a: seen.update(idle=len(a.terminal.frames)),
                  lambda a: a.spawn(a.run_command(Refresh)), lambda a: None, lambda a: None,
                  lambda a: seen.update(after=a.terminal.frames[-1], total=len(a.terminal.frames))])
    assert seen["idle"] == seen["count"]  # an unchanged frame writes nothing
    assert seen["total"] == seen["count"] + 1
    assert len(seen["after"]) >= seen["first"] * 0.9


def test_alt_f5_shows_the_console_until_a_key_which_goes_nowhere(tmp_path, monkeypatch):
    from navkit.events import KeyEvent

    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    written = []
    monkeypatch.setattr("navigator.subshell.Subshell.write", lambda self, data: written.append(data))
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [KeyEvent("f5", alt=True), lambda a: None,
                  lambda a: seen.update(shown=a.shell.console_visible,
                                        console=a.focused is a.shell.console),
                  KeyEvent("x", "x"), lambda a: None,
                  lambda a: seen.update(back=a.shell.console_visible, panel=a.focused is a.manager.left,
                                        line=a.shell.command_line.value)])
    assert seen == {"shown": True, "console": False, "back": False, "panel": True, "line": ""}
    assert written == []
