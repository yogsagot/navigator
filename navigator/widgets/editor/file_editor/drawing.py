"""^Q[ the bracket pair, F4's line drawing, Ctrl+J 0's macros, the ^K1-9/^Q1-9 markers and
the block's place kept with the file.

A mixin of :class:`FileEditor` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``file_editor.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import asyncio

from navkit.events import KeyEvent
from navkit.i18n import tr

from navigator.widgets.editor.commands import SwitchDrawMode, SelectMacro, BracketPair, GotoMarker, PlaceMarker
from navigator.lib.editor import columns
from navigator.lib.editor.document import Pos
from navigator.widgets.editor.file_editor.helpers import _marking

# The surface is a stub with no module of its own, by design (navml.surface).
# pyright: reportMissingModuleSource=false
if TYPE_CHECKING:
    from navigator.widgets.editor.file_editor.file_editor_surface import FileEditor as _Base
else:
    from navkit.widget import Mixin as _Base


class Drawing(_Base):
    """^Q[ the bracket pair, F4's line drawing, Ctrl+J 0's macros, the ^K1-9/^Q1-9 markers and"""

    # -- ^Q[: the bracket pair ---------------------------------------------------------

    #: What opens, mapped to what closes it: ``SearchFwd``'s three pairs.
    BRACKETS = {"(": ")", "[": "]", "{": "}"}

    def bracket_pair(self) -> Pos | None:
        """Where the bracket under the cursor is answered, or None.

        DN's ``SearchFwd`` and ``SearchBwd``: an opening bracket looks forward
        and a closing one back, line after line, counting only brackets of its
        own kind -- strings and comments are not told apart, as they were not.
        """
        index, past = self._index()
        text = self._text()
        if past or index >= len(text):
            return None
        char = text[index]
        lines = self.document.lines
        if char in self.BRACKETS:
            opener, closer, step = char, self.BRACKETS[char], 1
        elif char in self.BRACKETS.values():
            closer = char
            opener = next(o for o, c in self.BRACKETS.items() if c == char)
            step = -1
        else:
            return None
        depth = 0
        line, at = self.line, index
        while 0 <= line < len(lines):
            row = lines[line]
            while 0 <= at < len(row):
                if row[at] == opener:
                    depth += step
                elif row[at] == closer:
                    depth -= step
                if depth == 0:
                    return Pos(line, at)
                at += step
            line += step
            if 0 <= line < len(lines):
                at = 0 if step > 0 else len(lines[line]) - 1
        return None

    async def on_bracket_pair(self, event: BracketPair) -> bool:
        """``cmBracketPair``: the cursor to the bracket's pair, if it has one."""
        found = self.bracket_pair()
        if found is not None:
            self._moved()
            self._go(found)
        return True

    # -- F4: line drawing ---------------------------------------------------------------

    #: The keys ``DrawLine`` answered, and the direction each goes.
    DRAW_KEYS = {"up": 0, "right": 1, "down": 2, "left": 3, "e": 0, "d": 1, "x": 2, "s": 3}

    async def on_switch_draw_mode(self, event: SwitchDrawMode) -> bool:
        """``cmSwitchDrawMode``: off, single, double, off; the pen lifted."""
        self.draw_mode = (self.draw_mode + 1) % 3
        self._pen = None
        return True

    async def _run_key(self, event: KeyEvent) -> bool:
        """While drawing, the arrows (and ^E ^D ^X ^S) are ``DrawLine``'s before any
        command they are bound to: a key table hands a command on without the
        Shift or Ctrl that decide here between drawing, erasing and moving."""
        if self.draw_mode and self._draw_key(event):
            return True
        return await super()._run_key(event)

    def _draw_key(self, event: KeyEvent) -> bool:
        key = event.key
        direction = self.DRAW_KEYS.get(key)
        if direction is None or event.alt or (len(key) == 1 and not event.ctrl):
            return False
        if event.shift:
            how = "draw"
        elif event.ctrl:
            how = "erase"
        else:
            how = "move"
        self.draw_line(direction, how)
        return True

    def _cell(self, line: int, col: int) -> str:
        """The character in a cell, a blank past a line's end or outside the text."""
        if not 0 <= line < len(self.document) or col < 0:
            return " "
        text = self.document.lines[line]
        index, past = columns.index_at(text, col, self.tab_size)
        return " " if past or index >= len(text) else text[index]

    def _put(self, line: int, col: int, char: str) -> None:
        """*char* into a cell, the line padded out to it with blanks if short."""
        text = self.document.lines[line]
        index, past = columns.index_at(text, col, self.tab_size)
        if past or index >= len(text):
            self.buffer.insert(Pos(line, len(text)), " " * past + char)
        elif text[index] != char:
            self.buffer.delete(Pos(line, index), Pos(line, index + 1))
            self.buffer.insert(Pos(line, index), char)

    def draw_line(self, direction: int, how: str) -> None:
        """``DrawLine``: draw, erase or only move one cell *direction* (0 up, 1 right,
        2 down, 3 left).

        Drawing or erasing is skipped going straight back the way the pen came;
        either way the cursor then moves, a line added below the last, and the
        pen remembers the side it came in by.
        """
        from navigator.lib.editor import linedraw

        line, col = self.line, self.col
        double = self.draw_mode == 2
        if how != "move" and self._pen != direction:
            up, down = self._cell(line - 1, col), self._cell(line + 1, col)
            left, right = self._cell(line, col - 1), self._cell(line, col + 1)
            self._moved()
            self._begin()
            if how == "draw":
                self._put(line, col, linedraw.drawn(
                    up, right, down, left, double=double, direction=direction, came=self._pen,
                ))
            else:
                for (y, x, char, arm) in ((line - 1, col, up, 4), (line + 1, col, down, 1),
                                         (line, col - 1, left, 2)):
                    new = linedraw.without_arm(char, arm) if 0 <= y < len(self.document) and x >= 0 else None
                    if new is not None:
                        self._put(y, x, new)
                self._put(line, col, " ")
                text = self.document.lines[line]
                if columns.width(text, self.tab_size) > col + 1:
                    new = linedraw.without_arm(right, 8)
                    if new is not None:
                        self._put(line, col + 1, new)
            self._end()
        self._moved()
        if direction == 0:
            self._go_column(line - 1, col)
        elif direction == 2:
            if line == len(self.document) - 1:
                self._begin()
                self.buffer.insert(self.document.end, self.document.newline)
                self._end()
            self._go_column(line + 1, col)
        elif direction == 1:
            self._go_column(line, col + 1)
        else:
            self._go_column(line, max(0, col - 1))
        if how != "move":
            self._pen = (direction + 2) % 4

    # -- Ctrl+J 0: macros ------------------------------------------------------------

    async def on_select_macro(self, event: SelectMacro) -> bool:
        self.spawn(self.select_macro())
        return True

    async def select_macro(self) -> None:
        """``cmSelectMacro``: this file's macros (``macros.ini``) in a box, and
        the one chosen played -- a departure, DN's was empty."""
        import asyncio

        from navml.widgets.dialog.dialog import Dialog
        from navml.widgets.menu.popup_menu import PopupMenu
        from navml.widgets.menu.sub_menu import SubMenu

        from navigator.lib.config import macros

        app = self.application
        sections = await asyncio.to_thread(macros.read)
        name = self.path.name if self.path is not None else ""
        found = macros.macros_for(sections, name)
        if not found:
            await Dialog(title=tr("Macros"), prompt=tr("macros.ini has no macro for this file"),
                         buttons="ok").execute(app)
            self.focus()
            return
        menu = SubMenu()
        items = [menu.add_item(macro.name.replace("~", "~~")) for macro in found]
        title = tr("Macros")
        width, height = PopupMenu.measure(menu, app, self, title)
        ox, oy = self.offset()
        box = PopupMenu(menu, ox + self.x + max(0, (self.width - width) // 2),
                        oy + self.y + max(0, (self.height - height) // 2), behind=self, title=title)
        chosen = await box.execute(app)
        self.focus()
        if chosen is None:
            return
        unknown = await macros.play_steps(self, found[items.index(chosen)].steps)
        if unknown:
            await Dialog(title=tr("Macros"), prompt=tr("Not an editor command: {names}").format(
                names=", ".join(unknown)), buttons="ok").execute(app)
            self.focus()

    # -- ^K1-9 and ^Q1-9 -----------------------------------------------------------

    async def on_place_marker(self, event: PlaceMarker) -> bool:
        """``cmPlaceMarker``: the cursor's place, kept."""
        self.markers[event.marker - 1] = (self.line, self.col)
        return True

    @_marking
    async def on_goto_marker(self, event: GotoMarker) -> bool:
        """``cmGotoMarker``: the cursor to a marker that is set, in the middle of the
        window (``Pos := Delta - Size div 2``, then ``CenterScreen``).  A marker
        past a text that has since got shorter lands on its last line."""
        place = self.markers[event.marker - 1]
        if place is None:
            return True
        self._moved()
        line, col = place
        self._move_to(line, col)
        rows, cols = max(1, self.height), max(1, self.width)
        self.top = max(0, min(self.line - rows // 2, len(self.document) - 1))
        self.left = max(0, self.col - cols // 2)
        return True

    def markers_text(self) -> str:
        """The markers as the edit history keeps them: ``line:col`` nine times, empty where unset."""
        return ",".join("" if m is None else f"{m[0]}:{m[1]}" for m in self.markers)

    def restore_markers(self, text: str) -> None:
        """:meth:`markers_text`'s form read back; anything unreadable is unset."""
        markers: list[tuple[int, int] | None] = [None] * 9
        for index, part in enumerate(text.split(",")[:9]):
            line, _, col = part.partition(":")
            if line.isdigit() and col.isdigit():
                markers[index] = (int(line), int(col))
        self.markers = markers

    def block_place(self) -> str:
        """The block as the edit history keeps it, DN's ``fBlockStart``/``fBlockEnd``:
        ``line:col-line:col`` for a stream block, ``|`` before a column block's
        two corners, empty for none."""
        if self.vertical_blocks:
            if self.column_block is None:
                return ""
            (l1, c1), (l2, c2) = self.column_block
            return f"|{l1}:{c1}-{l2}:{c2}"
        if self.block is None:
            return ""
        start, end = self.block
        return f"{start.line}:{start.index}-{end.line}:{end.index}"

    def restore_block_place(self, text: str, hidden: bool = False) -> None:
        """:meth:`block_place`'s form read back, and hidden again if it was.

        A departure: DN put ``Mark.A``/``Mark.B`` back blindly, and here a
        block that no longer lies in the text -- the file changed since --
        or is not of the kind :attr:`vertical_blocks` says is dropped, as an
        unreadable marker is.  A column block's columns may run past a line's
        end, as a rectangle always may; its lines may not.
        """
        column = text.startswith("|")
        ends = []
        for part in text.removeprefix("|").split("-"):
            line, _, col = part.partition(":")
            if not (line.isdigit() and col.isdigit()):
                return
            ends.append((int(line), int(col)))
        if len(ends) != 2 or column != self.vertical_blocks:
            return
        lines = self.document.lines
        if any(line >= len(lines) for line, _ in ends):
            return
        if column:
            self.column_block = (ends[0], ends[1])
        else:
            if any(col > len(lines[line]) for line, col in ends):
                return
            start, end = Pos(*ends[0]), Pos(*ends[1])
            if not start < end:
                return
            self.block = (start, end)
        self.block_hidden = hidden
