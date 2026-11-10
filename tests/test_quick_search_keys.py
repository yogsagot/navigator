"""The panel quick search's keys: DN's where POSIX names allow (``FLPANEL.PAS``)."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    here = tmp_path / "here"
    here.mkdir()
    for name in ("bat", "bee", "box", "c++", "my file"):
        (here / name).write_text(name)
    (here / "alpha").mkdir()
    return here


def search(*text):
    return [KeyEvent("s", ctrl=True), *[KeyEvent(c, c) for c in "".join(text)]]


def panel(a):
    return a.manager.left


def test_ins_tags_and_the_search_goes_on(place):
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}

    def look(a):
        p = panel(a)
        seen.update(search=p.quick_search, tagged={e.name for e in p.items if e.key in p.marked},
                    at=p.selected.name)

    run_app(app, [*search("b"), lambda a: None, KeyEvent("insert"), lambda a: None, look])
    assert seen["search"] == "b" and seen["tagged"] == {"bat"} and seen["at"] == "bee"


def test_keypad_gray_star_inverts_and_the_search_stays(place):
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}

    def look(a):
        p = panel(a)
        seen.update(search=p.quick_search, tagged=len(p.marked))

    run_app(app, [*search("b"), lambda a: None, KeyEvent("kp_multiply", "*"), lambda a: None, look])
    assert seen["search"] == "b" and seen["tagged"] == 5  # the five files; alpha keeps its own


def test_keypad_gray_plus_opens_its_box(place):
    from navml.widgets.dialog.dialog import Dialog

    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}
    run_app(app, [*search("b"), lambda a: None, KeyEvent("kp_plus", "+"),
                  Until(lambda a: isinstance(a.modal, Dialog)), lambda a: seen.update(box=type(a.modal).__name__),
                  KeyEvent("escape")])
    assert seen["box"] == "SelectDialog"


def test_a_plus_typed_is_searched(place):
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}
    run_app(app, [*search("c+"), lambda a: None, lambda a: seen.update(at=panel(a).selected.name,
                                                                     search=panel(a).quick_search)])
    assert seen == {"at": "c++", "search": "c+"}


def test_backslash_opens_change_directory_searching_what_was_typed(place):
    from navigator.widgets.tree.change_dir_dialog import ChangeDirDialog

    # A directory the tree shows beside the one it opens on: what typing the
    # letters into the box would find, which is all DN's replay did.
    (place.parent / "alps").mkdir()
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}
    run_app(app, [*search("al"), lambda a: None, KeyEvent("\\", "\\"),
                  Until(lambda a: isinstance(a.modal, ChangeDirDialog)), lambda a: None,
                  Until(lambda a: a.modal.tree.search), lambda a: None,
                  lambda a: seen.update(search=a.modal.tree.search, panel=panel(a).quick_search,
                                        at=a.modal.tree.selected_node.data),
                  KeyEvent("escape"), KeyEvent("escape")])
    assert seen["search"] == "al" and seen["panel"] is None
    assert Path(str(seen["at"])).name == "alps"


def test_space_is_searched_as_ever(place):
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}
    run_app(app, [*search("my f"), lambda a: None, lambda a: seen.update(at=panel(a).selected.name)])
    assert seen["at"] == "my file"


def test_ctrl_enter_still_ends_the_search_and_inserts_the_name(place):
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    run_app(app, [*search("box"), lambda a: None, KeyEvent("enter", ctrl=True), lambda a: None])
    assert panel(app).quick_search is None and app.shell.command_line.value == "box "


# -- with the command line hidden: Shift+character starts the search (DN's ``ouiHideCmdLine`` path) --


@pytest.fixture
def hidden_line(monkeypatch):
    from navigator.settings import SETTINGS

    monkeypatch.setattr(SETTINGS.interface, "hide_command_line", True)


@pytest.mark.usefixtures("hidden_line")
def test_shift_letter_with_the_line_hidden_starts_the_search(place):
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}
    run_app(app, [KeyEvent("b", "B", shift=True), lambda a: None,
                  lambda a: seen.update(search=panel(a).quick_search, at=panel(a).selected.name),
                  KeyEvent("o", "o"), lambda a: None, lambda a: seen.update(then=panel(a).selected.name)])
    assert seen == {"search": "B", "at": "bat", "then": "box"}


@pytest.mark.usefixtures("hidden_line")
@pytest.mark.parametrize("event", [KeyEvent("b", "b"), KeyEvent("\\", "\\", shift=True)])
def test_a_plain_letter_or_shift_backslash_with_the_line_hidden_does_nothing(place, event):
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    run_app(app, [event, lambda a: None])
    assert panel(app).quick_search is None and app.shell.command_line.value == ""


def test_shift_letter_with_the_line_shown_types_on_it(place):
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    run_app(app, [KeyEvent("b", "B", shift=True), lambda a: None])
    assert panel(app).quick_search is None and app.shell.command_line.value == "B"


@pytest.mark.usefixtures("hidden_line")
def test_with_the_tree_holding_the_keyboard_no_search_starts(place):
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    run_app(app, [KeyEvent("t", ctrl=True), lambda a: None, KeyEvent("tab"), lambda a: None,
                  KeyEvent("b", "B", shift=True), lambda a: None])
    assert panel(app).quick_search is None
