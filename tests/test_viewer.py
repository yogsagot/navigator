"""F3: the file viewer -- the model in ``navigator/lib/viewer/__init__.py`` and the window around it."""

from __future__ import annotations

import time

import pytest

from conftest import FakeTerminal, IDLE, run_app, settle, Until
from navkit.events import KeyEvent
from navkit.screen import ScreenBuffer

import navigator.lib.viewer as viewer_model
from navigator.__main__ import Navigator
from navigator.lib.viewer import (
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
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)


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
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE,
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
    run_app(app, [KeyEvent("down"), KeyEvent("f3"), IDLE])
    assert opened(app) is None


def test_the_key_bar_is_the_viewers_while_it_has_the_keyboard(files):
    app = navigator(files)
    shown = []
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE,
                  lambda a: shown.extend((c.title, a.command_enabled(c))
                                         for _, c, _, _ in a.shell.keybar.items())])
    # ``StatusDef hcView`` was 81 columns wide, so at 80 F10 Menu fell off the
    # end in DOS Navigator; *Hex/Text/Dump* is one column shorter than its
    # *Hex/ASCII/Dump*, so it fits here.
    assert [t for t, _ in shown] == [
        "Help", "(Un)Wrap", "Hex/Text/Dump", "Goto", "Filter", "Search", "Menu",
    ]
    # Goto is hex and dump only, as DN disabled cmGotoCell in text.
    assert dict(shown)["Goto"] is False


def test_keys_move_the_view_and_f4_cycles_the_modes(files):
    app = navigator(files)
    info = []
    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE,
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
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE, KeyEvent("f6"),
                  lambda a: info.append(opened(a).viewer.info_text)])
    assert info == ["[<=>][0% of 900 Bytes]{ASCII}"]


def test_escape_closes_it_and_the_panel_has_the_keyboard_again(files):
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE,
                  KeyEvent("escape"), lambda a: None])
    assert opened(app) is None
    assert app.focused is app.manager.active_panel



def test_closing_it_gives_the_keyboard_back_to_the_right_panel(files):
    # The window used to take the keyboard as it was mounted, before the
    # desktop had saved which panel the file manager had, so closing it
    # handed the keyboard to the left one.
    app = navigator(files)
    run_app(app, [KeyEvent("tab"), KeyEvent("end"), KeyEvent("f3"), IDLE,
                  KeyEvent("escape"), lambda a: None])
    assert opened(app) is None
    assert app.focused is app.manager.right

def test_f3_closes_it_again_as_midnight_commander_does(files):
    app = navigator(files)
    shown = []
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE,
                  lambda a: shown.extend(c.title for _, c, _, _ in a.shell.keybar.items()),
                  KeyEvent("f3"), IDLE])
    assert opened(app) is None
    assert app.focused is app.manager.active_panel
    # No caption: the status line stays ``StatusDef hcView``.
    assert "Close" not in shown and shown[1] == "(Un)Wrap"


def test_a_search_again_finds_the_next_hit_and_marks_it(files, monkeypatch):
    monkeypatch.setattr(viewer_model, "last_search", ViewSearch("LINE 050"))
    app = navigator(files)
    hits = []

    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE,
        KeyEvent("f7", shift=True), lambda a: None, lambda a: None,
        lambda a: hits.append((opened(a).viewer.hit, opened(a).viewer.top)),
    ], settle=0.05)
    assert hits == [((9 * 50, 8), 9 * 50)]


def search_steps(*steps):
    """F3 on text.txt, then *steps*; each ``"hit"`` records (hit, top), each
    ``"modal"`` the box's title (closing it)."""
    actions = [KeyEvent("end"), KeyEvent("f3"), IDLE]
    seen = []
    for step in steps:
        if step == "hit":
            actions += [lambda a: None, lambda a: None,
                        lambda a: seen.append((opened(a).viewer.hit, opened(a).viewer.top))]
        elif step == "modal":
            actions += [Until(lambda a: a.modal is not None),
                        lambda a: seen.append(a.modal.title), lambda a: a.modal.close(None)]
        else:
            actions.append(step)
    return actions, seen


def test_a_hit_goes_to_the_top_as_dns_did(files, monkeypatch):
    monkeypatch.setattr(viewer_model, "last_search", ViewSearch("LINE 005"))
    actions, seen = search_steps(KeyEvent("f7", shift=True), "hit")
    run_app(navigator(files), actions, settle=0.05)
    assert seen == [((9 * 5, 8), 9 * 5)]


def test_hits_in_the_last_screenful_are_each_found_once(files, monkeypatch):
    # The last screenful cannot go to the top, so the search goes on from a
    # hit that shows rather than finding it again.
    monkeypatch.setattr(viewer_model, "last_search", ViewSearch("LINE 09"))
    actions, seen = search_steps(*[KeyEvent("f7", shift=True), "hit"] * 10, KeyEvent("f7", shift=True), "modal")
    run_app(navigator(files), actions, settle=0.05)
    hits = [hit for hit, _ in seen[:10]]
    assert hits == [(9 * n, 7) for n in range(90, 100)]
    assert seen[9][1] == 9 * 100 - 9 * 19  # the last screenful: 19 rows
    assert seen[10] == "Error"


def test_after_scrolling_away_a_search_goes_on_from_the_view(files, monkeypatch):
    monkeypatch.setattr(viewer_model, "last_search", ViewSearch("LINE 0"))
    actions, seen = search_steps(KeyEvent("f7", shift=True), "hit",
                                 *[KeyEvent("pagedown")] * 2, KeyEvent("f7", shift=True), "hit")
    run_app(navigator(files), actions, settle=0.05)
    assert seen[0][0] == (0, 6)
    # Two pages of 18 rows down: line 036 is on top, and the first hit after it.
    assert seen[1][0] == (9 * 36, 6)


def test_ctrl_enter_continues_the_search(files, monkeypatch):
    monkeypatch.setattr(viewer_model, "last_search", ViewSearch("LINE 01"))
    actions, seen = search_steps(KeyEvent("f7", shift=True), "hit", KeyEvent("enter", ctrl=True), "hit")
    run_app(navigator(files), actions, settle=0.05)
    assert [hit for hit, _ in seen] == [(9 * 10, 7), (9 * 11, 7)]


def test_nothing_found_is_dns_error_box(files, monkeypatch):
    monkeypatch.setattr(viewer_model, "last_search", ViewSearch("no such text"))
    actions, seen = search_steps(KeyEvent("f7", shift=True), "modal")
    run_app(navigator(files), actions, settle=0.05)
    assert seen == ["Error"]


def test_in_hex_the_hits_row_goes_to_the_top_and_the_cursor_onto_it(files, monkeypatch):
    monkeypatch.setattr(viewer_model, "last_search", ViewSearch("LINE 050"))
    actions, seen = search_steps(KeyEvent("f4"), KeyEvent("f7", shift=True), "hit",
                                 lambda a: seen.append(("cursor", opened(a).viewer.cursor,
                                                        opened(a).viewer.row_bytes())))
    run_app(navigator(files), actions, settle=0.05)
    (hit, top), (_, cursor, per) = seen
    assert hit == (450, 8) and cursor == 450 and top == 450 - 450 % per


def test_the_hex_lines_bytes_are_searched_as_they_are():
    pattern, span = compile_search("", data=b"\x00A")
    assert pattern.search(b"..\x00a..") and not pattern.search(b"\x01a") and span == 2
    pattern, _ = compile_search("", data=b"\x00A", case=True)
    assert not pattern.search(b"\x00a") and pattern.search(b"\x00A")


def test_f7s_hex_line_finds_bytes_no_text_says_and_comes_back_on_them(files, monkeypatch):
    from navigator.widgets.viewer.viewer_find_dialog import ViewerFindDialog

    monkeypatch.setattr(viewer_model, "last_search", None)
    (files / "big.bin").write_bytes(b"\x00" * 300 + b"\xff\xfe" + b"\x00" * 300)
    app = navigator(files)
    seen = {}

    def look(a):
        box = a.modal
        seen.update(caption=box.hex_caption.text, y=(box.what.y, box.hex.y), hex=box.hex.data)

    run_app(app, [
        KeyEvent("home"), *[KeyEvent("down")] * 2, KeyEvent("f3"), IDLE,
        KeyEvent("f7"), Until(lambda a: isinstance(a.modal, ViewerFindDialog)),
        lambda a: a.modal.hex.focus(), *[KeyEvent(c.lower(), c) for c in "FFFE"], look, KeyEvent("enter"),
        Until(lambda a: a.modal is None and opened(a).viewer.hit is not None),
        lambda a: seen.update(hit=opened(a).viewer.hit, search=viewer_model.last_search),
        KeyEvent("f7"), Until(lambda a: isinstance(a.modal, ViewerFindDialog)),
        lambda a: seen.update(again=a.modal.hex.data), KeyEvent("escape"),
    ], settle=0.05)
    assert seen["caption"] == "He~x~" and seen["y"] == (3, 5) and seen["hex"] == b"\xff\xfe"
    assert seen["hit"] == (300, 2)
    assert seen["search"].data == b"\xff\xfe" and seen["search"].what == "\ufffd\ufffd"
    assert seen["again"] == b"\xff\xfe"


def test_text_the_hex_line_only_shows_keeps_no_bytes_of_its_own(files):
    from navigator.widgets.viewer.viewer_find_dialog import ViewerFindDialog

    box = ViewerFindDialog(last=ViewSearch("ab"), encoding="cp437")
    assert box.hex.data == b"ab"
    assert box.accept() == ViewSearch("ab")


def test_f7_asks_and_finds(files, monkeypatch):
    from navigator.widgets.viewer.viewer_find_dialog import ViewerFindDialog

    monkeypatch.setattr(viewer_model, "last_search", None)
    app = navigator(files)
    seen = []
    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE,
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
        KeyEvent("end"), KeyEvent("f3"), IDLE,
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
        release.jobs.append(job)
        # Bounded, so a search nobody stops fails a test instead of hanging it.
        deadline = time.monotonic() + 5
        while not (release.is_set() or job.stopped) and time.monotonic() < deadline:
            job.position = self.size // 2
            release.wait(0.01)
        return original(self, read, pattern, start, backward, span, job)

    monkeypatch.setattr(ViewSource, "_find", _find)
    monkeypatch.setattr(viewer_model, "last_search", ViewSearch("line 050"))
    release.jobs = []
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
        KeyEvent("end"), KeyEvent("f3"), IDLE,
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
        KeyEvent("end"), KeyEvent("f3"), IDLE,
        KeyEvent("f7", shift=True), lambda a: None, lambda a: None, lambda a: None,
        KeyEvent("escape"), lambda a: None, lambda a: None,
        lambda a: seen.append((a.modal, opened(a).viewer.hit)),
    ], settle=0.1)
    # Stopped, not "not found": no message, no hit.
    assert seen == [(None, None)]


def test_quitting_during_a_search_stops_its_thread(files, slow_search):
    # Never released: before the search's task stopped its job when cancelled,
    # the thread searched on and ``asyncio.run`` waited for it -- for ever.
    app = navigator(files)
    started = time.monotonic()
    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE,
        KeyEvent("f7", shift=True), lambda a: None, lambda a: None,
        lambda a: a.exit(),
    ], settle=0.1, timeout=3)
    assert slow_search.jobs and slow_search.jobs[0].stopped
    assert time.monotonic() - started < 2.5


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
    from navigator.lib.viewer import SearchJob

    job = SearchJob()
    job.stop()
    pattern, span = compile_search("a")
    assert make(b"aaa").find(pattern, 0, span=span, job=job) is None


def test_as_root_the_quick_view_title_is_dark_red_while_it_has_the_keyboard(files, monkeypatch):
    monkeypatch.setattr("os.geteuid", lambda: 0)
    app = navigator(files)
    seen = []

    def look(a):
        title = a.manager.quick.part_style("title")
        seen.append((title.fg, title.bg))

    run_app(app, [
        KeyEvent("end"), KeyEvent("q", ctrl=True), lambda a: None, look,
        KeyEvent("tab"), lambda a: None, look,
    ])
    assert seen[0][1] != 1
    assert seen[1] == (15, 1)


# -- the View menu -----------------------------------------------------------


def bar_captions(app) -> list[str]:
    from navml.widgets.dialog.control.control import parse_shortcut

    return [parse_shortcut(e.text)[0] for e in app.shell.menu.entries()]


def test_the_view_menu_is_on_the_bar_after_file_only_while_the_viewer_is_active(files):
    app = navigator(files)
    seen = []
    look = lambda a: seen.append("View" in bar_captions(a))   # noqa: E731
    run_app(app, [
        look,
        KeyEvent("end"), KeyEvent("f3"), IDLE,
        lambda a: seen.append(bar_captions(a)[:4]),
        KeyEvent("f9"), look,                   # the file manager comes forward
        KeyEvent("f9"), look,                   # and the viewer again
        KeyEvent("o", "o", ctrl=True), look,    # the windows put away
        KeyEvent("o", "o", ctrl=True), look,
        KeyEvent("escape"), look,               # closed
    ])
    assert seen == [False, ["≡", "File", "View", "Disk"], False, True, False, True, False]


def test_the_view_menu_switches_the_mode_and_ticks_the_one_in_force(files):
    from navigator.widgets.viewer.commands import SetViewFilter, SetViewMode, Unwrap

    app = navigator(files)
    seen = {}

    def ask(a):
        seen["mode"] = opened(a).viewer.mode
        seen["ticks"] = [a.command_checked(SetViewMode(m), a.focused)
                         for m in ("text", "hex", "dump")]
        seen["filter"] = a.command_checked(SetViewFilter(0), a.focused)
        seen["wrap"] = a.command_enabled(Unwrap, a.focused)

    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE,
        KeyEvent("v", "v", alt=True), lambda a: seen.update(open=a.shell.menu.is_open),
        # The modes are in View > Mo~d~e, nested so the box fits 80x25.
        KeyEvent("d", "d"), KeyEvent("h", "h"), lambda a: None, ask,
    ])
    assert seen["open"] is True
    assert seen["mode"] == "hex"
    assert seen["ticks"] == [False, True, False]
    assert seen["filter"] is True
    # F2 wraps text only, so its entry is greyed in hex as its key is.
    assert seen["wrap"] is False
    assert not app.shell.menu.is_open


def test_set_mode_keeps_the_offset_on_top_and_refuses_a_mode_it_lacks(files):
    from navigator.widgets.viewer.file_window import FileWindow

    window = FileWindow(files / "text.txt")
    viewer = window.viewer
    viewer.top = 90
    viewer.set_mode("hex")
    assert (viewer.mode, viewer.cursor) == ("hex", 90)
    viewer.set_filter(2)
    assert viewer.filter == 2
    with pytest.raises(ValueError):
        viewer.set_mode("braille")
    with pytest.raises(ValueError):
        viewer.set_filter(3)


# -- dump mode's keys (DN's ViewMode = 2: no cursor) --------------------------------------


@pytest.fixture
def dumped(files):
    """A viewer the F3 window's size on 10,240 bytes, several dump screens, in dump."""
    from navigator.widgets.viewer.file_viewer import FileViewer

    (files / "big.bin").write_bytes(bytes(range(256)) * 40)
    viewer = FileViewer()
    viewer.width, viewer.height = 78, 19
    viewer.open(files / "big.bin")
    viewer.set_mode("hex")
    viewer.set_mode("dump")
    return viewer


def press(viewer, name, **mods):
    import asyncio

    return asyncio.run(viewer.on_key(KeyEvent(name, **mods)))


def test_in_dump_the_arrows_and_pages_scroll_the_view(dumped):
    per = dumped.row_bytes()
    assert per == 64
    press(dumped, "down")
    assert dumped.top == per and dumped.cursor == dumped.top
    press(dumped, "up")
    assert dumped.top == 0
    press(dumped, "pagedown")
    assert dumped.top == 18 * per and dumped.cursor == dumped.top


def test_in_dump_ctrl_home_and_ctrl_end_go_to_the_files_ends(dumped):
    press(dumped, "pagedown")
    press(dumped, "end", ctrl=True)
    assert dumped.top == dumped._last_top() > 0 and dumped.cursor == dumped.top
    press(dumped, "home", ctrl=True)
    assert dumped.top == 0 and dumped.cursor == 0


def test_in_dump_ctrl_left_and_right_shift_the_rows_a_byte(dumped):
    press(dumped, "right", ctrl=True)
    assert dumped.top == 1
    press(dumped, "left", ctrl=True)
    assert dumped.top == 0


def test_in_dump_home_end_left_and_right_are_taken_and_do_nothing(dumped):
    press(dumped, "down")
    for name in ("home", "end", "left", "right", "tab"):
        assert press(dumped, name) is True
    assert dumped.top == dumped.row_bytes() and dumped.cursor == dumped.top


def test_hex_keeps_its_cursor_down_moves_it_before_the_view(dumped):
    dumped.set_mode("hex")
    press(dumped, "down")
    assert dumped.top == 0 and dumped.cursor == dumped.row_bytes()


def test_a_search_in_dump_starts_where_the_view_does(files, monkeypatch):
    # A hit above the view is not found first: the search starts at its top.
    (files / "big.bin").write_bytes(b"needle" + b"." * 5000 + b"needle" + b"." * 5000)
    monkeypatch.setattr(viewer_model, "last_search", ViewSearch("needle"))
    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("home"), *[KeyEvent("down")] * 2, KeyEvent("f3"), IDLE,
                  KeyEvent("f4"), KeyEvent("f4"), KeyEvent("pagedown"),
                  lambda a: seen.update(name=opened(a).viewer.path.name, top=opened(a).viewer.top,
                                        cursor=opened(a).viewer.cursor),
                  KeyEvent("f7", shift=True), Until(lambda a: opened(a).viewer.hit is not None),
                  lambda a: seen.update(hit=opened(a).viewer.hit)], settle=0.05)
    assert seen["name"] == "big.bin" and seen["top"] > 0 and seen["cursor"] == seen["top"]
    assert seen["hit"] == (5006, 6)


def test_dump_in_the_quick_view_scrolls_with_down(files):
    (files / "big.bin").write_bytes(bytes(range(256)) * 40)
    app = navigator(files)
    seen = {}

    def dump(a):
        a.manager.quick.viewer.set_mode("hex")
        a.manager.quick.viewer.set_mode("dump")

    run_app(app, [KeyEvent("home"), *[KeyEvent("down")] * 2, KeyEvent("q", ctrl=True),
                  Until(lambda a: a.manager.quick.viewer.path == files / "big.bin"), KeyEvent("tab"),
                  dump, KeyEvent("down"),
                  lambda a: seen.update(top=a.manager.quick.viewer.top,
                                        per=a.manager.quick.viewer.row_bytes())])
    assert seen["top"] == seen["per"]


# -- the option strip and hidden characters ---------------------------------------------------


def strip_span(window, command):
    return next(span for span in window.options.spans if span[2].command is command)


def click_option(command):
    from navkit.events import MouseClickEvent

    def action(app):
        window = opened(app)
        strip = window.options
        start = strip_span(window, command)[0]
        ox, oy = strip.offset()
        x, y = ox + strip.x + start, oy + strip.y
        app.post_event(MouseClickEvent(x=x, y=y, button="left", action="press"))
        app.post_event(MouseClickEvent(x=x, y=y, button="left", action="release"))
    return action


def test_the_viewer_strip_shows_mode_switches_encoding_and_type(files):
    from dataclasses import replace

    from navkit.capabilities import FULL

    app = Navigator(files, files, terminal=FakeTerminal(80, 24, info=replace(FULL, glyphs=1)))
    # Painted once, so the lexing thread has said there is no lexer.
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE, lambda a: screen(a)])
    window = opened(app)
    assert [span[3] for span in window.options.spans] == ["Text", "Wrap", "Hi", "Show", "UTF-8", "plain", "MD"]
    assert window.options.x + window.options.width == window.width - 3


def test_in_hex_mode_the_text_options_are_greyed(files):
    from navigator.widgets.editor.commands import SwitchHiddenChars
    from navigator.widgets.viewer.commands import HexMode, Unwrap

    app = navigator(files)
    seen = {}

    def look(a):
        window = opened(a)
        strip = window.options
        buffer = screen(a)
        ox, oy = strip.offset()
        at = lambda command: buffer.get(ox + strip.x + strip_span(window, command)[0], oy + strip.y)[1]  # noqa: E731
        seen.update(label=strip_span(window, HexMode)[3], wrap=at(Unwrap), hidden=at(SwitchHiddenChars),
                    grey=strip.part_style("item", disabled=True))

    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE, KeyEvent("f4"), look])
    assert seen["label"] == "Hex"
    assert seen["wrap"] == seen["grey"] and seen["hidden"] == seen["grey"]


def test_clicks_on_the_viewer_strip_switch_wrap_and_the_mode(files):
    from navigator.widgets.viewer.commands import HexMode, Unwrap

    app = navigator(files)
    seen = []
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE,
                  click_option(Unwrap), lambda a: None, lambda a: seen.append(opened(a).viewer.wrap),
                  click_option(HexMode), lambda a: None, lambda a: seen.append(opened(a).viewer.mode)])
    assert seen == [True, "hex"]


def test_the_viewer_strip_follows_its_setting(files):
    from navigator.settings import SETTINGS

    SETTINGS.viewer.show_options = False
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE])
    assert not opened(app).options.visible


def test_the_viewer_marks_blanks_tabs_and_each_kind_of_ending(tmp_path, quiet_console):
    from navigator.settings import SETTINGS

    (tmp_path / "dir").mkdir()
    (tmp_path / "text.txt").write_bytes(b"a b\tc  \r\nx\ny\rlast")
    SETTINGS.viewer.show_hidden = True
    app = navigator(tmp_path)
    seen = {}

    def look(a):
        buffer = screen(a)
        viewer = opened(a).viewer
        ox, oy = viewer.offset()
        seen["rows"] = ["".join(buffer.get(ox + viewer.x + x, oy + viewer.y + y)[0] or " "
                                for x in range(12)).rstrip() for y in range(4)]
        seen["mark"] = buffer.get(ox + viewer.x + 1, oy + viewer.y)[1]
        seen["plain"] = viewer.style

    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE, look])
    assert seen["rows"] == ["a·b→    c··⏎", "x↓", "y←", "last"]
    assert seen["mark"] == seen["plain"].derive(dim=True)


def test_the_view_menu_shows_f4_f6_and_hidden_characters_has_a_hotkey(files):
    from navml.widgets.menu.menu_box.menu_box import key_caption

    app = navigator(files)
    seen = {}

    def look(a):
        window = opened(a)
        # F4's and F6's entries head the Mode and Filters submenus.
        for menu, caption in ((window.view_menu_mode, "Hex/Text/Dump"), (window.view_menu_filter, "Filter"),
                              (window.view_menu, "Show hidden characters")):
            seen[caption] = key_caption(menu.entry(caption), a, a.focused)

    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE, look,
                  KeyEvent("v", "v", alt=True), KeyEvent("o", "o"), lambda a: None,
                  lambda a: seen.update(hidden=opened(a).viewer.show_hidden),
                  KeyEvent("v", "v", alt=True), KeyEvent("d", "d"), KeyEvent("x", "x"), lambda a: None,
                  lambda a: seen.update(mode=opened(a).viewer.mode)])
    assert seen == {"Hex/Text/Dump": "F4", "Filter": "F6",
                    "Show hidden characters": "Ctrl-Shift-8", "hidden": True, "mode": "hex"}


def test_hidden_characters_switch_from_the_view_menu(files):
    from navigator.widgets.editor.commands import SwitchHiddenChars

    app = navigator(files)
    seen = []
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE,
                  lambda a: a.spawn(opened(a).viewer.emit(SwitchHiddenChars())), lambda a: None,
                  lambda a: seen.append(opened(a).viewer.show_hidden)])
    assert seen == [True]


def test_ctrl_shift_8_switches_hidden_characters_in_the_viewer(files):
    app = navigator(files)
    seen = []
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE,
                  KeyEvent("8", ctrl=True, shift=True),
                  lambda a: seen.append(opened(a).viewer.show_hidden)])
    assert seen == [True]


def test_the_quick_view_s_own_menu_views_renders_and_closes_only_itself(files):
    from navml.widgets.dialog.control.control import parse_shortcut
    from navml.widgets.menu.commands import ShowContextMenu
    from navml.widgets.menu.menu_box.menu_box import key_caption
    from navml.widgets.menu.menu_item import MenuItem
    from navml.widgets.menu.popup_menu import PopupMenu

    app = navigator(files)
    seen = {}

    def popup(a):
        return next((c for c in a.root.children if isinstance(c, PopupMenu)), None)

    def quick(a):
        return a.manager.quick if a.manager.quick.visible else None

    def open_menu(a):
        a.spawn(quick(a).viewer.emit(ShowContextMenu()))

    def look(a):
        viewer = quick(a).viewer
        seen["items"] = [(parse_shortcut(e.text)[0], key_caption(e, a, viewer))
                         for e in popup(a).box.entries() if isinstance(e, MenuItem)]

    run_app(app, [
        KeyEvent("end"), KeyEvent("q", ctrl=True),
        Until(lambda a: quick(a) is not None and quick(a).viewer.source is not None),
        open_menu, Until(lambda a: popup(a) is not None), look,
        KeyEvent("c", "c"), Until(lambda a: popup(a) is None), lambda a: None,
        lambda a: seen.update(after=quick(a), manager=a.manager in a.shell.desktop.windows(),
                              keys=a.focused is a.manager.left),
        KeyEvent("q", ctrl=True), Until(lambda a: quick(a) is not None and quick(a).viewer.source is not None),
        open_menu, Until(lambda a: popup(a) is not None), KeyEvent("v", "v"),
        Until(lambda a: opened(a) is not None),
        lambda a: seen.update(viewing=opened(a).viewer.path),
    ])
    assert seen["items"] == [("View", "F3"), ("Markup view", "Shift-F4"), ("Close quick view", "Ctrl-Q")]
    assert seen["after"] is None and seen["manager"]  # the panel back, the file manager still open
    assert seen["keys"]  # the right click never took the keyboard, so closing leaves it where it was
    assert seen["viewing"] == files / "text.txt"


def test_a_row_wider_than_the_view_puts_a_scroll_bar_on_the_bottom_frame(tmp_path, quiet_console):
    """A departure, as the editor's: DN's viewer had the right frame's bar alone."""
    from navml.widgets.dialog.scroll_bar import ScrollEvent

    (tmp_path / "wide.txt").write_text("short\n" + "x" * 200 + "\nshort\n")
    app = navigator(tmp_path)
    seen = {}

    def look(a, key):
        window = opened(a)
        seen[key] = (window.hbar.visible, window.hbar.maximum, window.viewer.x_delta)
        seen["width"] = window.viewer.width

    def drag(a):
        window = opened(a)
        a.spawn(window.on_hbar_scroll(ScrollEvent(value=50)))

    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE, lambda a: look(a, "open"),
                  drag, lambda a: None, lambda a: look(a, "dragged"),
                  KeyEvent("f2"), lambda a: look(a, "wrapped")])
    visible, maximum, _ = seen["open"]
    # Its range is the widest row on screen less the view's width.
    assert visible and maximum == 200 - seen["width"]
    assert seen["dragged"][2] == 50
    assert seen["wrapped"][0] is False


def test_rows_that_fit_leave_the_bottom_frame_without_a_bar(files):
    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE,
                  lambda a: seen.update(visible=opened(a).hbar.visible)])
    assert seen["visible"] is False


def test_the_quick_view_has_the_bottom_bar_too_while_the_keyboard_is_in_it(tmp_path, quiet_console):
    from navml.widgets.dialog.scroll_bar import ScrollEvent

    (tmp_path / "wide.txt").write_text("x" * 300 + "\n")
    app = navigator(tmp_path)
    seen = {}

    def look(a, key):
        quick = a.manager.quick
        seen[key] = (quick.hbar.visible, quick.viewer.x_delta)

    run_app(app, [
        KeyEvent("end"), KeyEvent("q", ctrl=True),
        Until(lambda a: a.manager.quick.viewer.source is not None),
        lambda a: look(a, "panel"),
        lambda a: a.manager.quick.viewer.focus(), lambda a: look(a, "inside"),
        lambda a: a.spawn(a.manager.quick.on_hbar_scroll(ScrollEvent(value=40))), lambda a: None,
        lambda a: look(a, "dragged"),
    ])
    # As the right bar: hidden while the keyboard is with the panel.
    assert seen["panel"][0] is False
    assert seen["inside"][0] is True
    assert seen["dragged"][1] == 40


def test_the_right_bar_shows_only_while_the_file_is_taller_than_the_view(tmp_path, quiet_console):
    """A departure, asked for, as the bottom bar: DN's ``TViewScroll`` was always there."""
    (tmp_path / "a_short.txt").write_text("one\ntwo\n")
    (tmp_path / "b_long.txt").write_text("".join(f"line {n}\n" for n in range(100)))
    (tmp_path / "c_wide.txt").write_text("y" * 2000 + "\n")
    app = navigator(tmp_path)
    seen = {}

    def look(key):
        return lambda a: seen.update({key: opened(a).bar.visible})

    run_app(app, [
        KeyEvent("down"), KeyEvent("f3"), IDLE, look("short"), KeyEvent("escape"), IDLE,
        KeyEvent("down"), KeyEvent("f3"), IDLE, look("long"), KeyEvent("ctrl+end"), look("long at end"),
        KeyEvent("escape"), IDLE,
        KeyEvent("down"), KeyEvent("f3"), IDLE, look("wide"), KeyEvent("f2"), look("wide wrapped"),
        KeyEvent("f4"), look("wide in hex"),
    ])
    # One long line fits unwrapped; wrapped it is 26 rows, and in hex 125.
    assert seen == {"short": False, "long": True, "long at end": True,
                    "wide": False, "wide wrapped": True, "wide in hex": True}
