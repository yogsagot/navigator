"""The mouse and the context menu, syntax highlighting on a thread, and painting the three modes.

A mixin of :class:`FileViewer` (``navkit.widget.Mixin``): methods only; its state,
keys and the file are in ``file_viewer.py``.
"""

from __future__ import annotations

import bisect
import threading
from typing import TYPE_CHECKING, Any

from navkit.bidi import display_width
from navkit.events import KeyEvent, MouseClickEvent
from navkit.glyphs import GLYPHS_UNICODE
from navkit.i18n import tr, tr_n
from navkit.screen import Surface

from navml.background import Outcome
from navml.commands import CloseWindow
from navml.widgets.menu.context_menu import ContextMenu

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
from navigator.lib.viewer.layout import decode
from navigator.lib.viewer import (
    DUMP_CHARS_AT,
    HEX_PAIRS_AT,
    HIDDEN_MARKS,
    cp437,
    dump_row,
    hex_chars_at,
    hex_row,
    NotYet,
)
from navigator.widgets.viewer.file_viewer.helpers import (
    LEX_AHEAD,
    LEX_BACK,
    REMOTE_LEX_AHEAD,
    REMOTE_LEX_BACK,
    WHEEL_ROWS,
    _LEXER,
    _laid_row,
    _lex_window,
)

# The surface is a stub with no module of its own, by design (navml.surface).
# pyright: reportMissingModuleSource=false
if TYPE_CHECKING:
    from navigator.widgets.viewer.file_viewer.file_viewer_surface import FileViewer as _Base
else:
    from navkit.widget import Mixin as _Base


class Painting(_Base):
    """The mouse and the context menu, syntax highlighting on a thread, and painting the three modes."""

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
        if self.editable and self._click_byte(event.x, event.y):
            return True
        # DN's viewer had no row to point at: the outer quarters are Left and
        # Right, and the rest is Up above the middle and Down below it.
        await self._quarter(event.x, event.y)
        app = self.application
        if app is not None:
            # FVIEWER.PAS's ``repeat ... until not MouseEvent(Event,
            # evMouseMove+evMouseAuto)``: every move and every tick sends the
            # key of the quarter the pointer is in then, nothing off the view.
            async def again(x: int, y: int, auto: bool) -> None:
                if 0 <= x < self.width and 0 <= y < self.height:
                    await self._quarter(x, y)

            app.hold_mouse(self, event, again, moves=True)
        return True

    async def _quarter(self, x: int, y: int) -> None:
        """The key DN's press at *x*, *y* sent: Left or Right in the outer
        quarters, Up above the middle and Down below it."""
        if x < self.width // 4:
            key = "left"
        elif x >= self.width - self.width // 4:
            key = "right"
        else:
            key = "up" if y < self.height // 2 else "down"
        await self.on_key(KeyEvent(key))

    def _click_byte(self, x: int, y: int) -> bool:
        """A press on a pair or a character puts the cursor there, in that
        column and on that nibble: a departure -- DN's quarters had no byte
        to point at, and typing over one needs it."""
        offset = self.byte_at(x, y)
        if offset is None:
            return False
        self.cursor = offset
        self.in_chars = x >= hex_chars_at(self.row_bytes())
        self.nibble = 0 if self.in_chars else min(1, (x - HEX_PAIRS_AT) % 3)
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
        if self.in_chars:
            return hex_chars_at(per) + index % per, index // per
        return HEX_PAIRS_AT + (index % per) * 3 + self.nibble, index // per

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
            if self.filtering:
                self._paint_lines(surface)
            elif self.mode == "text":
                self._want_layout()
                if self.showing_picture:
                    self._paint_picture(surface)
                elif self.picture_pending:
                    self._say(surface, tr("Reading..."))
                elif self.rendering:
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
        edits = source.edits
        changed = self.part_style("changed") if edits else style
        for y in range(self.height):
            address = self.top + y * per
            if address >= self.size:
                break
            data = source.read(address, per)
            if hex_mode:
                surface.draw_text(0, y, hex_row(data, address, per, self.filter, self.source.table), style)
            else:
                surface.draw_text(0, y, dump_row(data, address, self.filter, self.source.table), style)
            if self.hit is None and not edits:
                continue
            chars_at = hex_chars_at(per) if hex_mode else DUMP_CHARS_AT
            for index, byte in enumerate(data):
                if self._hit_covers(address + index):
                    look = selected
                elif address + index in edits:
                    look = changed
                else:
                    continue
                if hex_mode:
                    surface.draw_text(HEX_PAIRS_AT + index * 3, y, f"{byte:02X}", look)
                    char = hex_row(data[index:index + 1], 0, 1, self.filter, self.source.table)[-1]
                else:
                    char = dump_row(data[index:index + 1], 0, self.filter, self.source.table)[-1]
                surface.set_cell(chars_at + index, y, char, look)
