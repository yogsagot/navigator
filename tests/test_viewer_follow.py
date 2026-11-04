"""F3's *Follow end* (Ctrl+T, ``tail -f``) and *Filter lines* (Ctrl+G, ``grep``):
departures, asked for -- the model in ``navigator/lib/viewer`` and the window."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, IDLE, run_app, Until
from navkit.events import KeyEvent
from navkit.screen import ScreenBuffer

from navigator.__main__ import Navigator
from navigator.lib.viewer import CHUNK, ViewSource
from navigator.lib.viewer.lines import LinePattern, LineScan, WINDOW, scan


# -- the model: the size looked at again ----------------------------------------


def test_refresh_says_grew_shrank_or_same(tmp_path):
    path = tmp_path / "log"
    path.write_bytes(b"one\n")
    source = ViewSource(path)
    assert source.refresh() == "same"
    with open(path, "ab") as stream:
        stream.write(b"two\n")
    assert source.refresh() == "grew"
    assert source.size == 8
    assert source.read(0, 8) == b"one\ntwo\n"
    path.write_bytes(b"x\n")
    assert source.refresh() == "shrank"
    assert source.read(0, 10) == b"x\n"


def test_the_chunk_cached_short_is_read_again(tmp_path):
    path = tmp_path / "log"
    path.write_bytes(b"a" * (CHUNK + 10))
    source = ViewSource(path)
    assert len(source.read(CHUNK, 100)) == 10  # the last chunk, cached short
    with open(path, "ab") as stream:
        stream.write(b"b" * 20)
    source.refresh()
    assert source.read(CHUNK, 100) == b"a" * 10 + b"b" * 20


def test_an_empty_file_written_to_is_followed(tmp_path):
    path = tmp_path / "log"
    path.write_bytes(b"")
    source = ViewSource(path)
    assert source.can_follow
    path.write_bytes(b"first\n")
    assert source.refresh() == "grew"
    assert source.read(0, 6) == b"first\n"


# -- the model: lines matched ------------------------------------------------------


def lines_of(data: bytes, pattern: LinePattern) -> LineScan:
    found = LineScan(pattern)
    found.scan(lambda offset, count: data[offset:offset + count], len(data))
    return found


def test_literal_case_and_invert():
    data = b"Error one\nfine\nerror two\r\nlast"
    assert [h.number for h in lines_of(data, LinePattern("error")).shown] == [1, 3]
    assert [h.number for h in lines_of(data, LinePattern("error", case=True)).shown] == [3]
    assert [h.text for h in lines_of(data, LinePattern("error", invert=True)).shown] == ["fine", "last"]
    # A literal is literal: the dot is a dot.
    assert lines_of(b"a.b\naxb\n", LinePattern("a.b")).shown[0].number == 1
    assert len(lines_of(b"a.b\naxb\n", LinePattern("a.b")).shown) == 1


def test_a_regular_expression_and_its_spans():
    found = lines_of(b"id=12 id=7\nnone\n", LinePattern(r"id=\d+", regex=True))
    assert [h.number for h in found.shown] == [1]
    assert found.spans("id=12 id=7") == [(0, 5), (6, 10)]
    with pytest.raises(Exception):
        LinePattern("(", regex=True).compile()


def test_the_crlf_ending_is_not_in_the_text():
    hit = lines_of(b"x\r\ny\r\n", LinePattern("x")).shown[0]
    assert hit.text == "x" and (hit.start, hit.end) == (0, 1)


def test_numbers_count_across_windows():
    data = b"".join(b"%07d\n" % n for n in range(WINDOW // 8 * 3))
    found = lines_of(data, LinePattern("0300000"))
    assert [h.number for h in found.shown] == [300001]
    assert found.shown[0].start == 300000 * 8


def test_a_scan_goes_on_from_where_it_stopped():
    data = bytearray(b"hit 1\nmiss\nhit 3 unfinished")
    found = LineScan(LinePattern("hit"))
    read = lambda offset, count: bytes(data[offset:offset + count])
    found.scan(read, len(data))
    assert [h.number for h in found.shown] == [1, 3] and found.lines == 2
    data += b" now ended\nhit 4\n"
    found.scan(read, len(data))
    assert [(h.number, h.text) for h in found.shown] == [
        (1, "hit 1"), (3, "hit 3 unfinished now ended"), (4, "hit 4")]
    assert found.tail is None


def test_the_hit_limit_stops_the_scan(monkeypatch):
    import navigator.lib.viewer.lines as lines

    monkeypatch.setattr(lines, "HIT_LIMIT", 3)
    found = lines_of(b"a\n" * 10, LinePattern("a"))
    assert len(found.shown) == 3 and found.truncated


def test_scan_reads_a_viewer_source(tmp_path):
    path = tmp_path / "f"
    path.write_bytes(b"one\ntwo\nthree\n")
    source = ViewSource(path)
    found = scan(LineScan(LinePattern("t")), source, source.size)
    assert [h.text for h in found.shown] == ["two", "three"]


# -- the window ------------------------------------------------------------------


@pytest.fixture
def log(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "log.txt").write_text("".join(f"line {n:03}\n" for n in range(100)))
    return tmp_path


def screen(app) -> ScreenBuffer:
    from conftest import settle

    buffer = ScreenBuffer(80, 24)
    app.shell.layout(80, 24)
    settle()
    app.shell.render_tree(buffer)
    return buffer


def text_of(buffer: ScreenBuffer) -> str:
    return "\n".join("".join(buffer.get(x, y)[0] or " " for x in range(buffer.width))
                     for y in range(buffer.height))


def viewer_of(app):
    from navigator.widgets.viewer.file_window import FileWindow

    window = app.shell.desktop.active_window
    return window.viewer if isinstance(window, FileWindow) else None


def append(path, text: str):
    def act(app):
        with open(path, "a") as stream:
            stream.write(text)
    return act


def test_ctrl_t_follows_the_end_as_the_file_grows(log):
    app = Navigator(log, log, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE, KeyEvent("ctrl+t"),
        lambda a: seen.update(following=viewer_of(a).follow),
        append(log / "log.txt", "brand new line\n"),
        Until(lambda a: viewer_of(a).size > 900, timeout=4),
        lambda a: seen.update(screen=text_of(screen(a))),
    ], timeout=8)
    assert seen["following"]
    assert "brand new line" in seen["screen"]
    assert "{Follow}" in seen["screen"]


def test_scrolling_up_lets_go(log):
    app = Navigator(log, log, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE, KeyEvent("ctrl+t"),
                  KeyEvent("pageup"), lambda a: seen.update(following=viewer_of(a).follow)])
    assert seen["following"] is False


def test_ctrl_g_shows_the_matching_lines_with_their_numbers(log):
    app = Navigator(log, log, terminal=FakeTerminal(80, 24))
    seen = {}

    def ask(app):
        from navigator.widgets.viewer.filter_lines_dialog import FilterLinesDialog

        dialog = app.modal
        assert isinstance(dialog, FilterLinesDialog)
        dialog.what.value = "line 04"
        dialog.close(dialog.accept())

    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE, KeyEvent("ctrl+g"),
        Until(lambda a: type(a.modal).__name__ == "FilterLinesDialog"), ask,
        Until(lambda a: viewer_of(a).lines is not None),
        lambda a: seen.update(screen=text_of(screen(a))),
        KeyEvent("down"), KeyEvent("down"), KeyEvent("enter"),
        lambda a: seen.update(top=viewer_of(a).top, lines=viewer_of(a).lines),
    ])
    shown = seen["screen"]
    assert "41│line 040" in shown and "50│line 049" in shown
    assert "line 039" not in shown and "line 050" not in shown
    assert "10 of 100 lines" in shown
    # Enter on the third row: the whole file, from line 42.
    assert seen["lines"] is None
    assert seen["top"] == 42 * 9


def test_a_file_across_a_network_follows_by_the_size_its_drive_gives():
    """``ChunkedSource.refresh`` takes the size a thread asked the drive for;
    the chunk that landed short is fetched again."""
    import threading

    from navigator.lib.viewer import ChunkedSource, NotYet

    data = bytearray(b"first\n")

    class Reader:
        def read_at(self, offset, count):
            return bytes(data[offset:offset + count])

        def close(self):
            pass

    class Origin:
        name = "remote.log"

    source = ChunkedSource(Origin(), len(data), Reader())
    landed = threading.Event()
    source.arrived = landed.set

    def read_all():
        for _ in range(200):
            try:
                return source.read(0, source.size)
            except NotYet:
                landed.wait(1)
                landed.clear()
        raise AssertionError("never landed")

    try:
        assert read_all() == b"first\n"
        assert source.refresh() == "same"  # nothing looked at on the loop
        data.extend(b"second\n")
        assert source.refresh(len(data)) == "grew"
        assert read_all() == b"first\nsecond\n"
    finally:
        source.close()
