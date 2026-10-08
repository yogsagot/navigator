"""A menu box opened on its own, anywhere, answering with the entry chosen.

Turbo Vision's ``TMenuPopup``: what DOS Navigator's ``SelectDrive`` ran to
offer the drive letters over a panel.  It is one :class:`MenuBox`, without the
bar, on a modal layer that covers the screen and takes every key and click,
and it is run the way a dialog is -- :meth:`PopupMenu.execute` returns once it
closes, with the :class:`MenuItem` chosen or None -- so the same rule holds:
**start it with ``spawn``, never await it inside a handler.**

The keys are ``TMenuView.Execute``'s for a box: Up and Down move, skipping
lines and wrapping round, Home and End go to the ends, Enter or the marked
letter chooses, Esc closes.  A click chooses what it is released on, a press
on a box closes every box opened above it, and a press outside every box
closes the popup.

**A box taller than the screen is cut to it and scrolls** (``MenuBox`` has
how); PgUp and PgDn then move a box's height, and the wheel moves the
selection one entry, without wrapping round.

**A submenu opens beside its entry**, as a :class:`MenuSession`'s does:
Enter, Right or a click on a :class:`SubMenu` entry opens its box two
columns in and one row under the entry, Esc or Left closes the top box, and
the answer is the :class:`MenuItem` chosen at whatever depth.  :attr:`box`
stays the first box; :attr:`boxes` is the open stack.

**A caller can add keys** (``keys=("ctrl+up",)``): one of them closes the box
answering with the entry selected in the top box, enabled or not, and :attr:`PopupMenu.pressed`
names the key -- so the caller can act on that entry and open the box again,
as the bookmarks' box does to move one.

**An entry need not ask for a command.**  A bar's item without one is greyed
until its feature exists; a popup's entries are usually choices its caller
reads off the answer, so here an item is enabled unless it is ``disabled``,
and only one that does name a command is asked whether it would run.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from navkit.events import KeyEvent, MouseClickEvent
from navkit.reactive import bind
from navkit.screen import Surface
from navkit.widget import Widget

from navml.widgets.dialog.control.control import parse_shortcut
from navml.widgets.menu.menu_box.menu_box import MenuBox
from navml.widgets.menu.menu_item.menu_item import MenuItem, MenuNode
from navml.widgets.menu.menu_line.menu_line import MenuLine
from navml.widgets.menu.sub_menu.sub_menu import SubMenu

if TYPE_CHECKING:
    from navkit.application import Application


class PopupBox(MenuBox):
    """A :class:`MenuBox` whose command-less items are choices, not stubs."""

    def enabled(self, entry: MenuNode) -> bool:
        if isinstance(entry, MenuItem) and entry.command is None:
            return not entry.disabled
        return super().enabled(entry)


class PopupMenu(Widget):
    """*menu*'s entries in a box at *x*, *y*, the entry *current* selected."""

    def __init__(self, menu: SubMenu | None = None, x: int = 0, y: int = 0, *,
                 current: int = -1, behind: Widget | None = None,
                 keys: tuple[str, ...] = (), **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.menu = menu if menu is not None else SubMenu()
        #: Where the box's top left corner goes, in screen coordinates; it is
        #: moved back onto the screen if it would not fit.
        self.at = (x, y)
        #: The entry selected when the box opens; -1 for the first one.
        self.start = current
        #: The widget whose point of view decides whether an entry that names
        #: a command is enabled.
        self.behind = behind
        #: Keys that close the box on the entry selected; see the module.
        self.keys = keys
        #: Which of :attr:`keys` closed it, or None if it was not one of them.
        self.pressed: str | None = None
        #: The index of the entry selected when the box closed.
        self.selected = -1
        self.box: PopupBox | None = None
        self._pending: asyncio.Future[Any] | None = None
        self.modal = True
        self.can_focus = True
        # The layer covers its parent, all four sides bound, as a menu's does.
        self.x = bind(lambda o: 0)
        self.y = bind(lambda o: 0)
        self.width = bind(lambda o: o.parent.width if o.parent is not None else 0)
        self.height = bind(lambda o: o.parent.height if o.parent is not None else 0)

    def layout(self, width: int, height: int) -> None:
        """The boxes are placed by :meth:`_drop`, never by a cascade."""

    @property
    def boxes(self) -> list[PopupBox]:
        """The open boxes, the first one first and the one taking keys last."""
        return [child for child in self.children if isinstance(child, PopupBox)]

    @staticmethod
    def measure(menu: SubMenu, app: Application | None = None,
                behind: Widget | None = None) -> tuple[int, int]:
        """The ``(width, height)`` the box for *menu* takes."""
        return MenuBox.measure(menu, app, behind)

    # -- running ----------------------------------------------------------------------

    async def execute(self, app: Application) -> MenuItem | None:
        """Show the box and answer with the item chosen, or None for Esc."""
        if getattr(app, "_dispatching", False):
            raise RuntimeError(
                "PopupMenu.execute() cannot be awaited from an event handler; "
                "start it with self.spawn(...) and let the handler return."
            )
        if self._pending is not None:
            raise RuntimeError("this popup is already showing")
        self._pending = asyncio.get_running_loop().create_future()
        app.overlay(self)
        self._open()
        try:
            return await self._pending
        finally:
            self._pending = None
            if self.parent is not None:
                self.parent.remove(self)

    def close(self, result: MenuItem | None = None) -> None:
        """Come down, answering *result*."""
        if self.box is not None:
            self.selected = self.box.current
        if self._pending is not None and not self._pending.done():
            self._pending.set_result(result)
        elif self._pending is None and self.parent is not None:
            self.parent.remove(self)

    def _open(self) -> None:
        self.box = self._drop(self.menu, *self.at, self.start)

    def _drop(self, menu: SubMenu, x: int, y: int, current: int = -1) -> PopupBox:
        """A box for *menu* with its corner at *x*, *y*, kept on the screen."""
        width, height = self.measure(menu, self.application, self.behind)
        width = min(width, max(10, self.width))
        height = min(height, max(3, self.height))
        x = max(0, min(x, self.width - width))
        y = max(0, min(y, self.height - height))
        box = PopupBox(menu, x=x, y=y, width=width, height=height)
        box.behind = self.behind
        self.add(box)
        if box.selectable(current):
            box.current = current
        else:
            box.current = -1
            box.step(1)
        return box

    def choose(self, index: int, box: PopupBox | None = None) -> None:
        """Enter on entry *index* of *box* (the top one): open a submenu
        beside it, or close with an item, if it can be chosen."""
        boxes = self.boxes
        box = box if box is not None else (boxes[-1] if boxes else None)
        entries = box.entries() if box is not None else []
        if not 0 <= index < len(entries):
            return
        entry = entries[index]
        box.current = index
        if not box.enabled(entry):
            return
        if isinstance(entry, SubMenu):
            for later in boxes[boxes.index(box) + 1:]:
                self.remove(later)
            self._drop(entry, box.x + 2, box.y + index - box.top + 2)
        elif isinstance(entry, MenuItem):
            self.close(entry)

    # -- input --------------------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        boxes = self.boxes
        if not boxes:
            return True
        box = boxes[-1]
        if event.matches("escape"):
            if len(boxes) > 1:
                self.remove(box)
            else:
                self.close(None)
        elif event.matches("left") and len(boxes) > 1:
            self.remove(box)
        elif event.matches("right"):
            entries = box.entries()
            if 0 <= box.current < len(entries) and isinstance(entries[box.current], SubMenu):
                self.choose(box.current)
        elif self.keys and event.matches(*self.keys):
            entries = box.entries()
            self.pressed = event.name
            self.close(entries[box.current] if 0 <= box.current < len(entries) else None)
        elif event.matches("up"):
            box.step(-1)
        elif event.matches("down"):
            box.step(1)
        elif event.matches("pageup"):
            box.page(-1)
        elif event.matches("pagedown"):
            box.page(1)
        elif event.matches("home"):
            box.current = -1
            box.step(1)
        elif event.matches("end"):
            box.current = len(box.entries())
            box.step(-1)
        elif event.matches("enter"):
            self.choose(box.current)
        elif event.char and not event.ctrl:
            index = letter_of(box.entries(), event.char)
            if index >= 0:
                self.choose(index)
        return True

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        boxes = self.boxes
        if not boxes:
            return True
        if event.button in ("wheel_up", "wheel_down"):
            boxes[-1].move(-1 if event.button == "wheel_up" else 1)
            return True
        if event.button != "left" or event.is_wheel:
            return True
        box = next((b for b in reversed(boxes) if b.contains(event.x, event.y)), None)
        if box is not None:
            if event.action == "press":
                for later in boxes[boxes.index(box) + 1:]:
                    self.remove(later)
            row = box.entry_at(event.y - box.y)
            inside = box.x + 2 <= event.x < box.x + box.width - 2
            if row >= 0 and inside and box.selectable(row):
                if event.action == "release":
                    self.choose(row, box)
                else:
                    box.current = row
            return True
        if event.action == "press":
            self.close(None)
        return True

    # -- painting -------------------------------------------------------------------------

    def render_tree(self, surface: Surface) -> None:
        """The box over its shadow; the layer itself paints and dims nothing."""
        if not self.visible:
            return
        for box in self.boxes:
            box.render_tree(surface.view(self.x, self.y, self.width, self.height))


def letter_of(entries: list[Any], char: str) -> int:
    """The entry whose marked letter is *char*, or -1."""
    char = char.lower()
    for index, entry in enumerate(entries):
        if isinstance(entry, MenuLine):
            continue
        if parse_shortcut(entry.text)[2] == char:
            return index
    return -1
