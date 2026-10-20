"""F3 on a file on another drive, read a chunk at a time
(``navigator.lib.viewer.ChunkedSource``): the window up at once whatever the
size, *Reading...* where a chunk is on its way, a move that needed one done
once it lands, search and *Save as* through the drive -- on the in-memory
drive, slowed so every chunk is really "not yet", and on a real SFTP server."""

from __future__ import annotations

import threading
import time

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent
from navigator.lib.drives import mount, unmount
from navigator.lib.drives.base import SeekingReader
from navigator.lib.drives.memory import MemoryDrive
from navigator.lib.viewer import CHUNK, ChunkedSource, NotYet

LINES = 60_000
TEXT = "".join(f"line {number:06d} of the long file\n" for number in range(LINES))


class Slow(SeekingReader):
    """A drive a round trip away: every read waits a little."""

    reads = 0

    def read_at(self, offset, count):
        time.sleep(0.01)
        type(self).reads += 1
        return super().read_at(offset, count)


@pytest.fixture
def memory(monkeypatch):
    drive = mount(MemoryDrive("chunked"))
    drive.make("/big.txt", TEXT)
    monkeypatch.setattr(MemoryDrive, "open_random", lambda self, location: Slow(self.open_read(location)))
    Slow.reads = 0
    yield drive
    unmount(drive.site)


def test_a_chunk_not_here_is_asked_for_and_said_when_it_lands(memory):
    origin = memory.location("/big.txt")
    source = ChunkedSource(origin, len(TEXT), memory.open_random(origin))
    landed = threading.Event()
    source.arrived = landed.set
    try:
        with pytest.raises(NotYet):
            source.read(0, 100)
        assert landed.wait(2)
        # Two fetchers: the read-ahead chunk 1 may land (and say so) before chunk 0.
        for _ in range(100):
            if source.ready(0, 20):
                break
            time.sleep(0.02)
        assert source.read(0, 20) == b"line 000000 of the l"
        # Read ahead: the chunks after the first were asked for with it.
        for _ in range(100):
            if source.ready(3 * CHUNK, 10):
                break
            time.sleep(0.02)
        assert source.ready(3 * CHUNK, 10)
        assert Slow.reads >= 4
        line = source.line(0, None)
        assert "".join(char for char, _ in line.cells) == "line 000000 of the long file"
    finally:
        source.close()


def test_search_reads_through_the_drive_on_its_thread(memory):
    origin = memory.location("/big.txt")
    source = ChunkedSource(origin, len(TEXT), memory.open_random(origin))
    try:
        import re

        found = source.find(re.compile(rb"line 059990"), 0)
        assert found is not None and TEXT.encode()[found[0]:found[0] + 11] == b"line 059990"
    finally:
        source.close()


@pytest.fixture
def desk(memory, tmp_path, monkeypatch):
    from navigator.__main__ import Navigator

    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    return Navigator(tmp_path, tmp_path, terminal=FakeTerminal(100, 30)), memory


def viewer_of(app):
    from navigator.widgets.viewer.file_window import FileWindow

    window = next((w for w in app.shell.desktop.windows() if isinstance(w, FileWindow)), None)
    return window.viewer if window is not None else None


def shown(app):
    """The viewer's first row as painted, or None while it says *Reading...*."""
    viewer = viewer_of(app)
    try:
        rows = viewer._text_rows(1)
    except NotYet:
        return None
    return "".join(char for char, _ in rows[0].cells) if rows else ""


def test_f3_opens_at_once_and_ctrl_page_down_goes_to_the_end_once_it_is_here(desk, tmp_path):
    app, memory = desk
    seen = {}

    def on_big(a):
        panel = a.manager.left
        panel.cursor = [entry.name for entry in panel.items].index("big.txt")

    run_app(app, [
        lambda a: setattr(a.manager.left, "location", memory.location("/")),
        Until(lambda a: "big.txt" in [e.name for e in a.manager.left.items]), on_big,
        KeyEvent("f3"), Until(lambda a: viewer_of(a) is not None, timeout=5),
        lambda a: seen.update(remote=viewer_of(a).remote, title=viewer_of(a).parent.title),
        Until(lambda a: shown(a) == "line 000000 of the long file", timeout=5),
        KeyEvent("pagedown", ctrl=True),
        Until(lambda a: shown(a) is not None and shown(a).startswith("line 0599"), timeout=10),
        lambda a: seen.update(end=viewer_of(a).percent()),
        KeyEvent("pageup", ctrl=True), Until(lambda a: shown(a) == "line 000000 of the long file", timeout=5),
        # The app exits without unmounting: closed here, or its queued
        # fetches would run on into the next test.
        lambda a: viewer_of(a).source.close(),
    ], timeout=30)
    assert seen["remote"] and seen["title"] == "mem://chunked/big.txt"
    assert seen["end"] == 100
    # Not the whole file: only what was looked at, and the read-ahead.
    assert Slow.reads * CHUNK < len(TEXT)


def test_save_as_writes_the_whole_file_from_its_drive(memory, tmp_path):
    from navigator.lib import viewer

    origin = memory.location("/big.txt")
    source = ChunkedSource(origin, len(TEXT), memory.open_random(origin))
    try:
        viewer.save_as(source, tmp_path / "copy.txt")
    finally:
        source.close()
    assert (tmp_path / "copy.txt").read_text() == TEXT


def test_an_sftp_file_is_read_a_chunk_at_a_time(tmp_path, monkeypatch):
    pytest.importorskip("paramiko")
    import re
    from pathlib import PurePosixPath

    from navigator.lib.drives import Location, Site
    from navigator.lib.drives.sessions import SESSIONS, Answers
    from sftp_server import PASSWORD, SftpServer

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("SSH_AUTH_SOCK", raising=False)
    monkeypatch.setattr("navigator.lib.drives.credentials.keyring_available", lambda: False)
    root = tmp_path / "served"
    root.mkdir()
    (root / "big.txt").write_text(TEXT)
    served = SftpServer(root)
    try:
        site = Site("sftp", "tester", "127.0.0.1", served.port)
        drive = SESSIONS.connect(site, Answers(password=PASSWORD, host_key="once"))
        origin = Location(site, PurePosixPath("/big.txt"))
        source = ChunkedSource(origin, len(TEXT), drive.open_random(origin))
        landed = threading.Event()
        source.arrived = landed.set
        try:
            middle = len(TEXT) // 2
            with pytest.raises(NotYet):
                source.read(middle, 10)
            assert landed.wait(5)
            for _ in range(100):
                if source.ready(middle, 10):
                    break
                time.sleep(0.02)
            assert source.read(middle, 10) == TEXT.encode()[middle:middle + 10]
            assert source.find(re.compile(rb"line 059999"), middle) is not None
        finally:
            source.close()
    finally:
        SESSIONS.close_all()
        served.stop()


def test_a_file_on_another_drive_is_highlighted_a_window_at_a_time(desk):
    from navigator.widgets.viewer.file_viewer import file_viewer

    app, memory = desk
    code = "".join(f"value_{number} = 'text {number}'  # note\n" for number in range(20_000))
    memory.make("/code.py", code)
    seen = {}

    def on_code(a):
        panel = a.manager.left
        panel.cursor = [entry.name for entry in panel.items].index("code.py")

    def spans(a):
        viewer = viewer_of(a)
        return viewer is not None and bool(viewer._spans)

    run_app(app, [
        lambda a: setattr(a.manager.left, "location", memory.location("/")),
        Until(lambda a: "code.py" in [e.name for e in a.manager.left.items]), on_code,
        KeyEvent("f3"), Until(lambda a: viewer_of(a) is not None, timeout=5),
        Until(spans, timeout=10),
        lambda a: seen.update(lexer=viewer_of(a).lexer_name, covered=viewer_of(a)._covered,
                              classes={span[2] for span in viewer_of(a)._spans}),
        KeyEvent("pagedown", ctrl=True),
        Until(lambda a: viewer_of(a)._covered[1] == len(code), timeout=10),
        lambda a: seen.update(end=viewer_of(a)._covered),
        lambda a: viewer_of(a).source.close(),
    ], timeout=30)
    assert seen["lexer"] == "python"
    # Only a window, not the whole file: two chunks past the top.
    assert seen["covered"][0] == 0 and seen["covered"][1] <= file_viewer.REMOTE_LEX_AHEAD
    assert any("comment" in str(classes) for classes in seen["classes"])
    assert seen["end"][0] > 0
