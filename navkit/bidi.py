"""Right-to-left text, laid out by Navigator rather than by the terminal.

A terminal is handed cells, left to right, and what it does with Hebrew or
Arabic among them differs from one to the next: VTE reorders a whole screen
row as one paragraph (tearing apart whatever shares it), kitty reverses the
letters of a word and nothing else, ghostty does nothing at all and joins no
Arabic letter.  None of that can be relied on, so the reordering is done here,
once per painted string, and the terminal is told -- or trusted -- to leave
the cells where they are put.

:func:`layout` is the one entry point.  It takes the logical text a widget
paints and returns *cells*: the visual order, left to right, each cell the
logical index it came from and what it shows.  The index is what lets a style
follow its character (the ``~A~`` run of a caption, wherever it lands), and a
caret be put beside the right one.

Three things happen on the way:

- **Arabic is shaped**: each letter becomes the presentation form its
  neighbours call for (``arabic-reshaper``, without its ligatures, so one
  letter stays one cell), and lam followed by alef becomes the one ligature
  glyph it must be, in one cell, its alef folded into the lam's.
- **The Unicode Bidi Algorithm orders it**: ``python-bidi``'s pure-Python
  implementation, run step by step so every character keeps its index -- its
  ``get_display`` returns only a string.  The paragraph direction is the first
  strong letter's, and the caller's *rtl* when there is none ("( )", "12:30").
- **Marks stay on their letter**: a combining mark is folded into the cell of
  the letter before it before ordering, so reversing a run cannot put niqqud
  or harakat in front of what they belong to.

Text with nothing right-to-left in it, and a left-to-right paragraph, comes
back one cell per character without the algorithm being run: that is nearly
every string a frame paints.  Everything else is cached, since a frame paints
the same few hundred strings every time.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Sequence
from typing import Any
from functools import lru_cache

import arabic_reshaper
from bidi.algorithm import (
    explicit_embed_and_overrides,
    get_embedding_levels,
    get_empty_storage,
    reorder_resolved_levels,
    resolve_implicit_levels,
    resolve_neutral_types,
    resolve_weak_types,
)
from bidi.mirror import MIRRORED

#: One painted cell of laid-out text: the logical index of the character it
#: starts with, and what it shows (a letter and the marks on it, a shaped
#: form, a mirrored bracket).
type LaidCell = tuple[int, str]

#: The classes that make text right-to-left, or able to be: the strong
#: letters, Arabic digits, and the explicit embeddings and overrides.
_RTL_CLASSES = frozenset({"R", "AL", "AN", "RLE", "RLO", "RLI", "LRE", "LRO", "PDF", "FSI"})

#: Letter forms, one per letter, and no ligatures: a ligature is two letters
#: in one glyph, and only lam-alef -- which Arabic cannot do without -- is
#: made, by :func:`_shape`, where its two indices can be kept track of.
_RESHAPER = arabic_reshaper.ArabicReshaper(configuration={
    "delete_harakat": False,
    "shift_harakat_position": False,
    "support_ligatures": False,
})

#: Lam's initial and medial forms, which a following alef joins.
_LAM_JOINING = {"ﻟ": 0, "ﻠ": 1}
#: Alef's final forms (madda, hamza above, hamza below, plain), and the
#: lam-alef ligature each makes: (isolated, final), by whether the lam was
#: joined to the letter before it.
_LAM_ALEF = {
    "ﺂ": ("ﻵ", "ﻶ"),
    "ﺄ": ("ﻷ", "ﻸ"),
    "ﺈ": ("ﻹ", "ﻺ"),
    "ﺎ": ("ﻻ", "ﻼ"),
}


_REGIONAL_A, _REGIONAL_Z = "\U0001f1e6", "\U0001f1ff"


def is_mark(char: str) -> bool:
    """Whether *char* draws on the character before it rather than a cell."""
    return unicodedata.category(char) in ("Mn", "Me")


#: What :func:`reveal` makes visible: the embeddings and overrides
#: (U+202A..U+202E) and isolates (U+2066..U+2069), which take no cell and
#: reorder what follows -- ``photo`` + U+202E + ``gpj.exe`` is painted as
#: ``photoexe.jpg`` -- and the C0 and C1 controls, which a terminal must
#: never be sent.  The marks of direction (LRM, RLM, ALM) stay hidden: they
#: cannot turn letters round, and right-to-left names use them in earnest.
_HIDDEN = frozenset(
    [chr(code) for code in range(0x202A, 0x202F)]
    + [chr(code) for code in range(0x2066, 0x206A)]
    + [chr(code) for code in range(0x20)]
    + [chr(code) for code in range(0x7F, 0xA0)]
)

#: A stand-in one cell wide (a private-use character, plane 16) that
#: :func:`reveal_runs` turns into the shown mark and its style, so the mark
#: is told apart from the same character typed in the name.
REVEALED = "\U0010fffd"


def reveal(text: str, mark: str = "\u2047", keep: str = "") -> str:
    """*text* with each character that would hide or reorder part of it --
    a direction override, an embedding, an isolate, a control -- shown as
    *mark*, one cell, and doing nothing.  *keep* names controls left alone
    (a caption's line breaks).

    For a file name on screen: what the name *is* (a copy, a rename, the
    command line) keeps every character.  One character for one, so a
    length measured before still holds.
    """
    if not any(char in _HIDDEN and char not in keep for char in text):
        return text
    return "".join(mark if char in _HIDDEN and char not in keep else char for char in text)


def reveal_runs(text: str, style: Any, mark: str, mark_style: Any) -> list[tuple[str, Any]]:
    """*text*, revealed with :data:`REVEALED` and then cut to fit, as runs
    for ``draw_runs``: the stand-ins become *mark* in *mark_style*."""
    if REVEALED not in text:
        return [(text, style)]
    runs: list[tuple[str, Any]] = []
    for index, piece in enumerate(text.split(REVEALED)):
        if index:
            runs.append((mark, mark_style))
        if piece:
            runs.append((piece, style))
    return runs


def has_rtl(text: str) -> bool:
    """Whether anything in *text* could make it lay out other than as written."""
    # Everything below Hebrew is left-to-right or neutral, and that is nearly
    # every character a frame paints: one comparison rules it out.
    return any(
        char >= "֐" and unicodedata.bidirectional(char) in _RTL_CLASSES
        for char in text
    )


def _clusters(text: str) -> list[tuple[int, str]]:
    """*text* as (index, base and the marks on it), in logical order.

    Two Regional Indicators are one cell too: a flag, which a terminal draws
    two cells wide over both (``navkit.screen.is_flag``).
    """
    out: list[tuple[int, str]] = []
    for index, char in enumerate(text):
        if (
            out
            and _REGIONAL_A <= char <= _REGIONAL_Z
            and len(out[-1][1]) == 1
            and _REGIONAL_A <= out[-1][1] <= _REGIONAL_Z
        ):
            start, cluster = out[-1]
            out[-1] = (start, cluster + char)
        elif out and is_mark(char):
            start, cluster = out[-1]
            out[-1] = (start, cluster + char)
        else:
            out.append((index, char))
    return out


def _shape(clusters: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Arabic letters in the forms their neighbours call for.

    The reshaper is asked for the bases alone, which keeps it one character
    in, one out (a mark would only be passed through), and a lam-alef pair is
    then folded into its ligature, which keeps the lam's index.
    """
    bases = "".join(cluster[0] for _, cluster in clusters)
    if not any("؀" <= char <= "ۿ" for char in bases):
        return clusters
    shaped = _RESHAPER.reshape(bases)
    if len(shaped) != len(bases):
        return clusters  # not the one-for-one this relies on: leave it unshaped
    out: list[tuple[int, str]] = []
    for (index, cluster), form in zip(clusters, shaped):
        if out and form in _LAM_ALEF and out[-1][1][:1] in _LAM_JOINING:
            start, lam = out[-1]
            ligature = _LAM_ALEF[form][_LAM_JOINING[lam[0]]]
            out[-1] = (start, ligature + lam[1:] + cluster[1:])
            continue
        out.append((index, form + cluster[1:]))
    return out


def text_rtl(text: str, default: bool = False) -> bool:
    """Whether *text* is a right-to-left paragraph: its first strong letter's
    direction, else *default*."""
    strong = _first_strong(text)
    return default if strong is None else strong == "R"


def _first_strong(text: str) -> str | None:
    for char in text:
        kind = unicodedata.bidirectional(char)
        if kind == "L":
            return "L"
        if kind in ("R", "AL"):
            return "R"
    return None


@lru_cache(maxsize=4096)
def layout(text: str, rtl: bool = False) -> tuple[LaidCell, ...]:
    """*text* in visual order, left to right, as :data:`LaidCell` cells.

    *rtl* is the direction of a paragraph with no strong letter to decide it,
    which is the surroundings': a right-to-left screen's ``( )`` is laid out
    as it would be inside Hebrew.  Explicit formatting characters (embeddings,
    overrides, marks of direction) take part in the ordering and are then
    left out: they have no cell of their own.
    """
    strong = _first_strong(text)
    if not has_rtl(text) and (strong == "L" or (strong is None and not rtl)):
        return tuple(_clusters(text))
    return _order(_clusters(text), strong == "R" or (strong is None and rtl))


def order_cells(
    chars: Sequence[str], rtl: bool = False, *, detect: bool = True
) -> list[LaidCell] | None:
    """A row of cells already laid out one per column, in visual order.

    *chars* is what each column shows -- a character and the marks on it,
    ``""`` for the second half of a wide one, a tab already spread over its
    columns -- as the viewer and the editor build their rows.  Returns
    ``(column, shown)`` per column, left to right, the column being the one
    in *chars* the cell came from; or None when the row reads as it is,
    which is what nearly every row of nearly every file does.  A lam-alef
    pair becomes one column, so a row can come back a column shorter.

    The paragraph's direction is its first strong letter's, else *rtl*;
    with *detect* false it is *rtl* whatever the row holds, which is what a
    terminal does with a line (VTE: left to right, unless told otherwise) --
    a row padded with blanks keeps them at its end.
    """
    text = "".join(chars)
    strong = _first_strong(text) if detect else None
    if not has_rtl(text) and (strong == "L" or (strong is None and not rtl)):
        return None
    return list(_ordered_cells(tuple(chars), strong == "R" or (strong is None and rtl)))


@lru_cache(maxsize=1024)
def _ordered_cells(chars: tuple[str, ...], rtl: bool) -> tuple[LaidCell, ...]:
    clusters = [(column, char) for column, char in enumerate(chars) if char != ""]
    out: list[LaidCell] = []
    for column, shown in _order(clusters, rtl):
        out.append((column, shown))
        if column + 1 < len(chars) and chars[column + 1] == "":
            out.append((column + 1, ""))
    return tuple(out)


#: The isolates (Unicode 6.3), which python-bidi 0.4 predates and refuses
#: (``AssertionError: LRI not allowed here``), as the embeddings they
#: generalise: what differs is only how neutrals at their edges resolve.
_ISOLATES = {"\u2066": "\u202a", "\u2067": "\u202b", "\u2069": "\u202c"}
#: FSI's stand-in: an embedding in the direction of what follows it.
_FSI = "\u2068"
#: What stands for a character with no bidirectional class -- unassigned, or a
#: noncharacter, for which ``unicodedata`` answers ``""`` and python-bidi
#: fails the same way: a neutral, U+FFFD, which is what it is shown as.
_NEUTRAL = "\ufffd"


def _classifiable(text: str) -> str:
    """*text* as the algorithm is given it: the same length, every character
    one python-bidi 0.4 has a class for.  Only the ordering sees this; each
    cell still shows its own character."""
    if text.isascii():
        return text
    out = []
    for index, char in enumerate(text):
        if char in _ISOLATES:
            char = _ISOLATES[char]
        elif char == _FSI:
            char = "\u202b" if _first_strong(text[index + 1:]) == "R" else "\u202a"
        elif not unicodedata.bidirectional(char):
            char = _NEUTRAL
        out.append(char)
    return "".join(out)


def _order(clusters: list[tuple[int, str]], rtl: bool) -> tuple[LaidCell, ...]:
    """*clusters* -- (index, a letter and its marks), logical order -- shaped,
    ordered by the Unicode Bidi Algorithm in a paragraph that is right to
    left when *rtl*, and mirrored where right-to-left."""
    clusters = _shape(clusters)
    bases = _classifiable("".join(cluster[0] for _, cluster in clusters))
    storage = get_empty_storage()
    base_level = 1 if rtl else 0
    storage["base_level"] = base_level
    storage["base_dir"] = "LR"[base_level]
    get_embedding_levels(bases, storage)
    for position, char in enumerate(storage["chars"]):
        char["at"] = position
    explicit_embed_and_overrides(storage)
    resolve_weak_types(storage, False)
    resolve_neutral_types(storage, False)
    resolve_implicit_levels(storage, False)
    reorder_resolved_levels(storage, False)
    cells: list[LaidCell] = []
    for char in storage["chars"]:
        index, cluster = clusters[char["at"]]
        if char["level"] % 2:
            cluster = MIRRORED.get(cluster[0], cluster[0]) + cluster[1:]
        cells.append((index, cluster))
    return tuple(cells)


def _widths(cells: tuple[LaidCell, ...]) -> list[int]:
    from navkit.screen import char_width  # navkit.screen imports this module

    return [max(1, char_width(cell)) for _, cell in cells]


def _written(cells: tuple[LaidCell, ...], rtl: bool) -> list[int]:
    """The column each visual cell is painted in, from the start of the text,
    as :meth:`navkit.screen.Surface.draw_runs` paints it."""
    widths = _widths(cells)
    total = sum(widths)
    columns, used = [], 0
    for width in widths:
        columns.append(total - used - width if rtl else used)
        used += width
    return columns


def display_width(text: str) -> int:
    """The cells *text* takes once painted (``Surface.draw_runs``): marks on
    their letter, format characters in none, a wide character in two, and an
    Arabic lam-alef pair in the one cell of its ligature -- where ``len()``
    would leave a centred Arabic caption a cell off."""
    if text.isascii() and text.isprintable():
        return len(text)
    from navkit.screen import char_width  # navkit.screen imports this module

    return sum(char_width(cell) for _, cell in layout(text))


def fit_cells(text: str, cells: int) -> str:
    """*text* cut to at most *cells* cells; a wide character that would
    straddle the edge is left out whole."""
    if text.isascii() and text.isprintable():
        return text[: max(0, cells)]
    from navkit.screen import char_width  # navkit.screen imports this module

    used = 0
    for index, char in enumerate(text):
        used += char_width(char)
        if used > cells:
            return text[:index]
    return text


def pad_cells(text: str, cells: int, align: str = "left") -> str:
    """*text* padded with blanks to *cells* cells -- ``str.ljust``, ``rjust``
    (*align* ``"right"``) and ``center`` counting cells, so a column of Chinese
    or Japanese lines up.  Never cut."""
    room = max(0, cells - display_width(text))
    if align == "right":
        return " " * room + text
    if align == "center":
        return " " * (room // 2) + text + " " * (room - room // 2)
    return text + " " * room


def painted_cells(text: str, rtl: bool = False) -> list[tuple[int, int, int]]:
    """``(index, column, width)`` for each cell *text* paints, left to right:
    the first character it holds, where it is painted from the start of the
    text (as :func:`caret_column` counts) and how wide it is.  For marking
    painted cells by what they hold -- a link over an address."""
    cells = layout(text, rtl)
    return [(start, column, width)
            for (start, _), column, width in zip(cells, _written(cells, rtl), _widths(cells))]


def caret_column(text: str, index: int, rtl: bool = False) -> int:
    """The column, from where *text* starts, of a caret before ``text[index]``.

    On the character itself, as a block caret sits on what will be pushed
    along, whichever way that is; at the end, past the end the paragraph
    grows from -- the left of a right-to-left one.  Columns are as
    :meth:`~navkit.screen.Surface.draw_runs` paints on a surface whose ``rtl``
    is *rtl* (reversed there, for the screen's mirror to put back), so the
    answer can be -1 or the text's width: just outside it.
    """
    cells = layout(text, rtl)
    if not cells:
        return 0
    columns = _written(cells, rtl)
    if index < len(text):
        for position, (start, cell) in enumerate(cells):
            if start <= index < start + len(cell):
                return columns[position]
    # At the end: past the end the paragraph grows from -- the left of a
    # right-to-left one, whatever its last character is ("2" ends "חדשה 2",
    # and what is typed next appears to its left).
    if text_rtl(text, rtl):
        # Left of the leftmost cell: painted reversed, that is past its end.
        return sum(_widths(cells)) if rtl else -1
    return -1 if rtl else sum(_widths(cells))


def index_at(text: str, column: int, rtl: bool = False) -> int:
    """The index in *text* a click at *column* (as :func:`caret_column`
    counts) lands on: the character painted there, or an end of the text."""
    cells = layout(text, rtl)
    columns = _written(cells, rtl)
    for (start, _), at in zip(cells, columns):
        if at == column:
            return start
    return len(text) if not cells or column > max(columns) or column < 0 else 0
