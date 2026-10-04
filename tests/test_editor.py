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
    from navigator.widgets.editor.commands import Clear, ClipboardCopy, ClipboardCut, ClipboardPaste

    _, editor = marked(files)
    assert not any(editor.enables(c()) for c in (ClipboardCut, ClipboardCopy, Clear))
    assert editor.enables(ClipboardPaste())


# -- marking with the mouse -------------------------------------------------------------------


def mouse(files, *events):
    """text.txt in an editor, then each *event* handed to it in turn: (x, y, action, **kw)."""
    from navkit.events import DoubleClickEvent, MouseClickEvent

    app = navigator(files)

    def deliver(spec):
        x, y, action, kw = spec
        kind = DoubleClickEvent if action == "double" else MouseClickEvent
        kw.setdefault("button", "left")
        if kind is MouseClickEvent:
            kw["action"] = action
        return lambda a: a.spawn(editor_window(a).editor.on_mouse_click(kind(x=x, y=y, **kw))
                                 if kind is MouseClickEvent
                                 else editor_window(a).editor.on_double_click(kind(x=x, y=y, **kw)))

    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None,
                  *[deliver(e) for e in events], lambda a: None])
    return app, editor_window(app).editor


def test_a_drag_marks_and_the_release_makes_it_the_primary_selection(files):
    app, editor = mouse(files, (2, 0, "press", {}), (3, 1, "move", {}), (3, 1, "release", {}))
    assert editor.block == (Pos(0, 2), Pos(1, 3))
    assert app.terminal.clipboard == [("rst line\nsec", True)]


def test_a_click_unmarks_and_a_shift_click_extends(files):
    _, editor = mouse(files, (0, 0, "press", {}), (4, 0, "move", {}), (4, 0, "release", {}),
                      (8, 0, "press", {"shift": True}), (8, 0, "release", {}))
    assert editor.block == (Pos(0, 0), Pos(0, 8))
    _, editor = mouse(files, (0, 0, "press", {}), (4, 0, "move", {}), (4, 0, "release", {}),
                      (6, 1, "press", {}), (6, 1, "release", {}))
    assert editor.block is None and (editor.line, editor.col) == (1, 6)


def test_a_double_click_marks_the_word(files):
    app, editor = mouse(files, (8, 0, "double", {}))
    assert editor.block_text == "line"
    assert app.terminal.clipboard == [("line", True)]


def test_a_middle_click_asks_for_the_primary_selection(files):
    app, _ = mouse(files, (0, 0, "press", {"button": "middle"}))
    assert app.terminal.clipboard_queries == [True]


# -- Persistent blocks ------------------------------------------------------------------------


def test_persistent_blocks_stay_through_movement_and_typing(files):
    _, editor = marked(files, KeyEvent("right", shift=True), KeyEvent("right", shift=True),
                       KeyEvent("end"), *typed("x"))
    assert editor.block_text == "fi"
    assert editor.document.encode().startswith(b"first linex\r\n")


def test_without_persistent_blocks_a_movement_unmarks(files):
    SETTINGS.editor.persistent_blocks = False
    _, editor = marked(files, KeyEvent("right", shift=True), KeyEvent("right"))
    assert editor.block is None


def test_without_persistent_blocks_typing_replaces_the_block(files):
    SETTINGS.editor.persistent_blocks = False
    _, editor = marked(files, *typed("ab"), KeyEvent("home"),
                       *[KeyEvent("right", shift=True)] * 7, *typed("X"))
    assert editor.document.encode().startswith(b"X line\r\n")
    assert editor.block is None and (editor.line, editor.col) == (0, 1)


def test_without_persistent_blocks_one_undo_takes_the_replacement_back(files):
    SETTINGS.editor.persistent_blocks = False
    _, editor = marked(files, *typed("ab"), KeyEvent("home"),
                       *[KeyEvent("right", shift=True)] * 7, *typed("X"),
                       KeyEvent("backspace", alt=True))
    # The replacement went as one, leaving the typing before the block alone.
    assert editor.document.encode().startswith(b"abfirst line\r\n")


@pytest.mark.parametrize("key", ["delete", "backspace"])
def test_without_persistent_blocks_del_and_backspace_take_the_block_alone(files, key):
    SETTINGS.editor.persistent_blocks = False
    _, editor = marked(files, KeyEvent("right"), *[KeyEvent("right", shift=True)] * 4,
                       KeyEvent(key))
    assert editor.document.encode().startswith(b"f line\r\n")


def test_without_persistent_blocks_a_paste_replaces_the_block(files):
    SETTINGS.editor.persistent_blocks = False
    _, editor = marked(files, KeyEvent("end", shift=True), PasteEvent("new"))
    assert editor.document.encode().startswith(b"new\r\nsecond")


# -- column blocks ----------------------------------------------------------------------------


def columns_editor(files, text: bytes, *keys):
    """*text* in an editor with column blocks in force, then *keys*."""
    SETTINGS.editor.vertical_blocks = True
    (files / "text.txt").write_bytes(text)
    return marked(files, *keys)


def test_shift_movement_marks_a_rectangle_across_short_lines(files):
    _, editor = columns_editor(files, b"abcdef\nab\nabcdef\n",
                               KeyEvent("right"), KeyEvent("right"),
                               *[KeyEvent("right", shift=True)] * 3,
                               *[KeyEvent("down", shift=True)] * 2)
    assert editor.rectangle == (0, 2, 2, 5)
    assert editor.block is None
    assert editor.block_text == "cde\n\ncde"


def test_cutting_a_rectangle_takes_each_lines_columns_and_undo_restores(files):
    app, editor = columns_editor(files, b"abcdef\nab\nabcdef\n",
                                 KeyEvent("right"), KeyEvent("right"),
                                 *[KeyEvent("right", shift=True)] * 3,
                                 *[KeyEvent("down", shift=True)] * 2,
                                 KeyEvent("delete", shift=True))
    assert editor.document.encode() == b"abf\nab\nabf\n"
    assert editor.column_block is None and (editor.line, editor.col) == (0, 2)
    assert app.terminal.clipboard == [("cde\n\ncde", False)]


def test_a_copied_rectangle_pastes_back_as_one(files):
    SETTINGS.system.system_clipboard = False
    _, editor = columns_editor(files, b"abcd\nefgh\n",
                               *[KeyEvent("right", shift=True)] * 2, KeyEvent("down", shift=True),
                               KeyEvent("insert", ctrl=True),
                               KeyEvent("up"), KeyEvent("end"),
                               KeyEvent("insert", shift=True), lambda a: None)
    assert editor.document.encode() == b"abcdab\nefghef\n"


def test_a_rectangle_pasted_past_short_lines_and_the_end_pads_and_adds(files):
    SETTINGS.system.system_clipboard = False
    _, editor = columns_editor(files, b"abcd\nefgh",
                               *[KeyEvent("right", shift=True)] * 2, KeyEvent("down", shift=True),
                               KeyEvent("insert", ctrl=True),
                               KeyEvent("down"), *[KeyEvent("right")] * 4,
                               KeyEvent("insert", shift=True), lambda a: None)
    assert editor.document.encode() == b"abcd\nefgh  ab\n      ef"


def test_a_tab_belongs_to_the_column_it_starts_in(files):
    # Columns 2 to 9: on "a\tbc" the tab starts at 1, outside; "b" at 8 is in, "c" at 9 is not.
    app, editor = columns_editor(files, b"abcdefghij\na\tbc\n",
                                 KeyEvent("right"), KeyEvent("right"),
                                 *[KeyEvent("right", shift=True)] * 7, KeyEvent("down", shift=True),
                                 KeyEvent("delete", shift=True))
    assert app.terminal.clipboard == [("cdefghi\nb", False)]
    assert editor.document.encode() == b"abj\na\tc\n"


def test_the_rectangle_moves_down_with_a_line_break_above_it(files):
    _, editor = columns_editor(files, b"top\nabcd\nefgh\n",
                               KeyEvent("down"), *[KeyEvent("right", shift=True)] * 2,
                               KeyEvent("up"), KeyEvent("home"), KeyEvent("enter"))
    assert editor.rectangle == (2, 0, 2, 2)
    assert editor.block_text == "ab"


def test_ctrl_b_v_switches_column_blocks_keeping_the_block_and_is_ticked(files):
    from navigator.widgets.editor.commands import SwitchBlock

    seen = []
    (files / "text.txt").write_bytes(b"abcdef\nghijkl\n")
    SETTINGS.interface.store_editor_position = False
    app = navigator(files)

    def look(a):
        editor = editor_window(a).editor
        seen.append((editor.vertical_blocks, editor.checks(SwitchBlock()), editor.block,
                     editor.rectangle))

    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None,
                  KeyEvent("right"), KeyEvent("right", shift=True), KeyEvent("right", shift=True),
                  KeyEvent("down", shift=True),
                  ctrl("b"), KeyEvent("v", "v"), look,
                  ctrl("b"), ctrl("v"), look])
    # The stream (0,1)-(1,3) is the rectangle with those corners, and back.
    assert seen == [
        (True, True, None, (0, 1, 1, 3)),
        (False, False, (Pos(0, 1), Pos(1, 3)), None),
    ]


# -- Ctrl+K and Ctrl+Q --------------------------------------------------------------------------


def ctrl(letter):
    return KeyEvent(letter, ctrl=True)


def chord(*keys):
    """Ctrl+K then *keys*: a letter plain, or a KeyEvent as given."""
    return [ctrl("k"), *[KeyEvent(k, k) if isinstance(k, str) else k for k in keys]]


def text_editor(files, text: bytes, *keys):
    """*text* in an editor, then *keys*; each open starts at the top, not where the last left off."""
    SETTINGS.interface.store_editor_position = False
    (files / "text.txt").write_bytes(text)
    return marked(files, *keys)


def test_ctrl_k_b_and_k_mark_with_the_letter_plain_or_with_ctrl(files):
    _, editor = text_editor(files, b"abcdef\n", KeyEvent("right"), *chord("b"),
                            *[KeyEvent("right")] * 3, ctrl("k"), ctrl("k"))
    assert editor.block_text == "bcd"
    _, editor = text_editor(files, b"abcdef\n", *[KeyEvent("right")] * 4, *chord("k"),
                            KeyEvent("home"), *chord("b"))
    assert editor.block_text == "abcd"  # the end first, then the start


def test_a_chords_second_key_never_types(files):
    _, editor = text_editor(files, b"abc\n", *chord("z"), *typed("x"))
    assert editor.document.encode() == b"xabc\n"


def test_the_info_line_shows_a_chord_waiting(files):
    seen = []
    (files / "text.txt").write_bytes(b"abc\n")
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None, ctrl("k"),
                  lambda a: seen.append(editor_window(a).editor.info_text),
                  KeyEvent("h", "h"), lambda a: seen.append(editor_window(a).editor.info_text)])
    assert seen[0].endswith(" ^K") and not seen[1].endswith("^K")


def test_ctrl_k_t_and_l_mark_a_word_and_a_line(files):
    _, editor = text_editor(files, b"one two\nthree\n", *[KeyEvent("right")] * 5, *chord("t"))
    assert editor.block_text == "two"
    _, editor = text_editor(files, b"one two\nthree\n", *chord("l"))
    assert editor.block_text == "one two\n"


def test_ctrl_k_h_and_alt_h_hide_the_block_and_show_it_again(files):
    seen = []
    (files / "text.txt").write_bytes(b"abcdef\n")
    SETTINGS.interface.store_editor_position = False
    app = navigator(files)

    def look(a):
        editor = editor_window(a).editor
        seen.append((editor.has_block, editor.marked, editor._block_columns(0)))

    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None,
                  *[KeyEvent("right", shift=True)] * 2, look,
                  *chord("h"), look, KeyEvent("h", alt=True), look])
    assert seen == [(True, True, (0, 2)), (False, True, None), (True, True, (0, 2))]


def test_a_hidden_block_waits_out_the_block_commands_and_follows_edits(files):
    from navigator.widgets.editor.commands import Clear, CopyBlock

    _, editor = text_editor(files, b"abcdef\n", KeyEvent("right"),
                            *[KeyEvent("right", shift=True)] * 2, KeyEvent("h", alt=True),
                            KeyEvent("home"), *typed("xy"))
    assert not editor.enables(Clear()) and not editor.enables(CopyBlock())
    assert editor.block == (Pos(0, 3), Pos(0, 5))  # moved with the text typed before it


def test_marking_anew_shows_a_hidden_block(files):
    _, editor = text_editor(files, b"abcdef\n", *[KeyEvent("right", shift=True)] * 2,
                            KeyEvent("h", alt=True), KeyEvent("end"), *chord("k"))
    assert editor.has_block and editor.block_text == "abcdef"


def test_ctrl_k_c_copies_the_block_to_the_cursor_and_marks_the_copy(files):
    _, editor = text_editor(files, b"abc\nxyz\n", *[KeyEvent("right", shift=True)] * 2,
                            KeyEvent("down"), KeyEvent("end"), *chord("c"))
    assert editor.document.encode() == b"abc\nxyzab\n"
    assert editor.block == (Pos(1, 3), Pos(1, 5))


def test_ctrl_k_v_moves_the_block_and_one_undo_puts_it_back(files):
    _, editor = text_editor(files, b"abc\nxyz\n", *[KeyEvent("right", shift=True)] * 2,
                            KeyEvent("down"), KeyEvent("end"), *chord("v"))
    assert editor.document.encode() == b"c\nxyzab\n"
    assert editor.block_text == "ab"
    _, editor = text_editor(files, b"abc\nxyz\n", *[KeyEvent("right", shift=True)] * 2,
                            KeyEvent("down"), KeyEvent("end"), *chord("v"),
                            KeyEvent("backspace", alt=True))
    assert editor.document.encode() == b"abc\nxyz\n"


def test_ctrl_k_v_inside_the_block_does_nothing(files):
    _, editor = text_editor(files, b"abcdef\n", *[KeyEvent("right", shift=True)] * 4,
                            KeyEvent("left"), KeyEvent("left"), *chord("v"))
    assert editor.document.encode() == b"abcdef\n"


def test_ctrl_k_y_deletes_the_block(files):
    _, editor = text_editor(files, b"abcdef\n", *[KeyEvent("right", shift=True)] * 2, *chord("y"))
    assert editor.document.encode() == b"cdef\n"


def test_ctrl_k_i_and_u_indent_and_unindent_the_blocks_lines(files):
    _, editor = text_editor(files, b"a\n b\nc\n", KeyEvent("down", shift=True),
                            KeyEvent("down", shift=True), *chord("i"))
    # The block ends at the start of line 2, which it does not touch.
    assert editor.document.encode() == b" a\n  b\nc\n"
    assert editor.block[0] == Pos(0, 0)
    _, editor = text_editor(files, b"\ta\n b\nc\n", KeyEvent("down", shift=True),
                            KeyEvent("down", shift=True), *chord("u"))
    assert editor.document.encode() == b"       a\nb\nc\n"


def test_ctrl_k_brackets_change_the_case_of_the_block(files):
    _, editor = text_editor(files, b"hello world\n", KeyEvent("end", shift=True), *chord("["))
    assert editor.document.encode() == b"HELLO WORLD\n"
    _, editor = text_editor(files, b"HELLO WORLD\n", KeyEvent("end", shift=True), *chord("]"))
    assert editor.document.encode() == b"hello world\n"
    _, editor = text_editor(files, b"hELLO wORLD\n", KeyEvent("end", shift=True), *chord("\\"))
    assert editor.document.encode() == b"Hello World\n"
    assert editor.block_text == "Hello World"


def test_ctrl_q_b_and_k_go_to_the_blocks_ends(files):
    _, editor = text_editor(files, b"abcdef\n", KeyEvent("right"),
                            *[KeyEvent("right", shift=True)] * 3, ctrl("q"), KeyEvent("b", "b"))
    assert editor.col == 1
    _, editor = text_editor(files, b"abcdef\n", KeyEvent("right"),
                            *[KeyEvent("right", shift=True)] * 3, KeyEvent("home"),
                            ctrl("q"), ctrl("k"))
    assert editor.col == 4


def test_ctrl_q_y_deletes_to_the_end_of_the_line(files):
    _, editor = text_editor(files, b"abcdef\n", KeyEvent("right"), KeyEvent("right"),
                            ctrl("q"), KeyEvent("y", "y"))
    assert editor.document.encode() == b"ab\n"


def test_column_blocks_take_the_k_commands_too(files):
    SETTINGS.editor.vertical_blocks = True
    _, editor = text_editor(files, b"abcd\nefgh\n", KeyEvent("right"), *chord("b"),
                            KeyEvent("down"), KeyEvent("right"), KeyEvent("right"), *chord("k"),
                            *chord("["))
    assert editor.rectangle == (0, 1, 1, 3)
    assert editor.document.encode() == b"aBCd\neFGh\n"
    _, editor = text_editor(files, b"abcd\nefgh\n", KeyEvent("right"),
                            KeyEvent("right", shift=True), KeyEvent("down", shift=True),
                            KeyEvent("end"), *chord("v"))
    # "b"/"f" out of columns 1-2, in again at the end of line 1: its column 4, less the
    # one column the block took out of it.  The text has no line 2, so one is added.
    assert editor.document.encode() == b"acd\neghb\n   f"


def test_ctrl_q_d_and_t_insert_the_date_and_the_time(files, monkeypatch):
    import time as time_module

    fixed = time_module.strptime("2026-10-04 09:05:07", "%Y-%m-%d %H:%M:%S")
    monkeypatch.setattr("navigator.widgets.editor.file_editor.file_editor._now", lambda: fixed)
    _, editor = text_editor(files, b"ab\n", KeyEvent("right"), ctrl("q"), KeyEvent("d", "d"),
                            KeyEvent(" ", " "), ctrl("q"), ctrl("t"))
    assert editor.document.encode() == b"a04-10-2026 09:05:07b\n"
    assert editor.col == 20


def test_the_date_is_inserted_even_in_overwrite(files, monkeypatch):
    import time as time_module

    fixed = time_module.strptime("2026-10-04", "%Y-%m-%d")
    monkeypatch.setattr("navigator.widgets.editor.file_editor.file_editor._now", lambda: fixed)
    _, editor = text_editor(files, b"ab\n", KeyEvent("insert"), ctrl("q"), KeyEvent("d", "d"))
    assert editor.document.encode() == b"04-10-2026ab\n"


# -- ^K R and ^K W, through DN's file dialog ------------------------------------------------


def block_file(files, text: bytes, *keys, divisor="lf"):
    """*text* in an editor whose file manager shows *files*, then *keys*."""
    SETTINGS.editor.line_divisor = divisor
    return text_editor(files, text, *keys)


def answer(name):
    """Type *name* in the file dialog's name line, and OK."""
    return [lambda a: None, *typed(name), KeyEvent("enter"), lambda a: None]


def test_ctrl_k_w_writes_the_block_with_the_line_divisor(files):
    block_file(files, b"one\r\ntwo\r\nthree\r\n", KeyEvent("down", shift=True),
               KeyEvent("down", shift=True), *chord("w"), *answer("part.txt"), divisor="crlf")
    # DN's BlockWrite: the Editor setup's divisor, none after the last line.
    assert (files / "part.txt").read_bytes() == b"one\r\ntwo\r\n"


def test_ctrl_k_w_asks_overwrite_append_or_cancel(files):
    (files / "part.txt").write_bytes(b"old")
    asked = []
    block_file(files, b"new\n", KeyEvent("end", shift=True), *chord("w"), *answer("part.txt"),
               lambda a: asked.append((a.modal.prompt, a.modal.no.text) if a.modal else None),
               KeyEvent("p", alt=True), lambda a: None)
    assert "already exists" in asked[0][0] and asked[0][1] == "A~p~pend"
    assert (files / "part.txt").read_bytes() == b"oldnew"


def test_ctrl_k_w_overwrites_on_yes_and_keeps_a_read_only_file_read_only(files):
    target = files / "part.txt"
    target.write_bytes(b"old")
    target.chmod(0o444)
    block_file(files, b"new\n", KeyEvent("end", shift=True), *chord("w"), *answer("part.txt"),
               KeyEvent("y", alt=True), lambda a: None,
               KeyEvent("enter"), lambda a: None)  # "Modify it anyway?" -- OK
    assert target.read_bytes() == b"new"
    assert target.stat().st_mode & 0o777 == 0o444


def test_ctrl_k_w_waits_for_a_block(files):
    from navigator.widgets.editor.commands import BlockWrite

    app, _ = text_editor(files, b"abc\n")
    assert app.command_enabled(BlockWrite) is False


def test_ctrl_k_w_writes_a_column_block_line_by_line(files):
    SETTINGS.editor.vertical_blocks = True
    block_file(files, b"abcd\nefgh\n", KeyEvent("right"), *[KeyEvent("right", shift=True)] * 2,
               KeyEvent("down", shift=True), *chord("w"), *answer("cols.txt"))
    assert (files / "cols.txt").read_bytes() == b"bc\nfg"


def test_ctrl_k_r_reads_a_file_in_marks_it_and_ends_column_blocks(files):
    SETTINGS.editor.vertical_blocks = True
    (files / "piece.txt").write_bytes(b"X\nY")
    _, editor = block_file(files, b"ab\r\n", KeyEvent("right"), *chord("r"), *answer("piece.txt"))
    assert editor.document.encode() == b"aX\r\nYb\r\n"
    assert editor.vertical_blocks is False
    assert editor.block_text == "X\nY" and (editor.line, editor.col) == (0, 1)


def test_ctrl_k_r_says_a_name_in_no_directory_is_invalid(files):
    said = []
    _, editor = block_file(files, b"ab\n", *chord("r"), *answer("nowhere/x.txt"),
                           lambda a: said.append(a.modal.prompt if a.modal else None))
    assert said == ["Invalid file name."]
    assert editor.document.encode() == b"ab\n"


# -- ^K1-9 and ^Q1-9: markers --------------------------------------------------------------------


def lines(count: int) -> bytes:
    return b"".join(b"line %03d\n" % n for n in range(count))


def test_ctrl_k_digit_places_a_marker_and_ctrl_q_digit_returns_to_it(files):
    _, editor = text_editor(files, lines(10), KeyEvent("down"), KeyEvent("down"),
                            KeyEvent("right"), *chord("3"), ctrl("pagedown"),
                            ctrl("q"), KeyEvent("3", "3"))
    assert (editor.line, editor.col) == (2, 1)


def test_going_to_a_marker_centres_it(files):
    _, editor = text_editor(files, lines(200), *[KeyEvent("pagedown")] * 4, *chord("1"),
                            ctrl("pageup"), ctrl("q"), KeyEvent("1", "1"))
    assert editor.top == max(0, editor.line - editor.height // 2)
    assert editor.top > 0


def test_an_unset_marker_goes_nowhere(files):
    _, editor = text_editor(files, lines(10), KeyEvent("down"), ctrl("q"), KeyEvent("7", "7"))
    assert (editor.line, editor.col) == (1, 0)


def test_a_markers_digit_never_types(files):
    _, editor = text_editor(files, b"abc\n", *chord("5"), ctrl("q"), KeyEvent("5", "5"))
    assert editor.document.encode() == b"abc\n"


def test_markers_come_back_with_the_edit_history(files):
    (files / "text.txt").write_bytes(lines(10))
    SETTINGS.interface.store_editor_position = False  # the markers come back regardless
    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None,
                  *[KeyEvent("down")] * 4, *chord("9"), KeyEvent("escape"), lambda a: None,
                  KeyEvent("f4"), lambda a: None, ctrl("q"), KeyEvent("9", "9"),
                  lambda a: seen.update(at=(editor_window(a).editor.line, editor_window(a).editor.col))])
    assert seen["at"] == (4, 0)
    from navigator.models.edit_record import EditRecord

    assert EditRecord.find(files / "text.txt").marks == ",,,,,,,,4:0"


# -- ^K S / Alt+T: sort block -----------------------------------------------------------------------


def column_marked(text: bytes, left: int, width: int, down: int):
    """Keys marking a column block from (0, *left*), *width* wide, *down* lines further."""
    return [*[KeyEvent("right")] * left, *[KeyEvent("right", shift=True)] * width,
            *[KeyEvent("down", shift=True)] * down]


def test_sort_orders_the_lines_by_the_blocks_columns(files):
    SETTINGS.editor.vertical_blocks = True
    text = b"x 3 c\ny 1 a\nz 2 b\nkeep\n"
    _, editor = text_editor(files, text, *column_marked(text, 2, 1, 2), KeyEvent("t", alt=True))
    assert editor.document.encode() == b"y 1 a\nz 2 b\nx 3 c\nkeep\n"
    assert editor.rectangle == (0, 2, 2, 3)


def test_sort_by_ctrl_k_s_keeps_each_places_line_ending_and_one_undo_restores(files):
    SETTINGS.editor.vertical_blocks = True
    text = b"b\r\na\nc"
    _, editor = text_editor(files, text, *column_marked(text, 0, 1, 2), *chord("s"))
    assert editor.document.encode() == b"a\r\nb\nc"
    _, editor = text_editor(files, text, *column_marked(text, 0, 1, 2), *chord("s"),
                            KeyEvent("backspace", alt=True))
    assert editor.document.encode() == text


def test_sort_is_case_sensitive_and_stable(files):
    SETTINGS.editor.vertical_blocks = True
    text = b"b2\na1\nB3\nb4\n"
    _, editor = text_editor(files, text, *column_marked(text, 0, 1, 3), KeyEvent("t", alt=True))
    assert editor.document.encode() == b"B3\na1\nb2\nb4\n"


def test_sort_needs_a_column_block(files):
    said = []
    _, editor = text_editor(files, b"b\na\n", KeyEvent("down", shift=True), KeyEvent("t", alt=True),
                            lambda a: None, lambda a: said.append(a.modal.prompt if a.modal else None))
    assert said == ["Vertical blocks need for this operation"]
    assert editor.document.encode() == b"b\na\n"


# -- Alt+Ins: calculate sum ------------------------------------------------------------------------


def test_alt_ins_puts_the_column_blocks_sum_on_the_clipboard(files):
    SETTINGS.editor.vertical_blocks = True
    text = b"a  12.5 x\nb   0.1 y\nc  n/a  z\nd  -2   w\n"
    app, editor = text_editor(files, text, *column_marked(text, 2, 5, 3), KeyEvent("insert", alt=True))
    assert app.terminal.clipboard == [("10.6", False)]
    assert editor.document.encode() == text  # the text is left alone


def test_the_sum_is_exact_and_written_without_trailing_zeros():
    from navigator.widgets.editor.file_editor.file_editor import block_sum

    assert block_sum(["0.1", "0.2"]) == "0.3"
    assert block_sum([" 1 000", "x", "-3"]) == "997"  # blanks removed, a word is nothing
    assert block_sum(["1e2", "2.50"]) == "102.5"
    assert block_sum([]) == "0"


def test_calculate_needs_a_column_block(files):
    said = []
    app, _ = text_editor(files, b"1\n2\n", KeyEvent("down", shift=True), KeyEvent("insert", alt=True),
                         lambda a: None, lambda a: said.append(a.modal.prompt if a.modal else None))
    assert said == ["Vertical blocks need for this operation"]
    assert app.terminal.clipboard == []


def test_ctrl_k_u_stays_unindent(files):
    from navigator.widgets.editor.commands import UnindentBlock
    from navigator.widgets.editor.file_editor import FileEditor
    from navkit.commands import key_table

    assert key_table(FileEditor)["ctrl+k u"] is UnindentBlock


# -- ^K P / Shift+F8: print block --------------------------------------------------------------------


@pytest.fixture
def spooler(monkeypatch):
    """``lp`` stood in for: what it was given, and what it answers."""
    import subprocess

    from navigator import printing

    jobs = []
    answer = {"code": 0, "stderr": b""}

    def run(argv, input=None, **kwargs):
        jobs.append((argv, input))
        return subprocess.CompletedProcess(argv, answer["code"], b"", answer["stderr"])

    monkeypatch.setattr(printing.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(printing.subprocess, "run", run)
    return jobs, answer


def test_shift_f8_asks_and_prints_the_block(files, spooler):
    jobs, _ = spooler
    asked = []
    text_editor(files, b"one\ntwo\nthree\n", KeyEvent("down", shift=True), KeyEvent("end", shift=True),
                KeyEvent("f8", shift=True), lambda a: None,
                lambda a: asked.append(a.modal.prompt if a.modal else None),
                KeyEvent("y", alt=True), lambda a: None, lambda a: None)
    assert asked == ["Print 2 lines?"]
    assert jobs == [(["lp"], b"one\ntwo\n")]


def test_ctrl_k_p_prints_and_no_prints_nothing(files, spooler):
    jobs, _ = spooler
    text_editor(files, b"one\ntwo\n", KeyEvent("end", shift=True), *chord("p"), lambda a: None,
                KeyEvent("n", alt=True), lambda a: None)
    assert jobs == []


def test_a_spooler_that_refuses_says_why(files, spooler):
    jobs, answer = spooler
    answer.update(code=1, stderr=b"lp: Error - No default destination.")
    said = []
    text_editor(files, b"one\n", KeyEvent("end", shift=True), KeyEvent("f8", shift=True), lambda a: None,
                KeyEvent("y", alt=True), lambda a: None, lambda a: None,
                lambda a: said.append(a.modal.prompt if a.modal else None))
    assert said == ["Cannot print: lp: Error - No default destination."]


def test_print_block_waits_for_a_block(files, spooler):
    from navigator.widgets.editor.commands import PrintBlock

    app, _ = text_editor(files, b"one\n")
    assert app.command_enabled(PrintBlock) is False


def test_lpr_stands_in_where_there_is_no_lp():
    from navigator.printing import print_command

    assert print_command(lambda name: "/bin/lp" if name == "lp" else None) == ["lp"]
    assert print_command(lambda name: "/bin/lpr" if name == "lpr" else None) == ["lpr"]
    assert print_command(lambda name: None) is None


def test_f8_prints_the_whole_text_as_it_stands(files, spooler):
    jobs, _ = spooler
    asked = []
    text_editor(files, b"one\r\ntwo\r\n", KeyEvent("end"), *typed("!"),
                KeyEvent("f8"), lambda a: None,
                lambda a: asked.append(a.modal.prompt if a.modal else None),
                KeyEvent("y", alt=True), lambda a: None, lambda a: None)
    # The unsaved edit is printed; the line break at the end makes no third line.
    assert asked == ["Print 2 lines?"]
    assert jobs == [(["lp"], b"one!\ntwo\n")]


def test_print_file_is_the_one_command_the_manager_binds_too():
    from navigator.commands import PrintFile
    from navigator.widgets.manager import commands as manager_commands

    assert manager_commands.PrintFile is PrintFile


# -- Alt+Left/Right, ^Q[ / ^Q^]: the bracket pair --------------------------------------------------


def test_alt_right_on_an_opening_bracket_goes_to_its_close_across_lines(files):
    text = b"f(a, (b),\n  c) + x\n"
    _, editor = text_editor(files, text, KeyEvent("right"), KeyEvent("right", alt=True))
    assert (editor.line, editor.col) == (1, 3)


def test_a_closing_bracket_goes_back_to_its_opener(files):
    text = b"f(a, (b),\n  c) + x\n"
    _, editor = text_editor(files, text, KeyEvent("down"), *[KeyEvent("right")] * 3,
                            KeyEvent("left", alt=True))
    assert (editor.line, editor.col) == (0, 1)


def test_only_the_same_kind_of_bracket_counts(files):
    text = b"[ ( ] ) ]\n"
    _, editor = text_editor(files, text, ctrl("q"), KeyEvent("[", "["))
    assert (editor.line, editor.col) == (0, 4)


def test_ctrl_q_ctrl_close_bracket_is_the_same_command(files):
    text = b"{x}\n"
    _, editor = text_editor(files, text, ctrl("q"), KeyEvent("]", ctrl=True))
    assert (editor.line, editor.col) == (0, 2)


def test_no_bracket_or_no_pair_stays_put(files):
    _, editor = text_editor(files, b"ab(c\n", KeyEvent("right", alt=True))
    assert (editor.line, editor.col) == (0, 0)
    _, editor = text_editor(files, b"ab(c\n", KeyEvent("right"), KeyEvent("right"),
                            KeyEvent("right", alt=True))
    assert (editor.line, editor.col) == (0, 2)


# -- the info line's block indicator ---------------------------------------------------------------


def click_info(at):
    """A left click on the info line, *at(editor)* columns into it, through the screen."""
    from navkit.events import MouseClickEvent

    def action(app):
        window = editor_window(app)
        info = window.info
        ox, oy = info.offset()
        x, y = ox + info.x + at(window.editor), oy + info.y
        app.post_event(MouseClickEvent(x=x, y=y, button="left", action="press"))
        app.post_event(MouseClickEvent(x=x, y=y, button="left", action="release"))
    return action


def test_a_click_on_the_block_indicator_switches_column_blocks(files):
    seen = []
    (files / "text.txt").write_bytes(b"abcdef\nghijkl\n")
    SETTINGS.interface.store_editor_position = False
    app = navigator(files)

    def look(a):
        editor = editor_window(a).editor
        seen.append((editor.vertical_blocks, editor.rectangle))

    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None,
                  KeyEvent("right", shift=True), KeyEvent("down", shift=True),
                  click_info(lambda e: e.block_indicator()[0] + 1), lambda a: None, look])
    assert seen == [(True, (0, 0, 1, 1))]  # the stream block, read as a rectangle


def test_a_click_elsewhere_on_the_info_line_does_nothing(files):
    seen = []
    (files / "text.txt").write_bytes(b"abc\n")
    SETTINGS.interface.store_editor_position = False
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None,
                  click_info(lambda e: 4), lambda a: None,
                  lambda a: seen.append((editor_window(a).editor.vertical_blocks,
                                         editor_window(a).zoomed))])
    assert seen == [(False, True)]


def test_the_indicator_is_found_however_long_the_code_before_it():
    from navigator.widgets.editor.file_editor import FileEditor

    editor = FileEditor()
    editor.buffer.document.lines[0] = "中"  # a code past three digits
    editor.revision += 1
    start, end = editor.block_indicator()
    assert editor.info_text[start:end] in ("(↔)", "(-)")


# -- Alt+G: go to line ------------------------------------------------------------------------------


def test_alt_g_goes_to_the_line_typed_keeping_the_column(files):
    _, editor = text_editor(files, lines(30), KeyEvent("right"), KeyEvent("right"),
                            KeyEvent("g", alt=True), lambda a: None, *typed("17"),
                            KeyEvent("enter"), lambda a: None)
    assert (editor.line, editor.col) == (16, 2)


def test_a_line_past_the_end_is_the_last_and_nonsense_goes_nowhere(files):
    _, editor = text_editor(files, lines(5), KeyEvent("g", alt=True), lambda a: None,
                            *typed("999"), KeyEvent("enter"), lambda a: None)
    assert editor.line == len(editor.document) - 1
    for text in ("0", "-3", "x"):
        _, editor = text_editor(files, lines(5), KeyEvent("down"), KeyEvent("g", alt=True),
                                lambda a: None, *typed(text), KeyEvent("enter"), lambda a: None)
        assert editor.line == 1, text


def test_goto_line_opens_with_the_number_last_typed(files):
    from navigator.widgets.editor.goto_line_dialog import GotoLineDialog
    from navigator.widgets.editor.goto_line_dialog import goto_line_dialog as module

    module._last["text"] = "12"
    assert GotoLineDialog().number.value == "12"


def test_a_click_on_the_info_lines_place_asks_for_a_line(files):
    seen = []
    (files / "text.txt").write_bytes(lines(5))
    SETTINGS.interface.store_editor_position = False
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None,
                  click_info(lambda e: e.place_indicator()[0]), lambda a: None,
                  lambda a: seen.append(a.modal.title if a.modal else None)])
    assert seen == ["Goto Line"]


# -- Ctrl+P / the info line's code: the character table --------------------------------------------


@pytest.fixture
def chart_on(monkeypatch):
    from navigator.widgets.shell.ascii_chart import ascii_chart as module

    def start(code):
        monkeypatch.setitem(module._last, "code", code)
    return start


def test_ctrl_p_types_the_character_picked(files, chart_on):
    chart_on(65)
    _, editor = text_editor(files, b"xy\n", KeyEvent("right"), KeyEvent("p", ctrl=True),
                            lambda a: None, KeyEvent("right"), KeyEvent("enter"), lambda a: None)
    assert editor.document.encode() == b"xBy\n"


def test_a_box_drawing_character_goes_in_as_unicode(files, chart_on):
    chart_on(0xB3)
    _, editor = text_editor(files, b"a\n", KeyEvent("p", ctrl=True), lambda a: None,
                            KeyEvent("enter"), lambda a: None)
    assert editor.document.encode() == "│a\n".encode()


def test_a_click_on_the_info_lines_code_opens_the_chart(files, chart_on):
    seen = []
    (files / "text.txt").write_bytes(b"abc\n")
    SETTINGS.interface.store_editor_position = False
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None,
                  click_info(lambda e: e.code_indicator()[0] + 1), lambda a: None,
                  lambda a: seen.append(a.modal.title if a.modal else None)])
    assert seen == ["ASCII Chart"]


def test_the_code_indicator_is_the_bracketed_code():
    from navigator.widgets.editor.file_editor import FileEditor

    editor = FileEditor()
    start, end = editor.code_indicator()
    assert editor.info_text[start:end] == "[000]"


# -- F3 Open and Shift+F2 Save as --------------------------------------------------------------------


def test_f3_opens_another_file_into_the_window(files):
    (files / "other.txt").write_bytes(b"other text\n")
    seen = []
    app, editor = text_editor(files, b"first\n", KeyEvent("f3"), lambda a: None,
                              lambda a: seen.append((a.modal.title, a.modal.pick.text) if a.modal else None),
                              *typed("other.txt"), KeyEvent("enter"), lambda a: None)
    assert seen == [("Open a File", "~O~pen")]
    assert editor.path == files / "other.txt"
    assert editor.document.encode() == b"other text\n"
    assert editor_window(app).title == f"Edit - {files / 'other.txt'}"


def test_f3_on_a_changed_text_asks_first_and_cancel_keeps_it(files):
    asked = []
    _, editor = text_editor(files, b"first\n", *typed("x"), KeyEvent("f3"), lambda a: None,
                            lambda a: asked.append(a.modal.prompt if a.modal else None),
                            KeyEvent("escape"), lambda a: None)
    assert asked == ["File text.txt was modified. Save?"]
    assert editor.document.encode() == b"xfirst\n" and editor.path == files / "text.txt"


def test_a_file_that_will_not_open_is_said_and_the_text_stays(files):
    said = []
    _, editor = text_editor(files, b"first\n", KeyEvent("f3"), lambda a: None,
                            *typed("missing.txt"), KeyEvent("enter"), lambda a: None,
                            lambda a: said.append(a.modal.prompt if a.modal else None))
    assert said and said[0].startswith("Cannot open")
    assert editor.document.encode() == b"first\n"


def test_shift_f2_saves_under_a_new_name_and_the_window_takes_it(files):
    seen = []
    app, editor = text_editor(files, b"first\n", *typed("x"), KeyEvent("f2", shift=True), lambda a: None,
                              lambda a: seen.append(a.modal.title if a.modal else None),
                              *typed("copy.txt"), KeyEvent("enter"), lambda a: None)
    assert seen == ["Save File As"]
    assert (files / "copy.txt").read_bytes() == b"xfirst\n"
    assert (files / "text.txt").read_bytes() == b"first\n"  # the old file untouched
    assert editor.path == files / "copy.txt" and not editor.modified
    assert editor_window(app).title == f"Edit - {files / 'copy.txt'}"


def test_save_as_over_a_file_asks_yes_or_cancel_without_append(files):
    (files / "copy.txt").write_bytes(b"old")
    asked = []
    _, editor = text_editor(files, b"new\n", KeyEvent("f2", shift=True), lambda a: None,
                            *typed("copy.txt"), KeyEvent("enter"), lambda a: None,
                            lambda a: asked.append((a.modal.prompt, a.modal.no.text) if a.modal else None),
                            KeyEvent("escape"), lambda a: None)
    assert "OK to overwrite it?" in asked[0][0] and asked[0][1] == "Cancel"
    assert (files / "copy.txt").read_bytes() == b"old"
    assert editor.path == files / "text.txt"


# -- Ctrl+F2: save all ------------------------------------------------------------------------------


def test_ctrl_f2_saves_every_changed_editor_and_leaves_the_rest(files):
    (files / "one.txt").write_bytes(b"one\n")
    (files / "two.txt").write_bytes(b"two\n")
    (files / "three.txt").write_bytes(b"three\n")
    stamp = (files / "three.txt").stat().st_mtime_ns
    SETTINGS.interface.store_editor_position = False
    app = navigator(files)

    def open_editor_on(name):
        def action(a):
            from navigator.file_history import open_editor
            open_editor(a.shell.desktop, files / name)
        return action

    run_app(app, [open_editor_on("one.txt"), lambda a: None, *typed("1"),
                  open_editor_on("two.txt"), lambda a: None, *typed("2"),
                  open_editor_on("three.txt"), lambda a: None,
                  KeyEvent("f2", ctrl=True), lambda a: None, lambda a: None])
    assert (files / "one.txt").read_bytes() == b"1one\n"
    assert (files / "two.txt").read_bytes() == b"2two\n"
    assert (files / "three.txt").stat().st_mtime_ns == stamp  # unchanged, not rewritten


def test_ctrl_f2_in_an_editor_is_not_hide_right(files):
    seen = []
    app, _ = text_editor(files, b"abc\n", *typed("x"), KeyEvent("f2", ctrl=True), lambda a: None,
                         lambda a: seen.append(a.manager.hidden_side))
    assert seen == [None]
    assert (files / "text.txt").read_bytes() == b"xabc\n"


# -- F7 find, Ctrl+F7 replace, Shift+F7 again, Alt+F7 reversed ---------------------------------------


@pytest.fixture
def fresh_search(monkeypatch):
    """A search record of DN's defaults for each test, as a new session has."""
    from navigator.editor import search

    data = search.SearchData()
    monkeypatch.setattr(search, "SEARCH", data)
    return data


def set_dialog(**changes):
    """An action setting the open dialog's controls: ``options=``, ``direction=``..."""
    def action(app):
        for name, value in changes.items():
            control = getattr(app.modal, name)
            control.value = value
            if hasattr(control, "sel"):
                control.sel = value
    return action


def modal_text(seen):
    return lambda a: seen.append(a.modal.prompt if a.modal else None)


TEXT = b"one cat\ntwo Cat\ncat three\n"


def test_f7_finds_from_the_start_and_lights_the_match(files, fresh_search):
    seen = {}
    _, editor = text_editor(files, TEXT, KeyEvent("down"), KeyEvent("f7"), lambda a: None,
                            *typed("cat"), KeyEvent("enter"), lambda a: None,
                            lambda a: seen.update(lit=editor_window(a).editor._found_columns(0)))
    assert (editor.line, editor.col) == (0, 7)
    assert seen["lit"] == (4, 7)


def test_the_find_dialog_opens_on_the_word_at_the_cursor(files, fresh_search):
    seen = []
    text_editor(files, TEXT, KeyEvent("right"), KeyEvent("f7"), lambda a: None,
                lambda a: seen.append(a.modal.text.value))
    assert seen == ["one"]


def test_shift_f7_finds_the_next_and_alt_f7_the_one_before(files, fresh_search):
    _, editor = text_editor(files, TEXT, KeyEvent("f7"), lambda a: None, *typed("cat"),
                            KeyEvent("enter"), lambda a: None,
                            KeyEvent("f7", shift=True), lambda a: None,
                            KeyEvent("f7", shift=True), lambda a: None)
    assert (editor.line, editor.col) == (2, 3)  # "Cat" counted: no case
    _, editor = text_editor(files, TEXT, KeyEvent("f7"), lambda a: None, *typed("cat"),
                            KeyEvent("enter"), lambda a: None,
                            KeyEvent("f7", shift=True), lambda a: None,
                            KeyEvent("f7", alt=True), lambda a: None)
    assert (editor.line, editor.col) == (0, 4)


def test_case_and_whole_words_and_backward(files, fresh_search):
    _, editor = text_editor(files, TEXT, KeyEvent("f7"), lambda a: None, *typed("Cat"),
                            set_dialog(options=1), KeyEvent("enter"), lambda a: None)
    assert (editor.line, editor.col) == (1, 7)
    _, editor = text_editor(files, TEXT, KeyEvent("f7"), lambda a: None, *typed("cat"),
                            set_dialog(direction=1), KeyEvent("enter"), lambda a: None)
    assert (editor.line, editor.col) == (2, 0)  # from the end, backward: the last


def test_nothing_found_says_so_and_the_cursor_stays(files, fresh_search):
    said = []
    _, editor = text_editor(files, TEXT, KeyEvent("down"), KeyEvent("f7"), lambda a: None,
                            *typed("dog"), KeyEvent("enter"), lambda a: None, modal_text(said))
    assert said == ["Search string not found"]
    assert (editor.line, editor.col) == (1, 0)


def test_selected_text_searches_only_the_block(files, fresh_search):
    _, editor = text_editor(files, TEXT, KeyEvent("down"), KeyEvent("down", shift=True),
                            KeyEvent("down", shift=True), KeyEvent("f7"), lambda a: None,
                            *typed("cat"), set_dialog(scope=1), KeyEvent("enter"), lambda a: None)
    assert (editor.line, editor.col) == (1, 7)


def test_replace_asks_and_yes_replaces_the_first_only(files, fresh_search):
    asked = []
    _, editor = text_editor(files, TEXT, KeyEvent("f7", ctrl=True), lambda a: None,
                            *typed("cat"), KeyEvent("tab"), *typed("dog"), KeyEvent("enter"),
                            lambda a: None, modal_text(asked), KeyEvent("y", alt=True), lambda a: None)
    assert asked == ["Replace this occurence?"]
    assert editor.document.encode() == b"one dog\ntwo Cat\ncat three\n"


def replace_cat_with_dog(a):
    """Fill *Replace* in: ``cat`` for ``dog``, whatever the last one left there."""
    a.modal.text.value, a.modal.new.value = "cat", "dog"


def test_change_all_with_all_replaces_everything_and_one_undo_takes_one_back(files, fresh_search):
    def change_all(a):
        a.spawn(a.modal.on_all_click(None))

    _, editor = text_editor(files, TEXT, KeyEvent("f7", ctrl=True), lambda a: None,
                            replace_cat_with_dog, change_all, lambda a: None,
                            KeyEvent("a", alt=True), lambda a: None, lambda a: None)
    assert editor.document.encode() == b"one dog\ntwo dog\ndog three\n"
    _, editor = text_editor(files, TEXT, KeyEvent("f7", ctrl=True), lambda a: None,
                            replace_cat_with_dog, change_all, lambda a: None,
                            KeyEvent("a", alt=True), lambda a: None, lambda a: None,
                            KeyEvent("enter"), lambda a: None,  # "2 replaces made": after All, unasked
                            KeyEvent("backspace", alt=True))
    assert editor.document.encode() == b"one dog\ntwo dog\ncat three\n"


def test_change_all_without_prompting_counts_what_it_made(files, fresh_search):
    said = []

    def change_all(a):
        a.modal.options.value = 0  # no prompt on replace
        a.spawn(a.modal.on_all_click(None))

    _, editor = text_editor(files, TEXT, KeyEvent("f7", ctrl=True), lambda a: None,
                            *typed("cat"), KeyEvent("tab"), *typed("dog"), change_all, lambda a: None,
                            lambda a: None, modal_text(said))
    assert said == ["3 replaces made"]
    assert editor.document.encode() == b"one dog\ntwo dog\ndog three\n"


def test_ctrl_q_f_and_a_open_find_and_replace(files, fresh_search):
    seen = []
    text_editor(files, TEXT, ctrl("q"), KeyEvent("f", "f"), lambda a: None,
                lambda a: seen.append(a.modal.title), KeyEvent("escape"), lambda a: None,
                ctrl("q"), ctrl("a"), lambda a: None, lambda a: seen.append(a.modal.title))
    assert seen == ["Find", "Replace"]
