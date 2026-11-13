"""What the FileEditor's mixins share: module-level helpers of
:mod:`navigator.widgets.editor.file_editor.file_editor`.
"""

from __future__ import annotations

import functools
import re
import threading
import time
from decimal import Decimal, InvalidOperation
from typing import Any, Awaitable, Callable, cast, TypeVar

from navkit.bidi import has_rtl, order_cells, text_rtl

from navml.background import Background
from navml.widgets.menu.commands import OpenMenu

from navigator.widgets.editor.commands import (
    SwitchDrawMode,
    FCenter,
    FJustify,
    FLeft,
    FRight,
    Replace,
    ReverseSearch,
    StartSearch,
    BracketPair,
    PrintBlock,
    SortBlock,
    GotoMarker,
    PlaceMarker,
    BlockRead,
    BlockWrite,
    InsertDate,
    InsertTime,
    CapitalizeBlock,
    CopyBlock,
    MoveBlockEnd,
    MoveBlockStart,
    HideBlock,
    IndentBlock,
    LowcaseBlock,
    BlockEnd,
    BlockStart,
    MarkLine,
    MarkWord,
    MoveBlock,
    UnindentBlock,
    UpcaseBlock,
    Clear,
    DeleteChar,
    DeleteToEnd,
    DeleteWordRight,
    MoveLeft,
    MoveRight,
    MoveUp,
    PageUp,
    ScrollDown,
    ScrollUp,
    Undo,
    SwitchBlock,
    WordLeft,
    WordRight,
)
from navigator.lib.editor import columns
from navigator.lib import highlight
from navigator.settings import SETTINGS


#: How many lines one wheel notch moves the view.
WHEEL_ROWS = 3

#: The thread syntax highlighting lexes on: one, so editors take turns.
_LEXER = Background("nav-lex", workers=1)

#: Lines lexed past the last one showing, so scrolling a little finds them done.
LEX_AHEAD = 200

#: A text longer than this many characters is not highlighted: an edit
#: near its end is lexed again from the start, and Pygments manages about
#: half a million characters a second -- this is some four seconds of a
#: thread competing with the loop for the interpreter.
LEX_LIMIT = 2 * 1024 * 1024


def _lex_text(name: str, file_type: str, lines: tuple[str, ...], until: int,
              stop: threading.Event) -> tuple[str, Any]:
    """On the thread: the lexer's name ("" for none) and the spans of *lines*
    through *until* -- False when the file has no lexer, None when stopped."""
    lexer = highlight.lexer_for(name, lines[0] if lines else "", file_type=file_type)
    if lexer is None:
        return "", False
    return highlight.lexer_label(lexer), highlight.lex_lines(lexer, lines, until, stop)

#: The text of the last column block copied, with the padded pieces it was
#: copied from: a paste of exactly that text goes in as a rectangle.  Shared
#: by every editor, as the clipboard is, and holding only the newest copy.
_COLUMN_CLIP: dict[str, list[str]] = {}


#: The keys besides letters that have a control byte, so a Ctrl form the
#: table could name: ``^K^[``, ``^K^]``, ``^K^\``.
_CONTROL_PUNCTUATION = frozenset("[]\\")


def _wordstar(prefix: str, letters: dict[str, Any], *, punctuation: bool = True) -> dict[str, Any]:
    """*prefix* then each key, and then each letter with Ctrl held too, as WordStar took them.

    So is ``[``, ``]`` and ``\\`` unless *punctuation* is False: the table
    has ``^K^[``, ``^K^]`` and ``^K^\\``, but ``^Q'['`` alone."""
    table = {}
    for key, command in letters.items():
        table[f"{prefix} {key}"] = command
        if len(key) == 1 and (key.isalpha() or (punctuation and key in _CONTROL_PUNCTUATION)):
            table[f"{prefix} ctrl+{key}"] = command
    return table


def _now() -> time.struct_time:
    """The time ^Q D and ^Q T write; a function so a test can fix it."""
    return time.localtime()


#: What Pascal's ``Val`` reads as a real: a sign, digits with a point, an exponent.
_NUMBER = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")


def block_sum(pieces: list[str]) -> str:
    """``CalcBlock``'s sum of *pieces*, each with its blanks removed (``DelSpaces``).

    A piece that is not a number counts as nothing, as ``Val``'s failure left
    0.  Written as ``Str(R:0:20)`` was, its trailing zeros and point cut --
    but added exactly, where DN's 6-byte ``Real`` would print 0.1 + 0.2 with
    its binary error.
    """
    total = Decimal(0)
    for piece in pieces:
        text = piece.replace(" ", "")
        if _NUMBER.fullmatch(text):
            try:
                total += Decimal(text)
            except InvalidOperation:
                pass
    written = format(total, "f")
    if "." in written:
        written = written.rstrip("0").rstrip(".")
    return "0" if written in ("", "-0") else written


#: A word, for Capitalize: letters and digits, not the underscore.
_WORD = re.compile(r"[^\W_]+")


def capitalize(text: str) -> str:
    """``CapCaseStr``: each word's first letter upper case, the rest lower."""
    return _WORD.sub(lambda m: m[0][:1].upper() + m[0][1:].lower(), text)


def _ordered(chars: list[str]) -> list[tuple[int, str]] | None:
    """``order_cells``, with every column of the line kept: a lam-alef pair,
    one ligature in one cell, leaves the alef's column over, and it is given
    a blank cell so what follows on the line -- a tab stop most of all --
    stays in the column the text has it in.  Not beside the ligature, which
    would open a gap inside the word, but beside the next blank after it in
    the text (one blank wider, where a tab or a space is anyway), or at the
    line's end when none follows.  ``""``, as the second half of a wide
    character is: painted as nothing, passed over by a move.
    """
    order = order_cells(chars)
    if order is None or len(order) == len(chars):
        return order
    kept = {at for at, _ in order}
    spare: dict[int, list[int]] = {}  # a cell's column -> the alef columns put beside it
    for at in range(len(chars)):
        if at in kept or chars[at] == "":
            continue
        beside = next((t for t in range(at + 1, len(chars)) if t in kept and chars[t] == " "), None)
        if beside is None:
            beside = max(kept)
        spare.setdefault(beside, []).append(at)
    out: list[tuple[int, str]] = []
    for at, shown in order:
        out.append((at, shown))
        out.extend((alef, "") for alef in spare.get(at, ()))
    return out


def _laid_line(
    text: str, tab: int, width: int, limit: int
) -> tuple[list[tuple[str, int]], list[tuple[int, str]] | None, int]:
    """Line *text* as the editor paints it: its cells, their painted order
    (None when the line reads as written) and how many columns in its first
    painted cell sits.

    A right-to-left line -- its first strong letter Hebrew or Arabic -- is
    right-aligned, as a word processor sets it: it ends against column
    *width*, or one further in when it is wider, so the cell left of it, where
    typing at its end appears, is always there.  A departure, as the rest of
    right-to-left text is.  A line with no Hebrew or Arabic is cut at *limit*,
    the screen's right edge, which is all render ever needs of a long one.
    """
    if not has_rtl(text):
        return columns.cells(text, tab, limit=limit), None, 0
    row = columns.cells(text, tab)
    order = _ordered([char for char, _ in row])
    if order is None or not text_rtl(text):
        return row, order, 0
    return row, order, max(width, len(order) + 1) - len(order)


def _painted_spans(text: str, tab: int, start: int | None, end: int | None) -> list[tuple[int, int]] | None:
    """The stretches of *text* painted between a block's ends on this line, or
    None when the line reads as written (and the block is the stretch it is).

    *start* is the block's start on this, its first line (None if it began
    above), *end* its end on its last (None if it goes on below).  An end is a
    caret, on the cell of the character at its index -- past the text when
    it is past the line's end.  Between two on one line the cells from one up
    to the other are the block's; from a start alone, towards the end the line
    reads to (left in a right-to-left line), the start's own cell included;
    up to an end alone, from where the line begins, its cell left out.

    On a right-to-left line (right-aligned, :func:`_laid_line`) a caret is the
    right-hand edge of its cell, where a caret before a Hebrew letter stands,
    and the line's end is the cell left of the text: two ends hold the cells
    between them on that side, so Shift+End from the line's start holds all
    of it.
    """
    row = columns.cells(text, tab)
    order = _ordered([char for char, _ in row])
    if order is None:
        return None
    cells = [row[at][1] for at, shown in order if shown != ""]
    bases = sorted(set(cells))
    reach = {base: (bases[k + 1] if k + 1 < len(bases) else len(text)) for k, base in enumerate(bases)}
    count = len(cells)

    rtl = text_rtl(text)

    def cell_of(index: int) -> int:
        if index >= len(text):
            return -1 if rtl else count
        return next((x for x, base in enumerate(cells) if base <= index < reach[base]), count)

    if start is not None and end is not None:
        low, high = sorted((cell_of(start), cell_of(end)))
        chosen = range(low + 1, high + 1) if rtl else range(low, high)
    elif start is not None:
        at = cell_of(start)
        if start >= len(text):
            chosen = range(0)
        else:
            chosen = range(0, at + 1) if rtl else range(at, count)
    elif end is not None:
        at = cell_of(end)
        chosen = range(at + 1, count) if rtl else range(0, at)
    else:
        chosen = range(count)
    picked = sorted({i for x in chosen for i in range(cells[x], reach[cells[x]])})
    spans: list[tuple[int, int]] = []
    for i in picked:
        if spans and spans[-1][1] == i:
            spans[-1] = (spans[-1][0], i + 1)
        else:
            spans.append((i, i + 1))
    return spans


_Handler = TypeVar("_Handler", bound=Callable[[Any, Any], Awaitable[bool]])


def _marking(handler: _Handler) -> _Handler:
    """A movement that, with its command's *extend* (Shift), drags the block along.

    The block grows from wherever the cursor stood unless that was one of the
    block's ends, in which case the other end stays put: Shift+Right then
    Shift+Left takes back what the first marked.  Without Shift, and with the
    Editor setup's *Persistent blocks* off, the block goes.
    """

    @functools.wraps(handler)
    async def moving(self: Any, event: Any) -> bool:
        before = self._here()
        extend = getattr(event, "extend", False)
        self._extending = extend
        try:
            done = await handler(self, event)
        finally:
            self._extending = False
        if extend:
            self._extend_block(before)
        elif not SETTINGS.editor.persistent_blocks:
            self._unmark()
        return done

    # The handler's own type, so a type checker sees the method it wrapped.
    return cast(_Handler, moving)


#: The WordStar keys of DN's ``EDITOR COMMANDS``, no longer bound by default
#: (see ``FileEditor.keys``): the diamond's and the deleting Ctrl keys, and
#: the two-key Ctrl+B, Ctrl+K and Ctrl+Q commands.  DN's Ctrl+X and Ctrl+C
#: (cursor down, page down) are not here -- they are the clipboard's either
#: way but in ``keybindings_dn151.ini``.  ``keybindings_wordstar.ini`` binds
#: exactly these, which a test holds it to.
WORDSTAR = {
    "ctrl+s": MoveLeft,
    "ctrl+d": MoveRight,
    "ctrl+e": MoveUp,
    "ctrl+a": WordLeft,
    "ctrl+f": WordRight,
    "ctrl+r": PageUp,
    "ctrl+w": ScrollUp,
    "ctrl+z": ScrollDown,
    "ctrl+g": DeleteChar,
    "ctrl+t": DeleteWordRight,
    **_wordstar("ctrl+b", {
        "v": SwitchBlock,
        "j": FJustify,
        "r": FRight,
        "l": FLeft,
        "c": FCenter,
    }),
    # ``EDITOR COMMANDS``' two-key half: WordStar's Ctrl+K and Ctrl+Q.
    **_wordstar("ctrl+k", {
        "b": BlockStart,
        "k": BlockEnd,
        "h": HideBlock,
        "c": CopyBlock,
        "v": MoveBlock,
        "y": Clear,
        "i": IndentBlock,
        "u": UnindentBlock,
        # ``^K^[``, ``^K^]``, ``^K^\``: the Ctrl forms are the table's.  The
        # plain ones are kept too (a departure: DN let a plain ``[`` after ^K
        # go): Ctrl+[ is Esc's byte, and arrives as itself only under the kitty
        # keyboard protocol.  ``ctrl+k escape`` is not bound for it -- Esc
        # after ^K is "never mind" to anyone now, not *Upper case*.
        "[": UpcaseBlock,
        "]": LowcaseBlock,
        "\\": CapitalizeBlock,
        "t": MarkWord,
        "l": MarkLine,
        "s": SortBlock,
        "p": PrintBlock,
        "r": BlockRead,
        "w": BlockWrite,
        # ``cmMenu``, ``^K^Q`` -- what F10 opens.  Its other key, the double
        # Alt (``kbDoubleAlt``), is dropped: only a terminal speaking the kitty
        # keyboard protocol reports a bare Alt, and a stray double tap would
        # pop the menu.
        "q": OpenMenu,
        # ``^K'1'`` to ``^K'9'``: the digit alone, as the table has it.
        **{str(n): PlaceMarker(n) for n in range(1, 10)},
    }),
    **_wordstar("ctrl+q", punctuation=False, letters={
        "b": MoveBlockStart,
        "k": MoveBlockEnd,
        "y": DeleteToEnd,
        "l": Undo,
        "d": InsertDate,
        "t": InsertTime,
        "f": StartSearch,
        "a": Replace,
        "r": ReverseSearch,
        # ``^Q'['`` and ``^Q^]``, as the table has them, neither with the other's form.
        "[": BracketPair,
        **{str(n): GotoMarker(n) for n in range(1, 10)},
        "m": SwitchDrawMode,
        # ``^Q^M``: Ctrl+M is Enter on a terminal that cannot tell them apart.
        "enter": SwitchDrawMode,
        # ``^Q^O``, ``^Q^I``, ``^Q^P`` and ``^Q^C`` -- ``cmSyncClipOut``/``In``,
        # ``cmWindowsPaste``/``Copy`` -- are dropped: they reached the Windows
        # clipboard beside DN's own, and the clipboard here is the system's.
    }),
    "ctrl+q ctrl+]": BracketPair,
}
