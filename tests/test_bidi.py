"""Right-to-left text and the mirrored screen (navkit.bidi, Surface.rtl)."""

from __future__ import annotations

import pytest

from navkit import i18n
from navkit.application import Application
from navkit.bidi import caret_column, index_at, layout, order_cells
from navkit.capabilities import BIDI_APP, BIDI_WORDS, TerminalInfo
from navkit.events import KeyEvent, MouseClickEvent
from navkit.screen import ScreenBuffer, for_words
from navkit.style import Style
from navkit.widget import Widget
from navigator.lib.editor.document import Pos

from conftest import FakeTerminal, RecordingWidget, run_app

RED = Style(fg="red")
BOLD = Style(bold=True)


def shown(text: str, rtl: bool = False) -> str:
    return "".join(cell for _, cell in layout(text, rtl))


def row(buffer: ScreenBuffer, y: int = 0) -> str:
    return "".join(buffer.get(x, y)[0] for x in range(buffer.width))


# -- layout ------------------------------------------------------------------


def test_left_to_right_text_is_left_alone():
    assert layout("readme.txt") == tuple(enumerate("readme.txt"))
    assert shown("readme.txt", rtl=True) == "readme.txt"


def test_hebrew_is_put_in_visual_order_with_its_extension_after_it():
    # A right-to-left paragraph: the name reads from the right, ".txt" ends it on the left.
    assert shown("מסמך חשוב.txt") == "txt.בושח ךמסמ"


def test_numbers_inside_hebrew_keep_their_own_order():
    assert shown("תמונות 2024") == "2024 תונומת"


def test_a_left_to_right_paragraph_keeps_its_hebrew_word_in_place():
    assert shown("mixed English עברית.md") == "mixed English תירבע.md"


def test_brackets_are_mirrored_inside_right_to_left_text():
    assert shown("קובץ (1).txt") == "txt.(1) ץבוק"


def test_neutral_text_takes_the_direction_it_is_given():
    assert [index for index, _ in layout("( )", rtl=True)] == [2, 1, 0]
    assert shown("( )", rtl=True) == "( )"
    assert shown("12:30", rtl=True) == "12:30"


def test_marks_stay_on_their_letter():
    cells = layout("שָׁלוֹם")
    assert [cell for _, cell in cells] == ["ם", "וֹ", "ל", "שָׁ"]


def test_arabic_is_shaped_and_lam_alef_is_one_cell():
    cells = layout("ملاحظات")
    assert len(cells) == 6  # seven letters, lam and alef in one ligature
    assert "ﻼ" in [cell for _, cell in cells]  # the final lam-alef
    assert shown("لعب") == "ﺐﻌﻟ"


def test_a_flag_is_one_cluster():
    assert layout("\U0001f1f1\U0001f1fb") == ((0, "\U0001f1f1\U0001f1fb"),)


# -- painting ----------------------------------------------------------------


def test_draw_runs_keeps_a_style_on_its_character():
    buffer = ScreenBuffer(6, 1)
    buffer.draw_runs(0, 0, [("א", Style()), ("ב", RED), ("ג", Style())])
    assert row(buffer) == "גבא   "
    assert buffer.get(1, 0)[1] == RED


def test_draw_text_cuts_the_logical_end_off():
    buffer = ScreenBuffer(4, 1)
    assert buffer.draw_text(0, 0, "אבגדה") == 4
    assert row(buffer) == "דגבא"


def test_format_characters_take_no_cell():
    buffer = ScreenBuffer(6, 1)
    assert buffer.draw_text(0, 0, "a‏b‮c") == 3


def test_text_on_a_mirrored_surface_reads_right_once_mirrored():
    buffer = ScreenBuffer(12, 1)
    buffer.rtl = True
    buffer.draw_text(0, 0, "readme.txt")
    buffer.draw_text(0, 0, "", Style())
    assert row(buffer.mirrored()) == "  readme.txt"
    buffer = ScreenBuffer(8, 1)
    buffer.rtl = True
    buffer.draw_text(0, 0, "אבג (1)")
    assert row(buffer.mirrored()).rstrip() == shown("אבג (1)").rjust(8).rstrip()


def test_mirroring_flips_frames_and_keeps_wide_characters_whole():
    buffer = ScreenBuffer(6, 1)
    buffer.set_cell(0, 0, "┌")
    buffer.set_cell(1, 0, "中")
    buffer.set_cell(5, 0, "►")
    flipped = buffer.mirrored()
    assert [flipped.get(x, 0)[0] for x in range(6)] == ["◄", " ", " ", "中", "", "┐"]


def test_a_widget_that_keeps_left_to_right_is_mirrored_back():
    class Keeper(Widget):
        mirrors = False

        def render(self, surface):
            surface.draw_text(0, 0, "ls -l")

    root = Widget(width=10, height=1)
    keeper = Keeper(x=0, y=0, width=6, height=1)
    root.add(keeper)
    buffer = ScreenBuffer(10, 1)
    buffer.rtl = True
    root.render_tree(buffer)
    assert row(buffer.mirrored()) == "    ls -l "


# -- kitty -------------------------------------------------------------------


def test_kitty_gets_an_arabic_run_reversed_with_its_colours_in_place():
    buffer = ScreenBuffer(5, 1)
    for x, (char, style) in enumerate([("ب", RED), ("p", Style()), ("d", Style()), (" ", Style()), ("x", Style())]):
        buffer.set_cell(x, 0, char, style)
    sent = for_words(buffer)
    assert row(sent) == "dpب x"
    assert sent.get(0, 0)[1] == RED  # kitty keeps colours where the cells are


def test_kitty_gets_each_stretch_of_hebrew_reversed_alone():
    buffer = ScreenBuffer(8, 1)
    buffer.draw_text(0, 0, "abגדה.x")
    assert row(for_words(buffer)) == "ab" + row(buffer)[2:5][::-1] + ".x "


def test_kitty_runs_break_at_a_change_of_weight():
    buffer = ScreenBuffer(3, 1)
    buffer.set_cell(0, 0, "ب")
    buffer.set_cell(1, 0, "x", BOLD)
    assert row(for_words(buffer)) == "بx "


def test_the_bidi_tier_is_detected_and_overridden():
    tty = {"TERM": "xterm-256color"}
    assert TerminalInfo.detect(env=tty, is_tty=True).bidi == BIDI_APP
    assert TerminalInfo.detect(env={"TERM": "xterm-kitty"}, is_tty=True).bidi == BIDI_WORDS
    assert TerminalInfo.detect(env={**tty, "NAVKIT_BIDI": "words"}, is_tty=True).bidi == BIDI_WORDS


# -- carets ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "rtl", "columns"),
    [
        ("abc", False, [0, 1, 2, 3]),
        ("abc", True, [2, 1, 0, -1]),
        ("אבג", True, [0, 1, 2, 3]),
        ("אבג", False, [2, 1, 0, -1]),
    ],
)
def test_the_caret_sits_beside_the_character_it_is_before(text, rtl, columns):
    assert [caret_column(text, i, rtl) for i in range(len(text) + 1)] == columns


def test_the_caret_at_the_end_of_hebrew_is_left_of_a_trailing_number():
    # "2" is painted leftmost; what is typed next appears to its left.
    assert caret_column("אב 2", 4) == -1
    assert caret_column("אב 2", 4, rtl=True) == 4


def test_a_click_finds_the_character_painted_there():
    assert [index_at("אבג", column) for column in range(3)] == [2, 1, 0]


# -- the language and the application ----------------------------------------


def test_a_catalogue_says_its_language_reads_right_to_left(tmp_path):
    (tmp_path / "he.toml").write_text('[meta]\nname = "עברית"\ndirection = "rtl"\n')
    i18n.register_directory(tmp_path)
    assert i18n.is_rtl("he")
    assert not i18n.is_rtl("en")


def _rtl_app(root: Widget, terminal: FakeTerminal) -> Application:
    app = Application(root, terminal=terminal)
    app.direction = "rtl"
    return app


def test_a_right_to_left_screen_is_painted_mirrored(terminal):
    class Label(Widget):
        def render(self, surface):
            surface.fill(0, 0, self.width, self.height, " ")
            surface.draw_text(0, 0, "[x] ok")

    app = _rtl_app(Label(width=40, height=10), terminal)
    run_app(app)
    assert row(app._front).endswith("[x] ok")


def test_a_click_reaches_the_widget_in_its_own_columns(terminal):
    root = RecordingWidget(width=40, height=10)
    run_app(_rtl_app(root, terminal), [MouseClickEvent(3, 4, "left")])
    assert root.mice == [(36, 4)]


def test_left_and_right_trade_places_on_a_mirrored_screen(terminal):
    root = RecordingWidget(width=40, height=10)
    run_app(_rtl_app(root, terminal), [KeyEvent("left"), KeyEvent("right", shift=True)])
    assert root.keys == ["right", "shift+left"]


# -- the viewer and the editor -------------------------------------------------


def test_order_cells_reorders_a_row_and_keeps_wide_characters_whole():
    assert order_cells(list("abc")) is None
    assert order_cells(["א", "ב", " ", "1", "中", ""]) == [
        (3, "1"), (4, "中"), (5, ""), (2, " "), (1, "ב"), (0, "א"),
    ]


def test_the_viewer_keeps_a_mark_on_its_letter(tmp_path):
    from navigator.lib.viewer import ViewSource

    path = tmp_path / "f"
    path.write_bytes("שָׁלוֹם\n".encode())
    row = ViewSource(path).line(0, None)
    assert [char for char, _ in row.cells] == ["שָׁ", "ל", "וֹ", "ם"]


def _painted_editor(tmp_path, text: str, col: int = 0):
    from navigator.widgets.editor.file_editor import FileEditor

    (tmp_path / "t.txt").write_text(text, encoding="utf-8")
    editor = FileEditor(width=20, height=3)
    editor.open(tmp_path / "t.txt")
    editor.col = col
    buffer = ScreenBuffer(20, 3)
    editor.render(buffer)
    return editor, buffer


def test_the_editor_paints_hebrew_in_reading_order(tmp_path):
    _, buffer = _painted_editor(tmp_path, "שלום 12.txt\n")
    assert row(buffer).rstrip() == shown("שלום 12.txt")


def test_the_editors_cursor_sits_where_its_column_is_painted(tmp_path):
    editor, _ = _painted_editor(tmp_path, "אבג\n", col=0)
    assert editor.cursor_position() == (2, 0)  # alef, the first letter, is painted last
    assert editor._logical_column(0, 2) == 0
    editor.col = 5  # past the text the columns are as they are
    assert editor.cursor_position() == (5, 0)


def test_the_editor_keeps_a_mark_on_its_letter():
    from navigator.lib.editor import columns

    assert [char for char, _ in columns.cells("שָׁלוֹם")] == ["שָׁ", "ל", "וֹ", "ם"]


def _editor_on(tmp_path, text: str, col: int):
    from navigator.widgets.editor.file_editor import FileEditor

    (tmp_path / "t.txt").write_text(text, encoding="utf-8")
    editor = FileEditor(width=30, height=3)
    editor.open(tmp_path / "t.txt")
    editor.col = col
    return editor


def _press(editor, command) -> None:
    import asyncio

    asyncio.run(getattr(editor, f"on_move_{command}")(None))


def test_left_and_right_move_by_where_the_editor_paints(tmp_path):
    # "אבג def": painted "def גבא" -- d e f at columns 0-2, ג ב א at 4-6.
    editor = _editor_on(tmp_path, "אבג def\n", col=0)  # on alef, painted rightmost
    painted = []
    for _ in range(6):
        _press(editor, "left")
        painted.append(editor.cursor_position()[0])
    assert painted == [5, 4, 3, 2, 1, 0]
    _press(editor, "left")
    assert editor.cursor_position()[0] == 0  # the left end: it stays
    _press(editor, "right")
    assert editor.cursor_position()[0] == 1


def test_right_from_the_rightmost_letter_goes_past_the_text(tmp_path):
    editor = _editor_on(tmp_path, "אבג\nx\n", col=0)
    _press(editor, "right")
    assert (editor.line, editor.col) == (0, 3)
    _press(editor, "right")
    assert (editor.line, editor.col) == (1, 0)


def test_a_left_to_right_line_moves_as_it_always_has(tmp_path):
    editor = _editor_on(tmp_path, "abc\n", col=1)
    _press(editor, "right")
    assert editor.col == 2


def _word(editor, command) -> None:
    import asyncio

    asyncio.run(getattr(editor, f"on_word_{command}")(None))


def test_ctrl_left_and_right_go_to_words_by_where_they_are_painted(tmp_path):
    # "אבג דה xy": painted "xy הד גבא"; the words start at x (0), ד (4) and א (8).
    editor = _editor_on(tmp_path, "אבג דה xy\nnext\n", col=0)
    assert editor.cursor_position()[0] == 8
    _word(editor, "left")
    assert editor.cursor_position()[0] == 4
    _word(editor, "left")
    assert editor.cursor_position()[0] == 0
    _word(editor, "right")
    assert editor.cursor_position()[0] == 4
    _word(editor, "right")
    _word(editor, "right")
    assert (editor.line, editor.col) == (0, 9)  # the end of the line, past the text
    _word(editor, "right")
    assert (editor.line, editor.col) == (1, 0)


def test_ctrl_right_on_a_left_to_right_line_is_dns(tmp_path):
    editor = _editor_on(tmp_path, "one two\n", col=0)
    _word(editor, "right")
    assert editor.col == 4


# -- blocks marked on a reordered line ------------------------------------------


def _shift(editor, command, times=1) -> None:
    import asyncio

    from navigator.widgets.editor.commands import MoveLeft, MoveRight

    event = {"left": MoveLeft, "right": MoveRight}[command](extend=True)
    for _ in range(times):
        asyncio.run(getattr(editor, f"on_move_{command}")(event))


def _lit(editor) -> str:
    """The characters of line 0 the block lights, left to right as painted."""
    from navigator.lib.editor import columns

    row = columns.cells(editor.document.lines[0], editor.tab_size)
    order = order_cells([char for char, _ in row]) or [(at, char) for at, (char, _) in enumerate(row)]
    picked = editor._block_picked(0)
    assert picked is not None
    return "".join(shown for at, shown in order if row[at][1] in picked[0])


def test_shift_arrows_mark_what_is_painted_between_the_ends(tmp_path):
    # "אבג xy": painted "xy גבא" -- x y at 0-1, ג ב א at 3-5.  From ג (painted 3)
    # Shift+Left twice: the space and y are lit, the cells passed over.
    editor = _editor_on(tmp_path, "אבג xy\n", col=2)
    _shift(editor, "left", 2)
    assert _lit(editor) == "y "
    assert editor.block_text == " y"  # in the text's own order


def test_a_painted_block_crossing_into_hebrew_holds_scattered_characters(tmp_path):
    # From y (painted 1) right to ב (painted 4): y, the space and ג are lit --
    # "ג" is the text's third letter, "y" its last: two stretches.
    editor = _editor_on(tmp_path, "אבג xy\n", col=5)
    _shift(editor, "right", 3)
    assert _lit(editor) == "y ג"
    assert editor.block_text == "ג y"
    editor._delete_block()
    assert editor.document.lines[0] == "אבx"


def test_copying_a_painted_block_puts_in_its_characters_in_text_order(tmp_path):
    import asyncio

    editor = _editor_on(tmp_path, "אבג xy\nend\n", col=5)
    _shift(editor, "right", 3)
    editor.line, editor.col = 1, 3
    asyncio.run(editor.on_copy_block(None))
    assert editor.document.lines[1] == "endג y"
    assert editor.block is not editor._painted_block  # the copy is the stretch it is


def test_a_block_on_left_to_right_lines_is_the_stretch_it_always_was(tmp_path):
    editor = _editor_on(tmp_path, "one two\n", col=0)
    _shift(editor, "right", 3)
    assert editor.block_text == "one"


def test_a_painted_block_over_two_lines_runs_to_the_end_each_line_reads_to(tmp_path):
    import asyncio

    from navigator.widgets.editor.commands import MoveDown

    # From ב on "אבג" Shift+Down to "xy": the first line from ב towards its
    # end (leftwards, it is Hebrew) -- ב and ג -- its break, then "x".
    editor = _editor_on(tmp_path, "אבג\nxy\n", col=1)
    asyncio.run(editor.on_move_down(MoveDown(extend=True)))
    assert editor.block_text == "בג\nx"


# -- column blocks on a reordered line -------------------------------------------


def test_a_column_blocks_columns_are_painted_columns(tmp_path):
    # Each line painted "xy גבא": columns 0-1 hold x and y, 2-4 the space, ג and ב.
    editor = _editor_on(tmp_path, "אבג xy\nאבג xy\n", col=0)
    editor.vertical_blocks = True
    editor.column_block = ((0, 0), (1, 2))
    assert editor.block_lines() == ["xy", "xy"]
    editor.column_block = ((0, 2), (1, 5))
    assert editor.block_lines() == ["בג ", "בג "]  # the text's order


def test_a_column_block_across_a_reordered_line_takes_scattered_characters(tmp_path):
    # Columns 1-4: y, the space, ג and ב -- indices 1-3 and 5 of "אבג xy".
    editor = _editor_on(tmp_path, "אבג xy\n", col=0)
    editor.vertical_blocks = True
    editor.column_block = ((0, 1), (0, 5))
    assert editor.block_lines() == ["בג y"]
    editor._delete_block()
    assert editor.document.lines[0] == "אx"


def test_shift_arrows_mark_a_column_block_by_painted_columns(tmp_path):
    editor = _editor_on(tmp_path, "אבג xy\n", col=0)  # on א, painted at 5
    editor.vertical_blocks = True
    _shift(editor, "left", 2)
    assert editor.rectangle == (0, 3, 0, 5)
    assert editor.block_lines() == ["בג"]


def test_finding_in_a_painted_block_passes_over_what_lies_between_its_stretches(tmp_path):
    from navigator.lib.editor.document import Pos
    from navigator.lib.editor.search import SearchData

    editor = _editor_on(tmp_path, "אבג xy\n", col=0)
    editor.vertical_blocks = True
    editor.column_block = ((0, 1), (0, 5))  # y, the space, ג, ב -- not x
    assert editor.find(Pos(0, 0), SearchData(text="x", selected=True), backward=False) is None
    assert editor.find(Pos(0, 0), SearchData(text="y", selected=True), backward=False) == (Pos(0, 5), Pos(0, 6))


# -- ^K I and ^K U at a column block's painted edge -------------------------------------


def _indent(editor, *, undo: bool = False, stop: bool = False) -> None:
    import asyncio

    from navigator.widgets.editor.commands import IndentBlock, UnindentBlock

    command = (UnindentBlock if undo else IndentBlock)(stop=stop)
    asyncio.run((editor.on_unindent_block if undo else editor.on_indent_block)(command))


def _painted(editor, number: int = 0) -> str:
    from navigator.lib.editor import columns

    row = columns.cells(editor.document.lines[number], editor.tab_size)
    order = order_cells([char for char, _ in row])
    return "".join(shown for _, shown in order) if order else "".join(char for char, _ in row)


def test_indenting_a_column_block_paints_the_blank_at_its_left_edge(tmp_path):
    # "אבג דה" painted "הד גבא"; the block's left edge at column 3, on ג.
    editor = _editor_on(tmp_path, "אבג דה\n", col=0)
    editor.vertical_blocks = True
    editor.column_block = ((0, 3), (0, 5))
    _indent(editor)
    assert _painted(editor) == "הד  גבא"  # ג and what follows pushed one cell right


def test_unindenting_takes_the_blank_painted_at_the_left_edge(tmp_path):
    editor = _editor_on(tmp_path, "אבג  דה\n", col=0)  # painted "הד  גבא"
    editor.vertical_blocks = True
    editor.column_block = ((0, 3), (0, 5))
    _indent(editor, undo=True)
    assert _painted(editor) == "הד גבא"


def test_a_stream_block_still_indents_at_the_lines_start(tmp_path):
    editor = _editor_on(tmp_path, "אבג\n", col=0)
    editor.block = (Pos(0, 0), Pos(0, 3))
    _indent(editor)
    assert editor.document.lines[0] == " אבג"
