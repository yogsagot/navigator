"""SmartPad: DOS Navigator's notepad, Alt+Q (``OpenSmartpad``, ``InsertInfo``; MICROED.PAS)."""

from __future__ import annotations

import time

import pytest

from conftest import IDLE, FakeTerminal, run_app
from navkit.events import KeyEvent

from navigator.lib.utilities import smartpad
from navigator.__main__ import Navigator
from navigator.models.edit_record import EditRecord

FIXED = time.strptime("2026-10-04 09:05:07", "%Y-%m-%d %H:%M:%S")
STAMP = "──────< 04-10-2026 09:05:07 >" + "─" * 36


@pytest.fixture
def pad(tmp_path, monkeypatch):
    """A file manager over *tmp_path*, SmartPad's directory beside it, the clock fixed."""
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr("navigator.widgets.shell.console.Console.start", lambda self, argv=None: None)
    notes = tmp_path / "notes"
    monkeypatch.setenv("SMARTPAD", str(notes))
    real = smartpad.stamp_text
    monkeypatch.setattr(smartpad, "stamp_text", lambda when=None: real(FIXED))
    return tmp_path, notes / "SmartPad.DN"


def front(app):
    return app.shell.desktop.active_window


def run(tmp_path, *actions):
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    run_app(app, [*actions, lambda a: None])
    return app


def test_alt_q_opens_the_pad_stamped_with_the_cursor_under_the_stamp(pad):
    tmp_path, path = pad
    seen = {}

    def look(a):
        window = front(a)
        desktop = a.shell.desktop
        seen.update(title=window.title, box=(window.x, window.y, window.width, window.height),
                    desk=(desktop.width, desktop.height), text=window.editor.document.encode(),
                    at=(window.editor.line, window.editor.col), modified=window.editor.modified)

    run(tmp_path, KeyEvent("q", alt=True), lambda a: None, look)
    assert seen["title"] == f"SmartPad(TM) - {path}"
    w, h = seen["desk"]
    assert seen["box"] == (2, 2, w - 4, h - 4)
    assert seen["text"] == f"{STAMP}\n".encode()
    assert seen["at"] == (1, 0)
    assert seen["modified"] is False  # the stamp alone is no change


def test_what_is_typed_is_saved_on_closing_without_a_question(pad):
    tmp_path, path = pad
    asked = []
    run(tmp_path, KeyEvent("q", alt=True), lambda a: None, *[KeyEvent(c, c) for c in "hi"],
        KeyEvent("escape"), IDLE, lambda a: asked.append(a.modal))
    assert asked == [None]
    assert path.read_text() == f"{STAMP}\nhi"


def test_a_pad_opened_and_closed_untouched_writes_nothing(pad):
    tmp_path, path = pad
    run(tmp_path, KeyEvent("q", alt=True), lambda a: None, KeyEvent("escape"), lambda a: None)
    assert not path.exists()


def test_old_notes_stay_and_the_stamp_goes_under_them(pad):
    tmp_path, path = pad
    path.parent.mkdir()
    path.write_text("old note\n")
    seen = []
    run(tmp_path, KeyEvent("q", alt=True), lambda a: None,
        lambda a: seen.append(front(a).editor.document.encode()))
    assert seen == [f"old note\n{STAMP}\n".encode()]


def test_a_second_alt_q_brings_the_same_pad_up_stamped_again(pad):
    tmp_path, _ = pad
    seen = []

    def count(a):
        windows = [w for w in a.shell.desktop.windows() if getattr(w, "smartpad", False)]
        seen.append((len(windows), windows[0].editor.document.encode().count(STAMP.encode())))

    run(tmp_path, KeyEvent("q", alt=True), lambda a: None, *[KeyEvent(c, c) for c in "x"],
        KeyEvent("f3", ctrl=True), lambda a: None,  # a new file manager in front
        KeyEvent("q", alt=True), lambda a: None, count,
        lambda a: seen.append(front(a).smartpad))
    assert seen == [(1, 2), True]


def test_the_pad_keeps_no_edit_history(pad):
    tmp_path, path = pad
    run(tmp_path, KeyEvent("q", alt=True), lambda a: None, KeyEvent("x", "x"),
        KeyEvent("escape"), IDLE)
    assert path.exists() and EditRecord.find(path) is None


def answer_file(monkeypatch, path):
    """*Open a File* and *Save File As* answered with *path*, unasked."""
    async def ask(self, *args, **kwargs):
        return path
    monkeypatch.setattr("navigator.widgets.editor.edit_window.EditWindow._ask_file", ask)


def test_save_as_makes_the_pad_an_ordinary_editor_and_alt_q_opens_a_fresh_pad(pad, monkeypatch):
    from conftest import Until

    tmp_path, path = pad
    other = tmp_path / "kept.txt"
    answer_file(monkeypatch, other)
    seen = {}

    def look(a):
        window = front(a)
        seen.update(flag=window.smartpad, title=window.title, path=window.editor.path)
        seen["was"] = window

    run(tmp_path, KeyEvent("q", alt=True), lambda a: None, *[KeyEvent(c, c) for c in "hi"],
        KeyEvent("f2", shift=True), Until(lambda a: other.exists()), lambda a: None, look,
        KeyEvent("q", alt=True), lambda a: None,
        lambda a: seen.update(pad=front(a) is not seen["was"] and front(a).smartpad,
                              stamps=seen["was"].editor.document.encode().count(STAMP.encode())))
    assert seen["flag"] is False and seen["path"] == other
    assert seen["title"] == f"Edit - {other}"
    assert other.read_text() == f"{STAMP}\nhi"
    assert not path.exists()  # the pad's own file kept what it had: nothing
    assert seen["pad"] and seen["stamps"] == 1  # the kept file was not stamped again


def test_open_saves_the_pad_unasked_and_the_window_is_an_ordinary_editor(pad, monkeypatch):
    from conftest import Until

    tmp_path, path = pad
    other = tmp_path / "other.txt"
    other.write_text("other\n")
    answer_file(monkeypatch, other)
    seen = {}
    run(tmp_path, KeyEvent("q", alt=True), lambda a: None, *[KeyEvent(c, c) for c in "hi"],
        KeyEvent("f3"), Until(lambda a: front(a).editor.path == other), lambda a: None,
        lambda a: seen.update(flag=front(a).smartpad, modal=a.modal, title=front(a).title))
    assert seen["modal"] is None  # no *Save?* for the pad
    assert path.read_text() == f"{STAMP}\nhi"
    assert seen["flag"] is False and seen["title"] == f"Edit - {other}"
