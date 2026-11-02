"""F3's hex editing: DOS Navigator's ``HexEdit`` and Shift+F2's ``WriteModify``.

The model's overlay (``ViewSource.patch``/``undo``/``revert``, ``store_edits``),
the keys in hex mode, the question on closing, and the root helper's
``open_update``/``write_at`` run as the user (``ELEVATION.command``)."""

from __future__ import annotations

import os
import sys

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.viewer import (
    CHUNK,
    CACHED_CHUNKS,
    ChunkedSource,
    FileChanged,
    ViewSource,
    compile_search,
    edit_runs,
    store_edits,
)

DATA = bytes(range(256)) * 4


@pytest.fixture
def source(tmp_path):
    path = tmp_path / "f.bin"
    path.write_bytes(DATA)
    return ViewSource(path)


# -- the model -------------------------------------------------------------------


def test_a_byte_typed_shows_through_read_peek_and_lines(source):
    source.read(0, 16)
    assert source.patch(3, 0x41)
    assert source.read(0, 5) == b"\x00\x01\x02A\x04"
    assert source.peek(3) == 0x41
    assert source.edited and source.edits == {3: 0x41}


def test_a_byte_typed_survives_its_chunk_leaving_the_cache(tmp_path):
    path = tmp_path / "big.bin"
    path.write_bytes(b"\0" * CHUNK * (CACHED_CHUNKS + 2))
    source = ViewSource(path)
    source.read(10, 1)
    source.patch(10, 0xFF)
    for index in range(1, CACHED_CHUNKS + 2):
        source.read(index * CHUNK, 1)
    assert 0 not in source._chunks
    assert source.read(10, 1) == b"\xff"


def test_only_a_byte_already_read_can_be_typed_over(source):
    assert not source.patch(5, 1)
    assert not source.edited


def test_typing_the_files_own_byte_back_is_no_edit(source):
    source.read(0, 8)
    source.patch(2, 0x99)
    source.patch(2, 0x02)
    assert not source.edited


def test_undo_takes_back_the_last_byte_typed(source):
    source.read(0, 8)
    source.patch(1, 0xAA)
    source.patch(1, 0xBB)
    assert source.undo() == 1 and source.peek(1) == 0xAA
    assert source.undo() == 1 and source.peek(1) == 0x01
    assert source.undo() is None
    assert not source.edited


def test_revert_puts_the_files_byte_back(source):
    source.read(0, 8)
    source.patch(4, 0xAA)
    source.patch(4, 0xBB)
    assert source.revert(4) and source.peek(4) == 4 and not source.edited
    assert not source.revert(4)
    assert source.undo() == 4 and source.peek(4) == 0xBB


def test_a_file_read_whole_cannot_be_edited(tmp_path):
    path = tmp_path / "proc"
    path.write_bytes(b"")
    source = ViewSource(path)
    assert not source.editable
    assert not source.patch(0, 1)


def test_neighbouring_bytes_are_one_run():
    assert edit_runs({5: 1, 3: 9, 4: 8, 10: 7}) == [(3, b"\x09\x08\x01"), (10, b"\x07")]


def test_store_writes_in_place(source):
    inode = os.stat(source.path).st_ino
    source.read(0, 300)
    for offset, byte in ((0, 0x10), (1, 0x11), (299, 0x12)):
        source.patch(offset, byte)
    edits = dict(source.edits)
    store_edits(source, edits)
    source.stored(edits)
    data = source.path.read_bytes()
    assert data[:2] == b"\x10\x11" and data[299] == 0x12 and data[2:299] == DATA[2:299]
    assert os.stat(source.path).st_ino == inode
    assert not source.edited and not source.can_undo


def test_a_byte_typed_while_storing_stays_an_edit(source):
    source.read(0, 8)
    source.patch(0, 0x10)
    written = dict(source.edits)
    source.patch(1, 0x11)
    store_edits(source, written)
    source.stored(written)
    assert source.edits == {1: 0x11}


def test_store_refuses_a_file_that_changed_size(source):
    source.read(0, 8)
    source.patch(0, 0x10)
    with open(source.path, "ab") as file:
        file.write(b"more")
    with pytest.raises(FileChanged):
        store_edits(source, dict(source.edits))
    assert source.path.read_bytes()[0] == 0


def test_search_sees_the_bytes_typed(source):
    source.read(0, 8)
    pattern, span = compile_search("QQ")
    edits = {100: ord("Q"), 101: ord("Q")}
    assert source.find(pattern, 0, span=span) is None
    assert source.find(pattern, 0, span=span, edits=edits) == (100, 2)


def test_a_file_on_another_drive_is_written_whole():
    from navigator.lib.drives import mount, unmount
    from navigator.lib.drives.memory import MemoryDrive

    drive = mount(MemoryDrive("hexedit"))
    try:
        origin = drive.make("/f.bin", DATA)
        source = ChunkedSource(origin, len(DATA), drive.open_random(origin))
        store_edits(source, {0: 0xEE, 513: 0xDD})
        with drive.open_read(origin) as file:
            data = file.read()
        assert data[0] == 0xEE and data[513] == 0xDD and data[1:513] == DATA[1:513]
        source.close()
    finally:
        unmount(drive.site)


# -- the root helper, run as the user ----------------------------------------------


@pytest.fixture
def helper():
    from navigator.lib.system import elevate
    from navigator.lib.system.elevate import ELEVATION

    ELEVATION.command = [sys.executable, "-I", "-c", elevate._BOOT]
    assert ELEVATION.begin() == elevate.READY_STATE
    yield ELEVATION
    ELEVATION.close()
    ELEVATION.command = None


def test_as_root_writes_in_place_through_the_helper(source, helper):
    inode = os.stat(source.path).st_ino
    source.read(0, 8)
    source.patch(7, 0x77)
    store_edits(source, dict(source.edits), as_root=True)
    assert source.path.read_bytes()[7] == 0x77
    assert os.stat(source.path).st_ino == inode


def test_the_helper_opens_no_file_that_is_not_there(tmp_path, helper):
    from navigator.lib.drives.root import ROOT_DRIVE

    with pytest.raises(FileNotFoundError):
        ROOT_DRIVE.patch_file(tmp_path / "missing", [(0, b"x")], size=0)
    assert not (tmp_path / "missing").exists()


def test_the_helper_refuses_a_changed_size(source, helper):
    from navigator.lib.drives.root import ROOT_DRIVE

    with pytest.raises(FileChanged):
        ROOT_DRIVE.patch_file(source.path, [(0, b"x")], size=1)


# -- the window ----------------------------------------------------------------------


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "zz.bin").write_bytes(DATA)
    return tmp_path


def opened(app):
    from navigator.widgets.viewer.file_window import FileWindow

    window = app.shell.desktop.active_window
    return window if isinstance(window, FileWindow) else None


def keys(text: str) -> list[KeyEvent]:
    return [KeyEvent(c.lower(), c, shift=c.isupper()) for c in text]


def in_hex():
    return [KeyEvent("end"), KeyEvent("f3"), Until(lambda a: opened(a) is not None),
            lambda a: opened(a).viewer.set_mode("hex")]


def test_hex_digits_type_over_nibbles_and_shift_f2_stores(files):
    app = Navigator(files, files, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [
        *in_hex(),
        *keys("4a"), KeyEvent("q", "q"), *keys("F"),
        lambda a: seen.update(cursor=opened(a).viewer.cursor, nibble=opened(a).viewer.nibble,
                              edited=opened(a).viewer.edited, info=opened(a).viewer.info_text),
        KeyEvent("f2", shift=True), Until(lambda a: not opened(a).viewer.edited),
    ])
    assert seen["edited"] and seen["info"].startswith("*[")
    # 4, A, then F: "q" was swallowed; F is the next byte's high nibble.
    assert (seen["cursor"], seen["nibble"]) == (1, 1)
    data = (files / "zz.bin").read_bytes()
    assert data[0] == 0x4A and data[1] == 0xF1 and data[2:] == DATA[2:]


def test_tab_types_characters(files):
    app = Navigator(files, files, terminal=FakeTerminal(80, 24))
    run_app(app, [
        *in_hex(),
        KeyEvent("tab"), *keys("Hi"),
        KeyEvent("f2", shift=True), Until(lambda a: not opened(a).viewer.edited),
    ])
    assert (files / "zz.bin").read_bytes()[:3] == b"Hi\x02"


def test_cursor_sits_on_the_nibble_or_the_character(files):
    app = Navigator(files, files, terminal=FakeTerminal(80, 24))
    seen = []
    run_app(app, [
        *in_hex(),
        KeyEvent("right"), lambda a: seen.append(opened(a).viewer.cursor_position()),
        KeyEvent("tab"), lambda a: seen.append(opened(a).viewer.cursor_position()),
    ])
    from navigator.lib.viewer import HEX_PAIRS_AT, hex_chars_at, hex_row_bytes

    assert seen[0] == (HEX_PAIRS_AT + 1, 0)
    assert seen[1] == (hex_chars_at(hex_row_bytes(78)), 0)


def test_ctrl_z_and_backspace_take_bytes_back(files):
    app = Navigator(files, files, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [
        *in_hex(),
        KeyEvent("tab"), *keys("abc"),
        KeyEvent("z", ctrl=True), KeyEvent("backspace"),
        lambda a: seen.update(edits=dict(opened(a).viewer.source.edits), cursor=opened(a).viewer.cursor),
    ])
    assert seen == {"edits": {0: ord("a")}, "cursor": 1}


def test_closing_with_bytes_typed_asks_and_no_loses_them(files):
    app = Navigator(files, files, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [
        *in_hex(), *keys("ff"),
        KeyEvent("escape"), Until(lambda a: a.modal is not None),
        lambda a: seen.update(still=opened(a) is not None, modal=type(a.modal).__name__),
        KeyEvent("n", alt=True), Until(lambda a: opened(a) is None),
        lambda a: seen.update(closed=True),
    ])
    assert seen["still"] and seen["modal"] == "Dialog"
    assert seen["closed"]
    assert (files / "zz.bin").read_bytes() == DATA


def test_the_quick_view_types_nothing(files):
    from navigator.widgets.viewer.file_viewer import FileViewer

    viewer = FileViewer()
    viewer.open(files / "zz.bin")
    viewer.mode = "hex"
    assert not viewer.editable
