"""Right-to-left text and the mirrored screen (navkit.bidi, Surface.rtl)."""

from __future__ import annotations

import pytest

from navkit import i18n
from navkit.application import Application
from navkit.bidi import REVEALED, caret_column, display_width, index_at, layout, order_cells, reveal, reveal_runs
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
    assert TerminalInfo.detect(env={**tty, "KITTY_WINDOW_ID": "1"}, is_tty=True).bidi == BIDI_WORDS


@pytest.mark.parametrize(
    ("env", "reorders", "multiplexer"),
    [
        ({"TERM": "xterm-256color"}, "", ""),
        ({"TERM": "xterm-256color", "KONSOLE_VERSION": "230805"}, "konsole", ""),
        ({"TERM": "mlterm"}, "mlterm", ""),
        ({"TERM": "screen.xterm-256color", "MLTERM": "3.9.3", "STY": "1.pts"}, "mlterm", "screen"),
        ({"TERM": "tmux-256color", "KONSOLE_VERSION": "230805", "TMUX": "/tmp/t,1,0"}, "konsole", "tmux"),
    ],
)
def test_a_terminal_that_reorders_its_own_way_is_recognised(env, reorders, multiplexer):
    info = TerminalInfo.detect(env=env, is_tty=True)
    assert (info.reorders, info.multiplexer) == (reorders, multiplexer)


def _started(**flags):
    import io

    from navkit.terminal import Terminal

    out = io.StringIO()
    terminal = Terminal(input_stream=io.StringIO(), output_stream=out, info=TerminalInfo(**flags))
    terminal.start()
    entered = out.getvalue()
    terminal.stop()
    return entered, out.getvalue()[len(entered):]


def test_the_terminal_is_asked_to_reorder_nothing_and_given_its_bidi_back():
    entered, left = _started()
    assert "\x1b[8l" in entered and entered.index("\x1b[8l") < entered.index("\x1b[2J")
    assert "\x1b[8h" in left and "50;" not in entered


@pytest.mark.parametrize(
    ("reorders", "off", "on"),
    [
        ("konsole", "\x1b]50;BidiRenderingEnabled=false\x07", "\x1b]50;BidiRenderingEnabled=true\x07"),
        ("mlterm", "\x1b]5379;use_ctl=false\x07", "\x1b]5379;use_ctl=true\x07"),
    ],
)
def test_konsole_and_mlterm_get_their_own_switch(reorders, off, on):
    entered, left = _started(reorders=reorders)
    assert "\x1b[8l" + off in entered
    assert "\x1b[8h" + on in left


def test_inside_screen_the_switch_is_passed_through():
    entered, left = _started(reorders="konsole", multiplexer="screen")
    assert "\x1bP\x1b[8l\x1b\\\x1bP\x1b]50;BidiRenderingEnabled=false\x07\x1b\\" in entered
    assert "\x1bP\x1b[8h\x1b\\" in left


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


def test_a_left_to_right_line_moves_as_it_always_has(tmp_path):
    editor = _editor_on(tmp_path, "abc\n", col=1)
    _press(editor, "right")
    assert editor.col == 2


def _word(editor, command) -> None:
    import asyncio

    asyncio.run(getattr(editor, f"on_word_{command}")(None))


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


def test_a_block_on_left_to_right_lines_is_the_stretch_it_always_was(tmp_path):
    editor = _editor_on(tmp_path, "one two\n", col=0)
    _shift(editor, "right", 3)
    assert editor.block_text == "one"


# -- column blocks on a reordered line -------------------------------------------


# -- ^K I and ^K U at a column block's painted edge -------------------------------------


def _indent(editor, *, undo: bool = False, stop: bool = False) -> None:
    import asyncio

    from navigator.widgets.editor.commands import IndentBlock, UnindentBlock

    command = (UnindentBlock if undo else IndentBlock)(stop=stop)
    asyncio.run((editor.on_unindent_block if undo else editor.on_indent_block)(command))


def test_a_stream_block_still_indents_at_the_lines_start(tmp_path):
    editor = _editor_on(tmp_path, "אבג\n", col=0)
    editor.block = (Pos(0, 0), Pos(0, 3))
    _indent(editor)
    assert editor.document.lines[0] == " אבג"


# -- characters that hide part of a name ---------------------------------------


def test_reveal_shows_what_would_reorder_or_hide_text():
    assert reveal("photo\u202egpj.exe") == "photo\u2047gpj.exe"
    assert shown(reveal("photo\u202egpj.exe")) == "photo\u2047gpj.exe"  # nothing turned round
    assert reveal("a\u2066b\u2069c\x1b", "?") == "a?b?c?"
    assert reveal("\u200fשלום") == "\u200fשלום"  # a mark of direction is used in earnest
    assert reveal("plain.txt") == "plain.txt"


def test_reveal_runs_styles_only_the_stand_ins():
    text = reveal("a\u202eb?", REVEALED)
    assert reveal_runs(text, RED, "?", BOLD) == [("a", RED), ("?", BOLD), ("b?", RED)]


# -- input lines -----------------------------------------------------------------


def _line(value: str, cursor: int):
    from navml.widgets.dialog.input_line import InputLine

    line = InputLine(value=value, width=20, height=1)
    line.cursor = cursor
    line.render(ScreenBuffer(20, 1))
    return line


def _press_line(line, key: str, **mods) -> None:
    from conftest import awaited

    awaited(line.on_key(KeyEvent(key, **mods)))


def test_arrows_move_an_input_line_s_caret_to_the_neighbouring_painted_place():
    # "ab אבג": painted "ab גבא", alef at column 5.  From the caret on alef,
    # Left goes onto bet (column 4), not back to the blank before alef.
    line = _line("ab אבג", 3)
    assert line.caret_column() == 1 + 5
    _press_line(line, "left")
    assert (line.cursor, line.caret_column()) == (4, 1 + 4)
    _press_line(line, "right")
    assert line.cursor == 3
    plain = _line("abc", 1)
    _press_line(plain, "left")
    assert plain.cursor == 0


def test_an_input_line_selects_what_is_painted_between_the_carets():
    line = _line("ab אבג", 3)  # on alef, column 5
    _press_line(line, "left", shift=True)
    _press_line(line, "left", shift=True)  # onto gimel, column 3
    assert line.picked() == [4, 5]  # bet and gimel, painted at 3 and 4
    assert line.selected_text == "בג"
    _press_line(line, "delete")
    assert line.value == "ab א" and line.cursor == 4


def test_ctrl_arrows_go_to_the_nearest_painted_word_start():
    line = _line("abc אבג דהו", 0)
    _press_line(line, "right", ctrl=True)
    assert line.cursor == 8  # dalet's word is painted first after "abc "


# -- the viewer ------------------------------------------------------------------


def _viewer(tmp_path, text: str, width: int, wrap: bool):
    from conftest import settle
    from navigator.lib.viewer import ViewSource
    from navigator.widgets.viewer.file_viewer.file_viewer import FileViewer

    path = tmp_path / "t.txt"
    path.write_text(text, encoding="utf-8")
    root = Widget(width=width, height=4)
    viewer = root.add(FileViewer(x=0, y=0, width=width, height=4))
    viewer.open(path, source=ViewSource(path))
    viewer.wrap = wrap
    settle()
    return viewer


def test_a_wrapped_hebrew_line_reads_right_to_left_on_every_row(tmp_path):
    # The second row holds only Latin, but it is a piece of a Hebrew line:
    # "abc def" there is still a run inside a right-to-left paragraph.
    viewer = _viewer(tmp_path, "אבג דהו abc de.\n", 8, wrap=True)
    buffer = ScreenBuffer(8, 4)
    viewer.render(buffer)
    assert row(buffer, 0) == shown("אבג דהו ", True)
    assert row(buffer, 1).rstrip() == ".abc de"  # the full stop ends a Hebrew sentence


def test_a_search_hit_is_scrolled_to_where_it_is_painted(tmp_path):
    line = "אבג " * 30 + "xyz\n"
    viewer = _viewer(tmp_path, line, 20, wrap=False)
    offset = line.encode().index(b"xyz")
    viewer.show_hit(offset, 3)
    # "xyz" begins the right-to-left paragraph's painted row, at the left.
    assert viewer.x_delta == 0
    buffer = ScreenBuffer(20, 4)
    viewer.render(buffer)
    assert row(buffer).startswith("xyz ")  # decoded past the screen to be painted


# -- widths ----------------------------------------------------------------------


def test_display_width_counts_the_cells_painted():
    assert display_width("abc") == 3
    assert display_width("لا") == 1  # lam-alef: one ligature
    assert display_width("שָׁלוֹם") == 4  # marks on their letters
    assert display_width("日本") == 4
    assert display_width("a\u200fb") == 2


def test_a_centred_arabic_caption_is_centred_on_what_it_paints():
    from navml.widgets.dialog.label import Label

    label = Label(text="سلام لا", align="center", width=11, height=1)
    buffer = ScreenBuffer(11, 1)
    label.render(buffer)
    painted = [x for x in range(11) if buffer.get(x, 0)[0] != " "]
    # Seven letters and a blank in five cells -- "salam" has a lam-alef as
    # well -- so three blank on either side, where len() made it two and four.
    assert (painted[0], 10 - painted[-1]) == (3, 3)


# -- links in dialog text ------------------------------------------------------


@pytest.mark.parametrize("mirrored", [False, True])
def test_a_link_in_hebrew_text_covers_the_address_where_it_is_painted(mirrored):
    from navml.widgets.dialog.static_text import StaticText

    url = "https://x.io"
    text = StaticText(text=f"בקרו ב {url} היום", links=True, width=30, height=1)
    buffer = ScreenBuffer(30, 1)
    buffer.rtl = mirrored
    text.render(buffer)
    linked = "".join(buffer.get(x, 0)[0] for x in range(30) if buffer.get(x, 0)[1].link == url)
    # An rtl surface holds it reversed (and its slashes flipped) for the mirror.
    assert len(linked) == len(url) and ("x.io" in linked or "oi.x" in linked)


# -- the rendered Markdown view -----------------------------------------------------


def test_a_right_to_left_paragraph_is_set_against_the_right_edge():
    from navigator.lib.viewer.markdown import render
    from navigator.widgets.viewer.file_viewer.file_viewer import _laid_row

    layout = render("שלום עולם\n\n- אבג\n\nplain\n".encode(), 20)
    rows = [row for row in layout.rows if row.cells]
    hebrew, item, plain = rows
    cells, columns = _laid_row(hebrew, 20)
    assert "".join(cell[0] for cell in cells) == " " * 11 + shown("שלום עולם")
    assert columns[:11] == [None] * 11
    cells, _ = _laid_row(item, 20)
    text = "".join(cell[0] for cell in cells)
    assert text.startswith(item.text[: item.lead]) and text.endswith("גבא")  # the bullet stays put
    assert "".join(cell[0] for cell in _laid_row(plain, 20)[0]) == "plain"


def test_a_grid_column_starts_after_its_widest_caption_as_painted():
    from navml.widgets.dialog.check_boxes import CheckBoxes

    boxes = CheckBoxes(items=["سلام", "x", "a", "b"], width=40, height=2)
    # Four letters in three cells (a lam-alef), the mark's four and two between.
    assert boxes.column_x(1) == 3 + 6


def test_the_dbase_structure_box_holds_its_columns_left_to_right():
    from navigator.widgets.viewer.db_window.db_window import _table_row

    heading, row_ = _table_row("שם", "סוג", "אורך", "עשרוניים"), _table_row("AGE", "מספרי", "3", "0")
    # Each column starts in the same cell on both lines, painted.
    assert shown(heading).index("סוג"[::-1]) == shown(row_).index("מספרי"[::-1])
