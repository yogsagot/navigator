"""Pictures on the terminal: the kitty graphics protocol and sixel.

A widget that shows a picture paints nothing of it.  It hands a
:class:`Picture` to :meth:`~navkit.screen.Surface.place_image`, which stamps
the cells the picture covers (:attr:`~navkit.style.Style.image`) and records
it on the frame; once the frame is composed, :class:`GraphicsLayer` writes
the picture over those cells, after the diff.

**A picture anything paints over is not shown at all.**  Paint order is the
z-order, so a window, a menu, a dialog or a shadow landing on a picture
overwrites some of its stamps, and a picture is shown only while every one of
them survives -- which is also what keeps it inside its widget, a stamp
clipped off by a view never having been written.  Clipping it to what is
left would mean cutting the picture to an arbitrary shape every frame, which
neither protocol can do; hiding it is what a terminal can be relied on for.

Positions are read off the frame as it goes to the terminal -- the stamps'
cells after a right-to-left screen has been mirrored -- so a picture lands
wherever its widget's cells did, mirrored or kept left to right.

The two protocols differ in what is left behind.  A kitty picture is an
object the terminal keeps above the text: it is placed once, stays put
through any amount of text written under it, and has to be deleted to go.
A sixel picture is pixels written into the cells: text written over it
erases it, so it is written again whenever its cells were, and the cells of
one that goes are rewritten as the blanks they are.
"""

from __future__ import annotations

import base64
import itertools
import re
from dataclasses import dataclass, field

#: kitty image ids start above :data:`navkit.terminal.GRAPHICS_QUERY_ID`
#: and stay within the 24 bits every implementation accepts.
_IDS = itertools.count()

#: The base64 a kitty command may carry in one chunk.
KITTY_CHUNK = 4096


def _next_id() -> int:
    return 256 + next(_IDS) % 0xFFFF00


@dataclass(eq=False)
class Picture:
    """A picture, ready to be written *cols* x *rows* cells large.

    *png* is what kitty is sent (PNG, which every kitty implementation
    decodes itself); *sixel* the whole ``DCS ... ST`` sequence for exactly
    this many cells, encoded by whoever made the picture -- off the loop, it
    being the slow half.  Either may be missing, and a terminal speaking the
    protocol whose half is missing is shown nothing.
    """

    cols: int
    rows: int
    png: bytes | None = None
    sixel: str | None = None
    id: int = field(default_factory=_next_id)

    def drawable(self, protocol: str) -> bool:
        return bool(self.png if protocol == "kitty" else self.sixel if protocol == "sixel" else False)


def _apc(keys: str, payload: str = "") -> str:
    return f"\x1b_G{keys};{payload}\x1b\\" if payload else f"\x1b_G{keys}\x1b\\"


def kitty_transmit(picture: Picture) -> str:
    """Send *picture*'s PNG to kitty under its id, without showing it.

    In :data:`KITTY_CHUNK` pieces, as the protocol asks; ``q=2`` everywhere,
    so the terminal answers nothing -- an answer would arrive as typed keys.
    """
    data = base64.b64encode(picture.png or b"").decode("ascii")
    chunks = [data[i : i + KITTY_CHUNK] for i in range(0, len(data), KITTY_CHUNK)] or [""]
    out = []
    for index, chunk in enumerate(chunks):
        more = int(index < len(chunks) - 1)
        if index == 0:
            out.append(_apc(f"a=t,f=100,t=d,i={picture.id},q=2,m={more}", chunk))
        else:
            out.append(_apc(f"m={more},q=2", chunk))
    return "".join(out)


def kitty_place(picture: Picture, x: int, y: int) -> str:
    """Show *picture* with its top left at cell *x*, *y*, scaled to its cells.

    ``C=1`` leaves the cursor where it was.  Placing it again moves it."""
    return (
        f"\x1b[{y + 1};{x + 1}H"
        + _apc(f"a=p,i={picture.id},p=1,c={picture.cols},r={picture.rows},C=1,q=2")
    )


def kitty_hide(picture_id: int) -> str:
    """Take *picture_id*'s placement off the screen, keeping its data."""
    return _apc(f"a=d,d=i,i={picture_id},q=2")


def kitty_free(picture_id: int) -> str:
    """Take *picture_id* off the screen and out of the terminal's memory."""
    return _apc(f"a=d,d=I,i={picture_id},q=2")


#: Every placement off the screen, the data kept.
KITTY_HIDE_ALL = _apc("a=d,d=a,q=2")
#: Every placement off the screen and every picture out of memory.
KITTY_FREE_ALL = _apc("a=d,d=A,q=2")


# -- sixel ---------------------------------------------------------------------

_tables: dict[tuple[int, int], bytes] = {}


def _table(index: int, bit: int) -> bytes:
    """A translation sending colour *index* to ``1 << bit``, anything else to 0."""
    table = _tables.get((index, bit))
    if table is None:
        raw = bytearray(256)
        raw[index] = 1 << bit
        table = _tables[(index, bit)] = bytes(raw)
    return table


_RUN = re.compile(rb"(.)\1{3,}", re.DOTALL)


def _rle(data: bytes) -> bytes:
    return _RUN.sub(lambda m: b"!%d%c" % (len(m[0]), m[1][0]), data)


def sixel_encode(
    pixels: bytes,
    width: int,
    height: int,
    palette: list[tuple[int, int, int]],
    transparent: int | None = None,
) -> str:
    """A ``DCS q ... ST`` sixel image of *pixels*: one palette index a pixel,
    row after row, *width* wide.

    *palette* is at most 256 ``(r, g, b)`` triples; a pixel of colour
    *transparent* is left unset, which the background shows through
    (``P2 = 1``).  Each band of six rows is written a colour at a time: the
    six rows are mapped to that colour's bit by ``bytes.translate`` and
    summed as integers -- the bits never meet, so a sum is an OR -- which
    keeps the per-pixel work in C.
    """
    out = [f'\x1bP0;1;0q"1;1;{width};{height}']
    for index, (r, g, b) in enumerate(palette):
        out.append(f"#{index};2;{r * 100 // 255};{g * 100 // 255};{b * 100 // 255}")
    head = "".join(out).encode("ascii")
    offset = int.from_bytes(b"\x3f" * width, "big")
    bands: list[bytes] = []
    for top in range(0, height, 6):
        rows = [pixels[(top + r) * width : (top + r + 1) * width] for r in range(min(6, height - top))]
        present = set().union(*(set(row) for row in rows))
        present.discard(transparent)  # type: ignore[arg-type]
        lines = []
        for colour in sorted(present):
            total = offset
            for bit, row in enumerate(rows):
                total += int.from_bytes(row.translate(_table(colour, bit)), "big")
            sixels = total.to_bytes(width, "big").rstrip(b"?")
            lines.append(b"#%d" % colour + _rle(sixels))
        bands.append(b"$".join(lines))
    return (head + b"-".join(bands) + b"\x1b\\").decode("ascii")


# -- the frame ---------------------------------------------------------------


class GraphicsLayer:
    """What pictures the terminal shows, and the escapes that change that.

    The application keeps one and calls :meth:`compose` every frame, between
    composing it and diffing it: whatever has to go before the diff (a
    picture taken away, so the cells written next are not drawn under it) is
    returned first, and what goes after it (a picture written over the cells
    the diff has just blanked) second.
    """

    def __init__(self) -> None:
        #: id -> (x, y) of every picture on the screen, and what it is.
        self._shown: dict[int, tuple[int, int, Picture]] = {}
        #: kitty ids whose data the terminal holds.
        self._sent: set[int] = set()

    @property
    def shown(self) -> dict[int, tuple[int, int]]:
        """Each picture on the screen, by id, at its top left cell."""
        return {pid: (x, y) for pid, (x, y, _) in self._shown.items()}

    def forget(self) -> None:
        """The terminal has dropped everything -- the alternate screen was
        left, or the protocol changed -- so nothing is shown or held."""
        self._shown.clear()
        self._sent.clear()

    def release(self, protocol: str) -> str:
        """What to write before the terminal is lent out, which forgets all."""
        out = KITTY_FREE_ALL if protocol == "kitty" and (self._sent or self._shown) else ""
        self.forget()
        return out

    def compose(self, placements, shown, front, protocol: str) -> tuple[str, str]:
        """The escapes before and after this frame's diff.

        *placements* is the frame's ``{id: (picture, y)}``
        (:attr:`ScreenBuffer.placements`), *shown* the buffer as it goes to
        the terminal -- where each picture's stamps are looked for -- and
        *front* what the terminal shows now, or None for a full repaint.  A
        sixel picture that goes has its cells in *front* invalidated, so the
        diff writes them again over its pixels.
        """
        full = front is None or front.width != shown.width or front.height != shown.height
        visible: dict[int, tuple[int, int, Picture]] = {}
        if protocol:
            for pid, (picture, y) in placements.items():
                x = _find(shown, pid, picture, y, room=protocol == "sixel")
                if x is not None and picture.drawable(protocol):
                    visible[pid] = (x, y, picture)

        before: list[str] = []
        after: list[str] = []
        if protocol == "kitty":
            if full and self._shown:
                before.append(KITTY_HIDE_ALL)
                self._shown.clear()
            for pid, (x, y, _) in self._shown.items():
                if visible.get(pid, (None, None))[:2] != (x, y):
                    before.append(kitty_hide(pid))
            for pid in sorted(self._sent - placements.keys()):
                before.append(kitty_free(pid))
                self._sent.discard(pid)
            for pid, (x, y, picture) in visible.items():
                if pid not in self._sent:
                    after.append(kitty_transmit(picture))
                    self._sent.add(pid)
                if full or self._shown.get(pid, (None, None))[:2] != (x, y):
                    after.append(kitty_place(picture, x, y))
        elif protocol == "sixel":
            for pid, (x, y, picture) in self._shown.items():
                if front is not None and not full and visible.get(pid, (None, None))[:2] != (x, y):
                    front.invalidate(x, y, picture.cols, picture.rows)
            for pid, (x, y, picture) in visible.items():
                if full or self._shown.get(pid, (None, None))[:2] != (x, y):
                    after.append(f"\x1b[{y + 1};{x + 1}H" + (picture.sixel or ""))
        self._shown = visible
        return "".join(before), "".join(after)


def _find(buffer, pid: int, picture: Picture, y: int, *, room: bool) -> int | None:
    """The column *picture*'s stamps start at in *buffer*, if every one of
    them is there, whole and rectangular -- or None.

    *room* asks for a row beneath it: a sixel picture reaching the last line
    scrolls the screen on some terminals.
    """
    bottom = y + picture.rows
    if y < 0 or bottom > buffer.height - (1 if room else 0):
        return None
    row = buffer._rows[y]
    x = next((i for i, (_, style) in enumerate(row) if style.image == pid), None)
    if x is None or x + picture.cols > buffer.width:
        return None
    for line in range(y, bottom):
        cells = buffer._rows[line][x : x + picture.cols]
        if any(style.image != pid for _, style in cells):
            return None
    return x
