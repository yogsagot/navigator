"""Terminals that are not UTF-8 (KOI8-R, CP866, EUC-JP...): the charset found,
frames encoded in it cell by cell, input and the console decoded through it.
A departure, asked for: DOS Navigator spoke the screen's code page."""

from __future__ import annotations

import io
from dataclasses import replace

import pytest

from navkit.capabilities import FULL, TerminalInfo
from navkit.console import ConsoleScreen
from navkit.events import KeyEvent
from navkit.glyphs import GLYPHS_ASCII, GLYPHS_UNICODE, ascii_twin
from navkit.terminal import InputParser, Terminal, encode_for, encode_key


@pytest.mark.parametrize("env, charset, tier", [
    ({"LANG": "ru_RU.KOI8-R"}, "koi8-r", GLYPHS_UNICODE),       # has box drawing
    ({"LANG": "ru_RU.CP866"}, "cp866", GLYPHS_UNICODE),
    ({"LANG": "ru_RU.CP1251"}, "cp1251", GLYPHS_ASCII),         # has none
    ({"LANG": "en_US.ISO-8859-1"}, "iso8859-1", GLYPHS_ASCII),
    ({"LANG": "de_DE.CP850"}, "cp850", GLYPHS_UNICODE),          # lacks only mixed tees
    ({"LANG": "ja_JP.eucJP"}, "euc_jp", GLYPHS_ASCII),           # single lines only
    ({"LANG": "en_US.UTF-8"}, "utf-8", GLYPHS_UNICODE),
    ({"LANG": "C"}, "utf-8", GLYPHS_ASCII),                     # says nothing: as before
    ({"LANG": "ja_JP.ISO-2022-JP"}, "ascii", GLYPHS_ASCII),     # stateful: plain ASCII
    ({"LC_ALL": "ru_RU.KOI8-U", "LANG": "en_US.UTF-8"}, "koi8-u", GLYPHS_UNICODE),
    ({"LANG": "en_US.UTF-8", "NAVKIT_CHARSET": "cp437"}, "cp437", GLYPHS_UNICODE),
    # Python's own LC_CTYPE when the locale LANG names is not installed (PEP 538).
    ({"LANG": "ru_RU.KOI8-R", "LC_CTYPE": "C.UTF-8"}, "koi8-r", GLYPHS_UNICODE),
])
def test_the_charset_comes_from_the_locale(env, charset, tier):
    info = TerminalInfo.detect(env={"TERM": "xterm", **env})
    assert (info.charset, info.glyphs) == (charset, tier)


def test_a_legacy_charset_never_gets_nerd_icons_or_braille():
    info = TerminalInfo.detect(env={"TERM": "xterm-kitty", "LANG": "ru_RU.KOI8-R"})
    assert info.glyphs == GLYPHS_UNICODE and not info.braille


def test_a_frame_is_encoded_in_the_charset_each_missing_character_by_its_twin():
    data = encode_for("╔═Файл▲ é日x", "koi8-r")
    assert data.decode("koi8-r") == "╔═Файл^ e??x"  # a wide character keeps both its cells
    assert encode_for("╔═Файл", "utf-8") == "╔═Файл".encode()
    assert [ascii_twin(char) for char in "▒█…☼"] == [":", "#", ".", "*"]


def test_the_terminal_writes_its_frames_in_the_charset():
    out = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    terminal = Terminal(output_stream=out, info=replace(FULL, charset="cp866"))
    terminal.write("┌─ Привет ─┐")
    terminal.flush()
    assert out.buffer.getvalue().decode("cp866") == "┌─ Привет ─┐"


def test_typed_text_and_pastes_are_read_in_the_charset():
    parser = InputParser()
    parser.charset = "koi8-r"
    assert [(event.key, event.char) for event in parser.feed(bytes([0xD6]))] == [("ж", "ж")]
    (alt,) = parser.feed(b"\x1b" + bytes([0xD6]))
    assert alt.alt and alt.char == "ж"
    (paste,) = parser.feed(b"\x1b[200~" + "привет".encode("koi8-r") + b"\x1b[201~")
    assert paste.text == "привет"


def test_a_multi_byte_character_split_across_reads_waits_for_the_rest():
    parser = InputParser()
    parser.charset = "euc_jp"
    data = "日本".encode("euc_jp")
    assert parser.feed(data[:1]) == []
    assert [event.char for event in parser.feed(data[1:])] == ["日", "本"]


def test_the_console_reads_and_types_in_the_charset():
    screen = ConsoleScreen(20, 2, charset="koi8-r")
    screen.feed("ls: файл\r\n".encode("koi8-r"))
    assert "".join(screen.written.get(x, 0)[0] or " " for x in range(8)) == "ls: файл"
    assert encode_key(KeyEvent("ж", "ж"), charset="koi8-r") == bytes([0xD6])
    assert encode_key(KeyEvent("ж", "ж")) == "ж".encode()


def test_an_application_hands_the_charset_to_its_parser_and_console():
    from conftest import FakeTerminal
    from navkit import console
    from navkit.application import Application
    from navkit.widget import Widget

    try:
        app = Application(Widget(), terminal=FakeTerminal(info=replace(FULL, charset="koi8-r")))
        assert app._parser.charset == "koi8-r" and console.CHARSET == "koi8-r"
        app.use_terminal_info(replace(FULL, charset="cp866"))
        assert app._parser.charset == "cp866"
    finally:
        console.CHARSET = "utf-8"
