"""≡ > Trashcan on/off: DOS Navigator's ``TTrashCan`` (GAUGES.PAS) and
``cmHideShowTools`` -- files dropped on it are erased."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import MouseClickEvent
from navkit.screen import ScreenBuffer

from navigator import desktop_state
from navigator.__main__ import Navigator
from navigator.settings import SETTINGS
from navigator.widgets.file_ops.delete_dialog import DeleteDialog
from navigator.widgets.shell.commands import ToggleTrashCan


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    for name in ("a.txt", "b.txt"):
        (tmp_path / name).write_text(name)
    (tmp_path / "full").mkdir()
    (tmp_path / "full" / "inside.txt").write_text("x")
    return tmp_path


def navigator(place: Path) -> Navigator:
    return Navigator(place, place, terminal=FakeTerminal(80, 24))


def toggle(a):
    a.spawn(a.run_command(ToggleTrashCan))


def test_hidden_until_the_menu_shows_it_in_the_desktops_corner(place):
    app = navigator(place)
    seen = {}

    def look(a):
        trash, desktop = a.shell.trash, a.shell.desktop
        buffer = ScreenBuffer(80, 24)
        a.root.render_tree(buffer)
        rows = ["".join(buffer.get(x, y)[0] for x in range(trash.x, trash.x + 5))
                for y in range(trash.y, trash.y + 3)]
        seen.update(where=(trash.x, trash.y), corner=(desktop.x + desktop.width - 6, desktop.y + desktop.height - 4),
                    rows=rows, ticked=a.command_checked(ToggleTrashCan))

    run_app(app, [lambda a: seen.update(before=a.shell.trash.visible), toggle, lambda a: None, look])
    assert seen["before"] is False
    assert seen["where"] == seen["corner"] and seen["ticked"] is True
    assert seen["rows"] == ["╤╤╪╤╤", "Trash", "└┴┴┴┘"]


def test_the_mouse_drags_it_and_a_resize_keeps_its_distance_from_the_corner(place):
    app = navigator(place)
    seen = {}

    def drag(a):
        trash = a.shell.trash
        start = (trash.x + 1, trash.y + 1)
        a.post_event(MouseClickEvent(*start, button="left", action="press"))
        a.post_event(MouseClickEvent(start[0] - 10, start[1] - 5, button="left", action="move"))
        a.post_event(MouseClickEvent(start[0] - 10, start[1] - 5, button="left", action="release"))
        seen["start"] = (trash.x, trash.y)

    run_app(app, [toggle, lambda a: None, drag, lambda a: None,
                  lambda a: seen.update(moved=(a.shell.trash.x, a.shell.trash.y), gaps=(a.shell.trash.gap_x,
                                                                                         a.shell.trash.gap_y))])
    assert seen["moved"] == (seen["start"][0] - 10, seen["start"][1] - 5)
    assert seen["gaps"] == (11, 6)


def drop_on_trash(name: str):
    def act(a):
        panel = a.manager.left
        index = [e.name for e in panel.items].index(name)
        ox, oy = panel.offset()
        x, y = ox + panel.x + 4, oy + panel.y + panel.inset + panel.header + index - panel.scroll
        trash = a.shell.trash
        a.post_event(MouseClickEvent(x, y, button="left", action="press"))
        a.post_event(MouseClickEvent(trash.x + 2, trash.y + 1, button="left", action="move"))
        a.post_event(MouseClickEvent(trash.x + 2, trash.y + 1, button="left", action="release"))
    return act


def test_files_dropped_on_it_are_erased_without_a_question(place):
    SETTINGS.file_manager.drag_drop_columns = True
    app = navigator(place)
    run_app(app, [toggle, lambda a: None, drop_on_trash("a.txt"), Until(lambda a: not (place / "a.txt").exists()),
                  drop_on_trash("full"), Until(lambda a: not (place / "full").exists())])
    assert (place / "b.txt").exists() and app.modal is None


def test_the_drag_and_drop_confirmation_asks_first(place):
    SETTINGS.file_manager.drag_drop_columns = True
    SETTINGS.confirmations.drag_and_drop = True
    app = navigator(place)
    run_app(app, [toggle, lambda a: None, drop_on_trash("a.txt"),
                  Until(lambda a: isinstance(a.modal, DeleteDialog))])
    assert (place / "a.txt").exists()


def test_the_desktop_keeps_it(place):
    app = navigator(place)
    seen = {}

    def save(a):
        a.shell.trash.place(10, 5)
        seen["saved"] = desktop_state.snapshot(a.shell.desktop)["trash"]

    run_app(app, [toggle, lambda a: None, save])
    second = navigator(place)

    async def restore(a):
        await desktop_state.restore(a.shell.desktop, {"version": 1, "windows": [], "trash": seen["saved"]})

    run_app(second, [lambda a: a.spawn(restore(a)), lambda a: None,
                     lambda a: seen.update(back=(a.shell.trash.visible, a.shell.trash.x - a.shell.desktop.x,
                                                 a.shell.trash.y - a.shell.desktop.y))])
    assert seen["saved"]["shown"] is True and seen["back"] == (True, 10, 5)
