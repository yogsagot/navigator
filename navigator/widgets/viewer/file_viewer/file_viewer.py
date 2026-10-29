"""F3's view: DOS Navigator's ``TFileViewer``, painting what ``navigator.lib.viewer`` reads.

**Written in Python alone**, because everything it shows is painted -- rows of
a file, in one of three modes -- and it declares nothing a document would place.
The window around it, ``FileWindow``, is the one with a markup half.

**Its state is a handful of numbers.**  ``top`` is the byte offset of the first
row shown, ``x_delta`` how far the text is scrolled sideways, ``cursor`` the
byte the hex cursor is on; ``mode``, ``wrap`` and ``filter`` are the three
switches the key bar flips.  Every one is reactive, so a key handler assigns
one and the frame follows -- nothing here paints on demand.  The rows are not
state: they are read from the source on every render, which costs one
``line()`` per visible row and is what lets ``top`` be a plain offset.

The keys are ``FVIEWER.PAS``'s ``HandleEvent``, and they differ between text and
the two hex modes the way they did there: in text the arrows move the *view*,
in hex they move a *cursor* and the view follows it.
"""

from __future__ import annotations

import bisect
import fnmatch
import functools
import threading
import unicodedata
from pathlib import Path
from typing import Any

from navkit.bidi import display_width, has_rtl, order_cells, text_rtl
from navkit.events import KeyEvent, MouseClickEvent
from navkit.glyphs import GLYPHS_UNICODE
from navkit.i18n import tr, tr_n
from navkit.reactive import computed, reactive
from navkit.screen import Surface
from navkit.widget import Widget
from navml.background import Background, Outcome
from navml.commands import CloseWindow
from navml.widgets.menu.context_menu import ContextMenu, ContextMenuHost

from navigator.lib import highlight
from navigator.widgets.viewer.commands import (
    AddFilter,
    ChooseEncoding,
    ContinueSearch,
    GotoAddress,
    HexMode,
    SearchFor,
    SetViewMode,
    SwitchRendered,
    Unwrap,
)
from navigator.settings import SETTINGS
from navigator.lib.viewer import html, markdown, pdf, rst
from navigator.lib.viewer.layout import RENDER_LIMIT, Layout, decode
from navigator.lib.viewer import (
    DUMP_CHARS_AT,
    WHOLE_LINE,
    FILTER_TAGS,
    HEX_PAIRS_AT,
    HIDDEN_MARKS,
    ViewSource,
    byte_table,
    cp437,
    ENCODINGS,
    dump_row,
    dump_row_bytes,
    group_digits,
    hex_chars_at,
    hex_row,
    hex_row_bytes,
    NotYet,
)

#: The three modes F4 cycles through, in DN's order.
MODES = ("text", "hex", "dump")

#: How many rows one wheel notch moves.
WHEEL_ROWS = 3

#: How far Ctrl+Left and Ctrl+Right move text sideways.
BIG_STEP = 20

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
RENDERERS = {"markdown": markdown.render, "rst": rst.render, "html": html.render, "pdf": pdf.render}


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
    return RENDERERS[format](data[:size], width, codec=codec, unicode=unicode)



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

class FileViewer(ContextMenuHost, Widget):
    """The inside of a viewer window: a file's rows, and the keys that move them."""

    #: Kept left to right on a right-to-left screen (``Widget.mirrors``):
    #: the file's own text, laid out left to right line by line.
    mirrors = False

    #: A search hit, drawn in *Selected text* [118]; a syntax token
    #: (:mod:`navigator.lib.highlight`), by its classes.
    #: A Markdown or HTML file's rendering, by what its cells are (``heading``,
    #: ``code``, ``link`` and the rest: :mod:`navigator.lib.viewer.layout`).
    parts = ("selected", "token", "md")

    #: The file, once :meth:`open` has read it.  Reactive so that the window's
    #: title can follow it; assigned only by :meth:`open`.
    path: Path | None = reactive(None)

    #: How many bytes the file had when it was opened.
    size: int = reactive(0)

    mode: str = reactive("text")
    wrap: bool = reactive(False)
    filter: int = reactive(0)
    #: File > Encoding: the code page the bytes are read in, one of
    #: ``viewer.ENCODINGS``'s; ``utf-8`` is DN's viewer with no ``XLT`` loaded.
    encoding: str = reactive("utf-8")

    #: The offset of the first row shown.
    top: int = reactive(0)

    #: Columns the text is scrolled to the left, in text mode.
    x_delta: int = reactive(0)

    #: The byte the hex cursor is on, in hex mode.
    cursor: int = reactive(0)

    #: The last search's hit, as ``(offset, length)``, drawn until the next.
    hit: tuple[int, int] | None = reactive(None)

    #: Text coloured by syntax, as ``highlight.ini`` says: a departure, DN's
    #: viewer had none.  Seeded from the setting, switched by View.
    syntax_highlight: bool = reactive(True)
    #: View > *File type*: the lexer chosen, ``none``, or empty for
    #: ``highlight.ini``'s choice (:func:`navigator.lib.highlight.lexer_for`).
    file_type: str = reactive("")
    #: Spaces, tabs and each line's ending drawn faintly in text mode: a
    #: departure, as the editor's.  Seeded from ``[viewer] show_hidden``.
    show_hidden: bool = reactive(False)
    #: The name of the lexer colouring the text, "" for none, None until the
    #: lexing thread has said: what the option strip shows as the file type.
    lexer_name: str | None = reactive(None)
    #: View > *Markup view*: a Markdown, reST, HTML or PDF file rendered rather than its
    #: source, in text mode -- a departure.  Seeded by :meth:`open` from
    #: ``[viewer]``'s ``render_markdown``/``markdown_masks`` and
    #: ``render_html``/``html_masks``.
    rendered: bool = reactive(False)
    #: The rendered row on top, while rendering; ``top`` follows it, at the
    #: offset of the source line that row's block starts on.
    render_row: int = reactive(0)
    #: The file laid out, for the width it was asked at; None until the
    #: thread has done it.
    render_layout: Any = reactive(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source: ViewSource | None = None
        self._again: Any = None
        self.syntax_highlight = SETTINGS.viewer.syntax_highlight
        self.show_hidden = SETTINGS.viewer.show_hidden
        self.rehighlight()
        self._forget_layout()
        # In __init__, not the class body: a plain class attribute would
        # shadow the reactive descriptor, as `Console` learned.
        self.can_focus = True

    def open(self, path: Path | str, *, source: ViewSource | None = None) -> None:
        """Show *path* from its start.  Raises ``OSError`` if it cannot be read.

        Given the *source*, opened already on a thread, nothing is read here.
        A ``ChunkedSource`` -- a file on another drive -- says when a chunk
        lands, and the viewer paints again and does what it had to leave.
        """
        if source is None:
            source = ViewSource(path)
        if self.source is not None:
            self.source.close()
        self.source = source
        #: What a missing chunk interrupted, to do once it is in.
        self._again: Any = None
        if getattr(source, "remote", False):
            source.arrived = self._chunk_arrived
        source.table = byte_table(self.encoding)
        self.rehighlight()
        self._forget_layout()
        self.rendered = bool(self.format_by_name(source.path))
        self.path = source.path
        self.size = source.size
        self.top = self.x_delta = self.cursor = self.render_row = 0
        self.hit = None

    def close_file(self) -> None:
        """Show nothing: what a quick view shows for a directory."""
        if self.source is not None:
            self.source.close()
        self.source = None
        self.rehighlight()
        self._forget_layout()
        self.path = None
        self.size = 0
        self.top = self.x_delta = self.cursor = self.render_row = 0
        self.hit = None

    def _chunk_arrived(self) -> None:
        """On the fetching thread: tell the loop."""
        app = self.application
        if app is not None and app.is_running:
            app.call_from_thread(self._chunk_landed)

    def _chunk_landed(self) -> None:
        again, self._again = self._again, None
        if again is not None:
            again()
        self.invalidate()

    @property
    def remote(self) -> bool:
        """Whether the file is read across a network, a chunk at a time."""
        return bool(getattr(self.source, "remote", False))

    def unmounting(self) -> None:
        # Let the file go with the window.  A read reopens it, so a viewer
        # that is put back somewhere still works.
        super().unmounting()
        if self.source is not None:
            self.source.close()

    # -- geometry of the modes -------------------------------------------------

    @property
    def wrap_width(self) -> int | None:
        """The width rows are wrapped at, or ``None`` when they are not."""
        return max(1, self.width) if self.wrap and self.mode == "text" else None

    def row_bytes(self) -> int:
        """How many bytes one hex or dump row shows."""
        if self.mode == "dump":
            return dump_row_bytes(self.width)
        return hex_row_bytes(self.width)

    def _text_rows(self, count: int, max_cols: int | None = None):
        """The first *count* text rows from ``top``, fewer at the end of the file."""
        rows, offset = [], self.top
        source = self.source
        if source is None:
            return rows
        for _ in range(count):
            row = source.line(offset, self.wrap_width, filter=self.filter,
                              max_cols=max_cols)
            if row is None:
                break
            rows.append(row)
            offset = row.next
        return rows

    def _last_top(self) -> int:
        """The furthest ``top`` may go: the last row on the last screen row."""
        if self.source is None:
            return 0
        if self.mode == "text":
            return self.source.last_page_top(self.height, self.wrap_width)
        per = self.row_bytes()
        if self.size == 0:
            return 0
        # Keep the phase ``top`` has, so Ctrl+Left's shift survives the end.
        phase = self.top % per
        last_row = self.size - 1 - (self.size - 1 - phase) % per
        return max(min(phase, self.top), last_row - (max(1, self.height) - 1) * per)

    # -- the info line ----------------------------------------------------------

    @computed
    def info_text(self) -> str:
        """DN's ``TViewInfo``: ``[<=>][42% of 12,345 Bytes]{ASCII}``.

        In hex mode the percentage gives way to the cursor's offset and a
        ruler of the row's columns, as ``TViewInfo.Draw`` wrote it.
        """
        if self.mode == "hex":
            per = self.row_bytes()
            phase = self.top % per
            ruler = "─".join(f"{(i + phase) % 256:02X}" for i in range(per))
            text = f"[{self.cursor & 0xFFFFFFFF:08X} {ruler}"
        else:
            text = "[>=<][" if self.wrap else "[<=>]["
            text += tr("{percent}% of {size} Bytes").format(percent=self.percent(), size=group_digits(self.size))
        tag = "" if self.encoding == "utf-8" else "{" + dict(ENCODINGS)[self.encoding].split()[0] + "}"
        return text + "]" + FILTER_TAGS[self.filter] + tag

    @computed
    def render_mark(self) -> str:
        """``{Markdown}`` or ``{HTML}`` after the info line, which a click
        switches: while *Markup view* is on, and -- struck through by the
        window -- while it is off for a file the masks name.  Empty where it
        cannot render."""
        if self.mode != "text" or not self.can_render:
            return ""
        if self.rendered or self.format_by_name(self.path):
            return "{" + self.format_label() + "}"
        return ""

    def percent(self) -> int:
        """How far into the file the view is: 100 once the end is showing."""
        layout = self.render_layout if self.rendering else None
        if layout is not None:
            last = self._render_last_row()
            return 100 if self.render_row >= last else self.render_row * 100 // max(1, len(layout.rows))
        try:
            if self.size == 0 or self._end_showing():
                return 100
        except NotYet:
            pass  # the end's rows not here yet: by the offset, then
        return self.top * 100 // self.size

    def _end_showing(self) -> bool:
        if self.mode == "text":
            rows = self._text_rows(self.height, max_cols=1)
            return len(rows) < self.height or (bool(rows) and rows[-1].next >= self.size)
        return self.top + self.height * self.row_bytes() >= self.size

    # -- moving ----------------------------------------------------------------

    @_when_here
    def seek(self, offset: int) -> None:
        """Show the row holding *offset* at the top, as far as the end allows.

        What the scroll bar and a goto both call: DN's ``Seek`` followed by
        the ``CountUp`` that snaps it to a line start.
        """
        if self.source is None:
            return
        offset = max(0, min(offset, self.size))
        if self.rendering:
            self._render_go(self.render_layout.row_for(offset))
            return
        if self.mode == "text":
            self.top = min(self.source.line_start(offset, self.wrap_width), self._last_top())
            return
        per = self.row_bytes()
        self.top = max(0, offset - (offset - self.top) % per)
        self.top = min(self.top, max(0, self._last_top()))
        self._keep_cursor()

    @_when_here
    def scroll_rows(self, count: int) -> None:
        """Move the view *count* rows, down for positive; the ends stop it."""
        if self.source is None:
            return
        if self.rendering:
            self._render_go(self.render_row + count)
            return
        if self.mode != "text":
            per = self.row_bytes()
            top = self.top + count * per
            if top < 0:
                top = self.top % per
            self.top = max(0, min(top, self._last_top()))
            self._keep_cursor()
            return
        width = self.wrap_width
        top = self.top
        if count < 0:
            for _ in range(-count):
                if top <= 0:
                    break
                top = self.source.prev_line_start(top, width)
        else:
            last = self._last_top()
            for _ in range(count):
                if top >= last:
                    break
                row = self.source.line(top, width, max_cols=1)
                if row is None:
                    break
                top = row.next
        self.top = top

    def to_start(self) -> None:
        self.top = self.x_delta = self.render_row = 0
        self.cursor = 0

    @_when_here
    def to_end(self) -> None:
        """DN's ``SeekEOF``: the last screenful."""
        if self.rendering:
            self._render_go(self._render_last_row())
        elif self.mode == "text":
            self.top = self._last_top()
        else:
            self.top = self._last_top()
            self.cursor = max(0, self.size - 1)

    def _keep_cursor(self) -> None:
        """Pull the hex cursor back into the rows that show."""
        if self.size == 0:
            self.cursor = 0
            return
        last = min(self.size - 1, self.top + self.height * self.row_bytes() - 1)
        self.cursor = min(max(self.cursor, self.top), max(self.top, last))

    def move_cursor(self, delta: int) -> None:
        """Move the hex cursor *delta* bytes, and the view after it."""
        if self.size == 0:
            return
        cursor = min(max(self.cursor + delta, 0), self.size - 1)
        self.cursor = cursor
        self.follow_cursor()

    def follow_cursor(self) -> None:
        """Scroll whole rows until the hex cursor is on screen."""
        per = self.row_bytes()
        rows = max(1, self.height)
        top = self.top
        if self.cursor < top:
            top -= -(-(top - self.cursor) // per) * per
        elif self.cursor >= top + rows * per:
            top += ((self.cursor - top) // per - rows + 1) * per
        self.top = max(0, top)

    def cycle_mode(self) -> None:
        """F4: text, hex, dump."""
        self.set_mode(MODES[(MODES.index(self.mode) + 1) % len(MODES)])

    def set_mode(self, mode: str) -> None:
        """Show the file in *mode*.  The offset shown on top stays on top."""
        if mode not in MODES:
            raise ValueError(f"{mode!r} is not a viewer mode; they are {', '.join(MODES)}")
        if mode == self.mode:
            return
        offset = self.top
        self.mode = mode
        if mode == "hex":
            # DN's cursor starts where the view does.
            self.cursor = offset
        elif mode == "text":
            self.x_delta = 0
            self.seek(offset)

    def toggle_wrap(self) -> None:
        """F2.  The row on top stays on top, cut where the new width cuts it."""
        self.wrap = not self.wrap
        self.x_delta = 0
        self._snap_top()

    @_when_here
    def _snap_top(self, clamp: bool = False) -> None:
        """``top`` back on the start of the row holding it, in the widths in
        force -- and, *clamp*, no further than the last screenful."""
        if self.source is not None and self.mode == "text":
            top = self.source.line_start(self.top, self.wrap_width)
            self.top = min(top, self._last_top()) if clamp else top

    def cycle_filter(self) -> None:
        """F6: no filter, ``{ASCII}``, ``{Printable}``."""
        self.set_filter((self.filter + 1) % len(FILTER_TAGS))

    def set_encoding(self, codec: str) -> None:
        """Read the file in *codec* from now on: ``SetXlatFile``.  The row at
        the top stays the row at the top, found again in the new widths."""
        if codec not in dict(ENCODINGS):
            raise ValueError(f"{codec} is not one of the viewer's encodings")
        self.encoding = codec
        if self.source is not None:
            self.source.table = byte_table(codec)
            self._snap_top(clamp=True)
        self.invalidate()

    def set_filter(self, filter: int) -> None:
        if not 0 <= filter < len(FILTER_TAGS):
            raise ValueError(f"{filter} is not a viewer filter; there are {len(FILTER_TAGS)}")
        self.filter = filter

    # -- Markup view: Markdown, reST, HTML and PDF rendered ---------------------

    @staticmethod
    def format_by_name(path: Path | str | None) -> str:
        """The format *path* is rendered in when it opens -- ``pdf``,
        ``html``, ``rst`` or ``markdown`` -- or "" for none: its name one of
        ``[viewer]``'s ``pdf_masks``, ``html_masks``, ``rst_masks`` or
        ``markdown_masks``, that format's switch on."""
        if path is None:
            return ""
        settings = SETTINGS.viewer
        name = Path(path).name.lower()
        for format, on, masks in (("pdf", settings.render_pdf, settings.pdf_masks),
                                  ("html", settings.render_html, settings.html_masks),
                                  ("rst", settings.render_rst, settings.rst_masks),
                                  ("markdown", settings.render_markdown, settings.markdown_masks)):
            if on and any(fnmatch.fnmatchcase(name, mask.strip().lower())
                          for mask in masks.split(";") if mask.strip()):
                return format
        return ""

    def format_label(self) -> str:
        """What the mark calls the format: *PDF*, *HTML*, *reST*, *Markdown*."""
        format = self.render_format
        if format == "pdf":
            return tr("PDF")
        if format == "html":
            return tr("HTML")
        if format == "rst":
            return tr("reST")
        return tr("Markdown")

    @computed
    def render_format(self) -> str:
        """What the file is rendered as: the format its name says, else
        Markdown -- switched on for any other text, it is read as Markdown."""
        return self.format_by_name(self.path) or "markdown"

    @property
    def can_render(self) -> bool:
        """Whether this file can be rendered at all: no bigger than
        ``RENDER_LIMIT`` (a PDF, ``PDF_LIMIT``), since it is read and parsed whole."""
        limit = pdf.PDF_LIMIT if self.render_format == "pdf" else RENDER_LIMIT
        return self.source is not None and self.size <= limit

    @property
    def rendering(self) -> bool:
        """Whether the rows painted are the rendering's: text mode, *Markup
        view* on, and the layout in."""
        return self.mode == "text" and self.rendered and self.render_layout is not None and self.can_render

    def toggle_rendered(self) -> None:
        """View > *Markup view*.  The block on top stays on top: the rendering
        starts at the source line on top, the source at the block's line."""
        self.rendered = not self.rendered
        self.hit = None
        if self.rendering:
            self._render_go(self.render_layout.row_for(self.top))
        elif self.mode == "text":
            self.x_delta = 0
            self.seek(self.top)

    def _forget_layout(self) -> None:
        stop = getattr(self, "_render_stop", None)
        if stop is not None:
            stop.set()
        #: What the layout was asked for -- where, encoding, size, width, glyphs --
        #: and what it was made for: never asked twice, so a failure cannot loop.
        self._render_asked: Any = None
        self._render_for: Any = None
        self._render_stop: threading.Event | None = None
        if self.render_layout is not None:
            self.render_layout = None

    def _render_last_row(self) -> int:
        layout = self.render_layout
        return max(0, len(layout.rows) - max(1, self.height)) if layout is not None else 0

    def _render_go(self, row: int) -> None:
        """The rendered row *row* on top, as far as the ends allow, and ``top`` at its line."""
        layout = self.render_layout
        row = max(0, min(row, self._render_last_row()))
        self.render_row = row
        self.top = layout.rows[row].src if layout.rows else 0

    def _want_layout(self) -> None:
        """Ask the thread for a layout at the width and glyphs in force, unless
        one is in or on its way.  Until it lands, the one there is painted --
        or the source, the first time."""
        source = self.source
        if source is None or not self.rendered or self.mode != "text" or not self.can_render:
            return
        remote = self.remote
        unicode = self.glyphs >= GLYPHS_UNICODE
        where = str(source.origin) if remote else str(source.path)
        format = self.render_format
        key = (where, self.encoding, self.size, max(1, self.width), unicode, format)
        if key in (self._render_for, self._render_asked):
            return
        self._render_asked = key
        stop = threading.Event()
        self._render_stop = stop
        _RENDERER.run(self, _lay_out, str(source.path), source._data, self.size, self.encoding,
                      max(1, self.width), unicode, source.read_blocking if remote else None, format,
                      done=lambda outcome: self._laid_out(outcome, key, stop))

    def _laid_out(self, outcome: Outcome, key: Any, stop: threading.Event) -> None:
        if stop is not self._render_stop or stop.is_set():
            return  # another file, or forgotten meanwhile
        self._render_stop = None
        try:
            layout = outcome.result()
        except Exception:
            # Unreadable now, or text the parser cannot take: the source.
            self._render_for = key
            return
        self._render_for = key
        rendering = self.rendering
        self.render_layout = layout
        if self.mode == "text" and self.rendered:
            if not rendering:
                self.hit = None
            self._render_go(layout.row_for(self.top))

    @_when_here
    def _whole(self, row, limit: int) -> tuple:
        """*row*'s cells, all of them when right-to-left text in it was cut at
        *limit*: what is painted at the left of a reordered line can come from
        its far end, which the screen-sized decoding stopped short of."""
        cells = row.cells
        if self.wrap_width is not None or len(cells) < limit or self.source is None:
            return cells
        if not has_rtl("".join(char for char, _ in cells)):
            return cells
        whole = self.source.line(row.start, None, filter=self.filter, max_cols=WHOLE_LINE)
        return whole.cells if whole is not None else cells

    def _ordered(self, cells, row, paragraphs: dict[int, bool]) -> list | None:
        """*row*'s cells in reading order (:func:`navkit.bidi.order_cells`),
        or None; *paragraphs* caches each wrapped line's direction by its start."""
        chars = [char for char, _ in cells]
        width = self.wrap_width
        if width is None or self.source is None:
            return order_cells(chars)
        start = self.source.line_start(row.start, None)
        rtl = paragraphs.get(start)
        if rtl is None:
            rtl = paragraphs[start] = self._line_rtl(start, row, chars)
        return order_cells(chars, rtl, detect=False)

    def _line_rtl(self, start: int, row, chars: list[str]) -> bool:
        """Whether the line starting at *start* reads right to left: its first
        strong letter's direction, read row by row up to *row* at most."""
        offset = start
        while offset < row.start:
            piece = self.source.line(offset, self.wrap_width, filter=self.filter)
            if piece is None or piece.next <= offset:
                break
            text = "".join(char for char, _ in piece.cells)
            if any(unicodedata.bidirectional(char) in ("L", "R", "AL") for char in text):
                return text_rtl(text)
            offset = piece.next
        return text_rtl("".join(chars))

    def show_hit(self, offset: int, length: int) -> None:
        """Put a search hit on screen and mark it.

        DN's ``ContinueSearch``: the hit's row goes to the top unless it is
        already showing, and sideways the text is scrolled to centre it when
        it is off the edge.
        """
        self.hit = (offset, length)
        if self.source is None:
            return
        if self.rendering:
            row = self.render_layout.row_for(offset)
            if not self.render_row <= row < self.render_row + max(1, self.height):
                self._render_go(row)
            return
        if self.mode != "text":
            self.cursor = offset
            per = self.row_bytes()
            if not self.top <= offset < self.top + self.height * per:
                self.top = max(0, offset - (offset - self.top) % per)
            return
        rows = self._text_rows(self.height, max_cols=1)
        if not any(r.start <= offset < r.next for r in rows):
            self.top = self.source.line_start(offset, self.wrap_width)
        if self.wrap_width is None:
            row = self.source.line(self.source.line_start(offset), None,
                                   filter=self.filter, max_cols=WHOLE_LINE)
            column = 0
            if row:
                cells = row.cells
                start = next((i for i, (_, at) in enumerate(cells) if at >= offset), 0)
                order = order_cells([char for char, _ in cells])
                if order is not None and start < len(cells):
                    # The hit's first column where reordering painted it.
                    column = next((x for x, (at, _) in enumerate(order) if at == start), start)
                else:
                    column = start
            if not self.x_delta <= column < self.x_delta + self.width:
                self.x_delta = max(0, column - self.width // 2)

    # -- keys ------------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        if self.source is None:
            return False
        name = event.name
        rows = max(1, self.height - 1)
        if name in ("ctrl+pageup",):
            self.to_start()
        elif name in ("ctrl+pagedown",):
            self.to_end()
        elif self.rendering:
            return self._rendered_key(name, rows)
        elif self.mode == "text":
            return self._text_key(name, rows)
        else:
            return self._hex_key(name, rows)
        return True

    def _text_key(self, name: str, rows: int) -> bool:
        if name == "up":
            self.scroll_rows(-1)
        elif name == "down":
            self.scroll_rows(1)
        elif name == "pageup":
            self.scroll_rows(-rows)
        elif name == "pagedown":
            self.scroll_rows(rows)
        elif name == "ctrl+home":
            self.to_start()
        elif name == "ctrl+end":
            self.to_end()
        elif self.wrap and name in ("left", "right", "ctrl+left", "ctrl+right", "home", "end"):
            # Nothing is off the side of a wrapped row.
            pass
        elif name == "left":
            self.x_delta = max(0, self.x_delta - 1)
        elif name == "right":
            self.x_delta += 1
        elif name == "ctrl+left":
            self.x_delta = max(0, self.x_delta - BIG_STEP)
        elif name == "ctrl+right":
            self.x_delta += BIG_STEP
        elif name == "home":
            self.x_delta = 0
        elif name == "end":
            self._to_longest_end()
        else:
            return False
        return True

    def _rendered_key(self, name: str, rows: int) -> bool:
        """The rendering's keys: rows up and down; nothing is off its side."""
        moves = {"up": -1, "down": 1, "pageup": -rows, "pagedown": rows}
        if name in moves:
            self.scroll_rows(moves[name])
        elif name in ("ctrl+home", "home"):
            self.to_start()
        elif name in ("ctrl+end", "end"):
            self.to_end()
        elif name not in ("left", "right", "ctrl+left", "ctrl+right"):
            return False
        return True

    @_when_here
    def _to_longest_end(self) -> None:
        """CM_END: far enough to show the end of the longest row showing."""
        longest = max((len(r.cells) for r in self._text_rows(self.height)), default=0)
        self.x_delta = max(0, longest - self.width)

    def _hex_key(self, name: str, rows: int) -> bool:
        per = self.row_bytes()
        if name == "up":
            if self.cursor >= per:
                self.move_cursor(-per)
        elif name == "down":
            if self.cursor + per < self.size:
                self.move_cursor(per)
        elif name == "pageup":
            self.scroll_rows(-rows)
            if self.cursor >= rows * per:
                self.move_cursor(-rows * per)
            self._keep_cursor()
        elif name == "pagedown":
            self.scroll_rows(rows)
            self.move_cursor(rows * per)
            self._keep_cursor()
        elif name == "left":
            self.move_cursor(-1)
        elif name == "right":
            self.move_cursor(1)
        elif name == "ctrl+left":
            # Shift the rows' start by a byte, as DN's did.
            if self.top > 0:
                self.top -= 1
            self._keep_cursor()
        elif name == "ctrl+right":
            if self.top + 1 < self.size:
                self.top += 1
            self._keep_cursor()
        elif name == "home":
            self.cursor = self.cursor - (self.cursor - self.top) % per
        elif name == "end":
            self.cursor = min(self.size - 1, self.cursor - (self.cursor - self.top) % per + per - 1)
        elif name == "ctrl+home":
            self.cursor = self.top + (self.cursor - self.top) % per
        elif name == "ctrl+end":
            column = (self.cursor - self.top) % per
            last_row = self.top + (max(1, self.height) - 1) * per
            while last_row + column >= self.size and last_row > self.top:
                last_row -= per
            self.cursor = min(self.size - 1, last_row + column)
        else:
            return False
        return True

    # -- the mouse -------------------------------------------------------------

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        await super().on_mouse_click(event)
        if self.source is None:
            return False
        if event.is_wheel:
            if event.button in ("wheel_up", "wheel_down"):
                step = -WHEEL_ROWS if event.button == "wheel_up" else WHEEL_ROWS
                self.scroll_rows(step)
                return True
            return False
        if event.action != "press" or event.button != "left":
            return False
        self.focus()
        # DN's viewer had no row to point at: the outer quarters are Left and
        # Right, and the rest is Up above the middle and Down below it.
        if event.x < self.width // 4:
            key = "left"
        elif event.x >= self.width - self.width // 4:
            key = "right"
        else:
            key = "up" if event.y < self.height // 2 else "down"
        await self.on_key(KeyEvent(key))
        return True

    # -- the context menu --------------------------------------------------------

    def context_menu(self) -> ContextMenu | None:
        """The View menu's most used entries.  Whoever holds the viewer runs
        them -- the F3 window; a quick view, which has none of them, greys
        them all."""
        if self.source is None:
            return None
        menu = ContextMenu()
        menu.add_item(tr("He~x~/Text/Dump"), HexMode)
        menu.add_item(tr("~T~ext"), SetViewMode("text"))
        menu.add_item(tr("~H~ex"), SetViewMode("hex"))
        menu.add_item(tr("~D~ump"), SetViewMode("dump"))
        menu.add_line()
        menu.add_item(tr("~W~rap lines"), Unwrap)
        menu.add_item(tr("~M~arkup view"), SwitchRendered)
        menu.add_item(tr("Fi~l~ter"), AddFilter)
        menu.add_line()
        menu.add_item(tr("~S~earch..."), SearchFor)
        menu.add_item(tr("Search a~g~ain"), ContinueSearch)
        menu.add_item(tr("Go to add~r~ess..."), GotoAddress)
        menu.add_line()
        menu.add_item(tr("Encod~i~ng..."), ChooseEncoding)
        menu.add_line()
        menu.add_item(tr("~C~lose"), CloseWindow)
        return menu

    # -- syntax highlight --------------------------------------------------------

    def rehighlight(self) -> None:
        """Forget the tokens: another file, another encoding, or ``highlight.ini`` saved."""
        stop = getattr(self, "_lex_stop", None)
        if stop is not None:
            stop.set()
        #: What the tokens were lexed for -- path, encoding, size, file type -- and the
        #: bytes they cover, ``[start, end)``; the spans, and their starts for
        #: ``bisect``.
        self._lexed_for: Any = None
        self._covered = (0, 0)
        self._spans: list[highlight.Span] = []
        self._starts: list[int] = []
        #: The stop flag of the lexing in flight, else None.
        self._lex_stop: threading.Event | None = None
        #: The window last asked for: never asked twice, or a line longer
        #: than the window would have it lexed over and over.
        self._asked: tuple[int, int] | None = None
        #: No lexer for this file: plain text, until something changes.
        self._plain = False
        app = self.application
        if app is not None and app.is_running:
            self.invalidate()

    def _tokens(self, top: int, bottom: int) -> list[highlight.Span] | None:
        """The spans to paint ``[top, bottom)`` with, or None for plain text;
        a window around *top* is asked for when they do not cover it."""
        source = self.source
        if not self.syntax_highlight or source is None or self.size == 0:
            return None
        # Across a network a smaller window, read through the source's own
        # blocking read -- the chunk cache is the loop's -- on the thread.
        remote = self.remote
        where = str(source.origin) if remote else str(source.path)
        key = (where, self.encoding, self.size, self.file_type)
        if key != self._lexed_for:
            self.rehighlight()
            self._lexed_for = key
        if self._plain:
            return None
        start, end = self._covered
        if (top < start or (bottom > end and end < self.size)) and self._lex_stop is None:
            back, ahead = (REMOTE_LEX_BACK, REMOTE_LEX_AHEAD) if remote else (LEX_BACK, LEX_AHEAD)
            low, high = max(0, top - back), min(self.size, top + ahead)
            if (low, high) == self._asked:
                return self._spans
            self._asked = (low, high)
            stop = threading.Event()
            self._lex_stop = stop
            _LEXER.run(self, _lex_window, str(source.path), self.file_type, source._data, low, high, self.size,
                       self.encoding, stop, source.read_blocking if remote else None,
                       done=lambda outcome: self._lexed(outcome, stop))
        return self._spans

    def _lexed(self, outcome: Outcome, stop: threading.Event) -> None:
        if stop is not self._lex_stop:
            return  # forgotten by rehighlight meanwhile
        self._lex_stop = None
        try:
            label, answer = outcome.result()
        except Exception:
            # Unreadable now, or a lexer that fails on this text: plain.
            label, answer = "", False
        if self.lexer_name != label:
            self.lexer_name = label
        if answer is None:
            return
        if answer is False:
            self._plain, self._spans, self._starts = True, [], []
        else:
            start, end, spans = answer
            self._covered, self._spans = (start, end), spans
            self._starts = [span[0] for span in spans]
        app = self.application
        if app is not None and app.is_running:
            # Not when answered on the spot, from inside ``render``.
            self.invalidate()

    # -- painting --------------------------------------------------------------

    def cursor_position(self) -> tuple[int, int] | None:
        """The hardware cursor on the hex pair under ``cursor``, as DN put it."""
        if self.mode != "hex" or self.size == 0:
            return None
        per = self.row_bytes()
        index = self.cursor - self.top
        if not 0 <= index < self.height * per:
            return None
        return HEX_PAIRS_AT + (index % per) * 3, index // per

    def byte_at(self, x: int, y: int) -> int | None:
        """The offset of the byte painted at *x*, *y* in the hex and dump
        modes -- its pair or its character -- else None."""
        if self.mode == "text" or self.source is None:
            return None
        per = self.row_bytes()
        if self.mode == "hex":
            chars_at = hex_chars_at(per)
            if HEX_PAIRS_AT <= x < HEX_PAIRS_AT + per * 3 and (x - HEX_PAIRS_AT) % 3 < 2:
                column = (x - HEX_PAIRS_AT) // 3
            elif chars_at <= x < chars_at + per:
                column = x - chars_at
            else:
                return None
        elif DUMP_CHARS_AT <= x < DUMP_CHARS_AT + per:
            column = x - DUMP_CHARS_AT
        else:
            return None
        offset = self.top + y * per + column
        return offset if 0 <= y < self.height and offset < self.size else None

    def tooltip_at(self, x: int, y: int) -> str:
        """In the hex and dump modes, the byte under the pointer: where it is,
        and its value every way the row does not show it.  Only a byte already
        read -- which a byte on screen is -- since this runs on the loop."""
        offset = self.byte_at(x, y)
        byte = self.source.peek(offset) if offset is not None and self.source is not None else None
        if byte is None:
            return super().tooltip_at(x, y)
        table = self.source.table
        char = table[byte] if table is not None else cp437(byte)
        return "\n".join((
            tr("Offset {hex} ({decimal})").format(hex=f"{offset:08X}", decimal=f"{offset:,}"),
            tr("Byte {hex}, decimal {decimal}, octal {octal}, binary {binary}").format(
                hex=f"{byte:02X}", decimal=byte, octal=f"{byte:03o}", binary=f"{byte:08b}"),
            tr("Character {char}").format(char=char),
        ))

    def info_tooltip(self) -> str:
        """What the info line leaves out: the whole name and the exact size."""
        if self.source is None:
            return ""
        return "\n".join((str(self.path), tr_n("{count} byte", "{count} bytes", self.size, count=f"{self.size:,}")))

    def render(self, surface: Surface) -> None:
        style = self.style
        surface.fill(0, 0, self.width, self.height, " ", style)
        if self.source is None:
            return
        try:
            if self.mode == "text":
                self._want_layout()
                if self.rendering:
                    self._paint_rendered(surface)
                else:
                    self._render_text(surface)
            else:
                self._render_hex(surface)
        except NotYet:
            # A file across a network, its chunk on the way: painted again
            # when it lands (``_chunk_landed``).
            surface.fill(0, 0, self.width, self.height, " ", style)
            self._say(surface, tr("Reading..."))
        except OSError as error:
            surface.fill(0, 0, self.width, self.height, " ", style)
            self._say(surface, tr("Cannot read the file: {error}").format(error=error.strerror or error))

    def _say(self, surface: Surface, text: str) -> None:
        if self.height and self.width:
            text = text[: self.width]
            surface.draw_text(max(0, (self.width - display_width(text)) // 2), self.height // 2, text, self.style)

    def _hit_covers(self, offset: int) -> bool:
        hit = self.hit
        return hit is not None and hit[0] <= offset < hit[0] + hit[1]

    def _render_text(self, surface: Surface) -> None:
        style, selected = self.style, self.part_style("selected")
        x_delta = 0 if self.wrap else self.x_delta
        limit = x_delta + self.width
        rows = self._text_rows(self.height, max_cols=limit)
        spans = self._tokens(self.top, rows[-1].next) if rows else None
        starts = self._starts if spans else None
        looks: dict[tuple[str, ...], Any] = {}
        hidden = self.show_hidden
        tier = 0 if self.glyphs >= GLYPHS_UNICODE else 1
        paragraphs: dict[int, bool] = {}
        for y, row in enumerate(rows):
            cells = self._whole(row, limit)
            # Hebrew or Arabic in the row: its cells in reading order, each
            # still carrying its offset (navkit.bidi.order_cells).  A wrapped
            # row is a piece of its line, whose first strong letter says
            # which way all of its rows read -- as a paragraph is broken into
            # lines first and each line then ordered (UBA's L1).
            order = self._ordered(cells, row, paragraphs)
            if order is not None:
                cells = [(shown, cells[column][1]) for column, shown in order]
            token = 0
            data = b""
            if hidden:
                data = self._hidden_row(surface, y, row, x_delta, tier)
            if starts:
                token = max(0, bisect.bisect_right(starts, cells[min(x_delta, len(cells) - 1)][1]) - 1) if cells else 0
            for x in range(self.width):
                column = x + x_delta
                if column >= len(cells):
                    break
                char, at = cells[column]
                if self._hit_covers(at):
                    look = selected
                else:
                    look = style
                    if spans:
                        if order is not None:
                            # Reordered, the offsets no longer only grow along the row.
                            token = max(0, bisect.bisect_right(starts, at) - 1)
                        # The cells' offsets only grow along a row: one pointer will do.
                        while token < len(spans) and spans[token][1] <= at:
                            token += 1
                        if token < len(spans) and spans[token][0] <= at:
                            classes = spans[token][2]
                            look = looks.get(classes)
                            if look is None:
                                look = looks[classes] = self.part_style("token", classes=classes)
                if char == "":
                    if x == 0:
                        surface.set_cell(x, y, " ", look)
                    continue
                if x == self.width - 1 and column + 1 < len(cells) and cells[column + 1][0] == "":
                    # Half a wide character would spill past the edge.
                    surface.set_cell(x, y, " ", look)
                    continue
                if hidden and 0 <= at - row.start < len(data):
                    byte = data[at - row.start]
                    if byte == 0x20 or (byte == 0x09 and (column == 0 or cells[column - 1][1] != at)):
                        # A blank, or a tab's first column: its mark, faint.
                        surface.set_cell(x, y, HIDDEN_MARKS[chr(byte)][tier], look.derive(dim=True))
                        continue
                surface.set_cell(x, y, char, look)

    def _paint_rendered(self, surface: Surface) -> None:
        """The rows of the rendering from ``render_row``.  A cell's look is its
        classes' under ``FileViewer::md``; a code token's foreground is the
        editor highlight's (``::token``) over the code's background."""
        layout = self.render_layout
        selected = self.part_style("selected")
        looks: dict[Any, Any] = {}
        marks = self._render_marks(layout)
        width = self.width
        for y in range(self.height):
            index = self.render_row + y
            if index >= len(layout.rows):
                break
            cells, columns = _laid_row(layout.rows[index], width)
            for x, (char, classes, link) in enumerate(cells[:width]):
                if (index, columns[x]) in marks:
                    look = selected
                else:
                    look = looks.get((classes, link))
                    if look is None:
                        look = looks[classes, link] = self._render_look(classes, link)
                if char == "":
                    if x == 0:
                        surface.set_cell(x, y, " ", look)
                    continue
                if x == width - 1 and x + 1 < len(cells) and cells[x + 1][0] == "":
                    surface.set_cell(x, y, " ", look)
                    continue
                surface.set_cell(x, y, char, look)

    def _render_look(self, classes: tuple[str, ...], link: str | None) -> Any:
        if "token" in classes:
            cut = classes.index("token")
            look = self.part_style("md", classes=classes[:cut])
            token = self.part_style("token", classes=classes[cut + 1:])
            if token.fg is not None:
                look = look.derive(fg=token.fg)
        elif classes:
            look = self.part_style("md", classes=classes)
        else:
            look = self.style
        return look.derive(link=link) if link else look

    def _render_marks(self, layout: Any) -> frozenset[tuple[int, int]]:
        """The ``(row, column)`` cells of the rendering the search hit is in:
        its text looked for, blanks run together and case aside, in the rows
        of the block holding its offset.  None when the markup split it."""
        hit = self.hit
        if hit is None or self.source is None or not layout.rows:
            return frozenset()
        cached = getattr(self, "_render_marked", None)
        if cached is not None and cached[0] == (hit, id(layout)):
            return cached[1]
        marks: frozenset[tuple[int, int]] = frozenset()
        try:
            needle = " ".join(decode(self.source.read(hit[0], hit[1]), self.encoding).split()).casefold()
        except (NotYet, OSError):
            return marks
        if needle:
            text: list[str] = []
            where: list[tuple[int, int]] = []
            for index in layout.block_rows(layout.row_for(hit[0])):
                for column, (char, _, _) in enumerate(layout.rows[index].cells):
                    if char == "" or (char.isspace() and (not text or text[-1] == " ")):
                        continue
                    for piece in " " if char.isspace() else char.casefold():
                        text.append(piece)
                        where.append((index, column))
                if text and text[-1] != " ":
                    # A row's end is a blank between its words and the next row's.
                    text.append(" ")
                    where.append((-1, -1))
            found = "".join(text).find(needle)
            if found >= 0:
                marks = frozenset(cell for cell in where[found:found + len(needle)] if cell[0] >= 0)
        self._render_marked = ((hit, id(layout)), marks)
        return marks

    def _hidden_row(self, surface: Surface, y: int, row: Any, x_delta: int, tier: int) -> bytes:
        """*Hidden characters* on one text row: the mark of the ending that closes
        it, a cell past its text, painted here; returned, the bytes behind the
        cells that show, which the caller marks the blanks and tabs among."""
        source, cells = self.source, row.cells
        if row.next > row.start:
            tail = source.read(max(row.start, row.next - 2), min(2, row.next - row.start))
            ending = "\r\n" if tail.endswith(b"\r\n") else {b"\n": "\n", b"\r": "\r"}.get(tail[-1:])
            x = len(cells) - x_delta
            if ending is not None and 0 <= x < self.width:
                look = self.part_style("selected") if self._hit_covers(row.next - 1) else self.style
                surface.set_cell(x, y, HIDDEN_MARKS[ending][tier], look.derive(dim=True))
        shown = cells[x_delta:x_delta + self.width]
        if not shown:
            return b""
        return source.read(row.start, shown[-1][1] - row.start + 1)

    def _render_hex(self, surface: Surface) -> None:
        style, selected = self.style, self.part_style("selected")
        per = self.row_bytes()
        source = self.source
        hex_mode = self.mode == "hex"
        for y in range(self.height):
            address = self.top + y * per
            if address >= self.size:
                break
            data = source.read(address, per)
            if hex_mode:
                surface.draw_text(0, y, hex_row(data, address, per, self.filter, self.source.table), style)
            else:
                surface.draw_text(0, y, dump_row(data, address, self.filter, self.source.table), style)
            if self.hit is None:
                continue
            chars_at = hex_chars_at(per) if hex_mode else DUMP_CHARS_AT
            for index, byte in enumerate(data):
                if not self._hit_covers(address + index):
                    continue
                if hex_mode:
                    surface.draw_text(HEX_PAIRS_AT + index * 3, y, f"{byte:02X}", selected)
                    char = hex_row(data[index:index + 1], 0, 1, self.filter, self.source.table)[-1]
                else:
                    char = dump_row(data[index:index + 1], 0, self.filter, self.source.table)[-1]
                surface.set_cell(chars_at + index, y, char, selected)
