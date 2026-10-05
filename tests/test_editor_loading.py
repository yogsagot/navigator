"""Reading a file for the editor on a thread: *Reading file*, Cancel, and too large.

DN's ``ReadBlock`` (MICROED.PAS): the file read a block at a time behind
``WriteMsg(dlReadingFile)``, Esc between blocks, and ``OutOfMemory`` for a file
the memory left would not hold.
"""

from __future__ import annotations

import os
import random
import re
import threading
import time
from collections import Counter

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent
from navkit.glyphs import GLYPHS_ASCII, GLYPHS_UNICODE, spinner

from navigator import memory, smartpad
from navigator.__main__ import Navigator
from navigator.editor import document as document_module
from navigator.editor.document import Document, LineReader, decode, read_document, read_text
from navigator.job import Job, Stopped
from navigator.memory import NOT_ENOUGH_MEMORY, NotEnoughMemory, parse_meminfo
from navigator.settings import SETTINGS
from navigator.widgets.editor import loading


# -- the reader -------------------------------------------------------------------------

_OLD_BREAK = re.compile(rb"\r\n|\r|\n")


def old_from_bytes(data: bytes) -> tuple[list[str], list[str], str]:
    """``Document.from_bytes`` as it was before the reader: the oracle."""
    lines, endings, start = [], [], 0
    for match in _OLD_BREAK.finditer(data):
        lines.append(decode(data[start:match.start()]))
        endings.append(match.group().decode("ascii"))
        start = match.end()
    lines.append(decode(data[start:]))
    endings.append("")
    counts = Counter(e for e in endings if e)
    return lines, endings, counts.most_common(1)[0][0] if counts else "\n"


def fed(data: bytes, sizes) -> Document:
    reader = LineReader()
    pos = 0
    for size in sizes:
        reader.feed(data[pos:pos + size])
        pos += size
    reader.feed(data[pos:])
    return reader.finish()


def as_tuple(document: Document) -> tuple[list[str], list[str], str]:
    return document.lines, document.endings, document.newline


def test_the_reader_splits_as_from_bytes_did_however_the_bytes_are_cut():
    rng = random.Random(1987)
    alphabet = [b"a", b"\r", b"\n", b"\xc3", b"\xa9", b"\xff", b"\xe2\x82", b"\xe2\x82\xac"]
    for _ in range(3000):
        data = b"".join(rng.choice(alphabet) for _ in range(rng.randrange(0, 40)))
        want = old_from_bytes(data)
        assert as_tuple(Document.from_bytes(data)) == want, data
        sizes = [rng.randrange(1, 10) for _ in range(len(data))]
        assert as_tuple(fed(data, sizes)) == want, (data, sizes)


@pytest.mark.parametrize("data, sizes", [
    (b"a\r\nb", [2]),            # CR ends one chunk, LF starts the next: one CRLF
    (b"a\r", [2]),               # a CR at the very end is a break of its own
    (b"\r\r\n", [1, 1]),
    (b"", []),
    (b"x\r\ny\nz\r\nw\n", [3]),  # a tie goes to the ending met first
    (b"\r", [1]),
    (b"no break at all", [4, 4]),
])
def test_the_reader_at_the_edges(data, sizes):
    assert as_tuple(fed(data, sizes)) == old_from_bytes(data)


def test_a_file_read_in_small_chunks_round_trips(tmp_path):
    for i, data in enumerate([b"", b"one", b"one\r\ntwo\nthree\rfour", b"\n\n\r\n",
                              b"tab\there\r\n\xff\xfe broken \xc3\n"]):
        path = tmp_path / f"f{i}"
        path.write_bytes(data)
        assert read_document(path, chunk=3).encode() == data
        assert read_text(path, chunk=2) == decode(data)


class ReadJob(Job):
    def __init__(self):
        super().__init__()
        self.position = self.total = 0


def test_a_stopped_read_raises_stopped(tmp_path):
    path = tmp_path / "f"
    path.write_bytes(b"line\n" * 100)
    job = ReadJob()
    job.stop()
    with pytest.raises(Stopped):
        read_document(path, job, chunk=8)


def test_a_read_says_how_far_it_has_got(tmp_path):
    path = tmp_path / "f"
    path.write_bytes(b"line\n" * 100)
    job = ReadJob()
    read_document(path, job, chunk=8)
    assert (job.position, job.total) == (500, 500)


def test_a_fifo_and_a_directory_are_refused_without_being_opened(tmp_path):
    fifo = tmp_path / "pipe"
    os.mkfifo(fifo)
    with pytest.raises(OSError, match="Not a regular file"):
        read_document(fifo)
    with pytest.raises(OSError, match="Not a regular file"):
        read_document(tmp_path)


# -- too large for memory ---------------------------------------------------------------


def test_a_file_larger_than_the_budget_is_refused_before_it_is_opened(tmp_path, monkeypatch):
    path = tmp_path / "big"
    path.write_bytes(b"x" * 1000)
    opened = []
    real_open = open
    monkeypatch.setattr(document_module, "open",
                        lambda *a, **k: opened.append(a) or real_open(*a, **k), raising=False)
    with pytest.raises(NotEnoughMemory):
        read_document(path, budget=999)
    assert opened == []


def test_short_lines_trip_the_budget_after_the_first_chunk(tmp_path):
    # 2000 bytes, but a thousand lines cost far more than their characters.
    path = tmp_path / "short"
    path.write_bytes(b"x\n" * 1000)
    job = ReadJob()
    with pytest.raises(NotEnoughMemory):
        read_document(path, job, chunk=100, budget=10_000)
    assert job.position == 100  # projected from the first chunk, not read to the end


def test_meminfo_is_read_in_kilobytes():
    text = "MemTotal:       32694140 kB\nMemFree:  100 kB\nMemAvailable:   19563572 kB\n"
    assert parse_meminfo(text) == 19563572 * 1024
    assert parse_meminfo("MemTotal: 1 kB\n") is None


def test_without_proc_the_free_pages_are_asked(monkeypatch):
    def no_proc(*args, **kwargs):
        raise FileNotFoundError(args[0])

    monkeypatch.setattr(memory, "open", no_proc, raising=False)
    pages = {"SC_AVPHYS_PAGES": 10, "SC_PAGE_SIZE": 4096}
    monkeypatch.setattr(memory.os, "sysconf", lambda name: pages[name])
    assert memory.available_memory() == 40960


# -- in the application -----------------------------------------------------------------


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "text.txt").write_bytes(b"first line\nsecond line\n")
    return tmp_path


@pytest.fixture
def slow_read(monkeypatch):
    """Reads that stop half way until released, so *Reading file* comes up at once."""
    release = threading.Event()
    jobs = []
    real = document_module.read_document

    def read(path, job=None, **kwargs):
        if job is not None:
            jobs.append(job)
            job.total = 200
            while not (release.is_set() or job.stopped):
                job.position = 100
                release.wait(0.01)
            if job.stopped:
                raise Stopped
        return real(path, job, **kwargs)

    monkeypatch.setattr(document_module, "read_document", read)
    monkeypatch.setattr(loading, "read_document", read)
    monkeypatch.setattr(loading, "SLOW_PROGRESS_DELAY", 0.05)
    release.jobs = jobs
    return release


def navigator(path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def editor_windows(app):
    from navigator.widgets.editor.edit_window import EditWindow

    return [w for w in app.shell.desktop.windows() if isinstance(w, EditWindow)]


def writewin(app):
    from navigator.widgets.file_ops.write_win import WriteWin

    return isinstance(app.modal, WriteWin)


def test_a_slow_read_shows_reading_file_with_a_turning_spinner_then_opens(files, slow_read):
    app = navigator(files)
    seen = {}

    def look(a):
        box = a.modal
        seen.update(message=box.notice, percent=box.bar.percent, frame=box.spinner.frame,
                    windows=len(editor_windows(a)))

    def look_again(a):
        seen["later"] = a.modal.spinner.frame
        slow_read.set()

    run_app(app, [KeyEvent("end"), KeyEvent("f4"), Until(writewin), Until(lambda a: a.modal.bar.percent == 50),
                  look, lambda a: None, lambda a: None, lambda a: None, look_again,
                  Until(lambda a: editor_windows(a) and a.modal is None)], settle=0.05)
    assert seen["message"] == "Reading file"
    assert seen["percent"] == 50
    assert seen["windows"] == 0
    assert seen["later"] > seen["frame"]
    window = editor_windows(app)[0]
    assert window.editor.document.encode() == b"first line\nsecond line\n"
    assert window.editor.focused


def test_cancel_stops_the_read_and_opens_nothing(files, slow_read):
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), Until(writewin),
                  KeyEvent("enter"), Until(lambda a: a.modal is None), lambda a: None])
    assert editor_windows(app) == []
    assert slow_read.jobs[0].stopped


def test_f4_twice_during_a_slow_read_opens_one_window(files, slow_read):
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), Until(writewin),
                  lambda a: a.spawn(a.manager.edit()), lambda a: None,
                  lambda a: slow_read.set(),
                  Until(lambda a: editor_windows(a) and a.modal is None), lambda a: None])
    assert len(editor_windows(app)) == 1


def test_a_file_too_large_is_refused_with_dns_message(files, monkeypatch):
    monkeypatch.setattr(loading, "edit_budget", lambda: 5)
    app = navigator(files)
    seen = []
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), Until(lambda a: a.modal is not None),
                  lambda a: seen.append(a.modal.prompt), KeyEvent("enter"), lambda a: None])
    assert seen == [NOT_ENOUGH_MEMORY]
    assert editor_windows(app) == []


def test_load_text_cancelled_keeps_the_text_and_the_title(files, slow_read):
    SETTINGS.interface.store_editor_position = False
    (files / "other.txt").write_bytes(b"other\n")
    app = navigator(files)
    slow_read.set()  # F4's own read goes through
    seen = {}

    def hold(a):
        slow_read.clear()

    run_app(app, [KeyEvent("end"), KeyEvent("f4"), Until(lambda a: editor_windows(a)),
                  hold, KeyEvent("f3"), lambda a: None,
                  *[KeyEvent(c, c) for c in "other.txt"], KeyEvent("enter"),
                  Until(writewin), KeyEvent("escape"), Until(lambda a: a.modal is None),
                  lambda a: seen.update(title=editor_windows(a)[0].title,
                                        text=editor_windows(a)[0].editor.document.encode())])
    assert seen == {"title": f"Edit - {files / 'text.txt'}", "text": b"first line\nsecond line\n"}


def test_ctrl_k_r_cancelled_inserts_nothing(files, slow_read):
    SETTINGS.interface.store_editor_position = False
    (files / "piece.txt").write_bytes(b"piece\n")
    app = navigator(files)
    slow_read.set()
    seen = []
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), Until(lambda a: editor_windows(a)),
                  lambda a: slow_read.clear(),
                  KeyEvent("k", ctrl=True), KeyEvent("r", "r"), lambda a: None,
                  *[KeyEvent(c, c) for c in "piece.txt"], KeyEvent("enter"),
                  Until(writewin), KeyEvent("escape"), Until(lambda a: a.modal is None),
                  lambda a: seen.append(editor_windows(a)[0].editor.document.encode())])
    assert seen == [b"first line\nsecond line\n"]


def test_alt_q_twice_during_a_slow_read_opens_one_pad(files, slow_read, monkeypatch):
    monkeypatch.setenv("SMARTPAD", str(files / "notes"))
    app = navigator(files)
    run_app(app, [KeyEvent("q", alt=True), Until(writewin), KeyEvent("q", alt=True),
                  lambda a: None, lambda a: slow_read.set(),
                  Until(lambda a: editor_windows(a) and a.modal is None), lambda a: None])
    assert len([w for w in editor_windows(app) if w.smartpad]) == 1
    assert smartpad._opening is False


# -- the spinner ------------------------------------------------------------------------


def test_the_spinner_degrades_to_ascii():
    assert spinner("dos", GLYPHS_ASCII) == "|/-\\"
    assert spinner("braille", GLYPHS_UNICODE).startswith("⠋")
    assert spinner("nonsense") == spinner("dos")


def test_a_spinner_turns_only_while_mounted():
    from navkit.application import Application
    from navml.widgets.spinner import Spinner

    root = Spinner(width=1, height=1)
    root.interval = 10
    app = Application(root, terminal=FakeTerminal(4, 1))
    frames = []
    run_app(app, [lambda a: time.sleep(0), lambda a: None, lambda a: frames.append(root.frame)],
            settle=0.05)
    assert frames[0] >= 3


# -- saving -----------------------------------------------------------------------------


@pytest.fixture
def slow_write(monkeypatch):
    """Saves that wait before their first byte until released -- or stopped."""
    from navigator.editor import save as save_module
    from navigator.widgets.editor.edit_window import edit_window

    release = threading.Event()
    jobs = []
    real = save_module.write_file

    def write(path, data, job=None):
        if job is not None:
            jobs.append(job)
            chunks = [data] if isinstance(data, bytes) else data

            def held():
                deadline = time.monotonic() + 5
                while not (release.is_set() or job.stopped) and time.monotonic() < deadline:
                    release.wait(0.01)
                yield from chunks

            data = held()
        return real(path, data, job)

    monkeypatch.setattr(edit_window, "write_file", write)
    monkeypatch.setattr(loading, "SLOW_PROGRESS_DELAY", 0.05)
    release.jobs = jobs
    return release


def test_encode_lines_gives_the_documents_bytes_whatever_the_step():
    data = b"one\r\ntwo\nthree\rfour\n\xff"
    document = Document.from_bytes(data)
    for step in (1, 2, 3, 100):
        assert b"".join(document_module.encode_lines(document.lines, document.endings,
                                                     step=step)) == data


def test_a_save_point_undone_while_it_was_written_saves_nothing():
    from navigator.editor.buffer import EditBuffer
    from navigator.editor.document import Pos

    buffer = EditBuffer(Document.from_bytes(b"abc"))
    buffer.insert(Pos(0, 0), "x")
    point = buffer.save_point()
    buffer.undo()
    buffer.mark_saved(point)
    assert buffer.modified
    assert buffer.document.encode() == b"abc"


def test_typing_during_a_save_is_not_saved_and_leaves_the_text_changed(
        files, slow_write, monkeypatch):
    monkeypatch.setattr(loading, "SLOW_PROGRESS_DELAY", 10)  # no box: keys reach the text
    app = navigator(files)
    seen = {}

    def look(a):
        seen.update(disk=(files / "text.txt").read_bytes(),
                    modified=editor_windows(a)[0].editor.modified)

    run_app(app, [KeyEvent("end"), KeyEvent("f4"), Until(lambda a: editor_windows(a)),
                  KeyEvent("a", "a"), KeyEvent("f2"), lambda a: None,
                  KeyEvent("b", "b"), lambda a: slow_write.set(),
                  Until(lambda a: (files / "text.txt").read_bytes().startswith(b"a")),
                  lambda a: None, look,
                  KeyEvent("f2"), Until(lambda a: not editor_windows(a)[0].editor.modified)])
    assert seen == {"disk": b"afirst line\nsecond line\n", "modified": True}
    assert (files / "text.txt").read_bytes() == b"abfirst line\nsecond line\n"


def test_cancel_on_writing_file_leaves_the_file_as_it_was(files, slow_write):
    app = navigator(files)
    seen = []
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), Until(lambda a: editor_windows(a)),
                  KeyEvent("z", "z"), KeyEvent("f2"), Until(writewin),
                  lambda a: seen.append(a.modal.notice),
                  KeyEvent("escape"), Until(lambda a: a.modal is None), lambda a: None,
                  lambda a: seen.append(editor_windows(a)[0].editor.modified)])
    assert seen == ["Writing file", True]
    assert slow_write.jobs[0].stopped
    assert (files / "text.txt").read_bytes() == b"first line\nsecond line\n"
    assert sorted(p.name for p in files.iterdir()) == ["text.txt"]  # no temporary left


def test_a_file_written_in_place_cannot_be_cancelled(files, slow_write):
    os.link(files / "text.txt", files / "twin.txt")
    app = navigator(files)
    seen = []

    def look(a):
        seen.append((a.modal.cancellable, a.modal.ok.visible))

    run_app(app, [KeyEvent("end"), KeyEvent("f4"), Until(lambda a: editor_windows(a)),
                  KeyEvent("z", "z"), KeyEvent("f2"), Until(writewin),
                  Until(lambda a: not a.modal.cancellable), look,
                  KeyEvent("escape"), lambda a: None,
                  lambda a: seen.append(writewin(a)), lambda a: slow_write.set(),
                  Until(lambda a: a.modal is None and not editor_windows(a)[0].editor.modified)])
    assert seen == [(False, False), True]
    assert (files / "twin.txt").read_bytes() == b"zfirst line\nsecond line\n"


def test_two_saves_at_once_write_one_after_the_other(files, slow_write, monkeypatch):
    monkeypatch.setattr(loading, "SLOW_PROGRESS_DELAY", 10)
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), Until(lambda a: editor_windows(a)),
                  KeyEvent("z", "z"), KeyEvent("f2"), lambda a: None, KeyEvent("f2"),
                  lambda a: None, lambda a: slow_write.set(),
                  Until(lambda a: len(slow_write.jobs) == 2
                        and not editor_windows(a)[0].editor.modified),
                  lambda a: None])
    assert (files / "text.txt").read_bytes() == b"zfirst line\nsecond line\n"
    assert app.modal is None  # neither save said it failed


def test_closing_with_yes_during_a_save_waits_for_it_and_closes(files, slow_write, monkeypatch):
    monkeypatch.setattr(loading, "SLOW_PROGRESS_DELAY", 10)
    app = navigator(files)
    seen = []
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), Until(lambda a: editor_windows(a)),
                  KeyEvent("z", "z"), KeyEvent("f2"), lambda a: None,
                  KeyEvent("escape"), Until(lambda a: a.modal is not None),
                  lambda a: seen.append(a.modal.prompt),
                  KeyEvent("enter"), lambda a: None, lambda a: slow_write.set(),
                  Until(lambda a: not editor_windows(a)), lambda a: None])
    assert seen == ["File text.txt was modified. Save?"]
    assert (files / "text.txt").read_bytes() == b"zfirst line\nsecond line\n"
