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
from navigator.settings import SETTINGS


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



def test_closing_it_gives_the_keyboard_back_to_the_right_panel(files):
    # The window used to take the keyboard as it was mounted, before the
    # desktop had saved which panel the file manager had, so closing it
    # handed the keyboard to the left one.
    app = navigator(files)
    run_app(app, [KeyEvent("tab"), KeyEvent("end"), KeyEvent("f4"), lambda a: None,
                  KeyEvent("escape"), lambda a: None])
    assert editor_window(app) is None
    assert app.focused is app.manager.right

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


# -- the Editor menu ---------------------------------------------------------


def bar_captions(app) -> list[str]:
    from navml.widgets.dialog.control.control import parse_shortcut

    return [parse_shortcut(e.text)[0] for e in app.shell.menu.entries()]


def test_the_editor_menu_is_on_the_bar_after_file_only_while_the_editor_is_active(files):
    app = navigator(files)
    seen = []
    look = lambda a: seen.append("Editor" in bar_captions(a))   # noqa: E731
    run_app(app, [
        look,
        KeyEvent("end"), KeyEvent("f4"), lambda a: None,
        lambda a: seen.append(bar_captions(a)[:4]),
        KeyEvent("f9"), look,
        KeyEvent("f9"), look,
        KeyEvent("escape"), look,
    ])
    assert seen == [False, ["≡", "File", "Editor", "Disk"], False, True, False]


def test_editor_file_save_writes_and_edit_undo_undoes(files):
    app = navigator(files)
    run_app(app, [
        KeyEvent("end"), KeyEvent("f4"), lambda a: None, *typed("!"), lambda a: None,
        KeyEvent("e", "e", alt=True), KeyEvent("f", "f"), KeyEvent("s", "s"), lambda a: None,
        *typed("?"), lambda a: None,
        KeyEvent("e", "e", alt=True), KeyEvent("e", "e"), KeyEvent("u", "u"), lambda a: None,
    ])
    assert (files / "text.txt").read_bytes() == b"!first line\r\nsecond\tline\r\n"
    # Undo took the "?" back off, which returns the text to its save point.
    assert not editor_window(app).editor.modified
    assert not app.shell.menu.is_open


def test_an_editor_feature_still_to_come_is_greyed(files):
    from navml.widgets.menu.menu_box import MenuBox

    app = navigator(files)
    seen = {}

    def ask(a):
        menu = editor_window(a).edit_menu
        probe = MenuBox(None)
        probe.behind = a.focused
        a.root.add(probe)
        seen["justify"] = probe.enabled(menu.entry("Paragraph").entry("Justify"))
        seen["save"] = probe.enabled(menu.entry("File").entry("Save"))
        a.root.remove(probe)

    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None, ask])
    assert seen == {"justify": False, "save": True}


# -- Backspace unindents ----------------------------------------------------------------


def backspaced(tmp_path, text: str, line: int, col: int, times: int = 1):
    """*text* in an editor, the cursor put on *line*/*col*, Backspace *times*."""
    (tmp_path / "dir").mkdir(exist_ok=True)
    (tmp_path / "text.txt").write_text(text)
    app = navigator(tmp_path)

    def place(a):
        editor = editor_window(a).editor
        editor.line, editor.col = line, col

    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None, place,
                  *[KeyEvent("backspace") for _ in range(times)]])
    editor = editor_window(app).editor
    return editor.document.encode().decode(), editor.col


def test_backspace_in_the_indent_goes_back_to_a_shallower_line_above(tmp_path, quiet_console):
    text = "a\n    b\n        c\n        d\n"
    assert backspaced(tmp_path, text, 3, 8) == ("a\n    b\n        c\n    d\n", 4)
    assert backspaced(tmp_path, text, 3, 8, times=2) == ("a\n    b\n        c\nd\n", 0)


def test_backspace_on_the_text_is_still_one_character(tmp_path, quiet_console):
    assert backspaced(tmp_path, "a\n    bc\n", 1, 5) == ("a\n    c\n", 4)


def test_a_tab_that_overshoots_is_made_up_with_spaces(tmp_path, quiet_console):
    # A tab to column 8 under a line indented 2: the tab goes, two spaces stay.
    assert backspaced(tmp_path, "  a\n\tb\n", 1, 8) == ("  a\n  b\n", 2)


def test_past_the_end_of_a_blank_line_the_cursor_only_moves(tmp_path, quiet_console):
    assert backspaced(tmp_path, "    a\n\n", 1, 8) == ("    a\n\n", 4)


def test_undo_takes_an_unindent_back_whole(tmp_path, quiet_console):
    (tmp_path / "dir").mkdir()
    (tmp_path / "text.txt").write_text("a\n        b\n")
    app = navigator(tmp_path)

    def place(a):
        editor = editor_window(a).editor
        editor.line, editor.col = 1, 8

    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None, place,
                  KeyEvent("backspace"), KeyEvent("backspace", alt=True)])
    assert editor_window(app).editor.document.encode() == b"a\n        b\n"


def test_without_backspace_unindents_one_blank_goes(tmp_path, quiet_console):
    SETTINGS.editor.backspace_unindents = False
    assert backspaced(tmp_path, "a\n    b\n", 1, 4) == ("a\n   b\n", 3)


# -- Line divisor ---------------------------------------------------------------------------


@pytest.mark.parametrize("divisor, newline", [("lf", "\n"), ("crlf", "\r\n"), ("cr", "\r")])
def test_a_new_file_breaks_lines_as_line_divisor_says(tmp_path, divisor, newline):
    from navigator.widgets.editor.file_editor import FileEditor

    SETTINGS.editor.line_divisor = divisor
    editor = FileEditor()
    editor.open(tmp_path / "new.txt", new=True)
    assert editor.document.newline == newline


def test_enter_in_an_empty_file_types_the_line_divisor(tmp_path, quiet_console):
    SETTINGS.editor.line_divisor = "crlf"
    (tmp_path / "dir").mkdir()
    (tmp_path / "text.txt").write_bytes(b"")
    app = navigator(tmp_path)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None,
                  *typed("a"), KeyEvent("enter"), *typed("b")])
    assert editor_window(app).editor.document.encode() == b"a\r\nb"


def test_a_file_with_breaks_keeps_its_own(tmp_path):
    from navigator.widgets.editor.file_editor import FileEditor

    SETTINGS.editor.line_divisor = "crlf"
    (tmp_path / "unix.txt").write_bytes(b"one\ntwo\n")
    editor = FileEditor()
    editor.open(tmp_path / "unix.txt")
    assert editor.document.newline == "\n"


# -- Shift+F4: Edit new file ----------------------------------------------------------------


def edit_named(tmp_path, name: str, *after):
    app = navigator(tmp_path)
    seen = {}
    run_app(app, [KeyEvent("f4", shift=True), lambda a: None, *typed(name), KeyEvent("enter"),
                  lambda a: None, *after,
                  lambda a: seen.update(window=editor_window(a), modal=a.modal)])
    return app, seen["window"], seen["modal"]


def test_shift_f4_edits_a_new_file_that_saving_creates(files):
    app, window, _ = edit_named(files, "fresh.txt", *typed("hi"), KeyEvent("f2"), lambda a: None)
    assert window is not None and window.editor.path == files / "fresh.txt"
    assert (files / "fresh.txt").read_bytes() == b"hi"


def test_shift_f4_on_an_existing_name_edits_that_file(files):
    _, window, _ = edit_named(files, "text.txt")
    assert window.editor.document.encode() == b"first line\r\nsecond\tline\r\n"


def test_shift_f4_takes_a_name_under_a_directory_and_refuses_a_missing_one(files):
    _, window, _ = edit_named(files, "dir/inner.txt")
    assert window.editor.path == files / "dir" / "inner.txt"
    _, window, modal = edit_named(files, "nowhere/inner.txt")
    assert window is None and modal is not None and modal.title == "Cannot edit file"
    assert not (files / "nowhere").exists()


def test_shift_f4_on_a_directory_is_refused(files):
    _, window, modal = edit_named(files, "dir")
    assert window is None and modal.title == "Cannot edit file"


# -- blocks and the clipboard -----------------------------------------------------------------


def test_a_place_shifts_with_an_insert_or_delete_around_it():
    from navigator.editor.document import shifted

    at = Pos(1, 4)
    assert shifted(at, "insert", Pos(0, 2), Pos(0, 5)) == at            # a line above, no break
    assert shifted(at, "insert", Pos(1, 1), Pos(1, 3)) == Pos(1, 6)     # earlier on its line
    assert shifted(at, "insert", Pos(1, 1), Pos(2, 0)) == Pos(2, 3)     # a break before it
    assert shifted(at, "insert", Pos(1, 4), Pos(1, 6)) == Pos(1, 6)     # right at it: goes before
    assert shifted(at, "insert", Pos(1, 4), Pos(1, 6), stay=True) == at
    assert shifted(at, "delete", Pos(1, 0), Pos(1, 2)) == Pos(1, 2)
    assert shifted(at, "delete", Pos(0, 3), Pos(1, 6)) == Pos(0, 3)     # inside: closes up
    assert shifted(at, "delete", Pos(0, 3), Pos(1, 1)) == Pos(0, 6)


def test_the_buffer_tells_its_listeners_of_undone_edits_too():
    buffer = EditBuffer(Document.from_bytes(b"abc"))
    heard = []
    buffer.listeners.append(lambda *change: heard.append(change))
    buffer.begin((0, 0))
    buffer.insert(Pos(0, 1), "XY")
    buffer.end()
    buffer.undo()
    assert heard == [("insert", Pos(0, 1), Pos(0, 3)), ("delete", Pos(0, 1), Pos(0, 3))]


def marked(files, *keys):
    """The editor on text.txt after *keys*: Shift+movements mark, the rest act."""
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None, *keys])
    return app, editor_window(app).editor


def test_shift_with_a_movement_marks_and_back_unmarks(files):
    _, editor = marked(files, KeyEvent("right", shift=True), KeyEvent("right", shift=True),
                       KeyEvent("down", shift=True))
    assert editor.block == (Pos(0, 0), Pos(1, 2))
    assert editor.block_text == "first line\nse"
    _, editor = marked(files, KeyEvent("right", shift=True), KeyEvent("left", shift=True))
    assert editor.block is None


def test_ctrl_insert_copies_the_block_with_plain_line_breaks(files):
    app, editor = marked(files, *[KeyEvent("right")] * 6, KeyEvent("down", shift=True),
                         KeyEvent("insert", ctrl=True))
    assert app.terminal.clipboard == [("line\nsecond", False)]
    assert editor.block == (Pos(0, 6), Pos(1, 6))  # a copy leaves it marked


def test_shift_delete_cuts_and_undo_brings_it_back(files):
    app, editor = marked(files, *[KeyEvent("right")] * 6, KeyEvent("down", shift=True),
                         KeyEvent("delete", shift=True))
    assert app.terminal.clipboard == [("line\nsecond", False)]
    assert editor.document.encode() == b"first \tline\r\n"
    assert editor.block is None and (editor.line, editor.col) == (0, 6)
    _, editor = marked(files, *[KeyEvent("right")] * 6, KeyEvent("down", shift=True),
                       KeyEvent("delete", shift=True), KeyEvent("backspace", alt=True))
    assert editor.document.encode() == b"first line\r\nsecond\tline\r\n"


def test_ctrl_delete_clears_without_touching_the_clipboard(files):
    app, editor = marked(files, KeyEvent("end", shift=True), KeyEvent("delete", ctrl=True))
    assert app.terminal.clipboard == []
    assert editor.document.encode() == b"\r\nsecond\tline\r\n"


def test_shift_insert_pastes_in_the_files_own_line_breaks(files):
    SETTINGS.system.system_clipboard = False  # Navigator's own, which a test can read back
    app, editor = marked(files, *[KeyEvent("right")] * 6, KeyEvent("down", shift=True),
                         KeyEvent("insert", ctrl=True), KeyEvent("pagedown", ctrl=True),
                         KeyEvent("insert", shift=True), lambda a: None)
    assert editor.document.encode() == b"first line\r\nsecond\tline\r\nline\r\nsecond"


def test_the_block_follows_text_typed_before_it_and_not_after(files):
    _, editor = marked(files, *[KeyEvent("right")] * 6, KeyEvent("end", shift=True),
                       KeyEvent("home"), *typed("ab"), KeyEvent("end"), *typed("z"))
    assert editor.block == (Pos(0, 8), Pos(0, 12))
    assert editor.block_text == "line"


def test_the_block_is_painted_in_its_own_colour(files):
    app, editor = marked(files, KeyEvent("right", shift=True))
    buffer = screen(app)
    selected = editor.part_style("selected")
    cells = [buffer.get(x, y) for y in range(buffer.height) for x in range(buffer.width)]
    assert sum(1 for char, style in cells if style == selected) == 1
    assert ("f", selected) in cells


def test_cut_copy_and_clear_wait_for_a_block(files):
    from navigator.widgets.editor.commands import ClearBlock, ClipboardCopy, ClipboardCut, ClipboardPaste

    _, editor = marked(files)
    assert not any(editor.enables(c()) for c in (ClipboardCut, ClipboardCopy, ClearBlock))
    assert editor.enables(ClipboardPaste())
