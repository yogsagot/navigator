"""Options > Configuration > Startup: *Auto run User Menu*, *Clear history*,
*Inactivity hour exit* and *Preserve directory* (``osuAutoMenu``,
``osuKillHistory``, ``osuInactivityExit``, ``osuPreserveDir``)."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app

from navigator.__main__ import Navigator, clear_histories
from navigator.models.view_record import ViewRecord
from navigator.settings import SETTINGS
from navml.history import HISTORY


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.delenv("DNIDLE", raising=False)
    for name in ("one", "two", "start"):
        (tmp_path / name).mkdir()
    return tmp_path


def navigator(left: Path, right: Path | None = None) -> Navigator:
    return Navigator(left, right or left, terminal=FakeTerminal(100, 30))


def test_auto_run_user_menu_opens_it_at_the_start(place):
    SETTINGS.startup.auto_user_menu = True
    seen = {}
    run_app(navigator(place / "one"), [Until(lambda a: getattr(a.modal, "title", None) == "Error"),
                                       lambda a: seen.update(prompt=a.modal.prompt)])
    assert seen["prompt"] == "File dn.mnu not found"

    SETTINGS.startup.auto_user_menu = False
    run_app(navigator(place / "one"), [lambda a: None, lambda a: seen.update(modal=a.modal)])
    assert seen["modal"] is None


def test_clear_history_keeps_what_is_pinned(place):
    HISTORY.add("command", "make")
    HISTORY.add("command", "ls")
    HISTORY.pin("command", "ls")
    ViewRecord.store(place / "a")
    ViewRecord.store(place / "b")
    ViewRecord.toggle_pin(str(place / "b"))
    clear_histories()
    assert HISTORY.entries("command") == ["ls"]
    assert [record.path for record in ViewRecord.ordered()] == [str(place / "b")]


def idle(app: Navigator) -> Navigator:
    app.idle_exit_after = 0.05
    app.idle_check_every = 0.01
    return app


def test_an_idle_hour_exits_only_with_the_box_ticked(place):
    seen = {}
    run_app(idle(navigator(place / "one")), [lambda a: None] * 8 + [lambda a: seen.update(running=a.is_running)])
    assert seen["running"]

    SETTINGS.startup.inactivity_exit = True
    run_app(idle(navigator(place / "one")), [Until(lambda a: not a.is_running)])


def test_dnidle_runs_in_place_of_the_exit(place, monkeypatch):
    SETTINGS.startup.inactivity_exit = True
    monkeypatch.setenv("DNIDLE", "screensaver")
    ran: list[str] = []
    seen = {}

    def capture(a):
        a.shell.run_command = lambda command, typed=True: ran.append(command)

    run_app(idle(navigator(place / "one")), [capture, Until(lambda a: ran),
                                             lambda a: seen.update(running=a.is_running)])
    assert ran[0] == "screensaver" and seen["running"]


def test_preserve_directory_keeps_the_panel_where_it_was_after_a_command(place):
    seen = {}

    def finish(a):
        a.shell.command_finished(0, place / "two")

    run_app(navigator(place / "one"), [finish, lambda a: seen.update(path=a.manager.left.path)])
    assert seen["path"] == place / "two"

    SETTINGS.startup.preserve_directory = True
    run_app(navigator(place / "one"), [finish, lambda a: seen.update(path=a.manager.left.path)])
    assert seen["path"] == place / "one"


def test_a_restored_desktops_active_panel_opens_in_the_start_directory_unless_preserved(place):
    from navigator.models.saved_desktop import SavedDesktop
    from navigator.widgets.manager.manager import Manager

    SETTINGS.startup.autosave_desktop = True
    seen = {}

    def save_one_and_two():
        SavedDesktop.query().delete()  # or the start restores the last one
        run_app(navigator(place / "one", place / "two"), [lambda a: a.manager.right.focus(), lambda a: None])

    def look(a):
        manager = next(w for w in a.shell.desktop.windows() if isinstance(w, Manager))
        seen["paths"] = (manager.left.path, manager.right.path)

    save_one_and_two()
    run_app(navigator(place / "start"), [lambda a: None, lambda a: None, look])
    assert seen["paths"] == (place / "one", place / "start")

    SETTINGS.startup.preserve_directory = True
    save_one_and_two()
    run_app(navigator(place / "start"), [lambda a: None, lambda a: None, look])
    assert seen["paths"] == (place / "one", place / "two")
