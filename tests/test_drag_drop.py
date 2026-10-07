"""Dragging files out of a panel with the mouse: File Manager Setup's
*Drag-and-drop* (``fmoDragAndDrop``) and Confirmations' *Drag and drop*
(``cfMouseConfirm``) -- DN's ``CM_DragDropper``, ``DragMover``, ``CM_Dropped``."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent, MouseClickEvent

from navigator.__main__ import Navigator
from navigator.settings import SETTINGS
from navigator.widgets.file_ops.copy_dialog import CopyDialog
from navigator.widgets.manager.panel.drag import DragLabel


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    for name in ("a", "b"):
        (tmp_path / name).mkdir()
    for name in ("f1.txt", "f2.txt"):
        (tmp_path / "a" / name).write_text(name)
    (tmp_path / "a" / "sub").mkdir()
    SETTINGS.file_manager.drag_drop_columns = True
    return tmp_path


def navigator(place: Path) -> Navigator:
    return Navigator(place / "a", place / "b", terminal=FakeTerminal(80, 24))


def at(side: str, name: str | None = None):
    """Screen coordinates of *name*'s row in *side*'s panel, or of its empty middle."""
    def where(app):
        panel = getattr(app.manager, side)
        ox, oy = panel.offset()
        if name is None:
            row = len(panel.items) + 2
        else:
            row = [e.name for e in panel.items].index(name) - panel.scroll
        return ox + panel.x + 4, oy + panel.y + panel.inset + panel.header + row
    return where


def mouse(where, action: str, **kwargs):
    def act(app):
        x, y = where(app)
        app.post_event(MouseClickEvent(x, y, button="left", action=action, **kwargs))
    return act


def drag(source, target, *, shift: bool = False, seen: dict | None = None) -> list:
    def look(a):
        if seen is not None:
            seen["label"] = next((w.text for w in a.root.children if isinstance(w, DragLabel)), None)
    return [mouse(source, "press"), mouse(target, "move"), look, mouse(target, "release", shift=shift),
            lambda a: None]


def test_a_file_dragged_onto_the_other_panel_is_copied_there(place):
    seen = {}
    run_app(navigator(place), [*drag(at("left", "f1.txt"), at("right"), seen=seen),
                               Until(lambda a: (place / "b" / "f1.txt").exists())])
    assert seen["label"] == " f1.txt "
    assert (place / "a" / "f1.txt").exists()


def test_shift_at_the_release_moves(place):
    run_app(navigator(place), [*drag(at("left", "f1.txt"), at("right"), shift=True),
                               Until(lambda a: (place / "b" / "f1.txt").exists()
                                     and not (place / "a" / "f1.txt").exists())])


def test_a_tagged_row_carries_every_tagged_file(place):
    seen = {}

    def tag(a):
        a.manager.left.marked = frozenset({"f1.txt", "f2.txt"})

    run_app(navigator(place), [tag, *drag(at("left", "f2.txt"), at("right"), seen=seen),
                               Until(lambda a: (place / "b" / "f2.txt").exists()
                                     and (place / "b" / "f1.txt").exists())])
    assert seen["label"] == " 2 selected files "


def test_on_its_own_panel_only_a_directory_row_takes_a_drop(place):
    run_app(navigator(place), [*drag(at("left", "f1.txt"), at("left", "sub")),
                               Until(lambda a: (place / "a" / "sub" / "f1.txt").exists())])
    run_app(navigator(place), [*drag(at("left", "f2.txt"), at("left", "f1.txt")), lambda a: None])
    assert sorted(p.name for p in (place / "a").iterdir()) == ["f1.txt", "f2.txt", "sub"]


def test_a_directory_is_not_dropped_into_itself(place):
    run_app(navigator(place), [*drag(at("left", "sub"), at("left", "sub")), lambda a: None])
    assert list((place / "a" / "sub").iterdir()) == []


def test_without_the_box_a_press_and_move_drags_nothing(place):
    SETTINGS.file_manager.drag_drop_columns = False
    seen = {}
    run_app(navigator(place), [*drag(at("left", "f1.txt"), at("right"), seen=seen), lambda a: None])
    assert seen["label"] is None and not (place / "b" / "f1.txt").exists()


def test_the_confirmation_puts_up_the_copy_dialog_aimed_at_the_drop(place):
    SETTINGS.confirmations.drag_and_drop = True
    seen = {}
    run_app(navigator(place), [*drag(at("left", "f1.txt"), at("right")),
                               Until(lambda a: isinstance(a.modal, CopyDialog)),
                               lambda a: seen.update(target=a.modal.target.value), KeyEvent("enter"),
                               Until(lambda a: (place / "b" / "f1.txt").exists())])
    assert seen["target"] == str(place / "b" / "f1.txt")  # one file: its name, as F5's
