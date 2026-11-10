"""A press on a panel's title: DN's ``TTopView`` -- *Change drive* on its drive part, *Change directory* on the rest."""

from __future__ import annotations

import zipfile

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent, MouseClickEvent

from navigator.__main__ import Navigator


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "west").mkdir()
    (tmp_path / "east" / "deep").mkdir(parents=True)
    with zipfile.ZipFile(tmp_path / "west" / "a.zip", "w") as zipped:
        zipped.writestr("src/x.txt", "x")
    return tmp_path


def press_title(panel, at: str):
    """A left press on *panel*'s title: on its first path cell, or in its middle."""
    text = panel.title_text()
    start = panel.label_x(text)
    mark = panel.remembered_mark()
    first = start + 1 + (len(mark) + 1 if mark else 0)
    x = first if at == "drive" else start + len(text) - 3
    ox, oy = panel.offset()
    return MouseClickEvent(ox + panel.x + x, oy + panel.y, "left", "press")


def popup(app):
    from navml.widgets.menu.popup_menu import PopupMenu

    return next((c for c in app.root.children if isinstance(c, PopupMenu)), None)


def test_a_press_on_the_inactive_panels_root_opens_its_bookmarks(place):
    app = Navigator(place / "west", place / "east" / "deep", terminal=FakeTerminal(100, 30))
    seen = {}
    run_app(app, [lambda a: a.post_event(press_title(a.manager.right, "drive")), Until(lambda a: popup(a) is not None),
                  lambda a: seen.update(focused=a.manager.active_panel is a.manager.right), KeyEvent("escape")])
    assert seen["focused"]


def test_a_press_on_the_rest_opens_change_directory_for_that_panel(place):
    from navigator.widgets.tree.change_dir_dialog import ChangeDirDialog

    app = Navigator(place / "west", place / "east" / "deep", terminal=FakeTerminal(100, 30))
    seen = {}
    run_app(app, [lambda a: a.post_event(press_title(a.manager.right, "rest")),
                  Until(lambda a: isinstance(a.modal, ChangeDirDialog)),
                  lambda a: seen.update(at=a.modal.accept(), focused=a.manager.active_panel is a.manager.right),
                  KeyEvent("escape")])
    assert str(seen["at"]).endswith("deep") and seen["focused"]


def test_inside_an_archive_the_prefix_is_the_drive_part(place):
    app = Navigator(place / "west", place / "east", terminal=FakeTerminal(160, 30))
    seen = {}

    def on(name):
        def go(a):
            panel = a.manager.left
            panel.cursor = [e.name for e in panel.items].index(name)
        return go

    def parts(a):
        p = a.manager.left
        text = p.title_text()
        start = p.label_x(text)
        seen.update(first=p.title_part_at(start + 1, 0), last=p.title_part_at(start + len(text) - 3, 0),
                    off=p.title_part_at(1, 0), text=text)

    run_app(app, [on("a.zip"), KeyEvent("enter"), Until(lambda a: a.manager.left.location.outer is not None),
                  Until(lambda a: "src" in [e.name for e in a.manager.left.items]), on("src"), KeyEvent("enter"),
                  Until(lambda a: str(a.manager.left.location.path) == "/src"), lambda a: None, parts])
    assert seen["first"] == "drive" and seen["last"] == "directory" and seen["off"] is None, seen["text"]
