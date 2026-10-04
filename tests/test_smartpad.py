"""SmartPad: DOS Navigator's notepad, Alt+Q (``OpenSmartpad``, ``InsertInfo``; MICROED.PAS)."""

from __future__ import annotations

import time

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent

from navigator import smartpad
from navigator.__main__ import Navigator
from navigator.models.edit_record import EditRecord

FIXED = time.strptime("2026-10-04 09:05:07", "%Y-%m-%d %H:%M:%S")
STAMP = "──────< 04-10-2026 09:05:07 >" + "─" * 36


@pytest.fixture
def pad(tmp_path, monkeypatch):
    """A file manager over *tmp_path*, SmartPad's directory beside it, the clock fixed."""
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
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
        KeyEvent("escape"), lambda a: None, lambda a: asked.append(a.modal))
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
        KeyEvent("escape"), lambda a: None)
    assert path.exists() and EditRecord.find(path) is None
