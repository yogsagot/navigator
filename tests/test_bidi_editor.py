"""Right-to-left lines in the F4 editor: right-aligned, and what follows from it.

A line whose first strong letter is Hebrew or Arabic is painted against the
window's right edge (``_laid_line``), its end the cell left of its text.
"""

from __future__ import annotations

import asyncio

from navkit.screen import ScreenBuffer
from navigator.lib.editor import columns
from navigator.lib.editor.document import Pos

from test_bidi import row, shown

WIDTH = 30


def _editor(tmp_path, text: str, col: int = 0, width: int = WIDTH):
    from navigator.widgets.editor.file_editor import FileEditor

    (tmp_path / "t.txt").write_text(text, encoding="utf-8")
    editor = FileEditor(width=width, height=3)
    editor.open(tmp_path / "t.txt")
    editor.col = col
    return editor


def _painted(editor, y: int = 0) -> str:
    buffer = ScreenBuffer(editor.width, editor.height)
    editor.render(buffer)
    return row(buffer, y)


def _move(editor, command: str, *, extend: bool = False, times: int = 1) -> None:
    from navigator.widgets.editor import commands

    name = "".join(part.title() for part in command.split("_"))
    event = getattr(commands, f"Move{name}")(extend=True) if extend else None
    for _ in range(times):
        asyncio.run(getattr(editor, f"on_move_{command}")(event))


def _word(editor, command: str) -> None:
    asyncio.run(getattr(editor, f"on_word_{command}")(None))


def _x(editor) -> int:
    return editor.cursor_position()[0]


def _lit(editor) -> str:
    """The characters of line 0 the block lights, left to right as painted."""
    text = editor.document.lines[0]
    cells, order, _ = editor._laid(0)
    picked = editor._block_picked(0)
    assert picked is not None
    return "".join(s for at, s in order if s and cells[at][1] in picked[0])


# -- painting -------------------------------------------------------------------


def test_a_hebrew_line_ends_against_the_right_edge(tmp_path):
    editor = _editor(tmp_path, "שלום 12.txt\nabc\n", width=20)
    assert _painted(editor) == " " * 9 + shown("שלום 12.txt")
    assert _painted(editor, 1).rstrip() == "abc"  # a left-to-right line as ever


def test_a_left_to_right_line_with_hebrew_in_it_stays_left(tmp_path):
    editor = _editor(tmp_path, "ab אבג\n", width=20)
    assert _painted(editor).rstrip() == shown("ab אבג")


def test_a_line_wider_than_the_window_keeps_a_cell_for_its_end(tmp_path):
    editor = _editor(tmp_path, "א" * 25 + "\n", width=20)
    cells, order, shift = editor._laid(0)
    assert shift == 1  # the end's cell, left of the text, is column 0
    editor.col = 25
    assert editor._visual_column(0, 25) == 0


# -- the caret ----------------------------------------------------------------------


def test_the_caret_at_a_hebrew_lines_end_is_left_of_it(tmp_path):
    editor = _editor(tmp_path, "אבג\n", col=0, width=20)
    assert _x(editor) == 19  # alef, the first letter, against the right edge
    assert editor._logical_column(0, 19) == 0
    editor.col = 3
    assert _x(editor) == 16  # the end: the cell left of the text
    editor.col = 5  # past the end, further left
    assert _x(editor) == 14
    assert editor._logical_column(0, 14) == 5


def test_typing_at_a_hebrew_lines_end_appears_where_the_caret_was(tmp_path):
    editor = _editor(tmp_path, "אבג\n", col=3, width=20)
    caret = _x(editor)
    editor.buffer.insert(Pos(0, 3), "ד")
    assert _painted(editor)[caret] == "ד"


def test_a_click_left_of_a_hebrew_line_goes_past_its_end(tmp_path):
    editor = _editor(tmp_path, "אבג\n", width=20)
    assert editor._logical_column(0, 16) == 3
    assert editor._logical_column(0, 10) == 9


# -- Left and Right ---------------------------------------------------------------------


def test_left_and_right_move_by_where_the_editor_paints(tmp_path):
    # "אבג def": painted "def גבא" against the right edge -- d e f at 23-25, ג ב א at 27-29.
    editor = _editor(tmp_path, "אבג def\n", col=0)
    painted = []
    for _ in range(6):
        _move(editor, "left")
        painted.append(_x(editor))
    assert painted == [28, 27, 26, 25, 24, 23]
    _move(editor, "left")
    assert (editor.line, editor.col, _x(editor)) == (0, 7, 22)  # the end, left of the text
    _move(editor, "right")
    assert _x(editor) == 23


def test_right_from_the_rightmost_letter_stays_and_left_runs_on_to_the_next_line(tmp_path):
    editor = _editor(tmp_path, "אבג\nx\n", col=0)
    _move(editor, "right")
    assert (editor.line, editor.col) == (0, 0)  # the line's start: it stays
    _move(editor, "left", times=3)
    assert (editor.line, editor.col) == (0, 3)
    _move(editor, "left")
    assert (editor.line, editor.col) == (1, 0)


def test_ctrl_left_and_right_go_to_words_by_where_they_are_painted(tmp_path):
    # "אבג דה xy": painted "xy הד גבא" at 21-29; words start at א (29), ד (25), x (21).
    editor = _editor(tmp_path, "אבג דה xy\nnext\n", col=0)
    assert _x(editor) == 29
    _word(editor, "left")
    assert _x(editor) == 25
    _word(editor, "left")
    assert _x(editor) == 21
    _word(editor, "left")
    assert (editor.line, editor.col, _x(editor)) == (0, 9, 20)  # the end, left of the text
    _word(editor, "right")
    assert _x(editor) == 21
    editor.col = 9
    _word(editor, "left")
    assert (editor.line, editor.col) == (1, 0)  # on, the way the line reads


# -- blocks marked on a right-to-left line -----------------------------------------------


def test_shift_arrows_mark_the_cells_passed_over(tmp_path):
    # "אבג xy": painted "xy גבא" at 24-29.  From ג (27) Shift+Left twice: ג
    # and the space are passed over -- the caret is a cell's right-hand edge.
    editor = _editor(tmp_path, "אבג xy\n", col=2)
    _move(editor, "left", extend=True, times=2)
    assert _lit(editor) == " ג"
    assert editor.block_text == "ג "


def test_shift_end_from_a_hebrew_lines_start_holds_all_of_it(tmp_path):
    from navigator.widgets.editor.commands import LineEnd

    editor = _editor(tmp_path, "אבג\n", col=0)
    asyncio.run(editor.on_line_end(LineEnd(extend=True)))
    assert editor.block_text == "אבג"


def test_a_painted_block_crossing_into_hebrew_holds_scattered_characters(tmp_path):
    # From y (25) right to ב (28): the space, ג and ב are passed over; y is not.
    editor = _editor(tmp_path, "אבג xy\n", col=5)
    _move(editor, "right", extend=True, times=3)
    assert _lit(editor) == " גב"
    assert editor.block_text == "בג "
    editor._delete_block()
    assert editor.document.lines[0] == "אxy"


def test_copying_a_painted_block_puts_in_its_characters_in_text_order(tmp_path):
    editor = _editor(tmp_path, "אבג xy\nend\n", col=5)
    _move(editor, "right", extend=True, times=3)
    editor.line, editor.col = 1, 3
    asyncio.run(editor.on_copy_block(None))
    assert editor.document.lines[1] == "endבג "
    assert editor.block is not editor._painted_block  # the copy is the stretch it is


def test_a_painted_block_over_two_lines_runs_to_the_end_each_line_reads_to(tmp_path):
    from navigator.widgets.editor.commands import MoveDown

    editor = _editor(tmp_path, "אבג\nxy\n", col=1)
    asyncio.run(editor.on_move_down(MoveDown(extend=True)))
    assert editor.block_text == "בג\nx"


def test_a_recase_that_changes_lengths_keeps_the_block_painted(tmp_path):
    # "אבג ß": painted "ß גבא".  From ג (col 2) Shift+Left twice: the space and ß...
    editor = _editor(tmp_path, "xß אבג\n", col=0)
    _move(editor, "right", extend=True, times=2)
    assert editor.block_text == "xß"
    asyncio.run(editor.on_upper_block(None)) if hasattr(editor, "on_upper_block") else editor._recase(str.upper)
    assert editor.document.lines[0] == "XSS אבג"
    assert editor.block is editor._painted_block
    assert editor.block_text == "XSS"


def test_a_recase_inside_hebrew_keeps_a_painted_block_painted(tmp_path):
    editor = _editor(tmp_path, "אבג ßy\n", col=5)  # painted "ßy גבא"; y at its right
    _move(editor, "left", extend=True, times=2)  # over y and ß
    assert editor.block_text == "ßy"
    asyncio.run(editor.on_upcase_block(None))
    assert editor.document.lines[0] == "אבג SSY"
    assert editor.block is editor._painted_block
    assert editor.block_text == "SSY"


# -- column blocks on a right-to-left line -------------------------------------------------


def test_a_column_blocks_columns_are_painted_columns(tmp_path):
    # Each line painted "xy גבא" at 24-29.
    editor = _editor(tmp_path, "אבג xy\nאבג xy\n", col=0)
    editor.vertical_blocks = True
    editor.column_block = ((0, 24), (1, 26))
    assert editor.block_lines() == ["xy", "xy"]
    editor.column_block = ((0, 26), (1, 29))
    assert editor.block_lines() == ["בג ", "בג "]  # the text's order


def test_a_column_block_across_a_reordered_line_takes_scattered_characters(tmp_path):
    editor = _editor(tmp_path, "אבג xy\n", col=0)
    editor.vertical_blocks = True
    editor.column_block = ((0, 25), (0, 29))  # y, the space, ג, ב
    assert editor.block_lines() == ["בג y"]
    editor._delete_block()
    assert editor.document.lines[0] == "אx"


def test_shift_arrows_mark_a_column_block_by_painted_columns(tmp_path):
    editor = _editor(tmp_path, "אבג xy\n", col=0)  # on א, painted at 29
    editor.vertical_blocks = True
    _move(editor, "left", extend=True, times=2)
    assert editor.rectangle == (0, 27, 0, 29)
    assert editor.block_lines() == ["בג"]


def test_finding_in_a_painted_block_passes_over_what_lies_between_its_stretches(tmp_path):
    from navigator.lib.editor.search import SearchData

    editor = _editor(tmp_path, "אבג xy\n", col=0)
    editor.vertical_blocks = True
    editor.column_block = ((0, 25), (0, 29))  # y, the space, ג, ב -- not x
    assert editor.find(Pos(0, 0), SearchData(text="x", selected=True), backward=False) is None
    assert editor.find(Pos(0, 0), SearchData(text="y", selected=True), backward=False) == (Pos(0, 5), Pos(0, 6))


def _indent(editor, *, undo: bool = False) -> None:
    from navigator.widgets.editor.commands import IndentBlock, UnindentBlock

    command = (UnindentBlock if undo else IndentBlock)(stop=False)
    asyncio.run((editor.on_unindent_block if undo else editor.on_indent_block)(command))


def test_indenting_puts_the_blank_just_left_of_the_edge(tmp_path):
    # "אבג דה" painted "הד גבא" at 24-29; the block's left edge on ג (27).
    editor = _editor(tmp_path, "אבג דה\n", col=0)
    editor.vertical_blocks = True
    editor.column_block = ((0, 27), (0, 30))
    _indent(editor)
    assert editor.document.lines[0] == "אבג  דה"
    assert _painted(editor).endswith("הד  גבא")  # ג on stays; the rest grew leftwards
    assert _painted(editor).index("ג") == 27


def test_unindenting_takes_the_blank_an_indent_put_there(tmp_path):
    editor = _editor(tmp_path, "אבג  דה\n", col=0)  # painted "הד  גבא" at 23-29
    editor.vertical_blocks = True
    editor.column_block = ((0, 27), (0, 30))
    _indent(editor, undo=True)
    assert editor.document.lines[0] == "אבג דה"


def test_an_indent_falls_back_to_the_nearer_place(tmp_path):
    # A mixed line, Latin first: left-aligned, the edge on ב.  Whichever side
    # of ב the blank goes in the text, it is painted next to the edge.
    editor = _editor(tmp_path, "ab אבג\n", col=0)
    editor.vertical_blocks = True
    editor.column_block = ((0, 4), (0, 6))
    _indent(editor)
    text = editor.document.lines[0]
    assert sorted(text) == sorted("ab אבג ")
    cells, order, _ = editor._laid(0)
    blanks = [x for x, (at, s) in enumerate(order) if s == " " and cells[at][1] != 2]
    assert 3 in blanks or 4 in blanks


# -- the current column, and tab stops past a lam-alef -------------------------------------


def test_the_current_column_follows_the_painted_column(tmp_path):
    from navkit.style import Style

    editor = _editor(tmp_path, "אבג\nxyz\n", col=0, width=20)
    editor.highlight_column = True
    column = Style(reverse=True)
    plain = editor.part_style
    editor.part_style = lambda name, **kw: column if name == "current_column" else plain(name, **kw)
    buffer = ScreenBuffer(20, 3)
    editor.render(buffer)
    assert buffer.get(19, 1)[1] == column  # under alef, on every row
    assert buffer.get(0, 1)[1] != column


def test_a_lam_alef_ligature_keeps_the_tab_stops_after_it(tmp_path):
    editor = _editor(tmp_path, "x لا\tb\nx ab\tb\n")
    tab = editor.tab_size
    cells, order, shift = editor._laid(0)
    assert shift == 0 and len(order) == len(cells)  # a column for the alef, blank
    painted = _painted(editor)
    assert painted.index("b") == tab == _painted(editor, 1).rindex("b")
    assert "ﻻ" in painted  # the ligature itself


def test_a_lam_alef_s_blank_never_opens_a_gap_inside_its_word(tmp_path):
    editor = _editor(tmp_path, "سلام عليكم\n")
    painted = _painted(editor).strip()
    assert "  " in painted and " " not in painted.split("  ")[0] + painted.split("  ")[1]


def test_moving_over_a_lam_alef_passes_its_blank(tmp_path):
    # سلام: seen, lam and alef one ligature; its alef's column is a blank.
    editor = _editor(tmp_path, "سلام\n", col=0)
    seen = []
    for _ in range(3):
        _move(editor, "left")
        seen.append(editor.col)
    assert seen == [1, 3, 4]  # the ligature, mim, the end -- never the blank
