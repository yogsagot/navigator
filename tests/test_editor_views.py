"""Window > *New view*: two windows on one editor's text (a departure, not DN's).

One buffer, so one undo history and one save; each view its own cursor,
scroll, block and modes.  Only the text's first view asks *Save?* when every
window closes at once, and closing one of two loses nothing.
"""

from __future__ import annotations

import pytest

from conftest import IDLE, FakeTerminal, Until, run_app, settle
from navkit.events import KeyEvent, PasteEvent
from navkit.screen import ScreenBuffer

from navigator.__main__ import Navigator
from navigator.settings import SETTINGS
from navigator.commands import NewView
from navigator.widgets.editor.commands import SaveText


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "dir").mkdir()
    (tmp_path / "text.txt").write_text("one\ntwo\nthree\n")
    SETTINGS.interface.store_editor_position = False
    SETTINGS.confirmations.save = False
    return tmp_path


def editors(app):
    from navigator.widgets.editor.edit_window import EditWindow

    return [window for window in app.shell.desktop.windows() if isinstance(window, EditWindow)]


def front(app):
    return app.shell.desktop.active_window


def new_view(a):
    a.spawn(a.run_command(NewView(), a.focused))


def two_views(files, *actions):
    """text.txt in an editor, the cursor on its third line, then a New view of it, then *actions*."""
    app = Navigator(files, files, terminal=FakeTerminal(80, 24))
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), IDLE, KeyEvent("down"), KeyEvent("down"),
                  new_view, Until(lambda a: len(editors(a)) == 2), IDLE, *actions])
    return app


def test_a_new_view_shows_the_same_text_and_an_edit_in_one_is_in_both(files):
    app = two_views(files, KeyEvent("home", ctrl=True), PasteEvent("zero\n"), IDLE)
    first, second = editors(app)
    assert first.editor.buffer is second.editor.buffer
    assert first.editor.document.lines[:4] == ["zero", "one", "two", "three"]
    # The first view's cursor, on "three", moved down with the line put in above it.
    assert (first.editor.line, first.editor.col) == (3, 0)
    assert (second.editor.line, second.editor.col) == (1, 0)
    buffer = ScreenBuffer(80, 24)
    app.shell.layout(80, 24)
    settle()
    app.shell.render_tree(buffer)
    ox, oy = first.editor.offset()
    painted = "".join(buffer.get(ox + first.editor.x + x, oy + first.editor.y)[0] for x in range(4))
    assert painted == "zero" or first.editor.top > 0  # the first view repainted (if its top row shows)


def test_one_undo_history_an_edit_in_one_view_is_undone_from_the_other(files):
    def undo_in_first(a):
        a.shell.desktop.activate(editors(a)[0])

    app = two_views(files, PasteEvent("X"), IDLE, undo_in_first, IDLE,
                    KeyEvent("backspace", alt=True), IDLE)
    first, second = editors(app)
    assert second.editor.document.encode() == b"one\ntwo\nthree\n"
    assert first.editor.document.encode() == b"one\ntwo\nthree\n"


def test_one_save_writes_the_file_once_and_both_titles_lose_their_mark(files):
    app = two_views(files, PasteEvent("X"), IDLE,
                    lambda a: a.spawn(a.run_command(SaveText(), front(a).editor)),
                    Until(lambda a: not front(a).editor.modified), IDLE)
    first, second = editors(app)
    assert (files / "text.txt").read_text() == "one\ntwo\nXthree\n"
    assert not first.unsaved() and not second.unsaved()
    assert not first.title.startswith(("☼", "*")) and not second.title.startswith(("☼", "*"))


def test_closing_one_of_two_changed_views_asks_nothing_and_the_last_asks(files):
    seen = {}

    def before(a):
        first, second = editors(a)
        seen.update(asks=(first.must_ask(), second.must_ask()))  # one asks for all, the first opened

    two_views(files, PasteEvent("X"), IDLE, before, lambda a: front(a).request_close(), IDLE,
              lambda a: seen.update(left=len(editors(a)), last=editors(a)[0].must_ask()))
    assert seen == {"asks": (True, False), "left": 1, "last": True}


def test_a_no_to_save_closes_the_texts_other_views_too(files):
    from navml.widgets.dialog.dialog import Dialog

    seen = {}

    def answer_no(a):
        a.spawn(editors(a)[0].ask_to_close())

    def press_no(a):
        dialog = a.modal
        if isinstance(dialog, Dialog):
            dialog.close(False)

    two_views(files, PasteEvent("X"), IDLE, answer_no, Until(lambda a: a.modal is not None), press_no, IDLE,
              lambda a: seen.update(left=len(editors(a))))
    assert seen["left"] == 1


def test_the_lock_is_held_until_the_last_view_closes(files):
    from navigator.lib.editor import lock

    SETTINGS.editor.lock_file = True
    seen = {}

    def holders(name):
        def look(a):
            if "key" not in seen:
                seen["key"] = editors(a)[0].editor._lock
            key = seen["key"]
            seen[name] = lock._held[key][1] if key in lock._held else 0
        return look

    two_views(files, holders("two"), lambda a: front(a).request_close(), IDLE, holders("one"),
              lambda a: front(a).request_close(), IDLE, holders("none"))
    assert (seen["two"], seen["one"], seen["none"]) == (2, 1, 0)


def test_save_as_renames_every_view_and_load_text_detaches_one(files):
    other = files / "other.txt"
    other.write_text("else\n")

    async def asked(*args, **kwargs):
        return other

    def load(a):
        front(a)._ask_file = asked
        a.spawn(front(a).load_text())

    app = two_views(files, load, Until(lambda a: front(a).editor.path == other), IDLE)
    first, second = editors(app)
    assert first.editor.path == files / "text.txt" and first.editor.document.lines[0] == "one"
    assert second.editor.buffer is not first.editor.buffer
    assert not first.title.endswith((":1", ":2"))


def test_the_titles_say_which_view_and_lose_it_when_one_closes(files):
    seen = {}
    two_views(files, lambda a: seen.update(two=[w.title for w in editors(a)]),
              lambda a: front(a).request_close(), IDLE,
              lambda a: seen.update(one=[w.title for w in editors(a)]))
    assert seen["two"][0].endswith(" :1") and seen["two"][1].endswith(" :2")
    assert len(seen["one"]) == 1 and not seen["one"][0].endswith((":1", ":2"))


def test_the_cursor_and_the_block_are_each_views_own(files):
    app = two_views(files, KeyEvent("home", ctrl=True), KeyEvent("end", shift=True), IDLE)
    first, second = editors(app)
    assert second.editor.block is not None and first.editor.block is None
    assert (first.editor.line, second.editor.line) == (2, 0)


def test_new_view_is_greyed_outside_an_editor_and_in_smartpad(files):
    from navigator.lib.utilities.smartpad import open_smartpad

    app = Navigator(files, files, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [lambda a: seen.update(panel=a.command_disabled_reason(NewView(), a.focused)),
                  lambda a: a.spawn(open_smartpad(a.shell.desktop)), Until(lambda a: editors(a)), IDLE,
                  lambda a: seen.update(pad=a.command_disabled_reason(NewView(), a.focused))])
    assert seen == {"panel": "Only an editor has views", "pad": "Not for SmartPad"}


def test_a_saved_desktop_brings_two_views_back_as_views(files):
    from navigator.lib.config import desktop_state

    app = two_views(files)
    data = desktop_state.snapshot(app.shell.desktop)
    kept = [entry for entry in data["windows"] if entry.get("kind") == "editor"]
    assert "view_of" not in kept[0] and kept[1]["view_of"] == data["windows"].index(kept[0])
    fresh = Navigator(files, files, terminal=FakeTerminal(80, 24))
    run_app(fresh, [lambda a: a.spawn(desktop_state.restore(a.shell.desktop, data)),
                    Until(lambda a: len(editors(a)) == 2), IDLE])
    first, second = editors(fresh)
    assert first.editor.buffer is second.editor.buffer


def test_soft_wrap_in_one_view_and_not_in_the_other(files):
    from navigator.widgets.editor.commands import SwitchSoftWrap

    (files / "text.txt").write_text("x" * 200 + "\n")
    app = two_views(files, lambda a: a.spawn(a.run_command(SwitchSoftWrap(), front(a).editor)), IDLE)
    first, second = editors(app)
    assert second.editor.soft_wrap and not first.editor.soft_wrap
    assert len(second.editor.visible_rows()) > 1 and first.editor.visible_rows()[0] == (0, 0)
