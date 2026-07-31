"""ANSI terminal handling: raw mode, screen setup and input decoding.

:class:`Terminal` owns the tty -- putting it into raw mode on the way in and
restoring it on the way out -- while :class:`InputParser` turns the resulting
byte stream into :mod:`navkit.events` objects.

The parser is fed incrementally and keeps whatever it cannot yet decode, so a
sequence split across two reads is decoded correctly once the rest arrives.
"""

from __future__ import annotations

import os
import sys
import termios
import tty
from typing import IO

from navkit.events import Event, KeyEvent, MouseEvent, PasteEvent

ALT_SCREEN_ON = "\x1b[?1049h"
ALT_SCREEN_OFF = "\x1b[?1049l"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
AUTOWRAP_OFF = "\x1b[?7l"
AUTOWRAP_ON = "\x1b[?7h"
# 1000: report button presses, 1002: also report drags, 1003: also report plain
# motion, 1006: report them in the unambiguous SGR format.
MOUSE_ON = "\x1b[?1000h\x1b[?1002h\x1b[?1006h"
MOUSE_OFF = "\x1b[?1006l\x1b[?1002l\x1b[?1000l"
PASTE_ON = "\x1b[?2004h"
PASTE_OFF = "\x1b[?2004l"
CLEAR_SCREEN = "\x1b[H\x1b[2J"

PASTE_START = b"\x1b[200~"
PASTE_END = b"\x1b[201~"

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
    """Decode an xterm modifier parameter into ``(ctrl, alt, shift)``."""
    bits = max(0, param - 1)
    return bool(bits & 4), bool(bits & 2), bool(bits & 1)


class InputParser:
    """Incremental decoder turning terminal input bytes into events."""

    def __init__(self) -> None:
        self._buf = bytearray()
        self._paste: bytearray | None = None
        self._incomplete = False

    @property
    def pending_escape(self) -> bool:
        """True if the buffer holds an escape sequence that may still grow.

        A lone ``ESC`` byte is indistinguishable from the start of a longer
        sequence, so the caller resolves the ambiguity with a short timeout and
        then calls :meth:`flush`.
        """
        return self._incomplete and bool(self._buf) and self._buf[0] == 0x1B

    def feed(self, data: bytes) -> list[Event]:
        """Decode *data*, returning every event it completes."""
        self._buf += data
        return self._parse()

    def flush(self) -> list[Event]:
        """Resolve a pending lone ``ESC`` into an escape key press."""
        if not self.pending_escape:
            return []
        del self._buf[:1]
        self._incomplete = False
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
                if event is not None:
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

    def _parse_escape(self) -> tuple[int, Event | None]:
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
            return final + 1, _csi_key(body, terminator)

        if second == 0x4F:  # SS3, e.g. ESC O P for F1
            if len(buf) < 3:
                return 0, None
            name = _LETTER_KEYS.get(chr(buf[2]))
            return 3, KeyEvent(name) if name else None

        # Anything else is Alt plus whatever follows.
        if second < 0x20 or second == 0x7F:
            return 2, _control_key(second, alt=True)
        length = _utf8_length(second)
        if len(buf) < 1 + length:
            return 0, None
        char = bytes(buf[1 : 1 + length]).decode("utf-8", "replace")
        return 1 + length, KeyEvent(char.lower(), char, alt=True, shift=char.isupper())


def _csi_key(body: bytes, terminator: str) -> Event | None:
    """Decode a non-mouse ``CSI`` sequence."""
    params = [int(p) if p.isdigit() else 0 for p in body.split(b";")] or [0]
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
    return MouseEvent(
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
    ):
        self._in = input_stream or sys.stdin
        self._out = output_stream or sys.stdout
        self.mouse = mouse
        self._saved_attrs: list | None = None
        self._started = False
        self._pending: list[str] = []

    @property
    def input_fd(self) -> int:
        return self._in.fileno()

    @property
    def is_tty(self) -> bool:
        try:
            return os.isatty(self.input_fd) and os.isatty(self._out.fileno())
        except (OSError, ValueError):
            return False

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
        self.write(ALT_SCREEN_ON + AUTOWRAP_OFF + HIDE_CURSOR + CLEAR_SCREEN)
        if self.mouse:
            self.write(MOUSE_ON)
        self.write(PASTE_ON)
        self.flush()

    def stop(self) -> None:
        if not self._started:
            return
        self._started = False
        self.write(PASTE_OFF)
        if self.mouse:
            self.write(MOUSE_OFF)
        self.write(AUTOWRAP_ON + SHOW_CURSOR + "\x1b[0m" + ALT_SCREEN_OFF)
        self.flush()
        if self._saved_attrs is not None:
            termios.tcsetattr(self.input_fd, termios.TCSADRAIN, self._saved_attrs)
            self._saved_attrs = None

    def set_title(self, title: str) -> None:
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