"""The editor's encodings and line endings: the model, the swap undo, the
bottom frame's markers and their boxes -- a departure, asked for."""

from __future__ import annotations

import codecs

import pytest

from conftest import IDLE, Until, run_app
from navkit.events import KeyEvent, MouseClickEvent

from navigator.lib.editor import encodings
from navigator.lib.editor.buffer import EditBuffer, State
from navigator.lib.editor.document import Document, LineReader, Pos, read_document
from navigator.settings import SETTINGS
from test_editor import editor_window, files, navigator, quiet_console, row_of, screen  # noqa: F401

SAMPLES = [
    b"",
    b"a\r\nb\nc",
    b"x\r",
    "żółw\n".encode(),
    codecs.BOM_UTF8 + "żółw\r\n".encode(),
    codecs.BOM_UTF16_LE + "x\r\ny\rz".encode("utf-16-le"),
    codecs.BOM_UTF16_BE + "q\nw\n".encode("utf-16-be"),
    b"\xff\xfe\x00",  # a UTF-16 mark on what does not decode: UTF-8 with its bytes kept
    b"\xef\xbb",
    b"bad \xff byte\n",
]


def chunked(data: bytes, size: int, encoding: str | None = None) -> Document:
    reader = LineReader(encoding)
    for at in range(0, len(data), size):
        reader.feed(data[at:at + size])
    return reader.finish()


@pytest.mark.parametrize("data", SAMPLES)
def test_every_text_round_trips_byte_for_byte_however_it_is_cut(data):
    document = Document.from_bytes(data)
    assert document.encode() == data
    for size in (1, 2, 3, 5, 64):
        try:
            again = chunked(data, size)
        except UnicodeDecodeError:
            again = chunked(data, size, encodings.UTF8)
        assert (again.lines, again.endings, again.encoding) == \
            (document.lines, document.endings, document.encoding)


def test_a_mark_says_the_encoding_and_is_not_part_of_the_text():
    assert Document.from_bytes(codecs.BOM_UTF8 + b"a").encoding == encodings.UTF8_BOM
    assert Document.from_bytes(codecs.BOM_UTF8 + b"a").lines == ["a"]
    utf16 = Document.from_bytes(codecs.BOM_UTF16_LE + "a\r\nb".encode("utf-16-le"))
    assert utf16.encoding == encodings.UTF16_LE and utf16.lines == ["a", "b"]
    assert utf16.line_ending == "CRLF"
    broken = Document.from_bytes(b"\xff\xfe\x00")
    assert broken.encoding == encodings.UTF8


def test_every_encoding_writes_back_what_it_read(tmp_path):
    text = "Grüße\r\nmir\r\n"
    for key, _, _ in encodings.CODECS:
        try:
            data = encodings.bom(key) + encodings.encode(text, key)
        except UnicodeEncodeError:
            continue
        path = tmp_path / key
        path.write_bytes(data)
        document = read_document(path, encoding=key, chunk=3)
        assert document.encode() == data, key


def test_the_ending_tally_follows_every_edit():
    document = Document.from_bytes(b"a\r\nb\r\nc")
    assert document.line_ending == "CRLF"
    document.insert(Pos(2, 1), "\nd")
    assert document.line_ending == "Mixed"
    document.delete(Pos(2, 1), Pos(3, 0))
    assert document.line_ending == "CRLF"
    document.delete(Pos(0, 0), document.end)
    # No break left: the one new lines take.
    assert document.line_ending == "CRLF" and not document.counts


def test_a_file_that_is_not_utf8_is_read_in_the_fallback(tmp_path):
    data = "привет\r\n".encode("cp1251")
    (tmp_path / "ru.txt").write_bytes(data)
    plain = read_document(tmp_path / "ru.txt")
    assert plain.encoding == encodings.UTF8 and plain.encode() == data
    russian = read_document(tmp_path / "ru.txt", fallback="cp1251")
    assert russian.encoding == "cp1251" and russian.lines[0] == "привет"
    assert russian.encode() == data
    # Valid UTF-8 stays UTF-8 whatever the fallback.
    (tmp_path / "ok.txt").write_bytes("привет".encode())
    assert read_document(tmp_path / "ok.txt", fallback="cp1251").encoding == encodings.UTF8


def test_reinterpreting_reads_the_same_bytes_again():
    data = "привет\n".encode("cp1251")
    document = Document.from_bytes(data)
    again = document.reinterpreted("cp1251")
    assert again.lines[0] == "привет" and again.encoding == "cp1251"
    assert again.encode() == data
    with pytest.raises(UnicodeDecodeError):
        Document.from_bytes(b"abc").reinterpreted(encodings.UTF16_LE)


def test_a_swap_is_one_undo_step_and_redo_puts_it_back():
    buffer = EditBuffer(Document.from_bytes(b"a\r\nb\r\n"))
    buffer.mark_saved()
    heard = []
    buffer.listeners.append(lambda kind, start, end: heard.append(kind))
    document = buffer.document
    buffer.swap(State(list(document.lines), ["\n", "\n", ""], "\n", document.encoding), (0, 0))
    assert document.encode() == b"a\nb\n" and buffer.modified and heard == ["endings"]
    buffer.undo()
    assert document.encode() == b"a\r\nb\r\n" and not buffer.modified
    assert document.line_ending == "CRLF"
    buffer.redo()
    assert document.encode() == b"a\nb\n" and document.line_ending == "LF"


def test_the_first_character_an_encoding_cannot_write():
    assert encodings.first_unencodable(["abc", "x€y"], "cp437") == (1, 1)
    assert encodings.first_unencodable(["abc", "x€y"], "cp1252") is None


# -- the window ----------------------------------------------------------------------


def marks_of(app) -> str:
    marks = editor_window(app).marks
    buffer = screen(app)
    ox, oy = marks.offset()
    row = row_of(buffer, oy + marks.y)
    return row[ox + marks.x:ox + marks.x + marks.width]


def test_the_bottom_frame_shows_the_line_ending_and_the_encoding(files):
    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), IDLE,
                  lambda a: seen.update(marks=marks_of(a), window=editor_window(a))])
    window = seen["window"]
    assert seen["marks"] in ("[CRLF]═[UTF-8]", "[CRLF]=[UTF-8]")
    assert window.marks.x == window.info.x + window.info.width + 1
    assert window.hbar.x >= window.marks.x + window.marks.width


def popup(app):
    from navml.widgets.menu.popup_menu import PopupMenu

    return next((child for child in app.root.children if isinstance(child, PopupMenu)), None)


def click(zone, button="left"):
    """A click on the marker *zone(editor)* names, through the screen."""
    def act(a):
        window = editor_window(a)
        start, _ = zone(window.editor)
        ox, oy = window.marks.offset()
        x, y = ox + window.marks.x + start, oy + window.marks.y
        a.post_event(MouseClickEvent(x, y, button, "press"))
        a.post_event(MouseClickEvent(x, y, button, "release"))
    return act


def ending_of(app) -> str:
    return editor_window(app).editor.document.line_ending


def test_a_left_click_on_the_line_ending_makes_it_the_next_kind(tmp_path, quiet_console):
    (tmp_path / "dir").mkdir()
    (tmp_path / "text.txt").write_bytes(b"a\r\nb\r\nc\n")  # Mixed, most lines CRLF
    app = navigator(tmp_path)
    seen = []
    ending = lambda editor: editor.ending_indicator()  # noqa: E731
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), IDLE,
                  *[step for _ in range(4)
                    for step in (click(ending), IDLE, lambda a: seen.append(ending_of(a)))],
                  lambda a: seen.append(popup(a))])
    # Mixed becomes the most common, then on round: CRLF, CR, LF, CRLF.
    assert seen == ["CRLF", "CR", "LF", "CRLF", None]
    # Each click is one undo step of its own.
    assert len([group for group in editor_window(app).editor.buffer.undo_stack if group.changes]) == 4


def test_a_right_click_on_the_line_ending_offers_them_all(files):
    app = navigator(files)
    seen = {}

    run_app(app, [KeyEvent("end"), KeyEvent("f4"), IDLE,
                  click(lambda editor: editor.ending_indicator(), "right"),
                  Until(lambda a: popup(a) is not None),
                  KeyEvent("up"), KeyEvent("enter"),  # from CRLF, the text's, up to LF
                  Until(lambda a: popup(a) is None), IDLE,
                  lambda a: seen.update(marks=marks_of(a)),
                  KeyEvent("f2"), IDLE])
    assert seen["marks"].startswith("[LF]")
    assert (files / "text.txt").read_bytes() == b"first line\nsecond\tline\n"


def test_save_with_encoding_writes_the_text_in_it_and_reopen_reads_it_again(tmp_path, quiet_console):
    from navigator.widgets.editor.commands import ReopenWithEncoding, SaveWithEncoding

    (tmp_path / "dir").mkdir()
    (tmp_path / "text.txt").write_bytes("Grüße\n".encode())
    app = navigator(tmp_path)
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), IDLE,
                  lambda a: a.spawn(editor_window(a).editor.emit(SaveWithEncoding(encodings.UTF16_LE))),
                  Until(lambda a: editor_window(a).editor.document.encoding == encodings.UTF16_LE),
                  lambda a: seen.update(marks=marks_of(a), modified=editor_window(a).editor.modified),
                  KeyEvent("f2"), IDLE,
                  lambda a: a.spawn(editor_window(a).editor.emit(ReopenWithEncoding("cp1252"))),
                  IDLE, lambda a: seen.update(after=editor_window(a).editor.document.encoding)])
    assert seen["marks"].endswith("[UTF-16LE]") and seen["modified"]
    assert (tmp_path / "text.txt").read_bytes() == codecs.BOM_UTF16_LE + "Grüße\n".encode("utf-16-le")
    # Not one-byte text: read as Windows-1252 the bytes are something else, but they read.
    assert seen["after"] == "cp1252"


def test_a_save_in_an_encoding_without_the_character_is_refused(tmp_path, quiet_console):
    from navigator.widgets.editor.commands import SaveWithEncoding

    (tmp_path / "dir").mkdir()
    (tmp_path / "text.txt").write_bytes("price €\n".encode())
    app = navigator(tmp_path)
    seen = {}

    def dialog(a):
        from navml.widgets.dialog.dialog import Dialog

        return isinstance(a.modal, Dialog)

    run_app(app, [KeyEvent("end"), KeyEvent("f4"), IDLE,
                  lambda a: a.spawn(editor_window(a).editor.emit(SaveWithEncoding("cp437"))),
                  Until(dialog),
                  lambda a: seen.update(encoding=editor_window(a).editor.document.encoding),
                  KeyEvent("escape")])
    assert seen["encoding"] == encodings.UTF8
    assert (tmp_path / "text.txt").read_bytes() == "price €\n".encode()


def test_the_editor_reads_a_file_that_is_not_utf8_in_the_fallback(tmp_path, quiet_console):
    (tmp_path / "dir").mkdir()
    (tmp_path / "text.txt").write_bytes("привет\n".encode("cp1251"))
    SETTINGS.editor.fallback_encoding = "cp1251"
    app = navigator(tmp_path)
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), IDLE,
                  lambda a: seen.update(lines=editor_window(a).editor.document.lines,
                                        marks=marks_of(a))])
    assert seen["lines"][0] == "привет"
    assert seen["marks"].endswith("[Windows-1251]")
