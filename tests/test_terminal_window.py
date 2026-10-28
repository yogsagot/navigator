"""A command in a window of its own: ``&command``, Shift+Enter, Execute OS
command's *In a window* and a user menu item's ``<&`` (a departure; DN ran one
program at a time).

Each runs a real child on a real pty, as ``test_process.py`` does, and waits
on what it prints or on its end rather than on a timer.
"""

from __future__ import annotations

import os

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.config.usermenu import commands_of
from navigator.settings import SETTINGS


def make(tmp_path, monkeypatch, width=80, height=24):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr("navigator.lib.system.tempdir.private_dir", lambda: tmp_path / "private")
    (tmp_path / "private").mkdir(exist_ok=True)
    return Navigator(tmp_path, tmp_path, terminal=FakeTerminal(width, height))


@pytest.fixture
def app(tmp_path, monkeypatch):
    return make(tmp_path, monkeypatch)


def terminal(app):
    from navigator.widgets.shell.terminal_window import TerminalWindow

    return next((w for w in app.shell.desktop.windows() if isinstance(w, TerminalWindow)), None)


def text(window) -> str:
    screen = window.view.screen
    surface = screen.surface
    return "\n".join("".join(surface.get(x, y)[0] or " " for x in range(screen.columns)).rstrip()
                     for y in range(screen.lines))


def ended(a) -> bool:
    window = terminal(a)
    return window is not None and window.view.status is not None


def showing(needle):
    return Until(lambda a: terminal(a) is not None and needle in text(terminal(a)))


def run(command):
    return lambda a: a.shell.run_command(command)


def test_an_ampersand_runs_the_line_in_a_window_that_stays_with_its_status(app):
    seen = {}

    def look(a):
        window = terminal(a)
        seen.update(text=text(window), title=window.title, zoomed=window.zoomed,
                    console=a.shell.console_visible, line=a.shell.command_line.value,
                    status=os.waitstatus_to_exitcode(window.view.status))

    run_app(app, [lambda a: a.shell.command_line.set_text("&printf hi; exit 3"), KeyEvent("enter"),
                  Until(ended), look, KeyEvent("escape"), lambda a: seen.update(gone=terminal(a) is None)])
    assert "hi" in seen["text"] and seen["status"] == 3
    assert seen["title"] == "printf hi; exit 3 - exit status 3"
    assert seen["zoomed"] and not seen["console"] and seen["line"] == ""
    assert seen["gone"]


def test_shift_enter_runs_the_line_in_a_window(app):
    run_app(app, [lambda a: a.shell.command_line.set_text("echo from-shift"), KeyEvent("enter", shift=True),
                  showing("from-shift")])
    assert terminal(app) is not None and terminal(app).command == "echo from-shift"


def test_closing_the_window_hangs_the_command_up(app):
    seen = {}

    def close(a):
        window = terminal(a)
        seen["process"] = window.view.process
        window.request_close()

    run_app(app, [run("&sleep 100"), Until(lambda a: terminal(a) is not None and terminal(a).view.busy),
                  close, Until(asking_to_close), KeyEvent("enter"),
                  Until(lambda a: seen["process"].status is not None)])
    assert terminal(app) is None
    with pytest.raises(ProcessLookupError):
        os.kill(seen["process"].pid, 0)


def asking_to_close(a) -> bool:
    return a.modal is not None and getattr(a.modal, "title", "") == "Close command window"


def running(a) -> bool:
    return terminal(a) is not None and terminal(a).view.busy


def test_no_keeps_a_running_command_and_its_window(app):
    seen = {}

    def look(a):
        seen.update(window=terminal(a), busy=terminal(a).view.busy, prompt=None)

    run_app(app, [run("&sleep 100"), Until(running), lambda a: terminal(a).request_close(),
                  Until(asking_to_close), lambda a: seen.update(prompt=a.modal.prompt),
                  KeyEvent("escape"), Until(lambda a: a.modal is None), look,
                  lambda a: terminal(a).view.stop()])
    assert seen["window"] is not None and seen["busy"]


def test_the_question_is_asked_only_while_the_command_runs_and_can_be_turned_off(app):
    seen = {}
    SETTINGS.confirmations.close_command_window = False
    try:
        run_app(app, [run("&sleep 100"), Until(running),
                      lambda a: seen.update(asks=terminal(a).must_ask()),
                      lambda a: terminal(a).request_close(), lambda a: None,
                      lambda a: seen.update(gone=terminal(a) is None, modal=a.modal)])
    finally:
        SETTINGS.confirmations.close_command_window = True
    assert not seen["asks"] and seen["gone"] and seen["modal"] is None


def test_alt_x_asks_about_a_running_command_too(app):
    seen = {}
    SETTINGS.confirmations.exit = False
    try:
        run_app(app, [run("&sleep 100"), Until(running),
                      lambda a: a.shell.desktop.activate(a.manager),
                      KeyEvent("x", alt=True), Until(asking_to_close),
                      KeyEvent("escape"), Until(lambda a: a.modal is None),
                      lambda a: seen.update(kept=terminal(a) is not None and terminal(a).view.busy,
                                            running=a.is_running),
                      lambda a: terminal(a).view.stop()])
    finally:
        SETTINGS.confirmations.exit = True
    assert seen["kept"] and seen["running"]


def test_a_command_that_ignores_the_hang_up_is_killed(app, monkeypatch):
    monkeypatch.setattr("navkit.process.HANG_UP_GRACE", 0.2)
    seen = {}

    def close(a):
        seen["process"] = terminal(a).view.process
        terminal(a).request_close()

    run_app(app, [run("&trap '' HUP; echo ready; sleep 100"), showing("ready"),
                  close, Until(asking_to_close), KeyEvent("enter"),
                  Until(lambda a: seen["process"].status is not None)])
    assert os.WTERMSIG(seen["process"].status) == 9


def test_every_key_but_the_window_keys_goes_to_the_program(app):
    seen = {}

    def look(a):
        seen.update(menu=a.modal is None, console=a.shell.console_visible, active=a.shell.desktop.active_window)

    run_app(app, [run("&cat"), Until(lambda a: terminal(a) is not None and terminal(a).view.busy),
                  KeyEvent("q", "q"), showing("q"),
                  KeyEvent("f10"), KeyEvent("o", ctrl=True), lambda a: None, look,
                  KeyEvent("f1", alt=True, shift=True), lambda a: None,
                  lambda a: seen.update(switched=a.shell.desktop.active_window)])
    assert seen["menu"] and not seen["console"] and seen["active"] is terminal(app)
    assert seen["switched"] is app.manager


def test_a_modal_window_holds_every_key(app):
    seen = {}

    def look(a):
        seen.update(modal=a.modal is terminal(a), active=a.shell.desktop.active_window is terminal(a))

    run_app(app, [lambda a: a.shell.run_in_window("cat", modal=True),
                  Until(lambda a: terminal(a) is not None and terminal(a).view.busy),
                  KeyEvent("f1", alt=True, shift=True), lambda a: None, look])
    assert seen["modal"] and seen["active"]


def test_a_window_not_zoomed_is_a_terminal_s_size_and_the_pty_is_told(tmp_path, monkeypatch):
    app = make(tmp_path, monkeypatch, 120, 40)
    seen = {}
    run_app(app, [lambda a: a.shell.run_in_window("stty size", zoomed=False), Until(ended),
                  lambda a: seen.update(rect=(terminal(a).width, terminal(a).height), text=text(terminal(a)),
                                        zoomed=terminal(a).zoomed)])
    assert seen["rect"] == (82, 26) and not seen["zoomed"]
    assert "24 80" in seen["text"]


def test_execute_os_command_in_a_window(app):
    from navigator.widgets.shell.commands import ExecuteOsCommand

    def asking(a):
        return a.modal is not None and a.modal.title == "Execute OS Command"

    def tick(a):
        a.modal.line.value = "echo boxed"
        a.modal.options.value = 1  # In a window, neither zoomed nor modal

    run_app(app, [lambda a: a.spawn(a.run_command(ExecuteOsCommand)), Until(asking), tick,
                  KeyEvent("enter"), showing("boxed")])
    assert not terminal(app).zoomed and not terminal(app).modal


def test_a_menu_item_with_its_window_line_runs_there_in_a_script_of_its_own(app, tmp_path):
    seen = {}

    def look(a):
        window = terminal(a)
        seen.update(title=window.title, zoomed=window.zoomed, modal=window.modal,
                    scripts=sorted(p.name for p in (tmp_path / "private").glob("usermenu*.sh")))

    commands = commands_of(["<& normal modal", "echo from-menu"])
    run_app(app, [lambda a: a.spawn(a.shell.run_commands(commands)), showing("from-menu"), Until(ended), look,
                  KeyEvent("escape"), lambda a: seen.update(
                      left=sorted(p.name for p in (tmp_path / "private").glob("usermenu*.sh")))])
    assert seen["title"].startswith("echo from-menu - ")
    assert not seen["zoomed"] and seen["modal"]
    assert seen["scripts"] == ["usermenu-1.sh"] and seen["left"] == []


def test_the_settings_say_how_a_window_opens(app):
    SETTINGS.system.command_window_zoomed = False
    SETTINGS.system.command_window_modal = True
    try:
        run_app(app, [run("&echo set"), showing("set")])
        assert not terminal(app).zoomed and terminal(app).modal
    finally:
        SETTINGS.system.command_window_zoomed = True
        SETTINGS.system.command_window_modal = False
