"""Decoding terminal input bytes into events."""

from __future__ import annotations

import pytest

from navkit.events import KeyEvent, KeyReleaseEvent, MouseClickEvent, PasteEvent
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
        (b" ", ["space"]),  # the key is " "; its name is bindable
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
        # Mode 1003: the pointer moving with no button held.
        (b"\x1b[<35;7;8M", (6, 7, "none", "move")),
        (b"\x1b[<64;3;3M", (2, 2, "wheel_up", "press")),
        (b"\x1b[<65;3;3M", (2, 2, "wheel_down", "press")),
    ],
)
def test_mouse_reports(parser, data, expected):
    (event,) = parser.feed(data)
    assert isinstance(event, MouseClickEvent)
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

# -- the kitty keyboard protocol ---------------------------------------------------


@pytest.mark.parametrize(
    ("kitty", "legacy"),
    [
        (b"\x1b[97u", b"a"),
        (b"\x1b[97;;97u", b"a"),
        (b"\x1b[97:65;2;65u", b"A"),
        (b"\x1b[49:33;2;33u", b"!"),
        (b"\x1b[32;;32u", b" "),
        (b"\x1b[97;5u", b"\x01"),
        (b"\x1b[113;7u", b"\x1b\x11"),
        (b"\x1b[120;3u", b"\x1bx"),
        (b"\x1b[120:88;4u", b"\x1bX"),
        (b"\x1b[32;5u", b"\x00"),
        (b"\x1b[13u", b"\r"),
        (b"\x1b[9u", b"\t"),
        (b"\x1b[9;2u", b"\x1b[Z"),
        (b"\x1b[127u", b"\x7f"),
        (b"\x1b[P", b"\x1bOP"),
        (b"\x1b[1;5:1P", b"\x1b[1;5P"),
        (b"\x1b[15;3:2~", b"\x1b[15;3~"),
        (b"\x1b[24~", b"\x1b[24~"),
        (b"\x1b[57399u", b"0"),
        (b"\x1b[57414u", b"\r"),
    ],
)
def test_a_kitty_key_is_the_same_event_as_its_legacy_form(kitty, legacy):
    legacy_parser = InputParser()
    want = legacy_parser.feed(legacy) + legacy_parser.flush()
    # A kitty key also says what is held, which is a ModifiersEvent beside it.
    got = [e for e in InputParser().feed(kitty) if isinstance(e, KeyEvent)]
    assert got == want


def test_the_kitty_escape_key_needs_no_timeout(parser):
    assert parser.feed(b"\x1b[27u") == [KeyEvent("escape")]
    assert not parser.pending_escape


def test_a_released_key_is_not_a_key(parser):
    events = parser.feed(b"\x1b[97;1:3u\x1b[15;1:3~")
    assert not any(isinstance(e, KeyEvent) for e in events)
    assert events == [KeyReleaseEvent("a", "a"), KeyReleaseEvent("f5")]


def test_a_kitty_press_says_its_release_will_follow(parser):
    (press,) = parser.feed(b"\x1b[32u")
    assert press == KeyEvent(" ", " ")
    assert press.releases is True
    (release,) = parser.feed(b"\x1b[32;1:3u")
    assert release == KeyReleaseEvent(" ", " ")


def test_a_legacy_press_promises_no_release(parser):
    (press,) = parser.feed(b" ")
    assert press.releases is False


def test_a_bare_modifier_moves_the_held_set_and_nothing_else(parser):
    from navkit.events import ModifiersEvent

    assert parser.feed(b"\x1b[57443;3u") == [ModifiersEvent(frozenset({"alt"}))]
    # A repeat of a held key changes nothing, so says nothing.
    assert parser.feed(b"\x1b[57443;3:2u") == []
    assert parser.feed(b"\x1b[57442;7u") == [ModifiersEvent(frozenset({"alt", "ctrl"}))]
    assert parser.feed(b"\x1b[57443;5:3u") == [ModifiersEvent(frozenset({"ctrl"}))]
    assert parser.feed(b"\x1b[57448;1:3u") == [ModifiersEvent(frozenset())]
    # Super is reported and ignored.
    assert parser.feed(b"\x1b[57444;9u") == []


def test_a_kitty_key_corrects_a_release_that_went_missing(parser):
    from navkit.events import ModifiersEvent

    parser.feed(b"\x1b[57441;2u")
    assert parser.modifiers == {"shift"}
    assert parser.feed(b"\x1b[97u") == [ModifiersEvent(frozenset()), KeyEvent("a", "a")]


def test_losing_the_focus_forgets_what_was_held(parser):
    from navkit.events import ModifiersEvent

    parser.feed(b"\x1b[57443;3u")
    assert parser.feed(b"\x1b[I") == []
    assert parser.feed(b"\x1b[O") == [ModifiersEvent(frozenset())]
    assert parser.feed(b"\x1b[O") == []


def test_legacy_input_never_holds_a_modifier(parser):
    # A legacy Ctrl+F5 is followed by no release, so believing it would leave
    # Ctrl held for good.
    assert names(parser.feed(b"\x1b[15;5~\x1b[1;3P\x1bx")) == ["ctrl+f5", "alt+f1", "alt+x"]
    assert parser.modifiers == frozenset()


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (b"\x1bO5R", ["ctrl+f3"]),
        (b"\x1bO5S", ["ctrl+f4"]),
        (b"\x1bO2P", ["shift+f1"]),
        (b"\x1bO1;3Q", ["alt+f2"]),
        (b"\x1bOP", ["f1"]),
    ],
)
def test_ss3_carries_a_modifier_too(parser, data, expected):
    assert names(parser.feed(data)) == expected


def test_a_split_ss3_modifier_waits_for_its_final_byte(parser):
    assert parser.feed(b"\x1bO5") == []
    assert names(parser.feed(b"R")) == ["ctrl+f3"]


# -- the other way: keys and the mouse back into bytes for a child -------------


from navkit.terminal import encode_key, encode_mouse


def test_a_left_press_still_parses_as_left():
    # The encoder's table once shared the parser's name and replaced it, and
    # every press came out as button "none".
    (event,) = InputParser().feed(b"\x1b[<0;10;10M")
    assert event.button == "left"


@pytest.mark.parametrize("key,normal,application", [
    ("up", b"\x1b[A", b"\x1bOA"),
    ("left", b"\x1b[D", b"\x1bOD"),
    ("home", b"\x1b[H", b"\x1bOH"),
    ("pageup", b"\x1b[5~", b"\x1b[5~"),   # not a cursor key: DECCKM leaves it
])
def test_application_cursor_mode_sends_ss3(key, normal, application):
    assert encode_key(KeyEvent(key)) == normal
    assert encode_key(KeyEvent(key), application_cursor=True) == application


@pytest.mark.parametrize("event,expected", [
    (KeyEvent("up", ctrl=True), b"\x1b[1;5A"),
    (KeyEvent("right", shift=True), b"\x1b[1;2C"),
    (KeyEvent("f5", ctrl=True), b"\x1b[15;5~"),
    (KeyEvent("f1", shift=True), b"\x1b[1;2P"),
    (KeyEvent("up", alt=True), b"\x1b[1;3A"),
    (KeyEvent("tab", shift=True), b"\x1b[Z"),
    (KeyEvent("x", "x", alt=True), b"\x1bx"),
    (KeyEvent("c", ctrl=True), b"\x03"),
])
def test_a_modified_special_key_keeps_its_modifier(event, expected):
    assert encode_key(event, application_cursor=True) == expected


def click(action="press", button="left", **mods):
    return MouseClickEvent(x=4, y=2, button=button, action=action, **mods)


def test_the_mouse_is_encoded_as_the_program_asked():
    assert encode_mouse(click(), tracking=1000, sgr=True) == b"\x1b[<0;5;3M"
    assert encode_mouse(click("release"), tracking=1000, sgr=True) == b"\x1b[<0;5;3m"
    assert encode_mouse(click(), tracking=1000) == b"\x1b[M %#"
    assert encode_mouse(click("release"), tracking=1000) == b"\x1b[M#%#"
    assert encode_mouse(click(button="wheel_down"), tracking=1000, sgr=True) == b"\x1b[<65;5;3M"
    assert encode_mouse(click(ctrl=True), tracking=1000, sgr=True) == b"\x1b[<16;5;3M"


def test_the_mouse_mode_decides_what_is_reported():
    assert encode_mouse(click(), tracking=0) == b""
    assert encode_mouse(click("release"), tracking=9) == b""
    assert encode_mouse(click("move"), tracking=1000, sgr=True) == b""
    assert encode_mouse(click("move"), tracking=1002, sgr=True) == b"\x1b[<32;5;3M"
    assert encode_mouse(click("move", "none"), tracking=1002, sgr=True) == b""
    assert encode_mouse(click("move", "none"), tracking=1003, sgr=True) == b"\x1b[<35;5;3M"


@pytest.mark.parametrize(
    ("data", "name", "char"),
    [
        # The kitty protocol reports the keypad by its own codes.
        (b"\x1b[57413u", "kp_plus", "+"),
        (b"\x1b[57412u", "kp_minus", "-"),
        (b"\x1b[57411u", "kp_multiply", "*"),
        (b"\x1b[57410u", "kp_divide", "/"),
        (b"\x1b[57413;2u", "shift+kp_plus", "+"),
        # A legacy terminal in application keypad mode sends SS3.
        (b"\x1bOk", "kp_plus", "+"),
        (b"\x1bOm", "kp_minus", "-"),
        (b"\x1bOj", "kp_multiply", "*"),
        (b"\x1bOo", "kp_divide", "/"),
        (b"\x1bO2k", "shift+kp_plus", "+"),
        # The rest of the keypad is folded into the keys it duplicates.
        (b"\x1bOM", "enter", "\n"),
        (b"\x1bOp", "0", "0"),
        (b"\x1bOy", "9", "9"),
        (b"\x1bOn", ".", "."),
    ],
)
def test_the_keypad_operators_are_keys_of_their_own(parser, data, name, char):
    """Gray + is not the + above the letters -- but it still types one."""
    [event] = [e for e in parser.feed(data) if isinstance(e, KeyEvent)]
    assert (event.name, event.char) == (name, char)
    if name.endswith(("kp_plus", "kp_minus", "kp_multiply", "kp_divide")):
        assert event.is_printable  # unbound, it types into a line


def test_a_bare_space_is_named_space_so_a_key_table_can_bind_it(parser):
    [event] = parser.feed(b" ")
    assert event.key == " " and event.char == " "  # it still types a blank
    assert event.name == "space"
    assert event.matches("space")


def test_a_keypad_operator_reaches_a_child_as_its_character():
    from navkit.terminal import encode_key

    assert encode_key(KeyEvent("kp_plus", "+")) == b"+"
    assert encode_key(KeyEvent("kp_minus", "-", shift=True)) == b"-"


def test_a_bare_plus_is_named_plus_because_a_spec_cannot_spell_it(parser):
    [event] = parser.feed(b"+")
    assert event.key == "+" and event.char == "+"
    assert event.name == "plus" and event.matches("plus")
