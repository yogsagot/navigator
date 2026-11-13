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

The methods are split by feature into mixins (``navkit.widget.Mixin``), one
module each beside this one -- ``moving``, ``markup_view``, ``lines``,
``key_handling``, ``painting`` -- with the module-level helpers in
``helpers``, re-exported here.  What stays here is the state, the file and the
info line.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navkit.i18n import tr
from navkit.reactive import computed, reactive
from navkit.widget import Widget

from navml.widgets.menu.context_menu import ContextMenuHost

from navigator.settings import SETTINGS
from navigator.lib.viewer import markdown
from navigator.lib.viewer import FILTER_TAGS, ViewSource, byte_table, ENCODINGS, group_digits, NotYet
from navigator.widgets.viewer.file_viewer.helpers import MODES, REMOTE_LEX_AHEAD, SPAN_LOOK, _laid_row

from navigator.widgets.viewer.file_viewer.moving import Moving
from navigator.widgets.viewer.file_viewer.markup_view import MarkupView
from navigator.widgets.viewer.file_viewer.lines import Lines
from navigator.widgets.viewer.file_viewer.key_handling import KeyHandling
from navigator.widgets.viewer.file_viewer.painting import Painting

class FileViewer(Moving, MarkupView, Lines, KeyHandling, Painting, ContextMenuHost, Widget):
    """The inside of a viewer window: a file's rows, and the keys that move them."""

    #: Kept left to right on a right-to-left screen (``Widget.mirrors``):
    #: the file's own text, laid out left to right line by line.
    mirrors = False

    #: A search hit, drawn in *Selected text* [118]; a syntax token
    #: (:mod:`navigator.lib.highlight`), by its classes.
    #: A Markdown or HTML file's rendering, by what its cells are (``heading``,
    #: ``code``, ``link`` and the rest: :mod:`navigator.lib.viewer.layout`).
    #: A byte typed over in hex and not stored yet, by ``changed`` (a
    #: departure: DN marked none).
    #: View > *Filter lines*' rows, by ``number`` (the gutter), ``cursor``
    #: (the row Enter goes to) and ``match`` (what matched in a line).
    parts = ("selected", "token", "md", "changed", "lines")

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

    #: Hex editing (DN's ``HexEdit``): which half of the byte's pair the
    #: cursor is on, 0 the high one; and whether it is in the characters to
    #: the right instead of the pairs -- DN's ``not HexEdit``, Tab's switch.
    nibble: int = reactive(0)
    in_chars: bool = reactive(False)
    #: Whether bytes typed over differ from the file's (``ViewSource.edited``),
    #: kept here so that Shift+F2 greys and the info line follow it.
    edited: bool = reactive(False)

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
    #: The file as a picture (:class:`navigator.lib.viewer.image.Shown`),
    #: for the size it was asked at, while the terminal draws pictures; None
    #: until the thread has made it.
    picture: Any = reactive(None)

    #: View > *Follow end* (Ctrl+T): the end kept in view as the file grows,
    #: ``tail -f`` -- a departure.  The window looks at the size; scrolling
    #: back up lets go.  Never kept in the view history.
    follow: bool = reactive(False)
    #: View > *Filter lines* (Ctrl+G): the scan whose lines are shown instead
    #: of the file's (:class:`navigator.lib.viewer.lines.LineScan`), or None.
    lines: Any = reactive(None)
    #: The filtered row on top, and the row the cursor is on.
    lines_row: int = reactive(0)
    lines_cursor: int = reactive(0)
    #: Bumped when the scan's lists grow: the scan itself is not reactive.
    lines_revision: int = reactive(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source: ViewSource | None = None
        self._again: Any = None
        #: Whether typing in hex mode types over bytes: the F3 window's
        #: viewer, never the quick view's, whose keys are the panel's.
        self.hex_editing = False
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
        self.nibble, self.in_chars, self.edited = 0, False, False
        self.hit = None
        self.follow = False
        self.lines = None

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
        self.follow = False
        self.lines = None

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

    # -- the info line ----------------------------------------------------------

    @computed
    def info_text(self) -> str:
        """DN's ``TViewInfo``: ``[<=>][42% of 12,345 Bytes]{ASCII}``.

        In hex mode the percentage gives way to the cursor's offset and a
        ruler of the row's columns, as ``TViewInfo.Draw`` wrote it.
        """
        follow = "{" + tr("Follow") + "}" if self.follow else ""
        if self.filtering:
            self.lines_revision  # the scan grew: said again
            scan = self.lines
            shown = len(scan.shown)
            text = "[" + tr("{shown} of {lines} lines").format(
                shown=group_digits(shown) + ("+" if scan.truncated else ""),
                lines=group_digits(max(scan.lines, shown)))
            return text + "]{" + tr("Lines: {pattern}").format(pattern=scan.pattern.text) + "}" + follow
        if self.mode == "hex":
            per = self.row_bytes()
            phase = self.top % per
            ruler = "─".join(f"{(i + phase) % 256:02X}" for i in range(per))
            text = f"[{self.cursor & 0xFFFFFFFF:08X} {ruler}"
            if self.edited:
                # Bytes typed and not stored: a departure, DN's line said nothing.
                text = "*" + text
        else:
            text = "[>=<][" if self.wrap else "[<=>]["
            text += tr("{percent}% of {size} Bytes").format(percent=self.percent(), size=group_digits(self.size))
        tag = "" if self.encoding == "utf-8" else "{" + dict(ENCODINGS)[self.encoding].split()[0] + "}"
        return text + "]" + FILTER_TAGS[self.filter] + tag + follow

    @computed
    def render_mark(self) -> str:
        """``{Markdown}`` or ``{HTML}`` after the info line, which a click
        switches: while *Markup view* is on, and -- struck through by the
        window -- while it is off for a file the masks name.  Empty where it
        cannot render."""
        if self.mode != "text" or self.filtering:
            return ""
        if not self.rendered and not self.remote and self.hex_editing and self.path is not None:
            # A JSON, YAML, TOML or XML file: Shift+F3 shows its data as a
            # tree, struck through here as any switch that is off.
            from navigator.lib.viewer.structured import kind_by_name

            if kind_by_name(self.path.name) is not None:
                return "{" + tr("Tree") + "}"
        if not self.can_render:
            return ""
        if self.rendered or self.format_by_name(self.path):
            return "{" + self.format_label() + "}"
        return ""

    @computed
    def row_span(self) -> int:
        """How many columns the widest row on screen takes: how far the bottom
        frame's scroll bar reaches (a departure, as the editor's -- DN's viewer
        had the right one alone).  Nothing counts the whole file's lines, so
        the rows showing are the measure, as End's ``CM_END`` measures them.
        0 where nothing goes sideways: wrapped, rendered, hex and dump."""
        self.size, self.encoding, self.filter  # a new size or reading: measured again
        if self.source is None:
            return 0
        if self.filtering:
            self.lines_revision
            shown = self.lines.shown[self.lines_row:self.lines_row + max(1, self.height)]
            if not shown:
                return 0
            gutter = len(str(shown[-1].number)) + 1
            return gutter + max(len(hit.text.expandtabs(8)) for hit in shown)
        if self.mode != "text" or self.wrap or self.rendering or self.showing_picture:
            return 0
        # Measured as far as ``SPAN_LOOK`` columns, or two views past where it
        # is scrolled to: a minified line is not decoded whole on every move,
        # and the bar reaches further as the view goes right.
        reach = max(SPAN_LOOK, self.x_delta + 2 * max(1, self.width))
        try:
            rows = self._text_rows(self.height, max_cols=reach)
        except (NotYet, OSError):
            return 0
        return max((len(row.cells) for row in rows), default=0)

    @computed
    def overflows(self) -> bool:
        """Whether there is more than the view holds, up or down: what shows
        the right frame's scroll bar (a departure, asked for, as the bottom
        one: DN's ``TViewScroll`` was always there).  A file that fits whole
        has none; nothing counts its lines, so in text the view's top is at
        the start and its last row on screen is the file's last."""
        self.size, self.encoding, self.filter, self.wrap
        if self.source is None or self.height <= 0:
            return False
        if self.filtering:
            self.lines_revision
            return len(self.lines.shown) > self.height
        if self.mode == "text" and self.showing_picture:
            return False
        if self.rendering:
            return len(self.render_layout.rows) > self.height
        if self.mode != "text":
            return self.size > self.height * self.row_bytes()
        if self.top > 0:
            return True
        try:
            return not self._end_showing()
        except (NotYet, OSError):
            return True

    def percent(self) -> int:
        """How far into the file the view is: 100 once the end is showing."""
        if self.filtering:
            shown = len(self.lines.shown)
            return 100 if self.lines_row >= self._lines_last_row() else self.lines_row * 100 // max(1, shown)
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

    @computed
    def render_format(self) -> str:
        """What the file is rendered as: the format its name says, else
        Markdown -- switched on for any other text, it is read as Markdown."""
        return self.format_by_name(self.path) or "markdown"
