"""Decoding terminal input bytes into events."""

from __future__ import annotations

import pytest

from navkit.events import KeyEvent, MouseEvent, PasteEvent
from navkit.terminal import InputParser


@pytest.fixture
def parser() -> InputParser:
    return InputParser()


def names(events) -> list[str]:
    return [event.name for event in events]


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (b"a", ["a"]),
        (b"Z", ["shift+z"]),
        (b"abc", ["a", "b", "c"]),
        (b"\x11", ["ctrl+q"]),
        (b"\x01\x1a", ["ctrl+a", "ctrl+z"]),
        (b"\r", ["enter"]),
        (b"\n", ["enter"]),
        (b"\t", ["tab"]),
        (b"\x7f", ["backspace"]),
        (b"\x08", ["backspace"]),
        (b"\x00", ["ctrl+space"]),
        (b" ", [" "]),
    ],
)
def test_plain_and_control_keys(parser, data, expected):
    assert names(parser.feed(data)) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (b"\x1b[A", ["up"]),
        (b"\x1b[B", ["down"]),
        (b"\x1b[C", ["right"]),
        (b"\x1b[D", ["left"]),
        (b"\x1b[H", ["home"]),
        (b"\x1b[F", ["end"]),
        (b"\x1bOP\x1bOQ\x1bOR\x1bOS", ["f1", "f2", "f3", "f4"]),
        (b"\x1b[15~\x1b[21~\x1b[24~", ["f5", "f10", "f12"]),
        (b"\x1b[2~\x1b[3~\x1b[5~\x1b[6~", ["insert", "delete", "pageup", "pagedown"]),
        (b"\x1b[Z", ["shift+tab"]),
        (b"\x1bx", ["alt+x"]),
        (b"\x1b\x11", ["ctrl+alt+q"]),
    ],
)
def test_escape_sequences(parser, data, expected):
    assert names(parser.feed(data)) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (b"\x1b[1;2A", "shift+up"),
        (b"\x1b[1;3A", "alt+up"),
        (b"\x1b[1;5A", "ctrl+up"),
        (b"\x1b[1;6A", "ctrl+shift+up"),
        (b"\x1b[1;8A", "ctrl+alt+shift+up"),
        (b"\x1b[3;5~", "ctrl+delete"),
    ],
)
def test_modifiers(parser, data, expected):
    assert names(parser.feed(data)) == [expected]


def test_unicode(parser):
    events = parser.feed("āβ☺".encode())
    assert [event.char for event in events] == ["ā", "β", "☺"]


def test_sequence_split_across_reads(parser):
    assert parser.feed(b"\x1b[2") == []
    assert names(parser.feed(b"1~")) == ["f10"]


def test_utf8_split_across_reads(parser):
    encoded = "ā".encode()
    assert parser.feed(encoded[:1]) == []
    assert [event.char for event in parser.feed(encoded[1:])] == ["ā"]


def test_lone_escape_waits_for_a_flush(parser):
    # A bare ESC is indistinguishable from the start of a longer sequence, so
    # the parser holds it until the application's timeout gives up on more.
    assert parser.feed(b"\x1b") == []
    assert parser.pending_escape is True
    assert names(parser.flush()) == ["escape"]
    assert parser.pending_escape is False


def test_flush_without_pending_escape_is_a_no_op(parser):
    assert parser.flush() == []


def test_escape_followed_by_escape(parser):
    assert names(parser.feed(b"\x1b\x1b[A")) == ["escape", "up"]


def test_unknown_sequence_is_dropped_not_replayed(parser):
    # Consumed, but reported as nothing rather than as garbage keystrokes.
    assert parser.feed(b"\x1b[99~") == []
    assert names(parser.feed(b"a")) == ["a"]


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (b"\x1b[<0;10;5M", (9, 4, "left", "press")),
        (b"\x1b[<0;10;5m", (9, 4, "left", "release")),
        (b"\x1b[<1;1;1M", (0, 0, "middle", "press")),
        (b"\x1b[<2;3;4M", (2, 3, "right", "press")),
        (b"\x1b[<32;7;8M", (6, 7, "left", "move")),
        (b"\x1b[<64;3;3M", (2, 2, "wheel_up", "press")),
        (b"\x1b[<65;3;3M", (2, 2, "wheel_down", "press")),
    ],
)
def test_mouse_reports(parser, data, expected):
    (event,) = parser.feed(data)
    assert isinstance(event, MouseEvent)
    assert (event.x, event.y, event.button, event.action) == expected


def test_mouse_modifiers(parser):
    (event,) = parser.feed(b"\x1b[<28;1;1M")  # 16 ctrl + 8 alt + 4 shift
    assert (event.ctrl, event.alt, event.shift) == (True, True, True)


def test_malformed_mouse_report_is_ignored(parser):
    assert parser.feed(b"\x1b[<0;1M") == []  # too few coordinates
    assert names(parser.feed(b"a")) == ["a"]  # and the stream stays in sync


def test_bracketed_paste(parser):
    (event,) = parser.feed(b"\x1b[200~hello world\x1b[201~")
    assert isinstance(event, PasteEvent)
    assert event.text == "hello world"


def test_paste_split_across_reads(parser):
    assert parser.feed(b"\x1b[200~part one ") == []
    events = parser.feed(b"part two\x1b[201~x")
    assert isinstance(events[0], PasteEvent)
    assert events[0].text == "part one part two"
    assert names(events[1:]) == ["x"]


def test_paste_end_marker_split_across_reads(parser):
    parser.feed(b"\x1b[200~text\x1b[201")
    (event,) = parser.feed(b"~")
    assert event.text == "text"


def test_paste_keeps_control_bytes_verbatim(parser):
    (event,) = parser.feed(b"\x1b[200~one\rtwo\x1b[201~")
    assert event.text == "one\rtwo"


def test_key_events_carry_their_text(parser):
    (event,) = parser.feed(b"A")
    assert isinstance(event, KeyEvent)
    assert (event.key, event.char, event.shift) == ("a", "A", True)
    assert event.is_printable