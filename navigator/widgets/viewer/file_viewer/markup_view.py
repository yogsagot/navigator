"""View > Markup view: Markdown, reST, HTML and PDF rendered, pictures, and showing a search hit
in them.

A mixin of :class:`FileViewer` (``navkit.widget.Mixin``): methods only; its state,
keys and the file are in ``file_viewer.py``.
"""

from __future__ import annotations

import fnmatch
import threading
import unicodedata
from pathlib import Path
from typing import TYPE_CHECKING, Any

from navkit.bidi import display_width, has_rtl, order_cells, text_rtl
from navkit.glyphs import GLYPHS_UNICODE
from navkit.i18n import tr
from navkit.screen import Surface

from navml.background import Outcome

from navigator.settings import SETTINGS
from navigator.lib.viewer import image, markdown, pdf, rst
from navigator.lib.viewer.layout import RENDER_LIMIT
from navigator.lib.viewer import WHOLE_LINE
from navigator.widgets.viewer.file_viewer.helpers import _RENDERER, _lay_out, _picture, _when_here

if TYPE_CHECKING:
    from navigator.widgets.viewer.file_viewer.file_viewer import FileViewer as _Base
else:
    from navkit.widget import Mixin as _Base


class MarkupView(_Base):
    """View > Markup view: Markdown, reST, HTML and PDF rendered, pictures, and showing a search hit"""

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
        for format, on, masks in (("image", settings.render_images, settings.image_masks),
                                  ("pdf", settings.render_pdf, settings.pdf_masks),
                                  ("html", settings.render_html, settings.html_masks),
                                  ("rst", settings.render_rst, settings.rst_masks),
                                  ("markdown", settings.render_markdown, settings.markdown_masks)):
            if on and any(fnmatch.fnmatchcase(name, mask.strip().lower())
                          for mask in masks.split(";") if mask.strip()):
                return format
        return ""

    def format_label(self) -> str:
        """What the mark calls the format: *Image*, *PDF*, *HTML*, *reST*, *Markdown*."""
        format = self.render_format
        if format == "image":
            return tr("Image")
        if format == "pdf":
            return tr("PDF")
        if format == "html":
            return tr("HTML")
        if format == "rst":
            return tr("reST")
        return tr("Markdown")

    @property
    def can_render(self) -> bool:
        """Whether this file can be rendered at all: no bigger than
        ``RENDER_LIMIT`` (a PDF, ``PDF_LIMIT``), since it is read and parsed
        whole.  A picture wants ``IMAGE_LIMIT``, a terminal that draws
        pictures, and Pillow unless it is a PNG on kitty."""
        format = self.render_format
        if format == "image":
            return (self.source is not None and self.size <= image.IMAGE_LIMIT
                    and image.can_show(self.source.path.name, self.graphics))
        limit = pdf.PDF_LIMIT if format == "pdf" else RENDER_LIMIT
        return self.source is not None and self.size <= limit

    def render_refusal(self) -> str:
        """Why *Markup view* is greyed for this file, or "" when it is not."""
        if self.can_render:
            return ""
        if self.render_format == "image" and self.source is not None:
            if not self.graphics:
                return tr("This terminal draws no pictures")
            if self.size > image.IMAGE_LIMIT:
                return tr("Too big to show as a picture")
            return image.available() or ""
        return tr("Not a markup file, or too big to render")

    @property
    def graphics(self) -> str:
        """How the terminal draws a picture -- ``kitty``, ``sixel`` -- or ""."""
        app = self.application
        return app.terminal.info.graphics if app is not None else ""

    @property
    def showing_picture(self) -> bool:
        """Whether the file is painted as a picture: text mode, *Markup
        view* on for a picture, and the picture in."""
        return (self.mode == "text" and self.rendered and self.render_format == "image"
                and self.picture is not None and self.can_render)

    @property
    def picture_pending(self) -> bool:
        """Whether a picture is on its way, and nothing to show meanwhile."""
        return (self.mode == "text" and self.rendered and self.render_format == "image"
                and self.picture is None and self._picture_asked != self._picture_for
                and self.can_render)

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
        self._picture_asked: Any = None
        self._picture_for: Any = None
        if self.picture is not None:
            self.picture = None

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
        if self.render_format == "image":
            self._want_picture()
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

    def _want_picture(self) -> None:
        """Ask the thread for the picture at the size, protocol and cell size
        in force, unless it is in or on its way; the one there is painted
        until it lands."""
        source = self.source
        app = self.application
        if source is None or app is None:
            return
        info = app.terminal.info
        remote = self.remote
        where = str(source.origin) if remote else str(source.path)
        # A row under it for what it is.
        cols, rows = max(1, self.width), max(1, self.height - 1)
        key = (where, self.size, cols, rows, info.graphics, info.cell_px)
        if key in (self._picture_for, self._picture_asked):
            return
        self._picture_asked = key
        _RENDERER.run(self, _picture, str(source.path), source._data, self.size, cols, rows,
                      info.cell_px, info.graphics, source.read_blocking if remote else None,
                      done=lambda outcome: self._pictured(outcome, key))

    def _pictured(self, outcome: Outcome, key: Any) -> None:
        if key != self._picture_asked:
            return  # another file or size, or forgotten meanwhile
        self._picture_for = key
        try:
            self.picture = outcome.result()
        except Exception:
            # Not a picture after all, or one nothing here reads: the source.
            self.picture = None
        self.invalidate()

    def _paint_picture(self, surface: Surface) -> None:
        """The picture in the middle, and under it what it is."""
        shown = self.picture
        picture = shown.picture
        room = max(1, self.height - 1)
        x, y = max(0, (self.width - picture.cols) // 2), max(0, (room - picture.rows) // 2)
        surface.place_image(picture, x, y, self.style)
        text = tr("{format} {width}×{height}").format(
            format=shown.format or tr("Image"), width=shown.width, height=shown.height)
        if self.height > 1:
            text = text[: self.width]
            surface.draw_text(max(0, (self.width - display_width(text)) // 2), self.height - 1, text, self.style)

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

    def hit_showing(self) -> bool:
        """Whether the last hit is on screen, which is when a search goes on
        from it rather than from the view.  DN went on from it only while it
        was on the first row (``FVIEWER.PAS``'s ``ContinueSearch``) -- a
        departure: a hit in the last screenful cannot be put on top, and
        DN's rule would find it again on every Shift+F7.  Everywhere else the
        hit is on the first row until something scrolls."""
        if self.hit is None or self.source is None:
            return False
        offset = self.hit[0]
        if self.filtering:
            index = self._lines_index(offset)
            return index is not None and index == self.lines_cursor
        if self.rendering:
            row = self.render_layout.row_for(offset)
            return self.render_row <= row < self.render_row + max(1, self.height)
        if self.mode != "text":
            return self.top <= offset < self.top + max(1, self.height) * self.row_bytes()
        return any(r.start <= offset < r.next for r in self._text_rows(self.height, max_cols=1))

    def show_hit(self, offset: int, length: int) -> None:
        """Put a search hit on screen and mark it.

        DN's ``ContinueSearch``: the hit's row goes to the top (``BufPos :=
        Lines[I].Pos``; in hex and dump the row holding it, the rows' byte
        phase kept) -- as far as the last screenful, where every scroll here
        stops -- and sideways the text is scrolled to centre it when it is off
        the edge.  Under *Filter lines* the lines cursor goes to it instead.
        """
        self.hit = (offset, length)
        if self.source is None:
            return
        if self.filtering:
            index = self._lines_index(offset)
            if index is not None:
                self._lines_to(index)
                return
            # Not on a line shown: the whole file again, at the hit.
            self.leave_lines()
        if self.rendering:
            self._render_go(self.render_layout.row_for(offset))
            return
        if self.mode != "text":
            per = self.row_bytes()
            self.top = min(max(0, offset - (offset - self.top) % per), self._last_top())
            self.cursor = offset if self.mode == "hex" else self.top
            return
        self.top = min(self.source.line_start(offset, self.wrap_width), self._last_top())
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
