"""Soft wrap: ``navigator.lib.editor.softwrap`` and the editor showing long lines on several rows.

A departure (DN's *Auto wrap* put real breaks in the text): the text never
changes, the cursor stays a line and a column of it, and only the painting
and the vertical movement learn of rows.
"""

from __future__ import annotations

import pytest

from conftest import IDLE, FakeTerminal, Until, run_app, settle
from navkit.events import KeyEvent, MouseClickEvent, PasteEvent
from navkit.screen import ScreenBuffer

from navigator.__main__ import Navigator
from navigator.lib.editor.columns import cells
from navigator.lib.editor.softwrap import column_at, locate, rows
from navigator.settings import SETTINGS


# -- the model ------------------------------------------------------------------------------


def shown(text: str, width: int) -> list[str]:
    line = cells(text, 8)
    return ["".join(glyph for glyph, _ in line[start:stop]) for start, stop in rows(line, width)]


def test_a_row_ends_at_the_last_blank_that_fits_and_keeps_it():
    assert shown("the quick brown fox jumps", 10) == ["the quick ", "brown fox ", "jumps"]


def test_a_word_longer_than_a_row_is_cut_where_the_row_ends():
    assert shown("abcdefghijklmnop", 5) == ["abcde", "fghij", "klmno", "p"]


def test_a_wide_character_is_never_split_and_a_full_last_row_gets_one_more():
    assert shown("ab日本語", 4) == ["ab日", "本語", ""]
    assert shown("abcde", 5) == ["abcde", ""]  # the caret at the end needs a cell
    assert shown("", 5) == [""]


def test_a_tab_is_the_columns_it_covers_from_the_lines_start():
    assert shown("a\tb", 4) == ["a   ", "    ", "b"]


def test_locate_and_column_at_go_back_and_forth():
    line_rows = rows(cells("the quick brown fox", 8), 10)
    assert line_rows == [(0, 10), (10, 19)]
    assert locate(line_rows, 4) == (0, 4)
    assert locate(line_rows, 10) == (1, 0)      # where one row ends and the next begins: the next's
    assert locate(line_rows, 19) == (1, 9)      # the line's end: its last row
    assert column_at(line_rows, 1, 3) == 13
    assert column_at(line_rows, 0, 20) == 9      # held to the row's last cell
    assert column_at(line_rows, 1, 20) == 30     # the last row's past the end, with line_end


# -- the editor ---------------------------------------------------------------------------------


LONG = "the quick brown fox jumps over the lazy dog and keeps running far away"
TEXT = f"short\n{LONG}\nend\n"


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "dir").mkdir()
    return tmp_path


def window(app):
    from navigator.widgets.editor.edit_window import EditWindow

    found = app.shell.desktop.active_window
    return found if isinstance(found, EditWindow) else None


def wrapped(files, text, *keys, width=32, height=12, **settings):
    """*text* in an editor with soft wrap on, 32 by 12 (an area 30 wide), then *keys*: the app and editor."""
    SETTINGS.editor.soft_wrap = True
    SETTINGS.interface.store_editor_position = False
    for name, value in settings.items():
        setattr(SETTINGS.editor, name, value)
    from navigator.models.edit_record import EditRecord
    from navigator.models.file_record import key_of

    # Each open a fresh one: the edit history would bring the last one's modes back.
    EditRecord.where(path=key_of(files / "text.txt")).delete()
    (files / "text.txt").write_text(text)
    app = Navigator(files, files, terminal=FakeTerminal(width, height))
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), Until(lambda a: window(a) is not None), IDLE, *keys])
    return app, window(app).editor


def screen(app, width=32, height=12) -> ScreenBuffer:
    buffer = ScreenBuffer(width, height)
    app.shell.layout(width, height)
    settle()
    app.shell.render_tree(buffer)
    return buffer


def painted(app, editor) -> list[str]:
    buffer = screen(app)
    ox, oy = editor.offset()
    return ["".join(buffer.get(ox + editor.x + x, oy + editor.y + y)[0] or " " for x in range(editor.width))
            for y in range(editor.height)]


def test_a_long_line_is_shown_on_several_rows_and_the_text_is_unchanged(files):
    app, editor = wrapped(files, TEXT)
    rows_shown = painted(app, editor)
    assert [row.rstrip() for row in rows_shown[:5]] == [
        "short", "the quick brown fox jumps", "over the lazy dog and keeps", "running far away", "end"]
    assert editor.document.lines[1] == LONG and editor.left == 0
    assert not editor.overflows_across


def test_down_and_up_go_by_rows_keeping_the_screen_column(files):
    _, editor = wrapped(files, TEXT, KeyEvent("down"), *[KeyEvent("right")] * 4, KeyEvent("down"))
    assert (editor.line, editor.col) == (1, 30)          # row 1 of the line (from 26), four along
    _, editor = wrapped(files, TEXT, KeyEvent("down"), *[KeyEvent("right")] * 4,
                        *[KeyEvent("down")] * 3)
    assert (editor.line, editor.col) == (2, 3)           # past the line's last row: the next line, held to its end
    _, editor = wrapped(files, TEXT, KeyEvent("down"), *[KeyEvent("right")] * 4,
                        *[KeyEvent("down")] * 3, KeyEvent("up"))
    assert (editor.line, editor.col) == (1, 58)          # back on the last row (from 54), the goal column kept


def test_home_and_end_stay_the_lines_own_start_and_end(files):
    _, editor = wrapped(files, TEXT, KeyEvent("down"), KeyEvent("down"), KeyEvent("end"))
    assert (editor.line, editor.col) == (1, len(LONG))
    _, editor = wrapped(files, TEXT, KeyEvent("down"), KeyEvent("down"), KeyEvent("end"), KeyEvent("home"))
    assert (editor.line, editor.col) == (1, 0)


def test_typing_at_a_rows_end_wraps_again_and_the_cursor_follows(files):
    app, editor = wrapped(files, "abcd efgh ijkl mnop qrst uvwx\n", KeyEvent("end"), PasteEvent(" yz"))
    rows_shown = painted(app, editor)
    assert rows_shown[1].startswith("yz")
    x, y = editor.cursor_cell()
    assert (x, y) == (2, 1)


def test_a_line_taller_than_the_screen_scrolls_by_rows(files):
    text = " ".join(f"w{n:02}" for n in range(200)) + "\n"
    _, editor = wrapped(files, text, KeyEvent("pagedown"))
    assert editor.top == 0 and editor.top_row > 0
    _, editor = wrapped(files, text, KeyEvent("down", ctrl=True), KeyEvent("down", ctrl=True))
    assert (editor.top, editor.top_row) == (0, 2)


def test_a_click_on_a_wrapped_row_puts_the_cursor_at_its_column(files):
    _, editor = wrapped(files, TEXT, lambda a: a.spawn(window(a).editor.on_mouse_click(
        MouseClickEvent(x=4, y=2, button="left", action="press"))), IDLE)
    assert (editor.line, editor.col) == (1, 30)


def test_the_block_and_current_line_paint_on_every_row_they_cover(files):
    app, editor = wrapped(files, TEXT, KeyEvent("down"), KeyEvent("end", shift=True))
    lit = editor.part_style("selected")
    buffer = screen(app)
    ox, oy = editor.offset()
    for y in (1, 2, 3):                                   # the long line's three rows
        assert buffer.get(ox + editor.x + 2, oy + editor.y + y)[1] == lit
    app, editor = wrapped(files, TEXT, KeyEvent("down"), highlight_line=True)
    current = editor.part_style("current_line")
    buffer = screen(app)
    ox, oy = editor.offset()
    for y in (1, 2, 3):                                   # past each row's text too
        assert buffer.get(ox + editor.x + 29, oy + editor.y + y)[1] == current
    assert buffer.get(ox + editor.x + 29, oy + editor.y + 4)[1] != current


def test_line_numbers_number_only_a_lines_first_row(files):
    app, editor = wrapped(files, TEXT, line_numbers=True)
    gutter = window(app).gutter
    buffer = screen(app)
    ox, oy = gutter.offset()
    numbers = ["".join(buffer.get(ox + gutter.x + x, oy + gutter.y + y)[0] for x in range(gutter.width)).strip()
               for y in range(5)]
    assert numbers == ["1", "2", "", "", "3"]


def test_soft_wrap_and_column_blocks_exclude_each_other(files):
    from navigator.widgets.editor.commands import SwitchBlock, SwitchSoftWrap

    _, editor = wrapped(files, TEXT)
    assert editor.refusal(SwitchBlock()) == "Not with soft wrap"
    _, editor = wrapped(files, TEXT, vertical_blocks=True)
    assert editor.soft_wrap is False                       # column blocks win
    assert editor.refusal(SwitchSoftWrap()) == "Not with column blocks"


def test_switching_it_from_the_menu_and_off_again(files):
    from navigator.widgets.editor.commands import SwitchSoftWrap

    def switch(a):
        a.spawn(a.run_command(SwitchSoftWrap(), window(a).editor))

    SETTINGS.editor.soft_wrap = False
    (files / "text.txt").write_text(TEXT)
    app = Navigator(files, files, terminal=FakeTerminal(32, 12))
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), IDLE, switch, IDLE,
                  lambda a: seen.update(on=window(a).editor.soft_wrap,
                                        ticked=window(a).editor.checks(SwitchSoftWrap())),
                  switch, IDLE, lambda a: seen.update(off=window(a).editor.soft_wrap)])
    assert seen == {"on": True, "ticked": True, "off": False}


def test_a_right_to_left_line_wraps_and_each_row_is_ordered_on_its_own(files):
    hebrew = " ".join(["שלום"] * 12)
    app, editor = wrapped(files, hebrew + "\n")
    rows_shown = painted(app, editor)
    # The buffer holds cells in screen order: each word is painted right to left.
    full = [row for row in rows_shown if "םולש" in row]
    assert len(full) == 2 and len(editor._rows(0)) == 2
    # Each row ordered on its own and right-aligned: its text ends against the right edge.
    assert all(row == row.rstrip() for row in full)
    assert all(row.count("םולש") == 6 for row in full)
