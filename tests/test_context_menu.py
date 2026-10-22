"""Context menus: a right click, the Menu key and Shift+F10.

navkit's ``ContextMenuEvent`` (a right press offered again), navml's
``ContextMenu``/``ContextMenuHost`` and the right button in ``PopupMenu``, and
the hosts: the file panels (and File Manager Setup's *Right button*), input
lines, the editor, the viewer and the console.
"""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent, MouseClickEvent
from navkit.widget import Widget

from navigator.__main__ import Navigator
from navigator.settings import SETTINGS
from navml.widgets.dialog.control.control import parse_shortcut
from navml.widgets.menu.context_menu import ContextMenu
from navml.widgets.menu.menu_bar import MenuBar
from navml.widgets.menu.menu_item import MenuItem
from navml.widgets.menu.popup_menu import PopupMenu
from navml.widgets.menu.sub_menu import SubMenu


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """The panels' listing, rows 2 to 6 of the left one: ``..``, ``alpha``,
    ``beta``, ``one.txt``, ``two.txt``."""
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "alpha").mkdir()
    (tmp_path / "beta").mkdir()
    (tmp_path / "one.txt").write_text("one\ntwo\nthree\n")
    (tmp_path / "two.txt").write_text("y" * 20)
    return tmp_path


def navigator(path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def popup(app) -> PopupMenu | None:
    return next((child for child in app.root.children if isinstance(child, PopupMenu)), None)


OPEN = Until(lambda app: popup(app) is not None)
SHUT = Until(lambda app: popup(app) is None)


def captions(app) -> list[str]:
    return [parse_shortcut(entry.text)[0] for entry in popup(app).box.entries()
            if isinstance(entry, (MenuItem, SubMenu))]


def enabled(app) -> dict[str, bool]:
    box = popup(app).box
    return {parse_shortcut(entry.text)[0]: box.enabled(entry)
            for entry in box.entries() if isinstance(entry, (MenuItem, SubMenu))}


def right(x: int, y: int, action: str = "press") -> MouseClickEvent:
    return MouseClickEvent(x=x, y=y, button="right", action=action)


# -- the panels -----------------------------------------------------------------------


def test_a_right_click_on_a_file_moves_the_cursor_and_offers_its_operations(tree):
    app = navigator(tree)
    seen = {}
    run_app(app, [right(5, 5), OPEN, lambda a: seen.update(captions=captions(a))])
    assert app.manager.left.selected.name == "one.txt"
    assert seen["captions"] == [
        "View", "Edit", "Copy...", "Rename/Move...", "Create symlink...", "Delete",
        "File Attributes...", "Make directory", "Select group...", "Unselect group...",
        "Invert selection", "Insert name", "Insert path",
    ]


def test_insert_name_from_the_menu_types_it_on_the_command_line(tree):
    app = navigator(tree)
    run_app(app, [right(5, 5), OPEN, KeyEvent("i", "i"), SHUT])
    assert app.shell.command_line.value.strip() == "one.txt"


def test_a_directory_offers_no_view_but_its_length(tree):
    app = navigator(tree)
    seen = {}
    run_app(app, [right(5, 3), OPEN, lambda a: seen.update(captions=captions(a))])
    assert app.manager.left.selected.name == "alpha"
    assert "View" not in seen["captions"]
    assert "Count directory length" in seen["captions"]


def test_the_parent_entry_offers_only_what_needs_no_selection(tree):
    app = navigator(tree)
    seen = {}
    run_app(app, [right(5, 2), OPEN, lambda a: seen.update(captions=captions(a))])
    assert seen["captions"] == [
        "Count directory length", "Make directory", "Select group...",
        "Unselect group...", "Invert selection", "Insert name", "Insert path",
    ]


def test_choosing_copy_runs_it_on_the_panel_clicked(tree):
    from navigator.widgets.file_ops.copy_dialog import CopyDialog

    app = navigator(tree)
    seen = {}
    # The right panel, which was not the active one: the click activates it.
    run_app(app, [right(45, 5), OPEN, KeyEvent("c", "c"),
                  Until(lambda a: isinstance(a.modal, CopyDialog)),
                  lambda a: seen.update(active=a.manager.active_panel)])
    assert seen["active"] is app.manager.right
    assert app.manager.right.selected.name == "one.txt"


def test_the_release_of_the_opening_click_chooses_nothing(tree):
    app = navigator(tree)
    seen = {}
    run_app(app, [right(5, 5), OPEN, right(5, 5, "release"),
                  lambda a: seen.update(open=popup(a) is not None)])
    assert seen["open"]


def test_a_right_drag_onto_an_entry_and_release_chooses_it(tree):
    from navigator.widgets.file_ops.mkdir_dialog import MkdirDialog

    app = navigator(tree)

    def onto(label):
        def action(a):
            box = popup(a).box
            row = next(i for i, e in enumerate(box.entries())
                       if isinstance(e, MenuItem) and parse_shortcut(e.text)[0] == label)
            ox, oy = box.offset()
            a.post_event(MouseClickEvent(x=ox + box.x + 3, y=oy + box.y + row - box.top + 1,
                                         button="right", action="move"))
            a.post_event(MouseClickEvent(x=ox + box.x + 3, y=oy + box.y + row - box.top + 1,
                                         button="right", action="release"))
        return action

    run_app(app, [right(5, 5), OPEN, onto("Make directory"),
                  Until(lambda a: isinstance(a.modal, MkdirDialog))])


def test_shift_f10_opens_the_menu_under_the_cursor(tree):
    app = navigator(tree)
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f10", shift=True), OPEN,
                  lambda a: seen.update(captions=captions(a), at=popup(a).at)])
    assert seen["captions"][:2] == ["View", "Edit"]
    # Below the cursor's row (6 on screen), not over it.
    assert seen["at"][1] == 7


def test_the_menu_key_opens_it_too(tree):
    app = navigator(tree)
    run_app(app, [KeyEvent("menu"), OPEN])


def test_with_tagged_files_the_menu_acts_on_them(tree):
    app = navigator(tree)
    seen = {}

    def tag(a):
        panel = a.manager.left
        panel.marked = frozenset(e.key for e in panel.items if e.name.endswith(".txt"))

    run_app(app, [tag, right(5, 3), OPEN, lambda a: seen.update(captions=captions(a))])
    assert "View" not in seen["captions"]
    assert seen["captions"][0] == "Copy..."


@pytest.fixture
def selecting(monkeypatch):
    monkeypatch.setattr(SETTINGS.file_manager, "right_button", "select")


def test_set_to_select_a_right_click_tags_and_opens_nothing(tree, selecting):
    app = navigator(tree)
    seen = {}
    run_app(app, [right(5, 5), right(5, 5, "release"), lambda a: None,
                  lambda a: seen.update(open=popup(a) is not None)])
    panel = app.manager.left
    assert not seen["open"]
    assert [e.name for e in panel.marked_entries] == ["one.txt"]


def test_set_to_select_a_right_drag_tags_every_row_it_passes(tree, selecting):
    app = navigator(tree)
    run_app(app, [right(5, 3), MouseClickEvent(x=5, y=6, button="right", action="move"),
                  right(5, 6, "release")])
    panel = app.manager.left
    assert [e.name for e in panel.marked_entries] == ["alpha", "beta", "one.txt", "two.txt"]
    assert panel.selected.name == "two.txt"


def test_set_to_select_a_drag_from_a_tagged_row_untags(tree, selecting):
    app = navigator(tree)

    def tag(a):
        panel = a.manager.left
        panel.marked = frozenset(e.key for e in panel.items if e.name != "..")

    run_app(app, [tag, right(5, 4), MouseClickEvent(x=5, y=5, button="right", action="move"),
                  right(5, 5, "release")])
    assert [e.name for e in app.manager.left.marked_entries] == ["alpha", "two.txt"]


def test_set_to_select_the_keyboard_still_opens_the_menu(tree, selecting):
    app = navigator(tree)
    run_app(app, [KeyEvent("f10", shift=True), OPEN])


# -- input lines ------------------------------------------------------------------------


def test_an_input_line_offers_the_clipboard_greyed_by_its_selection(tree):
    from navigator.widgets.file_ops.mkdir_dialog import MkdirDialog

    app = navigator(tree)
    seen = {}
    run_app(app, [KeyEvent("f7"), Until(lambda a: isinstance(a.modal, MkdirDialog)),
                  *[KeyEvent(c, c) for c in "abc"],
                  KeyEvent("f10", shift=True), OPEN,
                  lambda a: seen.update(captions=captions(a), enabled=enabled(a))])
    assert seen["captions"] == ["Cut", "Copy", "Paste", "Clear", "Select all"]
    assert seen["enabled"] == {
        "Cut": False, "Copy": True, "Paste": True, "Clear": False, "Select all": True,
    }


def test_select_all_then_cut_empties_the_line_onto_the_clipboard(tree):
    from navigator.widgets.file_ops.mkdir_dialog import MkdirDialog

    app = navigator(tree)
    seen = {}
    run_app(app, [KeyEvent("f7"), Until(lambda a: isinstance(a.modal, MkdirDialog)),
                  *[KeyEvent(c, c) for c in "abc"],
                  KeyEvent("f10", shift=True), OPEN, KeyEvent("a", "a"), SHUT,
                  KeyEvent("menu"), OPEN, KeyEvent("t", "t"), SHUT,
                  lambda a: seen.update(value=a.modal.entry.value)])
    assert seen["value"] == ""
    assert app.terminal.clipboard[-1] == ("abc", False)


# -- the editor ---------------------------------------------------------------------------


def editor(app):
    from navigator.widgets.editor.edit_window import EditWindow

    window = app.shell.desktop.active_window
    return window.editor if isinstance(window, EditWindow) else None


EDITING = Until(lambda a: editor(a) is not None and editor(a).document is not None)


def test_the_editor_offers_select_all_and_a_right_click_inside_the_block_keeps_it(tree):
    app = navigator(tree)
    seen = {}
    run_app(app, [KeyEvent("down"), KeyEvent("down"), KeyEvent("down"), KeyEvent("f4"),
                  EDITING, KeyEvent("f10", shift=True), OPEN,
                  lambda a: seen.update(captions=captions(a)),
                  KeyEvent("a", "a"), SHUT,
                  lambda a: seen.update(block=editor(a).block),
                  right(3, 3), OPEN,
                  lambda a: seen.update(after=editor(a).block, enabled=enabled(a))])
    assert seen["captions"][:10] == [
        "Undo", "Redo", "Cut", "Copy", "Paste", "Clear", "Delete line", "Delete word left",
        "Select all", "Find...",
    ]
    assert seen["block"] is not None
    assert seen["after"] == seen["block"]
    assert seen["enabled"]["Cut"] and seen["enabled"]["Indent block"]


# -- the menu bar --------------------------------------------------------------------------


def test_a_context_menu_never_joins_the_menu_bar():
    owner = Widget()
    window_menu = SubMenu(text="~W~indow menu", parent=owner)
    ContextMenu(text="context", parent=owner)
    bar = MenuBar()
    bar.context = owner
    assert bar.entries() == [window_menu]
