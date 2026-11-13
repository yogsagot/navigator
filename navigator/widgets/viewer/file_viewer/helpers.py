"""What the FileViewer's mixins share: module-level helpers of
:mod:`navigator.widgets.viewer.file_viewer.file_viewer`, which re-exports the public ones.
"""

from __future__ import annotations

import functools
import threading
from typing import Any

from navkit.bidi import order_cells

from navml.background import Background

from navigator.lib import highlight
from navigator.lib.viewer import image, markdown, pdf, rst
from navigator.lib.viewer.layout import Layout
from navigator.lib.viewer import NotYet


#: The three modes F4 cycles through, in DN's order.
MODES = ("text", "hex", "dump")

#: How many rows one wheel notch moves.
WHEEL_ROWS = 3

#: How far Ctrl+Left and Ctrl+Right move text sideways.
BIG_STEP = 20

#: How many columns of each row on screen the bottom scroll bar measures,
#: at least (``FileViewer.row_span``).
SPAN_LOOK = 4096

#: The thread syntax highlighting lexes on.
_LEXER = Background("nav-view-lex", workers=1)

#: How far before the top the lexing starts, and how far past it it goes:
#: a file this size or less is lexed whole, from its start, and coloured
#: exactly; further into a bigger one, a comment or string opened more than
#: ``LEX_BACK`` above the window is not known to be open.
LEX_BACK = 256 * 1024
LEX_AHEAD = 256 * 1024
#: The same for a file read across a network (``ChunkedSource``), where
#: every 64 KiB is a round trip: two chunks each way.
REMOTE_LEX_BACK = 128 * 1024
REMOTE_LEX_AHEAD = 128 * 1024

#: How much of the file's start is read for its ``#!`` line.
HEAD = 256

#: The thread a Markdown, reStructuredText, HTML or PDF file is read and laid out on.
_RENDERER = Background("nav-view-render", workers=1)

#: How each format a file can be rendered as is laid out.
RENDERERS = {"markdown": markdown.render, "rst": rst.render, "html": None, "pdf": pdf.render}


def _renderer(format: str) -> Any:
    """*format*'s renderer.  HTML's is imported on first use: ``html.parser``
    is a few milliseconds of every start, the quick view being in the
    file manager's markup whether or not it is ever shown."""
    found = RENDERERS[format]
    if found is None:
        from navigator.lib.viewer import html

        found = RENDERERS[format] = html.render
    return found


def _when_here(method: Any) -> Any:
    """For a file read across a network (``ChunkedSource``): a move that
    needs a chunk not here yet does nothing now and is done again, as it was
    asked, once the chunk lands.  Every method this wraps reads before it
    changes anything, so doing it again is doing it once."""
    @functools.wraps(method)
    def call(self: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return method(self, *args, **kwargs)
        except NotYet:
            self._again = lambda: call(self, *args, **kwargs)
            return None
    return call


def _lex_window(name: str, file_type: str, data: bytes | None, low: int, high: int,
                size: int, codec: str, stop: threading.Event, read: Any = None) -> Any:
    """On the thread: the lexer's name ("" for none) and the spans of the whole
    lines in ``[low, high)`` of the file, as ``(start, end, spans)`` -- False when
    it has no lexer, None when stopped.  *data* is the whole file when the viewer holds it (``/proc``);
    *read(offset, count)* reads a file on another drive, waiting (``ChunkedSource.read_blocking``);
    else it is read here."""
    if read is not None:
        head, window = read(0, HEAD), read(low, high - low)
    elif data is None:
        with open(name, "rb") as stream:
            head = stream.read(HEAD)
            stream.seek(low)
            window = stream.read(high - low)
    else:
        head, window = data[:HEAD], data[low:high]
    first = head.split(b"\n", 1)[0].decode("utf-8", errors="replace")
    lexer = highlight.lexer_for(name, first, file_type=file_type)
    if lexer is None:
        return "", False
    start, end = low, low + len(window)
    if low > 0:
        # From the first whole line: a lexer starts in its root state.
        cut = window.find(b"\n")
        if cut >= 0:
            window, start = window[cut + 1:], low + cut + 1
    if end < size:
        cut = window.rfind(b"\n")
        if cut >= 0:
            window, end = window[:cut + 1], start + cut + 1
    spans = highlight.lex_bytes(lexer, window, start, codec, stop)
    return highlight.lexer_label(lexer), None if spans is None else (start, end, spans)


def _lay_out(name: str, data: bytes | None, size: int, codec: str, width: int, unicode: bool,
             read: Any = None, format: str = "markdown") -> Layout:
    """On the thread: the whole file read -- held already (*data*), across a
    network (*read*), or here -- and laid out in *format*, *width* wide."""
    if read is not None:
        data = read(0, size)
    elif data is None:
        with open(name, "rb") as stream:
            data = stream.read(size)
    return _renderer(format)(data[:size], width, codec=codec, unicode=unicode)


def _picture(name: str, data: bytes | None, size: int, cols: int, rows: int,
             cell_px: tuple[int, int] | None, protocol: str, read: Any = None) -> image.Shown:
    """On the thread: the whole file read, as :func:`_lay_out` reads it, and
    made a picture *cols* x *rows* cells at most (:func:`navigator.lib.viewer.image.decode`)."""
    if read is not None:
        data = read(0, size)
    elif data is None:
        with open(name, "rb") as stream:
            data = stream.read(size)
    return image.decode(data[:size], cols, rows, cell_px, protocol)



def _laid_row(row: Any, width: int) -> tuple[list, list]:
    """A rendered *row*'s cells as painted, and the cell each came from (None
    for padding): Hebrew and Arabic in reading order, and a right-to-left
    paragraph's row -- after its gutter or bullet -- set against the right
    edge of *width*."""
    cells = row.cells
    if not row.rtl:
        order = order_cells([cell[0] for cell in cells])
        if order is None:
            return cells, list(range(len(cells)))
        return [(shown, *cells[column][1:]) for column, shown in order], [column for column, _ in order]
    lead, body = cells[: row.lead], cells[row.lead:]
    order = order_cells([cell[0] for cell in body], True, detect=False)
    picked = list(range(len(body))) if order is None else [column for column, _ in order]
    laid = body if order is None else [(shown, *body[column][1:]) for column, shown in order]
    pad = max(0, width - len(lead) - len(laid))
    blank = (" ", body[0][1] if body else (), None)
    return ([*lead, *[blank] * pad, *laid],
            [*range(len(lead)), *[None] * pad, *(row.lead + column for column in picked)])
