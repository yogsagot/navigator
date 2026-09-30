"""F4: the editor -- the model in ``navigator/editor/`` and the window around it."""

from __future__ import annotations

import os
import random

import pytest

from conftest import FakeTerminal, run_app, settle
from navkit.events import KeyEvent, PasteEvent
from navkit.screen import ScreenBuffer

from navigator.__main__ import Navigator
from navigator.editor import columns
from navigator.editor.buffer import EditBuffer
from navigator.editor.document import Document, Pos
from navigator.editor.save import write_file


# -- the document ------------------------------------------------------------------


@pytest.mark.parametrize("data", [
    b"",
    b"one",
    b"one\n",
    b"one\r\ntwo\nthree\rfour",
    b"\n\n\r\n",
    b"tab\there\n  trailing   \n",
    b"caf\xc3\xa9 \xff\xfe broken \xe2\x82 utf-8\n",
])
def test_a_document_round_trips_byte_for_byte(data):
    assert Document.from_bytes(data).encode() == data


def test_random_bytes_round_trip():
    rng = random.Random(4)
    for _ in range(200):
        data = bytes(rng.choice(b"ab \t\r\n\x00\x80\xc3\xa9\xff") for _ in range(rng.randint(0, 60)))
        assert Document.from_bytes(data).encode() == data


def test_new_lines_take_the_ending_the_file_uses_most():
    assert Document.from_bytes(b"a\r\nb\r\nc\n").newline == "\r\n"
    assert Document.from_bytes(b"no break").newline == "\n"


def test_insert_and_delete_keep_each_lines_ending():
    document = Document.from_bytes(b"ab\r\ncd\n")
    end = document.insert(Pos(0, 1), "X\nY")
    assert end == Pos(1, 1)
    assert document.encode() == b"aX\nYb\r\ncd\n"
    removed = document.delete(Pos(0, 1), Pos(1, 1))
    assert removed == "X\nY"
    assert document.encode() == b"ab\r\ncd\n"


def test_a_directory_is_refused(tmp_path):
    with pytest.raises(OSError):
        Document.load(tmp_path)


# -- columns -------------------------------------------------------------------------


def test_a_tab_runs_to_the_next_stop_and_its_columns_are_the_tab():
    line = "a\tb"
    assert columns.width(line) == 9
    assert columns.column_of(line, 2) == 8
    assert columns.index_at(line, 4) == (1, 0)
    assert columns.index_at(line, 8) == (2, 0)
    assert columns.index_at(line, 12) == (3, 3)


def test_a_wide_character_takes_two_columns():
    line = "日本"
    assert columns.width(line) == 4
    assert columns.index_at(line, 1) == (0, 0)
    assert columns.cells(line) == [("日", 0), ("", 0), ("本", 1), ("", 1)]


def test_a_byte_that_was_not_utf8_is_its_cp437_glyph():
    line = Document.from_bytes(b"\xff\x01").lines[0]
    assert [c for c, _ in columns.cells(line)] == [" ", "☺"]


# -- undo --------------------------------------------------------------------------


def test_typing_merges_into_one_undo_and_the_save_point_clears_modified():
    buffer = EditBuffer(Document.from_bytes(b"x"))
    assert not buffer.modified
    for index, char in enumerate("abc"):
        buffer.begin((0, index), "type")
        buffer.insert(Pos(0, index), char)
        buffer.end()
    assert buffer.document.encode() == b"abcx" and buffer.modified
    assert buffer.undo() == (0, 0)
    assert buffer.document.encode() == b"x" and not buffer.modified


def test_undoing_past_the_save_point_and_editing_leaves_it_modified():
    buffer = EditBuffer(Document.from_bytes(b""))
    buffer.begin((0, 0))
    buffer.insert(Pos(0, 0), "a")
    buffer.end()
    buffer.mark_saved()
    buffer.undo()
    assert buffer.modified
    buffer.begin((0, 0))
    buffer.insert(Pos(0, 0), "b")
    buffer.end()
    assert buffer.modified


def test_a_multi_line_delete_undoes_to_the_same_bytes():
    data = b"one\r\ntwo\nthree"
    buffer = EditBuffer(Document.from_bytes(data))
    buffer.begin((0, 0))
    buffer.delete(Pos(0, 1), Pos(2, 2))
    buffer.end()
    buffer.undo()
    assert buffer.document.encode() == data


# -- saving ------------------------------------------------------------------------


def test_saving_keeps_the_mode_and_writes_through_a_symlink(tmp_path):
    target = tmp_path / "real.txt"
    target.write_bytes(b"old")
    target.chmod(0o640)
    link = tmp_path / "link.txt"
    link.symlink_to(target)
    write_file(link, b"new")
    assert link.is_symlink()
    assert target.read_bytes() == b"new"
    assert target.stat().st_mode & 0o777 == 0o640


def test_a_hard_linked_file_is_written_in_place(tmp_path):
    first = tmp_path / "a"
    first.write_bytes(b"old")
    second = tmp_path / "b"
    os.link(first, second)
    write_file(first, b"new")
    assert second.read_bytes() == b"new"


# -- the window ----------------------------------------------------------------------


@pytest.fixture
def quiet_console(monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)


@pytest.fixture
def files(tmp_path, quiet_console):
    (tmp_path / "dir").mkdir()
    (tmp_path / "text.txt").write_bytes(b"first line\r\nsecond\tline\r\n")
    return tmp_path


def navigator(path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def screen(app) -> ScreenBuffer:
    buffer = ScreenBuffer(80, 24)
    app.shell.layout(80, 24)
    settle()
    app.shell.render_tree(buffer)
    return buffer


def row_of(buffer: ScreenBuffer, y: int) -> str:
    return "".join(buffer.get(x, y)[0] or " " for x in range(buffer.width))


def editor_window(app):
    from navigator.widgets.editor.edit_window import EditWindow

    window = app.shell.desktop.active_window
    return window if isinstance(window, EditWindow) else None


def typed(text: str) -> list[KeyEvent]:
    return [KeyEvent(c, c) for c in text]


def test_f4_opens_the_file_under_the_cursor_zoomed(files):
    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None,
                  lambda a: seen.update(buffer=screen(a))])
    window = editor_window(app)
    assert window is not None and window.zoomed
    assert window.title == f"Edit - {files / 'text.txt'}"
    assert window.editor.focused
    buffer = seen["buffer"]
    assert "first line" in row_of(buffer, 2)
    assert "second  line" in row_of(buffer, 3)
    assert "═══1:1 [102] (↔)" in row_of(buffer, 21) or "===1:1 [102]" in row_of(buffer, 21)


def test_f4_on_a_directory_opens_nothing(files):
    app = navigator(files)
    run_app(app, [KeyEvent("down"), KeyEvent("f4"), lambda a: None])
    assert editor_window(app) is None


def test_typing_edits_and_f2_writes_the_bytes_back(files):
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None,
                  KeyEvent("end"), *typed("!"), KeyEvent("down"), KeyEvent("end"), KeyEvent("enter"),
                  *typed("x"), lambda a: None, KeyEvent("f2"), lambda a: None,
                  lambda a: None])
    assert (files / "text.txt").read_bytes() == b"first line!\r\nsecond\tline\r\nx\r\n"
    assert not editor_window(app).editor.modified


def test_the_info_line_marks_a_changed_text(files):
    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None, *typed("z"),
                  lambda a: seen.update(info=editor_window(a).editor.info_text)])
    assert seen["info"].startswith("☼══1:2") or seen["info"].startswith("*==1:2")


def test_escape_on_a_changed_text_asks_and_cancel_keeps_it_open(files):
    from navml.widgets.dialog.dialog import Dialog

    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None, *typed("z"),
                  KeyEvent("escape"), lambda a: None,
                  lambda a: seen.update(asked=isinstance(a.modal, Dialog),
                                        prompt=a.modal.prompt if a.modal else ""),
                  KeyEvent("escape"), lambda a: None])
    assert seen["asked"] and "was modified. Save?" in seen["prompt"]
    assert editor_window(app) is not None


def test_no_closes_without_saving(files):
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None, *typed("z"),
                  KeyEvent("escape"), lambda a: None, KeyEvent("n", alt=True), lambda a: None])
    assert editor_window(app) is None
    assert (files / "text.txt").read_bytes() == b"first line\r\nsecond\tline\r\n"


def test_yes_saves_and_closes(files):
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None, *typed("z"),
                  KeyEvent("escape"), lambda a: None, KeyEvent("y", alt=True), lambda a: None,
                  lambda a: None])
    assert editor_window(app) is None
    assert (files / "text.txt").read_bytes() == b"zfirst line\r\nsecond\tline\r\n"


def test_an_unchanged_text_closes_at_once(files):
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None, KeyEvent("escape")])
    assert editor_window(app) is None


def test_undo_takes_back_a_word_typed(files):
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None, *typed("abc"),
                  KeyEvent("backspace", alt=True)])
    editor = editor_window(app).editor
    assert editor.document.encode() == b"first line\r\nsecond\tline\r\n"
    assert not editor.modified


def test_enter_home_and_end_stay_the_editors_with_text_on_the_command_line(files):
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None,
                  lambda a: a.shell.command_line.insert("ls"),
                  KeyEvent("end"), KeyEvent("enter"), lambda a: None])
    editor = editor_window(app).editor
    assert editor.line == 1
    assert app.shell.command_line.value == "ls"


def test_a_paste_brings_its_lines_in_the_files_own_breaks(files):
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None,
                  PasteEvent("a\nb\n")])
    editor = editor_window(app).editor
    assert editor.document.encode().startswith(b"a\r\nb\r\nfirst line")


def test_saving_re_reads_the_panel_showing_the_directory(files):
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None, *typed("z"),
                  lambda a: (files / "new.txt").write_text(""),
                  KeyEvent("f2"), lambda a: None, lambda a: None])
    names = [entry.name for entry in app.shell.manager.left.items]
    assert "new.txt" in names


def test_the_cursor_steps_over_a_tab_whole(files):
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None, KeyEvent("down"),
                  *[KeyEvent("right")] * 7])
    editor = editor_window(app).editor
    assert editor.col == 8  # six letters of "second", then the tab to its stop
