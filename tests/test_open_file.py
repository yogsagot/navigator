"""File > View > *Open...* and File > Edit > *Open...*: a file chosen in a
file box, viewed or edited (not DN's)."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.widgets.shell.commands import OpenEdit, OpenView
from navml.widgets.dialog.file_dialog import FileDialog


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "notes.txt").write_text("hello\n")
    return tmp_path


def opened(app, kind):
    """The viewer or editor in front, or None."""
    from navigator.widgets.editor.edit_window import EditWindow
    from navigator.widgets.viewer.file_window import FileWindow

    wanted = FileWindow if kind == "view" else EditWindow
    window = app.shell.desktop.active_window
    if not isinstance(window, wanted):
        return None
    return window.viewer if kind == "view" else window.editor


@pytest.mark.parametrize("command, kind", [(OpenView, "view"), (OpenEdit, "edit")])
def test_open_lists_the_panels_directory_and_opens_the_file_named(place, command, kind):
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    seen = {}

    def name_it(a):
        seen["directory"] = a.modal.directory
        seen["title"] = a.modal.title
        a.modal.target.value = "notes.txt"

    run_app(app, [lambda a: a.spawn(a.run_command(command)), Until(lambda a: isinstance(a.modal, FileDialog)),
                  name_it, KeyEvent("enter"), Until(lambda a: opened(a, kind) is not None),
                  lambda a: seen.update(path=opened(a, kind).path)])
    assert seen["directory"] == place
    assert seen["title"] == ("View file" if kind == "view" else "Edit file")
    assert seen["path"] == place / "notes.txt"


def test_open_to_edit_a_name_not_there_is_a_new_file(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    seen = {}

    def name_it(a):
        a.modal.target.value = "fresh.txt"

    run_app(app, [lambda a: a.spawn(a.run_command(OpenEdit)), Until(lambda a: isinstance(a.modal, FileDialog)),
                  name_it, KeyEvent("enter"), Until(lambda a: opened(a, "edit") is not None),
                  lambda a: seen.update(path=opened(a, "edit").path)])
    assert seen["path"] == place / "fresh.txt"
    assert not (place / "fresh.txt").exists()


@pytest.mark.parametrize("command, kind, variable", [(OpenView, "view", "PAGER"), (OpenEdit, "edit", "EDITOR")])
def test_with_the_internal_one_off_the_file_goes_to_the_environments_program(place, monkeypatch,
                                                                             command, kind, variable):
    from navigator.settings import SETTINGS

    setattr(SETTINGS.system, "internal_viewer" if kind == "view" else "internal_editor", False)
    monkeypatch.setenv(variable, "prog")
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    ran: list[str] = []

    def capture(a):
        a.shell.run_command = lambda line, typed=True: ran.append(line)

    def name_it(a):
        a.modal.target.value = "notes.txt"

    run_app(app, [capture, lambda a: a.spawn(a.run_command(command)), Until(lambda a: isinstance(a.modal, FileDialog)),
                  name_it, KeyEvent("enter"), Until(lambda a: ran)])
    assert ran == [f"prog {place}/notes.txt"]
    assert opened(app, kind) is None
