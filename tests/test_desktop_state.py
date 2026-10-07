"""Options > Save/Load desktop and Startup's *Autosave desktop* (``SaveDesktop``, ``RetrieveDesktop``)."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator import desktop_state
from navigator.__main__ import Navigator
from navigator.settings import SETTINGS
from navigator.widgets.manager.manager import Manager


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    SETTINGS.interface.store_editor_position = False
    for name in ("one", "two"):
        (tmp_path / name).mkdir()
    (tmp_path / "one" / "a.txt").write_text("hello\n")
    (tmp_path / "one" / "b.txt").write_text("b\n")
    return tmp_path


def navigator(place: Path, **kwargs) -> Navigator:
    return Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30), **kwargs)


def kinds(app) -> list[str]:
    return [type(w).__name__ for w in app.shell.desktop.windows()]


def arrange(a):
    """A desktop worth keeping: a manager in a state, a tree window and the calculator."""
    from navigator.widgets.shell.calculator_window import CalculatorWindow
    from navigator.widgets.tree.tree_window import TreeWindow

    left = a.manager.left
    left.view_mode = "detailed"
    left.sort_by("size")
    left.set_file_mask("*.txt")
    a.manager.right.focus()
    a.manager.switch_view(a.manager.info)
    a.shell.desktop.open(TreeWindow(start=a.manager.right.path))
    calc = a.shell.desktop.open(CalculatorWindow())
    calc.line.value = "6*7"


def cursor_on_b(a):
    """After the re-reads the sort and the mask asked for have landed."""
    left = a.manager.left
    left.cursor = [e.name for e in left.items].index("b.txt")


def test_save_then_load_brings_the_windows_and_their_state_back(place):
    from navigator.widgets.shell.commands import LoadDesktop, SaveDesktop

    app = navigator(place)
    seen = {}

    def close_all(a):
        for window in list(a.shell.desktop.windows()):
            window.close()

    def look(a):
        manager = next(w for w in a.shell.desktop.windows() if isinstance(w, Manager))
        left = manager.left
        seen.update(kinds=kinds(a), left=(left.path, left.view_mode, left.sort_mode, left.file_mask,
                                         left.selected.name if left.selected else None),
                    replaced=manager.replacement is manager.info and manager.replaced is manager.left,
                    calc=a.shell.desktop.windows()[-1].line.value)

    run_app(app, [arrange, lambda a: None, lambda a: None, cursor_on_b, lambda a: None,
                  lambda a: a.spawn(a.run_command(SaveDesktop)),
                  lambda a: None, close_all, lambda a: None,
                  lambda a: a.spawn(a.run_command(LoadDesktop)),
                  Until(lambda a: len(a.shell.desktop.windows()) == 3), lambda a: None, lambda a: None, look])
    assert seen["kinds"] == ["Manager", "TreeWindow", "CalculatorWindow"]
    assert seen["left"] == (place / "one", "detailed", "size", "*.txt", "b.txt")
    assert seen["replaced"] and seen["calc"] == "6*7"


def test_an_editor_comes_back_on_its_file(place):
    from navigator.widgets.editor.edit_window import EditWindow

    async def open_one(a):
        from navigator.file_history import open_editor

        await open_editor(a.shell.desktop, place / "one" / "a.txt")

    app = navigator(place)
    seen = {}

    async def round_trip(a):
        data = desktop_state.snapshot(a.shell.desktop)
        for window in list(a.shell.desktop.windows()):
            window.close()
        await desktop_state.restore(a.shell.desktop, data)
        editor = next(w for w in a.shell.desktop.windows() if isinstance(w, EditWindow))
        seen.update(path=editor.editor.path, front=a.shell.desktop.active_window is editor)

    run_app(app, [lambda a: a.spawn(open_one(a)), Until(lambda a: "EditWindow" in kinds(a)),
                  lambda a: a.spawn(round_trip(a)), Until(lambda a: "path" in seen)])
    assert seen == {"path": place / "one" / "a.txt", "front": True}


def test_load_with_nothing_saved_says_so(place):
    from navigator.widgets.shell.commands import LoadDesktop

    app = navigator(place)
    seen = {}
    run_app(app, [lambda a: a.spawn(a.run_command(LoadDesktop)), Until(lambda a: a.modal is not None),
                  lambda a: seen.update(prompt=a.modal.prompt), KeyEvent("enter")])
    assert seen["prompt"] == "No desktop has been saved"


def test_autosave_saves_on_exit_and_restores_at_the_next_start(place):
    SETTINGS.startup.autosave_desktop = True
    run_app(navigator(place), [arrange, lambda a: None, lambda a: None])
    second = navigator(place)
    seen = {}
    run_app(second, [Until(lambda a: len(a.shell.desktop.windows()) == 3), lambda a: None,
                     lambda a: seen.update(kinds=kinds(a), mode=next(
                         w for w in a.shell.desktop.windows() if isinstance(w, Manager)).left.view_mode)])
    assert seen["kinds"] == ["Manager", "TreeWindow", "CalculatorWindow"] and seen["mode"] == "detailed"


def test_without_autosave_nothing_is_saved_or_restored(place):
    run_app(navigator(place), [arrange, lambda a: None])
    assert desktop_state.load() is None
    desktop_state.save(navigator(place).shell.desktop)
    second = navigator(place)
    seen = {}
    run_app(second, [lambda a: None, lambda a: seen.update(kinds=kinds(a))])
    assert seen["kinds"] == ["Manager"]


def test_directories_on_the_command_line_win_over_the_first_managers(place):
    SETTINGS.startup.autosave_desktop = True
    run_app(navigator(place), [arrange, lambda a: None, lambda a: None])
    third = Navigator(place / "two", place / "two", terminal=FakeTerminal(100, 30), given=True)
    seen = {}

    def look(a):
        manager = next(w for w in a.shell.desktop.windows() if isinstance(w, Manager))
        seen.update(paths=(manager.left.path, manager.right.path), mode=manager.left.view_mode)

    run_app(third, [Until(lambda a: len(a.shell.desktop.windows()) == 3), lambda a: None, look])
    assert seen["paths"] == (place / "two", place / "two") and seen["mode"] == "detailed"
