"""``TDBViewer``: a dBase file's records in columns, a cell the cursor.

The first row is the field names; each row under it a record, its delete
flag in the first column and its fields after, each as wide as its name or
its value, whichever is wider, and a column between.  The cursor is a cell:
``Delta`` -- a field and a record -- and the view scrolls to keep it, a
whole field at a time across (``Pos``).  The keys are ``HandleEvent``'s.
"""

from __future__ import annotations

from typing import Any

from navkit.events import KeyEvent, MouseClickEvent
from navkit.i18n import tr
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.widget import Widget
from navml.widgets.menu.context_menu import ContextMenu, ContextMenuHost

from navigator.lib.viewer.dbf import DBFile


class DBViewer(ContextMenuHost, Widget):
    """The records, a cell at a time."""

    parts = ("titles", "cursor")

    #: ``Delta``: the cursor's field and record.
    field: int = reactive(0)
    record: int = reactive(0)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.can_focus = True
        self.db: DBFile | None = None
        #: ``Pos``: the first field shown, and the record on the first row.
        self.first_field = 0
        self.top = 0

    # -- the cursor ---------------------------------------------------------------

    def _clamp(self) -> None:
        db = self.db
        if db is None:
            return
        self.record = max(0, min(self.record, db.count - 1))
        self.field = max(0, min(self.field, len(db.fields) - 1))
        rows = max(1, self.height - 1)
        if self.top > self.record:
            self.top = self.record
        if self.top + rows - 1 < self.record:
            self.top = self.record - rows + 1
        self.top = max(0, self.top)
        if self.first_field > self.field:
            self.first_field = self.field
        while self.field > self.first_field + len(self.shown_fields()) - 1 and self.first_field < self.field:
            self.first_field += 1

    def shown_fields(self) -> list[int]:
        """The fields that fit whole from ``first_field`` on -- one at least."""
        db = self.db
        if db is None:
            return []
        shown, x = [], 1
        for index in range(self.first_field, len(db.fields)):
            x += db.fields[index].width + 1
            if x >= self.width:
                break
            shown.append(index)
        return shown or [self.first_field]

    def go(self, field: int | None = None, record: int | None = None) -> None:
        if field is not None:
            self.field = field
        if record is not None:
            self.record = record
        self._clamp()
        self.invalidate()

    async def on_key(self, event: KeyEvent) -> bool:
        db = self.db
        if db is None or event.alt:
            return False
        last_field, page = len(db.fields) - 1, max(1, self.height - 2)
        key = event.name
        if key == "enter":
            if self.field < last_field:
                self.go(field=self.field + 1)
            else:
                self.go(field=0, record=self.record + 1)
        elif key == "left":
            self.go(field=self.field - 1)
        elif key == "right":
            self.go(field=self.field + 1)
        elif key == "home":
            self.go(field=0)
        elif key == "end":
            self.go(field=last_field)
        elif key == "up":
            self.go(record=self.record - 1)
        elif key == "down":
            self.go(record=self.record + 1)
        elif key == "pageup":
            self.go(record=self.record - page)
        elif key == "pagedown":
            self.go(record=self.record + page)
        elif key == "ctrl+pageup":
            self.go(record=0)
        elif key == "ctrl+pagedown":
            self.go(record=db.count - 1)
        else:
            return False
        return True

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """A press in the left or right quarter moves a field, in the middle
        half's top or bottom a record -- ``evMouseDown``'s four arrows."""
        if event.action != "press" or event.button != "left":
            return event.is_wheel and await self._wheel(event)
        self.focus()
        if event.x < self.width // 4:
            self.go(field=self.field - 1)
        elif event.x >= self.width * 3 // 4:
            self.go(field=self.field + 1)
        elif event.y < self.height // 2:
            self.go(record=self.record - 1)
        else:
            self.go(record=self.record + 1)
        return True

    async def _wheel(self, event: MouseClickEvent) -> bool:
        self.go(record=self.record + (-3 if event.button == "wheel_up" else 3))
        return True

    # -- the context menu ---------------------------------------------------------

    def cell_at(self, x: int, y: int) -> tuple[int, int] | None:
        """The field and record of the cell at *x*, *y*, or None off every cell."""
        db = self.db
        if db is None or y < 1:
            return None
        record = self.top + y - 1
        if record >= db.count:
            return None
        left = 1
        for index in self.shown_fields():
            width = db.fields[index].width
            if left <= x < left + width:
                return index, record
            left += width + 1
        return None

    def prepare_context(self, x: int, y: int) -> None:
        """A right click on a cell makes it the cursor's, so *Memo view* and
        *Edit field* act on what was clicked."""
        cell = self.cell_at(x, y)
        if cell is not None:
            self.go(*cell)

    def context_point(self) -> tuple[int, int]:
        """Under the cursor's cell, so the box does not cover it."""
        db, x = self.db, 1
        if db is not None:
            for index in self.shown_fields():
                if index == self.field:
                    break
                x += db.fields[index].width + 1
        return x, min(self.record - self.top + 2, max(0, self.height - 1))

    def context_menu(self) -> ContextMenu | None:
        """The window's *View* menu -- a departure, asked for, as that menu is.
        ``DBWindow`` runs them, and greys *Memo view* off a memo field.  Built
        each time, so its captions follow the language."""
        from navml.commands import CloseWindow

        from navigator.widgets.viewer.commands import ContinueSearch, EditDbField, SearchFor, ShowFields, ShowMemo

        if self.db is None:
            return None
        menu = ContextMenu()
        menu.add_item(tr("~F~ields..."), ShowFields)
        menu.add_item(tr("~M~emo view"), ShowMemo)
        menu.add_item(tr("~E~dit field..."), EditDbField)
        menu.add_line()
        menu.add_item(tr("~S~earch..."), SearchFor)
        menu.add_item(tr("Search a~g~ain"), ContinueSearch)
        menu.add_line()
        menu.add_item(tr("~C~lose"), CloseWindow)
        return menu

    # -- painting -----------------------------------------------------------------

    def render(self, surface: Surface) -> None:
        db = self.db
        width, height = self.width, self.height
        plain, titles, cursor = self.style, self.part_style("titles"), self.part_style("cursor")
        surface.fill(0, 0, width, height, " ", plain)
        if db is None:
            return
        self._clamp()
        shown = self.shown_fields()
        surface.fill(0, 0, width, 1, " ", titles)
        x = 1
        for index in shown:
            surface.draw_text(x, 0, db.fields[index].name, titles, max(0, width - x))
            x += db.fields[index].width + 1
        for row in range(1, height):
            number = self.top + row - 1
            record = db.record(number)
            if record is None:
                break
            surface.draw_text(0, row, record[:1].decode("cp437", "replace"), plain, 1)
            x = 1
            for index in shown:
                field = db.fields[index]
                style = cursor if number == self.record and index == self.field else plain
                text = db.shown(record, field)
                surface.draw_text(x, row, text, style, max(0, min(len(text), width - x)))
                x += field.width + 1
