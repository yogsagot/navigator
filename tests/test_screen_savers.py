"""≡ > Screen rest and Options > Configuration > Screen savers: DOS Navigator's
``InsertIdler``, its four savers (IDLERS.PAS) and ``TSaversDialog``."""

from __future__ import annotations

import random
import re
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent, MouseClickEvent
from navkit.screen import ScreenBuffer

from navigator import savers
from navigator.__main__ import Navigator
from navigator.settings import SETTINGS
from navigator.widgets.setup.savers_dialog import SaversDialog
from navigator.widgets.shell.commands import SaversSetup, ScreenRest
from navigator.widgets.shell.screen_saver import KINDS, ScreenSaver


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "hello.txt").write_text("hello\n")
    return tmp_path


def navigator(place: Path) -> Navigator:
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    app.saver_check_every = 0.01
    return app


def saver(app) -> ScreenSaver | None:
    return app.modal if isinstance(app.modal, ScreenSaver) else None


def test_screen_rest_with_none_selected_is_star_flight_until_a_key(place):
    app = navigator(place)
    seen = {}
    run_app(app, [lambda a: a.spawn(a.run_command(ScreenRest)), Until(lambda a: saver(a) is not None),
                  lambda a: seen.update(kind=saver(a).kind), KeyEvent("x", "x"),
                  Until(lambda a: a.modal is None)])
    assert seen["kind"] == "star_flight"
    assert app.shell.command_line.value == ""  # the key that ended it typed nothing


@pytest.mark.parametrize("kind", KINDS)
def test_every_saver_paints_a_screen_of_its_own(place, kind):
    app = navigator(place)
    seen = {}

    def start(a):
        a.spawn(ScreenSaver(kind, rng=random.Random(3)).execute(a))

    def look(a):
        buffer = ScreenBuffer(80, 24)
        a.root.render_tree(buffer)
        text = "".join(buffer.get(x, y)[0] or " " for y in range(24) for x in range(80))
        seen["text"] = text

    run_app(app, [start, Until(lambda a: saver(a) is not None), *[lambda a: None] * 15, look,
                  MouseClickEvent(3, 3, button="left", action="press"), Until(lambda a: a.modal is None)])
    text = seen["text"]
    if kind != "flash_light":
        assert "Menu" not in text  # nothing of the desktop shows through
    if kind == "blackness":
        assert text.strip() == ""
    elif kind == "clock":
        # HH:MM, its colon blank half of each second.
        assert re.fullmatch(r"\d\d[: ]\d\d", text.strip())
    elif kind == "star_flight":
        assert set(text) - {" "} <= set("·∙•♦☼") and text.strip()
    else:
        # The spot shows a little of what is underneath, and only a little.
        assert 0 < len(text.replace(" ", "")) < 200


def test_the_idle_time_calls_a_selected_saver(place, monkeypatch):
    monkeypatch.setitem(savers.DELAYS, "1", 0.05)
    SETTINGS.savers.selected = "blackness"
    app = navigator(place)
    seen = {}
    run_app(app, [Until(lambda a: saver(a) is not None), lambda a: seen.update(kind=saver(a).kind)])
    assert seen["kind"] == "blackness"


def test_never_and_no_selection_call_nothing(place, monkeypatch):
    monkeypatch.setitem(savers.DELAYS, "1", 0.01)
    SETTINGS.savers.selected = "clock"
    SETTINGS.savers.time = "never"
    app = navigator(place)
    seen = []
    run_app(app, [*[lambda a: None] * 6, lambda a: seen.append(a.modal)])
    SETTINGS.savers.selected, SETTINGS.savers.time = "", "1"
    app = navigator(place)
    run_app(app, [*[lambda a: None] * 6, lambda a: seen.append(a.modal)])
    assert seen == [None, None]


def test_the_mouse_corners(place):
    SETTINGS.savers.update({"selected": "clock", "time": "never", "mouse": True})
    app = navigator(place)
    run_app(app, [MouseClickEvent(79, 0, action="move"), Until(lambda a: saver(a) is not None),
                  KeyEvent("x", "x"), Until(lambda a: a.modal is None)])

    # In the bottom right corner, the idle time calls nothing.
    SETTINGS.savers.time = "1"
    app = navigator(place)
    seen = []
    run_app(app, [MouseClickEvent(79, 23, action="move"), lambda a: setattr(a, "_last_input", -1000.0),
                  *[lambda a: None] * 5, lambda a: seen.append(a.modal)])
    assert seen == [None]


def test_an_external_saver_runs_on_the_console(place):
    directory = savers.savers_dir()
    directory.mkdir(parents=True)
    program = directory / "matrix"
    program.write_text("#!/bin/sh\n")
    program.chmod(0o755)
    (directory / "notes.txt").write_text("not a program")
    assert savers.external() == ["matrix"]
    SETTINGS.savers.selected = "matrix"
    app = navigator(place)
    ran: list[str] = []

    def capture(a):
        a.shell.run_command = lambda command, typed=True: ran.append(command)

    run_app(app, [capture, lambda a: a.spawn(a.run_command(ScreenRest)), Until(lambda a: ran)])
    assert ran == [str(program)]


def test_the_dialog_adds_and_removes_and_saves(place):
    app = navigator(place)
    seen = {}

    def work(a):
        dialog = a.modal
        seen["available"] = list(dialog.offered.items)
        dialog.offered.cursor = 2  # Clock
        a.post_event(KeyEvent("a", alt=True))

    def more(a):
        dialog = a.modal
        dialog.offered.cursor = 3  # Blackness
        a.post_event(KeyEvent("a", alt=True))
        a.post_event(KeyEvent("a", alt=True))  # once only

    def drop_first(a):
        dialog = a.modal
        seen["both"] = list(dialog.chosen.items)
        dialog.chosen.cursor = 0
        a.post_event(KeyEvent("r", alt=True))
        dialog.time.value = 3
        dialog.mouse.value = 1

    run_app(app, [lambda a: a.spawn(a.run_command(SaversSetup)),
                  Until(lambda a: isinstance(a.modal, SaversDialog)), work, more, lambda a: None, drop_first,
                  lambda a: None, KeyEvent("k", alt=True), Until(lambda a: a.modal is None)])
    assert seen["available"][:4] == ["∙ Star flight", "∙ Flash-light", "∙ Clock", "∙ Blackness"]
    assert seen["both"] == ["∙ Clock", "∙ Blackness"]
    assert SETTINGS.savers.names() == ["blackness"]
    assert SETTINGS.savers.time == "5" and SETTINGS.savers.mouse
    assert "selected = blackness" in SETTINGS.path.read_text()
