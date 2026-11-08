"""navml's HexLine: DOS Navigator's THexLine -- a linked line's bytes as hex
pairs, edited as hex (DIALOGS.PAS), here holding bytes its text cannot say."""

from __future__ import annotations

from conftest import FakeTerminal, run_app
from navkit.application import Application
from navkit.events import KeyEvent
from navkit.screen import ScreenBuffer
from navkit.widget import Widget

from navml.widgets.dialog.hex_line import HexLine
from navml.widgets.dialog.input_line import InputLine


def pair(encoding="utf-8"):
    """A text line and its hex line; the root lays them out at the
    terminal's width, 40 -- twelve pairs."""
    root = Widget()
    text = InputLine(parent=root)
    hex_line = HexLine(parent=root, y=1, height=1, link=text, encoding=encoding)
    app = Application(root, terminal=FakeTerminal(40, 5))
    return app, text, hex_line


def keys(text):
    return [KeyEvent(c.lower(), c) for c in text]


def in_hex(hex_line):
    return lambda a: hex_line.focus()


def test_digits_set_the_high_then_the_low_nibble_and_the_text_follows():
    app, text, hex_line = pair()
    run_app(app, [in_hex(hex_line), *keys("41"), lambda a: None])
    assert hex_line.data == b"A" and text.value == "A"
    assert (hex_line.cursor, hex_line.low) == (1, False)


def test_bytes_no_text_says_stay_bytes():
    app, text, hex_line = pair()
    run_app(app, [in_hex(hex_line), *keys("41ff"), lambda a: None, lambda a: None])
    assert hex_line.data == b"A\xff"
    assert text.value == "A�"


def test_left_and_right_step_a_nibble_and_backspace_and_del_take_a_byte():
    app, text, hex_line = pair()
    seen = {}
    run_app(app, [in_hex(hex_line), *keys("414243"),
                  KeyEvent("left"), lambda a: seen.update(one=(hex_line.cursor, hex_line.low)),
                  KeyEvent("left"), lambda a: seen.update(two=(hex_line.cursor, hex_line.low)),
                  KeyEvent("backspace"), lambda a: seen.update(back=hex_line.data),
                  KeyEvent("left"), KeyEvent("left"), KeyEvent("delete"),
                  lambda a: seen.update(gone=hex_line.data)])
    assert seen["one"] == (2, True) and seen["two"] == (2, False)
    assert seen["back"] == b"AC"            # the byte before, from a high nibble
    assert seen["gone"] == b"C" and text.value == "C"


def test_other_letters_are_swallowed_and_up_is_shift_tab():
    app, text, hex_line = pair()
    seen = {}
    run_app(app, [in_hex(hex_line), *keys("gz"), lambda a: seen.update(data=hex_line.data),
                  KeyEvent("up"), lambda a: seen.update(focused=a.focused)])
    assert seen["data"] == b"" and seen["focused"] is text


def test_typing_in_the_text_line_gives_its_bytes_in_the_encoding():
    for encoding, expected in (("utf-8", b"\xc3\xa9"), ("cp437", b"\x82")):
        app, text, hex_line = pair(encoding)
        run_app(app, [lambda a: text.focus(), KeyEvent("é", "é"), lambda a: None])
        assert hex_line.data == expected, encoding
        assert hex_line.cursor == len(expected)


def test_it_paints_pairs_and_puts_the_cursor_on_the_nibble():
    app, text, hex_line = pair()
    seen = {}

    def paint(a):
        buffer = ScreenBuffer(40, 5)
        a.root.layout(40, 5)
        a.root.render_tree(buffer)
        seen["row"] = "".join(buffer.get(x, 1)[0] or " " for x in range(8))
        seen["cursor"] = hex_line.cursor_position()

    run_app(app, [in_hex(hex_line), *keys("41ff"), KeyEvent("left"), paint])
    assert seen["row"] == " 41 FF  "
    assert seen["cursor"] == (1 + 3 * 1 + 1, 0)


def test_a_long_string_scrolls_to_keep_the_cursor_shown():
    app, text, hex_line = pair()
    run_app(app, [in_hex(hex_line), *keys("".join(f"{n:02x}" for n in range(1, 16))), lambda a: None])
    room = hex_line.room
    assert hex_line.cursor == 15 and room < 15 and hex_line.first == 15 - room + 1


def test_the_cursors_follow_each_other_across_a_two_byte_character():
    app, text, hex_line = pair()
    seen = {}
    run_app(app, [lambda a: text.focus(), *[KeyEvent(c, c) for c in "aéb"], KeyEvent("left"),
                  lambda a: seen.update(hex=hex_line.cursor),
                  in_hex(hex_line), KeyEvent("left"), KeyEvent("left"), KeyEvent("left"), KeyEvent("left"),
                  lambda a: seen.update(text=text.cursor, at=hex_line.cursor)])
    assert seen["hex"] == 3            # before "b": a, then é's two bytes
    assert seen["at"] == 1 and seen["text"] == 1   # on é's first byte, so before é
