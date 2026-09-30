"""F3: the file viewer -- the model in ``navigator/viewer.py`` and the window around it."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, run_app, settle
from navkit.events import KeyEvent
from navkit.screen import ScreenBuffer

import navigator.viewer as viewer_model
from navigator.__main__ import Navigator
from navigator.viewer import (
    CHUNK,
    LINE_LIMIT,
    ViewSearch,
    ViewSource,
    compile_search,
    cp437,
    dump_row,
    dump_row_bytes,
    hex_row,
    hex_row_bytes,
)


@pytest.fixture
def make(tmp_path):
    def make(data: bytes, name: str = "f") -> ViewSource:
        path = tmp_path / name
        path.write_bytes(data)
        return ViewSource(path)

    return make


def texts(source: ViewSource, width=None, filter=0) -> list[tuple[int, str]]:
    """Every row from the top: its start and what it shows."""
    rows, offset = [], 0
    while (row := source.line(offset, width, filter=filter)) is not None:
        rows.append((offset, "".join(c for c, _ in row.cells)))
        offset = row.next
    return rows


# -- lines ---------------------------------------------------------------------


def test_lines_end_at_lf_crlf_and_a_bare_cr(make):
    source = make(b"abc\r\nde\rf\n\ng")
    assert texts(source) == [(0, "abc"), (5, "de"), (8, "f"), (10, ""), (11, "g")]


def test_going_up_finds_every_line_start_coming_down_found(make):
    source = make(b"abc\r\nde\rf\n\n\r\n\tg\nlast")
    starts = [start for start, _ in texts(source)]
    for before, after in zip(starts, starts[1:]):
        assert source.prev_line_start(after) == before
    assert source.prev_line_start(starts[0]) == 0
    assert source.prev_line_start(source.size) == starts[-1]


def test_wrapped_rows_are_found_again_going_up(make):
    source = make(b"0123456789abcdefghij\nxy")
    rows = texts(source, width=6)
    assert rows == [(0, "012345"), (6, "6789ab"), (12, "cdefgh"), (18, "ij"), (21, "xy")]
    starts = [start for start, _ in rows]
    for before, after in zip(starts, starts[1:]):
        assert source.prev_line_start(after, 6) == before


def test_a_row_that_fills_the_width_exactly_does_not_leave_an_empty_one(make):
    assert texts(make(b"abcdef\ng"), width=6) == [(0, "abcdef"), (7, "g")]


def test_an_unwrapped_line_is_cut_at_the_limit_and_the_pieces_are_found_going_up(make):
    source = make(b"a" * (LINE_LIMIT * 2 + 10) + b"\nz")
    starts = [start for start, _ in texts(source)]
    assert starts == [0, LINE_LIMIT, 2 * LINE_LIMIT, 2 * LINE_LIMIT + 11]
    assert source.prev_line_start(starts[3]) == starts[2]
    assert source.prev_line_start(starts[2]) == starts[1]


def test_line_start_snaps_an_offset_to_its_row(make):
    source = make(b"one\ntwo\r\nthree")
    assert [source.line_start(o) for o in (0, 2, 3, 4, 7, 8, 9, 12)] == [0, 0, 0, 4, 4, 4, 9, 9]


def test_the_last_page_puts_the_last_row_at_the_bottom(make):
    source = make(b"1\n2\n3\n4\n5\n")
    assert source.last_page_top(2) == 6
    assert source.last_page_top(10) == 0


def test_a_read_spanning_chunks_is_whole(make):
    data = bytes(range(256)) * (CHUNK // 128)
    source = make(data)
    assert source.read(CHUNK - 3, 10) == data[CHUNK - 3:CHUNK + 7]
    assert source.read(len(data) - 2, 10) == data[-2:]


def test_a_directory_is_refused(tmp_path):
    with pytest.raises(OSError):
        ViewSource(tmp_path)


# -- cells ---------------------------------------------------------------------


def test_tabs_stop_every_eight_columns(make):
    assert texts(make(b"a\tb\t\tc")) == [(0, "a       b               c")]


def test_utf8_decodes_and_a_wide_character_takes_two_columns(make):
    row = make("ä漢x".encode()).line(0)
    assert [c for c, _ in row.cells] == ["ä", "漢", "", "x"]
    assert [at for _, at in row.cells] == [0, 2, 2, 5]


def test_a_byte_that_is_not_utf8_is_its_cp437_glyph(make):
    assert texts(make(b"\x01\xb0\xff\x7f")) == [(0, "☺░\xa0⌂")]
    assert cp437(0) == " " and cp437(0xC4) == "─"


def test_the_three_filters(make):
    data = "a\x01ä".encode() + b"\x90"
    source = make(data)
    assert texts(source, filter=0) == [(0, "a☺äÉ")]
    assert texts(source, filter=1) == [(0, "a···")]
    assert texts(source, filter=2) == [(0, "a·äÉ")]


# -- hex and dump --------------------------------------------------------------


def test_hex_and_dump_rows_are_dos_navigators():
    assert hex_row_bytes(80) == 17 and hex_row_bytes(12) == 1
    assert dump_row_bytes(80) == 64 and dump_row_bytes(10) == 16
    assert hex_row(b"OZ\x00\x90", 0x1F0, 5, 0) == "000001F0: 4F 5A 00 90    │ OZ.É"
    assert hex_row(b"\x01\x90", 0, 2, 1) == "00000000: 01 90 │ ··"
    assert dump_row(b"ab\x00", 0x10, 0) == "00000010 ab "


# -- searching -----------------------------------------------------------------


def test_search_ignores_case_beyond_ascii(make):
    pattern, span = compile_search("äB")
    source = make("xxÄb yy äB".encode())
    assert source.find(pattern, 0, span=span) == (2, 3)
    assert source.find(pattern, 3, span=span) == (9, 3)
    assert source.find(pattern, source.size, backward=True, span=span) == (9, 3)
    assert source.find(pattern, 9, backward=True, span=span) == (2, 3)


def test_case_sensitive_and_whole_words(make):
    source = make(b"Cab cab ab")
    pattern, span = compile_search("cab", case=True)
    assert source.find(pattern, 0, span=span) == (4, 3)
    pattern, span = compile_search("ab", words=True)
    assert source.find(pattern, 0, span=span) == (8, 2)


def test_a_hit_across_a_window_boundary_is_found(make):
    window = 1024 * 1024
    data = b"." * (window - 2) + b"needle" + b"." * 10
    source = make(data)
    pattern, span = compile_search("needle")
    assert source.find(pattern, 0, span=span) == (window - 2, 6)
    assert source.find(pattern, len(data), backward=True, span=span) == (window - 2, 6)


def test_nothing_found_is_none(make):
    pattern, span = compile_search("zz")
    assert make(b"abc").find(pattern, 0, span=span) is None


# -- the window ----------------------------------------------------------------


@pytest.fixture
def quiet_console(monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)


@pytest.fixture
def files(tmp_path, quiet_console):
    (tmp_path / "dir").mkdir()
    lines = "".join(f"line {n:03}\n" for n in range(100))
    (tmp_path / "text.txt").write_text(lines)
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


def opened(app):
    from navigator.widgets.viewer.file_window import FileWindow

    window = app.shell.desktop.active_window
    return window if isinstance(window, FileWindow) else None


def test_f3_opens_the_file_under_the_cursor_zoomed(files):
    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), lambda a: None,
                  lambda a: seen.update(buffer=screen(a))])
    window = opened(app)
    assert window is not None and window.zoomed
    assert window.title == str(files / "text.txt")
    assert window.list_name() == f"View - {files / 'text.txt'}"
    assert window._holds(app.focused)
    buffer = seen["buffer"]
    assert "line 000" in row_of(buffer, 2)
    assert "[<=>][" in row_of(buffer, 21)


def test_f3_on_a_directory_opens_nothing(files):
    app = navigator(files)
    run_app(app, [KeyEvent("down"), KeyEvent("f3"), lambda a: None])
    assert opened(app) is None


def test_the_key_bar_is_the_viewers_while_it_has_the_keyboard(files):
    app = navigator(files)
    shown = []
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), lambda a: None,
                  lambda a: shown.extend((c.title, a.command_enabled(c))
                                         for _, c, _, _ in a.shell.keybar.items())])
    # ``StatusDef hcView`` is 81 columns wide, and ``DrawSelect`` drops an item
    # that does not end before the edge: at 80 columns F10 Menu falls off the
    # end, as it did in DOS Navigator.
    assert [t for t, _ in shown] == [
        "Help", "(Un)Wrap", "Hex/ASCII/Dump", "Goto", "Filter", "Search",
    ]
    # Goto is hex and dump only, as DN disabled cmGotoCell in text.
    assert dict(shown)["Goto"] is False


def test_keys_move_the_view_and_f4_cycles_the_modes(files):
    app = navigator(files)
    info = []
    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), lambda a: None,
        KeyEvent("down"), KeyEvent("down"), KeyEvent("pagedown"),
        lambda a: info.append((opened(a).viewer.top, opened(a).viewer.info_text)),
        KeyEvent("pagedown", ctrl=True),
        lambda a: info.append((opened(a).viewer.top, opened(a).viewer.info_text)),
        KeyEvent("f4"),
        lambda a: info.append(opened(a).viewer.mode),
        KeyEvent("f4"),
        lambda a: info.append(opened(a).viewer.mode),
        KeyEvent("f4"),
        lambda a: info.append(opened(a).viewer.mode),
    ])
    # Each line is nine bytes; the viewer is 19 rows, so a page is 18.
    assert info[0] == (9 * 20, "[<=>][20% of 900 Bytes]")
    assert info[1] == (9 * 81, "[<=>][100% of 900 Bytes]")
    assert info[2:] == ["hex", "dump", "text"]


def test_f6_filters_and_the_info_line_says_so(files):
    app = navigator(files)
    info = []
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), lambda a: None, KeyEvent("f6"),
                  lambda a: info.append(opened(a).viewer.info_text)])
    assert info == ["[<=>][0% of 900 Bytes]{ASCII}"]


def test_escape_closes_it_and_the_panel_has_the_keyboard_again(files):
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), lambda a: None,
                  KeyEvent("escape"), lambda a: None])
    assert opened(app) is None
    assert app.focused is app.manager.active_panel



def test_closing_it_gives_the_keyboard_back_to_the_right_panel(files):
    # The window used to take the keyboard as it was mounted, before the
    # desktop had saved which panel the file manager had, so closing it
    # handed the keyboard to the left one.
    app = navigator(files)
    run_app(app, [KeyEvent("tab"), KeyEvent("end"), KeyEvent("f3"), lambda a: None,
                  KeyEvent("escape"), lambda a: None])
    assert opened(app) is None
    assert app.focused is app.manager.right

def test_f3_closes_it_again_as_midnight_commander_does(files):
    app = navigator(files)
    shown = []
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), lambda a: None,
                  lambda a: shown.extend(c.title for _, c, _, _ in a.shell.keybar.items()),
                  KeyEvent("f3"), lambda a: None])
    assert opened(app) is None
    assert app.focused is app.manager.active_panel
    # No caption: the status line stays ``StatusDef hcView``.
    assert "Close" not in shown and shown[1] == "(Un)Wrap"


def test_a_search_again_finds_the_next_hit_and_marks_it(files, monkeypatch):
    monkeypatch.setattr(viewer_model, "last_search", ViewSearch("LINE 050"))
    app = navigator(files)
    hits = []

    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), lambda a: None,
        KeyEvent("f7", shift=True), lambda a: None, lambda a: None,
        lambda a: hits.append((opened(a).viewer.hit, opened(a).viewer.top)),
    ], settle=0.05)
    assert hits == [((9 * 50, 8), 9 * 50)]


def test_f7_asks_and_finds(files, monkeypatch):
    from navigator.widgets.viewer.viewer_find_dialog import ViewerFindDialog

    monkeypatch.setattr(viewer_model, "last_search", None)
    app = navigator(files)
    seen = []
    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), lambda a: None,
        KeyEvent("f7"), lambda a: None,
        lambda a: seen.append(isinstance(a.modal, ViewerFindDialog)),
        *[KeyEvent(c, c) for c in "line 042"], KeyEvent("enter"),
        lambda a: None, lambda a: None,
        lambda a: seen.append(opened(a).viewer.hit),
    ], settle=0.05)
    assert seen == [True, (9 * 42, 8)]
    assert viewer_model.last_search == ViewSearch("line 042")


def test_f5_goes_to_a_hex_address(files):
    app = navigator(files)
    seen = []
    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), lambda a: None,
        KeyEvent("f4"), KeyEvent("f5"), lambda a: None,
        *[KeyEvent(c, c) for c in "1f"], KeyEvent("enter"),
        lambda a: None, lambda a: None,
        lambda a: seen.append((opened(a).viewer.cursor, opened(a).viewer.info_text[:10])),
    ], settle=0.05)
    assert seen == [(0x1F, "[0000001F ")]


@pytest.fixture
def slow_search(monkeypatch):
    """A search that takes long enough to put its progress up."""
    import threading

    release = threading.Event()
    original = ViewSource._find

    def _find(self, read, pattern, start, backward, span, job):
        while not (release.is_set() or job.stopped):
            job.position = self.size // 2
            release.wait(0.01)
        return original(self, read, pattern, start, backward, span, job)

    monkeypatch.setattr(ViewSource, "_find", _find)
    monkeypatch.setattr(viewer_model, "last_search", ViewSearch("line 050"))
    return release


def painted_row(widget) -> str:
    from navkit.screen import ScreenBuffer

    buffer = ScreenBuffer(widget.width, 1)
    widget.render(buffer)
    return "".join(buffer.get(x, 0)[0] for x in range(widget.width))


def test_a_long_search_shows_its_progress_and_finds(files, slow_search):
    from navigator.widgets.viewer.search_progress import SearchProgress

    app = navigator(files)
    seen = []

    def look(a):
        box = a.modal
        seen.append((type(box).__name__, box.bar.percent, painted_row(box.bar).count("█")))
        slow_search.set()

    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), lambda a: None,
        KeyEvent("f7", shift=True), lambda a: None, lambda a: None, lambda a: None,
        look, lambda a: None, lambda a: None,
        lambda a: seen.append((a.modal, opened(a).viewer.hit)),
    ], settle=0.1)
    assert seen[0] == ("SearchProgress", 50, 15)
    assert seen[1] == (None, (9 * 50, 8))


def test_stop_ends_a_search_and_says_nothing(files, slow_search):
    app = navigator(files)
    seen = []
    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), lambda a: None,
        KeyEvent("f7", shift=True), lambda a: None, lambda a: None, lambda a: None,
        KeyEvent("escape"), lambda a: None, lambda a: None,
        lambda a: seen.append((a.modal, opened(a).viewer.hit)),
    ], settle=0.1)
    # Stopped, not "not found": no message, no hit.
    assert seen == [(None, None)]


# -- the quick view -------------------------------------------------------------


def test_ctrl_q_shows_the_file_under_the_cursor_in_the_passive_panel(files):
    (files / "zz.txt").write_text("second file\n")
    app = navigator(files)
    seen = []

    def look(a):
        manager = a.manager
        seen.append((manager.replaced is manager.right, manager.quick.visible,
                     manager.right.visible, manager.quick.viewer.path,
                     a.focused is manager.left))

    run_app(app, [
        KeyEvent("down"), KeyEvent("down"), KeyEvent("q", ctrl=True), lambda a: None, look,
        KeyEvent("down"), lambda a: None, look,
        KeyEvent("up"), KeyEvent("up"), lambda a: None, look,
        KeyEvent("q", ctrl=True), lambda a: None,
        lambda a: seen.append((a.manager.replaced, a.manager.quick.visible,
                               a.manager.right.visible)),
    ])
    assert seen[0] == (True, True, False, files / "text.txt", True)
    # It follows the cursor, and shows nothing for a directory.
    assert seen[1][3] == files / "zz.txt"
    assert seen[2][3] is None
    assert seen[3] == (None, False, True)


def test_tab_takes_the_keyboard_into_the_quick_view_and_the_keys_scroll_it(files):
    app = navigator(files)
    seen = []
    run_app(app, [
        KeyEvent("end"), KeyEvent("q", ctrl=True), lambda a: None,
        KeyEvent("tab"), KeyEvent("pagedown"), lambda a: None,
        lambda a: seen.append((a.focused is a.manager.quick.viewer,
                               a.manager.quick.viewer.top, a.manager.quick.bar.visible)),
        KeyEvent("tab"), lambda a: None,
        lambda a: seen.append((a.focused is a.manager.left, a.manager.quick.bar.visible)),
    ])
    assert seen[0][0] and seen[0][1] > 0 and seen[0][2]
    assert seen[1] == (True, False)


def test_ctrl_t_swaps_the_quick_view_for_the_tree_in_the_same_place(files):
    app = navigator(files)
    seen = []
    run_app(app, [
        KeyEvent("end"), KeyEvent("q", ctrl=True), lambda a: None,
        KeyEvent("t", ctrl=True), lambda a: None,
        lambda a: seen.append((a.manager.replacement is a.manager.tree,
                               a.manager.replaced is a.manager.right,
                               a.manager.quick.visible, a.manager.tree.visible)),
    ])
    assert seen == [(True, True, False, True)]


def test_a_stopped_job_ends_the_search(make):
    from navigator.viewer import SearchJob

    job = SearchJob()
    job.stop()
    pattern, span = compile_search("a")
    assert make(b"aaa").find(pattern, 0, span=span, job=job) is None
