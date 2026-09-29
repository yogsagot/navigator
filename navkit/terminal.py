"""ANSI terminal handling: raw mode, screen setup and input decoding.

:class:`Terminal` owns the tty -- putting it into raw mode on the way in and
restoring it on the way out -- while :class:`InputParser` turns the resulting
byte stream into :mod:`navkit.events` objects.

The parser is fed incrementally and keeps whatever it cannot yet decode, so a
sequence split across two reads is decoded correctly once the rest arrives.
"""

from __future__ import annotations

import base64
import binascii
import os
import sys
import termios
import tty
from typing import IO

from navkit.capabilities import TerminalInfo
from navkit.events import Event, KeyEvent, ModifiersEvent, MouseClickEvent, PasteEvent

ALT_SCREEN_ON = "\x1b[?1049h"
ALT_SCREEN_OFF = "\x1b[?1049l"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
#: Cursor shapes, as DECSCUSR (``CSI Ps SP q``) spells them.  ``default`` is
#: the terminal's own configured shape, and is what navkit asks for unless a
#: widget says otherwise -- a caret that ignored the user's setting for no
#: reason would be the rudest thing in the library.
CURSOR_SHAPES = {
    "default": 0,
    "blink-block": 1,
    "block": 2,
    "blink-underline": 3,
    "underline": 4,
    "blink-bar": 5,
    "bar": 6,
}
CURSOR_SHAPE_RESET = "\x1b[0 q"
AUTOWRAP_OFF = "\x1b[?7l"
AUTOWRAP_ON = "\x1b[?7h"
def place_cursor(x: int, y: int, shape: str = "default") -> str:
    """Put the terminal's own cursor at *x*, *y* and show it.

    Zero-based, like everything else in navkit; the escape is one-based.  The
    shape is emitted first, because a terminal that does not know DECSCUSR
    ignores it and one that does should have applied it before the cursor
    appears.
    """
    out = ""
    code = CURSOR_SHAPES.get(shape, 0)
    if code:
        out += f"\x1b[{code} q"
    return out + f"\x1b[{y + 1};{x + 1}H" + SHOW_CURSOR


# 1000: report button presses, 1002: also report drags, 1003: also report plain
# motion, 1006: report them in the unambiguous SGR format.
# Plain motion is what makes ``:hovered`` possible; the application keeps it
# to itself, so no widget sees the extra traffic.
MOUSE_ON = "\x1b[?1000h\x1b[?1002h\x1b[?1003h\x1b[?1006h"
MOUSE_OFF = "\x1b[?1006l\x1b[?1003l\x1b[?1002l\x1b[?1000l"
PASTE_ON = "\x1b[?2004h"
PASTE_OFF = "\x1b[?2004l"
# The kitty keyboard protocol, pushed onto the terminal's own stack of flags
# and popped again: 1 disambiguates, 2 reports releases and repeats, 4 the
# shifted key, 8 every key -- a bare modifier included -- as an escape, 16 the
# text a key produces.  2 and 8 are the point: they are the only way a terminal
# says a modifier is *held*.  A terminal that does not know the sequence
# ignores it, so it is pushed without asking first.  Focus reporting (1004)
# comes with it, because a release that happens in another window never
# arrives, and losing the focus is the cue to forget what was held.
KEYBOARD_ON = "\x1b[>31u\x1b[?1004h"
KEYBOARD_OFF = "\x1b[?1004l\x1b[<u"
CLEAR_SCREEN = "\x1b[H\x1b[2J"
# OSC 4 rewrites one of the sixteen colour registers, OSC 104 with no argument
# puts all of them back.  This is the terminal's answer to what a DOS palette
# did to the VGA DAC, and the only way to reach a terminal that names nothing
# but the sixteen: pinning a colour cannot help when the terminal has no way to
# be told what the colour is.
PALETTE_RESET = "\x1b]104\x1b\\"

PASTE_START = b"\x1b[200~"
PASTE_END = b"\x1b[201~"
# The head of a terminal's answer to an OSC 52 clipboard query.  Only this
# OSC is decoded: ``ESC ]`` alone is also Alt+], and waiting for a terminator
# after every Alt+] would swallow what is typed next.
_CLIPBOARD_REPLY = b"\x1b]52;"
# An answer larger than this is not waited for any further: its bytes are
# dropped rather than held while the terminal keeps sending.
_CLIPBOARD_REPLY_MAX = 16 * 1024 * 1024


def clipboard_osc(text: str, *, primary: bool = False) -> str:
    """OSC 52: set the clipboard (``c``) or the primary selection (``p``)."""
    data = base64.b64encode(text.encode("utf-8")).decode("ascii")
    return f"\x1b]52;{'p' if primary else 'c'};{data}\x07"


def clipboard_query(*, primary: bool = False) -> str:
    """OSC 52 with ``?``: the terminal answers with the text, or not at all."""
    return f"\x1b]52;{'p' if primary else 'c'};?\x07"


def is_a_tty(*streams: IO[str]) -> bool:
    """True when every one of *streams* is a terminal.

    A free function rather than only a :class:`Terminal` property because the
    answer is wanted *before* a terminal exists: an application that states its
    own capabilities has to call :meth:`TerminalInfo.detect` first, and that
    needs to know.
    """
    try:
        return all(os.isatty(stream.fileno()) for stream in streams)
    except (OSError, ValueError):
        return False


def palette_sgr(palette: tuple[tuple[int, int, int], ...]) -> str:
    """The OSC 4 sequences setting the terminal's colour registers to *palette*."""
    return "".join(
        f"\x1b]4;{index};rgb:{r:02x}/{g:02x}/{b:02x}\x1b\\"
        for index, (r, g, b) in enumerate(palette)
    )


#: ``CSI <n> ~`` keys.
_TILDE_KEYS = {
    1: "home",
    2: "insert",
    3: "delete",
    4: "end",
    5: "pageup",
    6: "pagedown",
    7: "home",
    8: "end",
    11: "f1",
    12: "f2",
    13: "f3",
    14: "f4",
    15: "f5",
    17: "f6",
    18: "f7",
    19: "f8",
    20: "f9",
    21: "f10",
    23: "f11",
    24: "f12",
    29: "menu",
}

#: ``CSI <letter>`` and ``SS3 <letter>`` keys.
_LETTER_KEYS = {
    "A": "up",
    "B": "down",
    "C": "right",
    "D": "left",
    "E": "center",
    "F": "end",
    "H": "home",
    "P": "f1",
    "Q": "f2",
    "R": "f3",
    "S": "f4",
}

#: ``CSI <code> u`` keys that are not text.  The keypad is folded into the
#: keys it duplicates, as a legacy terminal does before it reaches us.
_KITTY_KEYS = {
    9: "tab",
    13: "enter",
    27: "escape",
    127: "backspace",
    57363: "menu",
    57414: "enter",
    57417: "left",
    57418: "right",
    57419: "up",
    57420: "down",
    57421: "pageup",
    57422: "pagedown",
    57423: "home",
    57424: "end",
    57425: "insert",
    57426: "delete",
    57427: "center",
}

#: What the keypad's text keys type.
_KITTY_KEYPAD = {
    **{57399 + digit: str(digit) for digit in range(10)},
    57409: ".",
    57410: "/",
    57411: "*",
    57412: "-",
    57413: "+",
    57415: "=",
    57416: ",",
}

#: The modifier keys themselves, and the modifier each one is -- ``None`` for
#: Super, Hyper, Meta and the level shifts, which navkit does not name.
_KITTY_MODIFIER_KEYS = {
    57441: "shift",
    57442: "ctrl",
    57443: "alt",
    57447: "shift",
    57448: "ctrl",
    57449: "alt",
    **{code: None for code in (57444, 57445, 57446, 57450, 57451, 57452, 57453, 57454)},
}

#: How many parameter bytes an SS3 key may carry before the parser stops
#: waiting for its final byte -- ``1;5`` is the longest any terminal sends.
_SS3_PARAMS_MAX = 4

#: A kitty event type: 1 press, 2 repeat, 3 release.
_RELEASE = 3

_CTRL_SYMBOLS = {0x1C: "\\", 0x1D: "]", 0x1E: "^", 0x1F: "_"}

_MOUSE_BUTTONS = {0: "left", 1: "middle", 2: "right"}
_WHEEL_BUTTONS = {0: "wheel_up", 1: "wheel_down", 2: "wheel_left", 3: "wheel_right"}


def _utf8_length(lead: int) -> int:
    """Return the length of the UTF-8 sequence starting with byte *lead*."""
    if lead < 0x80:
        return 1
    if lead >= 0xF0:
        return 4
    if lead >= 0xE0:
        return 3
    if lead >= 0xC0:
        return 2
    return 1  # stray continuation byte; consume it so we make progress


def _modifiers(param: int) -> tuple[bool, bool, bool]:
    """Decode an xterm modifier parameter into ``(ctrl, alt, shift)``.

    Only the three bits navkit names are read, so the kitty protocol's Super,
    Hyper, Meta, Caps Lock and Num Lock bits above them are ignored.
    """
    bits = max(0, param - 1)
    return bool(bits & 4), bool(bits & 2), bool(bits & 1)


def _held(param: int) -> frozenset[str]:
    """An xterm modifier parameter as the set :class:`ModifiersEvent` carries."""
    ctrl, alt, shift = _modifiers(param)
    return frozenset(
        name for name, on in (("ctrl", ctrl), ("alt", alt), ("shift", shift)) if on
    )


def _numbers(field: bytes) -> list[int]:
    """A ``:``-separated CSI parameter, an empty or non-numeric part as 0."""
    return [int(part) if part.isdigit() else 0 for part in field.split(b":")]


class InputParser:
    """Incremental decoder turning terminal input bytes into events."""

    def __init__(self) -> None:
        self._buf = bytearray()
        self._paste: bytearray | None = None
        self._incomplete = False
        #: The modifiers held down, as far as the kitty keyboard protocol has
        #: said.  Never touched by legacy input: a legacy Ctrl+F5 is followed
        #: by no release, so believing it would leave Ctrl held for good.
        self.modifiers: frozenset[str] = frozenset()

    @property
    def pending_escape(self) -> bool:
        """True if the buffer holds an escape sequence that may still grow.

        A lone ``ESC`` byte is indistinguishable from the start of a longer
        sequence, so the caller resolves the ambiguity with a short timeout and
        then calls :meth:`flush`.
        """
        if self._buf.startswith(_CLIPBOARD_REPLY):
            # A clipboard answer still arriving: a slow terminal, or a big
            # clipboard, is not a lone ESC and must not be flushed as one.
            return False
        return self._incomplete and bool(self._buf) and self._buf[0] == 0x1B

    def feed(self, data: bytes) -> list[Event]:
        """Decode *data*, returning every event it completes."""
        self._buf += data
        return self._parse()

    def flush(self) -> list[Event]:
        """Resolve a pending lone ``ESC`` into an escape key press."""
        if not self.pending_escape:
            return []
        self._incomplete = False
        if len(self._buf) >= 2 and self._buf[1] == 0x5D:
            # The start of a clipboard answer that never came: Alt+], and
            # whatever followed it typed as it was.
            del self._buf[:2]
            return [KeyEvent("]", "]", alt=True), *self._parse()]
        del self._buf[:1]
        return [KeyEvent("escape"), *self._parse()]

    def _parse(self) -> list[Event]:
        events: list[Event] = []
        self._incomplete = False
        while self._buf:
            if self._paste is not None:
                if not self._parse_paste(events):
                    break
                continue
            byte = self._buf[0]
            if byte == 0x1B:
                consumed, event = self._parse_escape()
                if consumed == 0:
                    self._incomplete = True
                    break
                del self._buf[:consumed]
                if isinstance(event, list):
                    events.extend(event)
                elif event is not None:
                    events.append(event)
                continue
            if byte < 0x20 or byte == 0x7F:
                del self._buf[:1]
                events.append(_control_key(byte))
                continue
            length = _utf8_length(byte)
            if len(self._buf) < length:
                self._incomplete = True
                break
            raw = bytes(self._buf[:length])
            del self._buf[:length]
            char = raw.decode("utf-8", "replace")
            events.append(KeyEvent(char.lower(), char, shift=char.isupper()))
        return events

    def _parse_paste(self, events: list[Event]) -> bool:
        """Consume pasted text; return False if more input is needed."""
        assert self._paste is not None
        index = bytes(self._buf).find(PASTE_END)
        if index < 0:
            # Keep back enough bytes that a split end marker still matches.
            take = len(self._buf) - (len(PASTE_END) - 1)
            if take > 0:
                self._paste += self._buf[:take]
                del self._buf[:take]
            return False
        self._paste += self._buf[:index]
        del self._buf[: index + len(PASTE_END)]
        events.append(PasteEvent(self._paste.decode("utf-8", "replace")))
        self._paste = None
        return True

    def _parse_escape(self) -> tuple[int, Event | list[Event] | None]:
        """Decode the escape sequence at the head of the buffer.

        Returns the number of bytes consumed -- zero when the sequence is not
        yet complete -- and the event it produced, if any.
        """
        buf = self._buf
        if len(buf) < 2:
            return 0, None
        second = buf[1]

        if second == 0x1B:  # ESC ESC -- report the first, re-parse the rest
            return 1, KeyEvent("escape")

        if second == 0x5B:  # CSI
            final = -1
            for index in range(2, len(buf)):
                if 0x40 <= buf[index] <= 0x7E:
                    final = index
                    break
            if final < 0:
                return 0, None
            body = bytes(buf[2:final])
            terminator = chr(buf[final])
            if body.startswith(b"<"):
                return final + 1, _mouse_event(body[1:], terminator)
            if terminator == "~" and body == b"200":
                self._paste = bytearray()
                return final + 1, None
            return final + 1, self._csi(body, terminator)

        if second == 0x5D:  # OSC -- only a clipboard reply is one
            head = bytes(buf[: len(_CLIPBOARD_REPLY)])
            if _CLIPBOARD_REPLY.startswith(head) and len(head) < len(_CLIPBOARD_REPLY):
                return 0, None
            if head == _CLIPBOARD_REPLY:
                return self._clipboard_reply()

        if second == 0x4F:  # SS3, e.g. ESC O P for F1
            # Some terminals put a modifier between the two, the way CSI
            # does: ESC O 5 R is Ctrl+F3, and ESC O 1;5 R has been seen too.
            # Read up to the final byte and decode it as CSI would.
            final, limit = 2, min(len(buf), 2 + _SS3_PARAMS_MAX)
            while final < limit and buf[final] in b"0123456789;":
                final += 1
            if final >= len(buf):
                return 0, None
            name = _LETTER_KEYS.get(chr(buf[final]))
            params = bytes(buf[2:final]).split(b";")
            if not name or final == 2:
                return final + 1, KeyEvent(name) if name else None
            ctrl, alt, shift = _modifiers(_numbers(params[-1])[0] or 1)
            return final + 1, KeyEvent(name, ctrl=ctrl, alt=alt, shift=shift)

        # Anything else is Alt plus whatever follows.
        if second < 0x20 or second == 0x7F:
            return 2, _control_key(second, alt=True)
        length = _utf8_length(second)
        if len(buf) < 1 + length:
            return 0, None
        char = bytes(buf[1 : 1 + length]).decode("utf-8", "replace")
        return 1 + length, KeyEvent(char.lower(), char, alt=True, shift=char.isupper())


    def _clipboard_reply(self) -> tuple[int, Event | None]:
        """``ESC ] 52 ; <selection> ; <base64> BEL`` -- the clipboard, as a paste.

        The text a terminal hands back for :func:`clipboard_query` arrives as a
        :class:`~navkit.events.PasteEvent`, so a paste asked for and a paste
        the terminal made on its own go the one way.  An empty answer -- the
        terminal declined, or the clipboard is empty -- is no event at all.
        """
        buf = bytes(self._buf)
        bel, st = buf.find(b"\x07"), buf.find(b"\x1b\\")
        ends = [(i, 1) for i in (bel,) if i >= 0] + [(i, 2) for i in (st,) if i >= 0]
        if not ends:
            if len(buf) > _CLIPBOARD_REPLY_MAX:
                return len(buf), None
            return 0, None
        end, size = min(ends)
        _, _, data = buf[len(_CLIPBOARD_REPLY) : end].partition(b";")
        try:
            text = base64.b64decode(data, validate=False).decode("utf-8", "replace")
        except (ValueError, binascii.Error):
            text = ""
        return end + size, PasteEvent(text) if text else None

    def _csi(self, body: bytes, terminator: str) -> list[Event]:
        """Decode a non-mouse ``CSI`` sequence, legacy or kitty.

        The kitty keyboard protocol is recognised by what legacy input never
        sends -- a ``u`` terminator, or an event type after a ``:`` -- and only
        that form may move :attr:`modifiers`.  A kitty press carries the
        whole held set, so each one also corrects a release that went missing.
        """
        fields = body.split(b";")
        if terminator in "IO" and body == b"":
            # Focus in, focus out.  Whatever was held when the focus left is
            # released somewhere this application will never hear about.
            return self._hold(frozenset()) if terminator == "O" else []
        key = _numbers(fields[0])
        mods = _numbers(fields[1]) if len(fields) > 1 else [1]
        param = mods[0] or 1
        kind = mods[1] if len(mods) > 1 else 1
        kitty = terminator == "u" or len(mods) > 1
        if terminator == "u":
            text = "".join(chr(c) for c in _numbers(fields[2]) if c) if len(fields) > 2 else ""
            code = key[0]
            if code in _KITTY_MODIFIER_KEYS:
                return self._modifier_key(_KITTY_MODIFIER_KEYS[code], param, kind)
            event = _kitty_key(code, key[1] if len(key) > 1 else 0, param, text)
        else:
            event = _csi_key(body, terminator)
        if not kitty:
            return [event] if event is not None else []
        out = self._hold(_held(param))
        if event is not None and kind != _RELEASE:
            out.append(event)
        return out

    def _modifier_key(self, name: str | None, param: int, kind: int) -> list[Event]:
        """A bare modifier pressed or released: the held set, and only that.

        The report's own modifier field is taken as the rest of the state, and
        the key's own modifier is then forced to what the event says, because
        the protocol leaves open whether a modifier counts itself.
        """
        held = set(_held(param))
        if name is not None:
            if kind == _RELEASE:
                held.discard(name)
            else:
                held.add(name)
        return self._hold(frozenset(held))

    def _hold(self, held: frozenset[str]) -> list[Event]:
        """Make *held* the held set, and say so if that changed it."""
        if held == self.modifiers:
            return []
        self.modifiers = held
        return [ModifiersEvent(held)]


def _kitty_key(code: int, shifted: int, param: int, text: str) -> KeyEvent | None:
    """A kitty ``CSI u`` key, as the legacy decoder would have reported it.

    The same key must reach a key table under the same name whichever way the
    terminal sent it, so this mirrors :func:`_control_key` and the text path
    of :meth:`InputParser._parse` rather than inventing a spelling: a capital
    is the lower-case key with ``shift`` and its ``char``, Ctrl+letter has no
    ``char``, Ctrl+Space is ``space``.
    """
    ctrl, alt, shift = _modifiers(param)
    name = _KITTY_KEYS.get(code)
    if name is not None:
        if name == "tab":
            return KeyEvent("tab", "\t", ctrl=ctrl, alt=alt, shift=shift)
        if name == "enter":
            return KeyEvent("enter", "\n", ctrl=ctrl, alt=alt, shift=shift)
        return KeyEvent(name, ctrl=ctrl, alt=alt, shift=shift)
    if code in _KITTY_KEYPAD:
        code = ord(_KITTY_KEYPAD[code])
    if code < 0x20 or 0xE000 <= code <= 0xF8FF:
        return None  # F13 and beyond, the locks, media keys: nothing to name
    if code == 0x20 and ctrl:
        return KeyEvent("space", " ", ctrl=True, alt=alt, shift=shift)
    if ctrl:
        return KeyEvent(chr(code), ctrl=True, alt=alt, shift=shift)
    char = text or (chr(shifted) if shift and shifted else chr(code))
    return KeyEvent(char.lower(), char, alt=alt, shift=char.isupper())


def _csi_key(body: bytes, terminator: str) -> Event | None:
    """Decode a legacy key ``CSI`` sequence (a kitty event type is tolerated)."""
    params = [_numbers(p)[0] for p in body.split(b";")] or [0]
    modifier = params[1] if len(params) > 1 else 1
    ctrl, alt, shift = _modifiers(modifier)

    if terminator == "~":
        name = _TILDE_KEYS.get(params[0])
        return KeyEvent(name, ctrl=ctrl, alt=alt, shift=shift) if name else None
    if terminator == "Z":  # shift+tab
        return KeyEvent("tab", "\t", shift=True)
    name = _LETTER_KEYS.get(terminator)
    if name is None:
        return None
    return KeyEvent(name, ctrl=ctrl, alt=alt, shift=shift)


def _mouse_event(body: bytes, terminator: str) -> Event | None:
    """Decode an SGR (1006) mouse report."""
    try:
        code, column, row = (int(p) for p in body.split(b";"))
    except ValueError:
        return None
    ctrl, alt, shift = bool(code & 16), bool(code & 8), bool(code & 4)
    if code & 64:
        button = _WHEEL_BUTTONS.get(code & 3, "none")
        action = "press"
    elif code & 32:
        button = _MOUSE_BUTTONS.get(code & 3, "none")
        action = "move"
    else:
        button = _MOUSE_BUTTONS.get(code & 3, "none")
        action = "release" if terminator == "m" else "press"
    return MouseClickEvent(
        x=column - 1,
        y=row - 1,
        button=button,
        action=action,
        ctrl=ctrl,
        alt=alt,
        shift=shift,
    )


def _control_key(byte: int, *, alt: bool = False) -> KeyEvent:
    """Decode a C0 control byte into a key press."""
    match byte:
        case 0x09:
            return KeyEvent("tab", "\t", alt=alt)
        case 0x0D | 0x0A:
            return KeyEvent("enter", "\n", alt=alt)
        case 0x08 | 0x7F:
            return KeyEvent("backspace", alt=alt)
        case 0x1B:
            return KeyEvent("escape", alt=alt)
        case 0x00:
            return KeyEvent("space", " ", ctrl=True, alt=alt)
    if 0x01 <= byte <= 0x1A:
        return KeyEvent(chr(ord("a") + byte - 1), ctrl=True, alt=alt)
    if byte in _CTRL_SYMBOLS:
        return KeyEvent(_CTRL_SYMBOLS[byte], ctrl=True, alt=alt)
    return KeyEvent(f"\\x{byte:02x}", ctrl=True, alt=alt)


#: What a named key is sent back out as -- the inverse of ``_TILDE_KEYS`` and
#: ``_LETTER_KEYS``, in the form a terminal in its normal (rather than
#: application) cursor mode emits.  ``enter`` is a carriage return because that
#: is what a tty in raw mode actually delivers, whatever the parser named it.
_KEY_SEQUENCES = {
    "up": "\x1b[A",
    "down": "\x1b[B",
    "right": "\x1b[C",
    "left": "\x1b[D",
    "home": "\x1b[H",
    "end": "\x1b[F",
    "insert": "\x1b[2~",
    "delete": "\x1b[3~",
    "pageup": "\x1b[5~",
    "pagedown": "\x1b[6~",
    "f1": "\x1bOP",
    "f2": "\x1bOQ",
    "f3": "\x1bOR",
    "f4": "\x1bOS",
    "f5": "\x1b[15~",
    "f6": "\x1b[17~",
    "f7": "\x1b[18~",
    "f8": "\x1b[19~",
    "f9": "\x1b[20~",
    "f10": "\x1b[21~",
    "f11": "\x1b[23~",
    "f12": "\x1b[24~",
    "tab": "\t",
    "enter": "\r",
    "backspace": "\x7f",
    "escape": "\x1b",
    "space": " ",
}

_SYMBOL_CTRL = {symbol: byte for byte, symbol in _CTRL_SYMBOLS.items()}


#: The keys DECCKM (application cursor mode) moves from ``CSI`` to ``SS3``.
_CURSOR_KEYS = frozenset({"up", "down", "right", "left", "home", "end"})


def _with_modifiers(sequence: str, modifier: int) -> str:
    """*sequence* carrying xterm's modifier parameter, ``1 + shift + 2*alt + 4*ctrl``.

    ``CSI A`` becomes ``CSI 1 ; m A``, ``CSI 15 ~`` becomes ``CSI 15 ; m ~``,
    and ``SS3 P`` -- F1 to F4 -- becomes ``CSI 1 ; m P``, which is what xterm
    sends and what every curses terminfo entry for it expects.
    """
    if sequence.startswith("\x1bO"):
        return f"\x1b[1;{modifier}{sequence[2:]}"
    if sequence.endswith("~"):
        return f"{sequence[:-1]};{modifier}~"
    return f"\x1b[1;{modifier}{sequence[-1]}"


def encode_key(event: KeyEvent, *, application_cursor: bool = False) -> bytes:
    """Turn a key press back into the bytes a terminal would have sent.

    The inverse of :class:`InputParser`, and needed for the same reason
    :mod:`navkit.console` exists: a child program on a pty this application
    owns has to be typed at, and what it expects is bytes, not events.

    *application_cursor* is the child's DECCKM, which a full-screen program
    turns on with its keypad (``smkx``): the arrows, Home and End then send
    ``SS3`` rather than ``CSI``, and a curses program recognises only the
    spelling its terminfo entry names -- so an arrow sent the other way does
    nothing at all in ``htop`` or ``mc``.

    A special key held with Shift, Alt or Ctrl carries xterm's modifier
    parameter rather than losing the modifier.  Alt on anything else is the
    ESC prefix, which is how the parser recognises it coming the other way.
    A key with no encoding -- a bare modifier, or one of the parser's
    ``\\xNN`` placeholders -- produces nothing rather than guessing.
    """
    key = event.key
    if key == "tab" and event.shift and not (event.ctrl or event.alt):
        return b"\x1b[Z"
    special = _KEY_SEQUENCES.get(key, "")
    if special.startswith("\x1b") and len(special) > 1:
        modifier = 1 + event.shift + 2 * event.alt + 4 * event.ctrl
        if modifier > 1:
            return _with_modifiers(special, modifier).encode()
        if application_cursor and key in _CURSOR_KEYS:
            return ("\x1bO" + special[-1]).encode()
        return special.encode()
    if event.ctrl:
        if len(key) == 1 and "a" <= key <= "z":
            text = chr(ord(key) - ord("a") + 1)
        elif key == "space":
            text = "\x00"
        elif key in _SYMBOL_CTRL:
            text = chr(_SYMBOL_CTRL[key])
        else:
            text = special
    elif special:
        text = special
    elif event.char:
        text = event.char
    elif len(key) == 1:
        text = key
    else:
        text = ""
    if not text:
        return b""
    return (("\x1b" + text) if event.alt else text).encode("utf-8", "replace")


#: The button number a mouse report carries, before modifiers and motion --
#: :data:`_MOUSE_BUTTONS` the other way round, and with the wheels folded in.
_MOUSE_CODES = {
    "left": 0, "middle": 1, "right": 2,
    "wheel_up": 64, "wheel_down": 65, "wheel_left": 66, "wheel_right": 67,
}


def encode_mouse(
    event: MouseClickEvent, *, tracking: int, sgr: bool = False
) -> bytes:
    """Turn a mouse action back into the report a program on a pty asked for.

    The mouse half of :func:`encode_key`.  *tracking* is the mode the program
    turned on -- 9 reports presses only, 1000 presses and releases, 1002 a
    held button's moves as well, 1003 every move -- and an action the mode
    does not report encodes to nothing.  *sgr* is mode 1006: ``CSI < b;x;y M``
    for a press and ``m`` for a release, which carries any column; without it
    the legacy ``CSI M`` form, which cannot name a column past 222.
    Coordinates are *event*'s, zero-based, in whatever the program's screen
    is -- the caller shifts them.
    """
    if tracking not in (9, 1000, 1002, 1003):
        return b""
    button = _MOUSE_CODES.get(event.button)
    action = event.action
    if action == "move":
        if tracking == 1003 or (tracking == 1002 and button is not None):
            code = (3 if button is None else button) + 32
        else:
            return b""
    elif button is None:
        return b""
    elif action == "release":
        if tracking == 9 or button >= 64:
            return b""
        code = button if sgr else 3
    else:
        code = button
    if tracking != 9:
        code += 4 * event.shift + 8 * event.alt + 16 * event.ctrl
    x, y = event.x + 1, event.y + 1
    if sgr:
        final = "m" if action == "release" else "M"
        return f"\x1b[<{code};{x};{y}{final}".encode()
    if x > 223 or y > 223:
        return b""
    return b"\x1b[M" + bytes((32 + code, 32 + x, 32 + y))


class Terminal:
    """The tty the application draws on.

    :meth:`start` switches to the alternate screen in raw mode; :meth:`stop`
    puts everything back.  Both are idempotent, so an application that dies
    mid-frame still leaves a usable terminal behind.
    """

    def __init__(
        self,
        *,
        input_stream: IO[str] | None = None,
        output_stream: IO[str] | None = None,
        mouse: bool = True,
        palette: tuple[tuple[int, int, int], ...] | None = None,
        reprogram_palette: bool = False,
        info: TerminalInfo | None = None,
    ):
        self._in = input_stream or sys.stdin
        self._out = output_stream or sys.stdout
        #: What this terminal supports.  Detected from the environment unless
        #: stated outright, and detected here rather than on first use so that
        #: it is one fixed answer for the life of the terminal -- a frame that
        #: quantised colours differently from the one before it would show up
        #: as the diff repainting cells nothing had changed.
        self.info = info or TerminalInfo.detect(is_tty=self.is_tty, palette=palette)
        #: Asked for only if wanted *and* supported: a caller says whether it
        #: wants mouse input at all, `info` says whether asking is any use.
        self.mouse = mouse and self.info.mouse
        #: Whether to rewrite the terminal's own sixteen colour registers, so
        #: that even a terminal naming nothing else paints the pinned palette.
        #: Off by default: it changes colours outside this application's cells
        #: for as long as it runs, and a process killed outright leaves them
        #: changed until something resets them.
        self.reprogram_palette = (
            reprogram_palette and self.info.palette is not None and self.info.alt_screen
        )
        self._saved_attrs: list | None = None
        self._started = False
        self._pending: list[str] = []

    @property
    def input_fd(self) -> int:
        return self._in.fileno()

    @property
    def is_tty(self) -> bool:
        return is_a_tty(self._in, self._out)

    @property
    def size(self) -> tuple[int, int]:
        """Current ``(columns, lines)``, falling back to 80x24."""
        try:
            size = os.get_terminal_size(self._out.fileno())
        except (OSError, ValueError):
            return 80, 24
        return max(1, size.columns), max(1, size.lines)

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        if self.is_tty:
            self._saved_attrs = termios.tcgetattr(self.input_fd)
            tty.setraw(self.input_fd)
        if self.info.alt_screen:
            self.write(ALT_SCREEN_ON)
        self.write(AUTOWRAP_OFF + HIDE_CURSOR + CLEAR_SCREEN)
        if self.mouse:
            self.write(MOUSE_ON)
        if self.info.bracketed_paste:
            self.write(PASTE_ON)
        if self.info.kitty_keyboard:
            self.write(KEYBOARD_ON)
        if self.reprogram_palette:
            self.write(palette_sgr(self.info.palette))
        self.flush()

    def stop(self) -> None:
        if not self._started:
            return
        self._started = False
        # Everything start() turned on, turned off in the reverse order.  Each
        # is guarded by the same flag, so a feature that was never asked for is
        # never cancelled either -- sending the reset regardless would be
        # harmless on a real terminal and noise in a pipe.
        if self.reprogram_palette:
            self.write(PALETTE_RESET)
        if self.info.kitty_keyboard:
            self.write(KEYBOARD_OFF)
        if self.info.bracketed_paste:
            self.write(PASTE_OFF)
        if self.mouse:
            self.write(MOUSE_OFF)
        # The shape reset is unconditional, like the SGR reset beside it: a
        # widget may have changed it at any point in the run, and the flag
        # that would say so belongs to a frame rather than to the terminal.
        self.write(AUTOWRAP_ON + CURSOR_SHAPE_RESET + SHOW_CURSOR + "\x1b[0m")
        if self.info.alt_screen:
            self.write(ALT_SCREEN_OFF)
        self.flush()
        if self._saved_attrs is not None:
            termios.tcsetattr(self.input_fd, termios.TCSADRAIN, self._saved_attrs)
            self._saved_attrs = None

    def set_clipboard(self, text: str, *, primary: bool = False) -> None:
        """Put *text* on the terminal's clipboard, or its primary selection."""
        if self.info.clipboard:
            self.write(clipboard_osc(text, primary=primary))
            self.flush()

    def query_clipboard(self, *, primary: bool = False) -> None:
        """Ask for the clipboard; the answer arrives as a paste, if at all."""
        if self.info.clipboard:
            self.write(clipboard_query(primary=primary))
            self.flush()

    def set_title(self, title: str) -> None:
        if self.info.title:
            self.write(f"\x1b]0;{title}\x07")

    def read(self, size: int = 65536) -> bytes:
        """Read available input.  Returns ``b""`` at end of input."""
        try:
            return os.read(self.input_fd, size)
        except (BlockingIOError, InterruptedError):
            return b""

    def write(self, text: str) -> None:
        """Queue *text* for output; nothing reaches the tty until :meth:`flush`."""
        if text:
            self._pending.append(text)

    def flush(self) -> None:
        if not self._pending:
            return
        data, self._pending = "".join(self._pending), []
        try:
            self._out.write(data)
            self._out.flush()
        except (BrokenPipeError, ValueError):
            pass

    def __enter__(self) -> Terminal:
        self.start()
        return self

    def __exit__(self, *_exc) -> None:
        self.stop()