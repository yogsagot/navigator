"""Ctrl+Q's view takes the viewer's keys while it has the keyboard.

DN's quick view was a ``TFileViewer`` under ``StatusDef hcView``: F2 wrap, F4
hex/dump, F5 go to, F6 filter, F7 and the searches again, Shift+F5 Save as,
Shift+F6 the code page -- handled by ``viewer_host`` here, as in the F3
window.  A key hcView did not list still reaches the panels (a departure).
And each Ctrl+Q opens the view as Viewer setup says (``ViOpt``).
"""

from __future__ import annotations

import pytest

from conftest import IDLE, FakeTerminal, Until, run_app
from navkit.events import KeyEvent

import navigator.lib.viewer as viewer_model
from navigator.__main__ import Navigator
from navigator.settings import SETTINGS


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr(viewer_model, "last_search", None)
    (tmp_path / "dir").mkdir()
    (tmp_path / "text.txt").write_text("".join(f"line {n:03}\n" for n in range(100)))
    (tmp_path / "zz.txt").write_text("another\n")
    return tmp_path


def navigator(path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def on_text(a):
    panel = a.manager.left
    panel.cursor = [e.name for e in panel.items].index("text.txt")


#: Ctrl+Q on text.txt, and Tab into the view.
INTO = [on_text, KeyEvent("q", ctrl=True), Until(lambda a: a.manager.quick.viewer.source is not None),
        KeyEvent("tab"), lambda a: None]


def quick(a):
    return a.manager.quick


def test_the_switches_are_the_viewers(files):
    app = navigator(files)
    seen = []

    def look(a):
        viewer = quick(a).viewer
        seen.append((viewer.wrap, viewer.mode, viewer.filter))

    run_app(app, [*INTO, look, KeyEvent("f2"), look, KeyEvent("f2"), KeyEvent("f4"), look,
                  KeyEvent("f4"), look, KeyEvent("f4"), KeyEvent("f6"), look])
    wrap = seen[0][0]
    assert seen[1][0] is not wrap
    assert [s[1] for s in seen[2:4]] == ["hex", "dump"]
    assert seen[4][1:] == ("text", 1)
    # F7 made no directory and F4 opened no editor on the way.
    assert sorted(p.name for p in files.iterdir()) == ["dir", "text.txt", "zz.txt"]
    assert app.shell.desktop.active_window is app.manager


def test_f5_goes_to_an_address_in_hex(files):
    from navigator.widgets.viewer.goto_dialog import GotoDialog

    app = navigator(files)
    seen = {}
    run_app(app, [*INTO, KeyEvent("f4"), KeyEvent("f5"), Until(lambda a: isinstance(a.modal, GotoDialog)),
                  *[KeyEvent(c, c) for c in "40"], KeyEvent("enter"), Until(lambda a: a.modal is None),
                  lambda a: seen.update(cursor=quick(a).viewer.cursor)])
    assert seen["cursor"] == 0x40


def test_f7_searches_and_shift_f7_finds_the_next(files):
    from navigator.widgets.viewer.viewer_find_dialog import ViewerFindDialog

    app = navigator(files)
    seen = []
    text = (files / "text.txt").read_bytes()
    run_app(app, [*INTO, KeyEvent("f7"), Until(lambda a: isinstance(a.modal, ViewerFindDialog)),
                  *[KeyEvent("space" if c == " " else c, c) for c in "line 05"], KeyEvent("enter"),
                  Until(lambda a: quick(a).viewer.hit is not None),
                  lambda a: seen.append(quick(a).viewer.hit[0]),
                  KeyEvent("f7", shift=True), Until(lambda a: quick(a).viewer.hit[0] != seen[0]),
                  lambda a: seen.append(quick(a).viewer.hit[0])])
    assert seen == [text.index(b"line 050"), text.index(b"line 051")]


def test_shift_f6_offers_the_code_pages(files):
    from navml.widgets.menu.popup_menu import PopupMenu

    app = navigator(files)
    seen = {}

    def popup(a):
        return next((c for c in a.root.children if isinstance(c, PopupMenu)), None)

    run_app(app, [*INTO, KeyEvent("f6", shift=True), Until(lambda a: popup(a) is not None),
                  lambda a: seen.update(title=popup(a).title), KeyEvent("escape")])
    assert seen["title"] == "Encoding"


def test_the_key_bar_names_the_viewers_keys_while_the_view_has_the_keyboard(files):
    from navigator.widgets.manager.commands import View
    from navigator.widgets.viewer.commands import AddFilter, GotoAddress, HexMode, SearchFor, Unwrap

    app = navigator(files)
    seen = {}

    def keys(name):
        return lambda a: seen.update({name: {k: type(c) for k, c in a.bindings().items()}})

    run_app(app, [on_text, KeyEvent("q", ctrl=True), Until(lambda a: quick(a).viewer.source is not None),
                  keys("panel"), KeyEvent("tab"), lambda a: None, keys("view")])
    view = seen["view"]
    assert [view[k] for k in ("f2", "f4", "f5", "f6", "f7")] == [Unwrap, HexMode, GotoAddress, AddFilter, SearchFor]
    # hcView did not list F3: it is still the panels' (a departure).
    assert view["f3"] is View
    assert seen["panel"]["f4"] is not HexMode


def test_f3_and_f8_still_reach_the_panels(files):
    from navigator.widgets.file_ops.delete_dialog import DeleteDialog
    from navigator.widgets.viewer.file_window import FileWindow

    app = navigator(files)
    seen = {}
    run_app(app, [*INTO, KeyEvent("f8"), Until(lambda a: isinstance(a.modal, DeleteDialog)),
                  KeyEvent("escape"), Until(lambda a: a.modal is None),
                  KeyEvent("f3"), Until(lambda a: isinstance(a.shell.desktop.active_window, FileWindow)),
                  lambda a: seen.update(path=a.shell.desktop.active_window.viewer.path)])
    assert seen["path"] == files / "text.txt"
    assert (files / "text.txt").exists()


def test_each_ctrl_q_opens_as_viewer_setup_says(files, monkeypatch):
    monkeypatch.setattr(SETTINGS.viewer, "hex_mode", True)
    monkeypatch.setattr(SETTINGS.viewer, "wrap_lines", True)
    app = navigator(files)
    seen = []

    def look(a):
        viewer = quick(a).viewer
        seen.append((viewer.mode, viewer.wrap, viewer.path.name if viewer.path else None))

    def on_zz(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index("zz.txt")

    run_app(app, [*INTO, look,
                  # Chosen by hand, then the cursor moves: the choice stays.
                  KeyEvent("f4"), KeyEvent("f4"), KeyEvent("tab"), on_zz,
                  Until(lambda a: quick(a).viewer.path.name == "zz.txt"), look,
                  # Off and on again: a new viewer, as ViOpt says.
                  KeyEvent("q", ctrl=True), KeyEvent("q", ctrl=True),
                  Until(lambda a: quick(a).viewer.source is not None), look])
    assert seen[0][:2] == ("hex", True)
    assert seen[1] == ("text", True, "zz.txt")
    assert seen[2][:2] == ("hex", True)


def test_save_as_is_refused_for_the_head_of_a_file_on_another_drive(files):
    from navigator.widgets.viewer.commands import SaveViewAs, SearchFor
    from navigator.widgets.viewer.quick_viewer import QuickViewer

    view = QuickViewer()
    assert view.refusal(SaveViewAs()) == "Nothing is open"
    assert view.refusal(SearchFor()) == "Nothing is open"
    view.viewer.open(files / "text.txt")
    try:
        assert view.refusal(SaveViewAs()) == ""
        view._use = object()
        assert view.refusal(SaveViewAs()) == "Only the start of the file was read"
        assert view.refusal(SearchFor()) == ""
    finally:
        view._use = None
        view.viewer.close_file()


def test_shift_f5_saves_a_copy_from_the_quick_view(files):
    from navml.widgets.dialog.file_dialog import FileDialog

    app = navigator(files)
    target = files / "copy.txt"

    def name_it(a):
        a.modal.target.value = str(target)

    run_app(app, [*INTO, KeyEvent("f5", shift=True), Until(lambda a: isinstance(a.modal, FileDialog)),
                  name_it, KeyEvent("enter"), Until(lambda a: target.exists())])
    assert target.read_bytes() == (files / "text.txt").read_bytes()
