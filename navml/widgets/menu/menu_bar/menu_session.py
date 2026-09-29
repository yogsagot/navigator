"""An open menu: the modal layer that holds its boxes and all input.

Turbo Vision ran a menu with ``ExecView``, a nested event loop.  navkit has one
loop and a modal overlay instead, so an open menu is a widget over the whole
screen that paints nothing of its own but the boxes' shadows, and answers
every key and click itself.  The rules it answers them by are
``TMenuView.Execute``'s:

* **Left and Right** move along the bar, re-opening the neighbour's box if one
  was open; inside a nested box Left closes it, and Right opens the selected
  submenu.
* **Up and Down** move within the top box, skipping lines and wrapping round;
  on the bar with nothing dropped, Down drops the box.
* **Enter** opens a submenu or chooses an entry; a letter chooses the entry
  whose marked letter it is.
* **Esc** closes the top box, and from the first box closes the whole menu --
  the bar passes on the Escape it was handed, as Turbo Vision's did.
* **The mouse** selects what it is over while the button is down, and chooses
  on release; a press outside every box and the bar closes the menu.
"""

from __future__ import annotations

from typing import Any

from navkit.events import KeyEvent, MouseClickEvent
from navkit.reactive import bind
from navkit.screen import Surface
from navkit.style import SHADOW  # noqa: F401 -- re-exported; tests read it here
from navkit.widget import Widget

from navml.widgets.dialog.control.control import parse_shortcut
from navml.widgets.menu.menu_box.menu_box import MenuBox
from navml.widgets.menu.menu_item.menu_item import MenuItem
from navml.widgets.menu.menu_line.menu_line import MenuLine
from navml.widgets.menu.sub_menu.sub_menu import SubMenu

class MenuSession(Widget):
    """The open menu of one :class:`MenuBar`."""

    def __init__(self, bar: Any, behind: Widget | None) -> None:
        super().__init__()
        self.bar = bar
        #: The widget that had the keyboard before the menu took it -- what
        #: decides which entries are enabled, and where a chosen command starts.
        self.behind = behind
        self.modal = True
        self.can_focus = True
        # Bound, all four sides, so that a layout parent steps around it --
        # which is also why it asks for no ``dock``: that hint is a
        # ``DockLayout``'s, and a menu must not need one to be imported.
        self.x = bind(lambda o: 0)
        self.y = bind(lambda o: 0)
        self.width = bind(lambda o: o.parent.width if o.parent is not None else 0)
        self.height = bind(lambda o: o.parent.height if o.parent is not None else 0)

    def layout(self, width: int, height: int) -> None:
        """The boxes are placed by :meth:`_drop`, never by a cascade."""

    @property
    def boxes(self) -> list[MenuBox]:
        return [child for child in self.children if isinstance(child, MenuBox)]

    # -- the bar -------------------------------------------------------------------

    def select(self, index: int, *, drop: bool) -> None:
        """Highlight bar entry *index*, closing every box; *drop* opens its box."""
        entries = self.bar.entries()
        if not entries:
            return
        index %= len(entries)
        for box in self.boxes:
            self.remove(box)
        self.bar.current = index
        if drop and isinstance(entries[index], SubMenu) and not entries[index].disabled:
            start, _ = self.bar.item_span(index)
            bx, by = self._bar_origin()
            self._drop(entries[index], bx + start - 1, by + 1)

    def _bar_origin(self) -> tuple[int, int]:
        """Where the bar is on this layer, which covers the screen."""
        dx, dy = self.bar.offset()
        return dx + self.bar.x, dy + self.bar.y

    def _drop(self, menu: SubMenu, x: int, y: int) -> MenuBox:
        """Open a box for *menu* with its corner at *x*, *y*, kept on screen."""
        width, height = MenuBox.measure(menu, self.application, self._asker())
        x = max(0, min(x, self.width - width))
        y = max(0, min(y, self.height - height))
        box = MenuBox(menu, x=x, y=y, width=width, height=height)
        box.behind = self._asker()
        self.add(box)
        box.current = -1
        box.step(1)
        return box

    def _asker(self) -> Widget | None:
        """Whose point of view the entries are judged from."""
        app = self.application
        return self.behind or (app.root if app is not None else None)

    # -- choosing --------------------------------------------------------------------

    async def choose(self, box: MenuBox, index: int) -> None:
        """Enter on entry *index* of *box*: open it, or close and run it."""
        entries = box.entries()
        if not 0 <= index < len(entries):
            return
        entry = entries[index]
        box.current = index
        if not box.enabled(entry):
            return
        if isinstance(entry, SubMenu):
            if box is not self.boxes[-1]:
                for later in self.boxes[self.boxes.index(box) + 1:]:
                    self.remove(later)
            self._drop(entry, box.x + 2, box.y + index + 2)
            return
        if isinstance(entry, MenuItem):
            await self._run(entry)

    async def _run(self, item: MenuItem) -> None:
        """Close the menu, then ask for the command from where the keys were."""
        app = self.application
        self.bar.close()
        if app is not None:
            await app.run_command(item.command)

    async def _choose_bar(self, index: int) -> None:
        """Enter on a bar entry: drop a submenu, run an item."""
        entry = self.bar.entries()[index]
        if entry.disabled:
            return
        if isinstance(entry, SubMenu):
            self.select(index, drop=True)
        elif isinstance(entry, MenuItem):
            probe = MenuBox(None)
            probe.behind = self._asker()
            self.add(probe)
            enabled = probe.enabled(entry)
            self.remove(probe)
            if enabled:
                await self._run(entry)

    # -- keys -------------------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        boxes = self.boxes
        bar = self.bar
        if event.matches("f10"):
            bar.close()
            return True
        if event.alt and len(event.key) == 1:
            index = bar.hotkey(event.key)
            if index >= 0:
                self.select(index, drop=True)
            return True
        if not boxes:
            return await self._bar_key(event)
        top = boxes[-1]
        if event.matches("escape"):
            if len(boxes) > 1:
                self.remove(top)
            else:
                bar.close()
        elif event.matches("up"):
            top.step(-1)
        elif event.matches("down"):
            top.step(1)
        elif event.matches("home"):
            top.current = -1
            top.step(1)
        elif event.matches("end"):
            top.current = len(top.entries())
            top.step(-1)
        elif event.matches("enter"):
            await self.choose(top, top.current)
        elif event.matches("right"):
            entries = top.entries()
            if 0 <= top.current < len(entries) and isinstance(entries[top.current], SubMenu):
                await self.choose(top, top.current)
            elif len(boxes) == 1:
                self.select(bar.current + 1, drop=True)
        elif event.matches("left"):
            if len(boxes) > 1:
                self.remove(top)
            else:
                self.select(bar.current - 1, drop=True)
        elif event.char and not event.ctrl:
            index = _letter(top.entries(), event.char)
            if index >= 0:
                await self.choose(top, index)
        return True

    async def _bar_key(self, event: KeyEvent) -> bool:
        """A key while the bar is highlighted and nothing is dropped."""
        bar = self.bar
        if event.matches("escape"):
            bar.close()
        elif event.matches("left"):
            self.select(bar.current - 1, drop=False)
        elif event.matches("right"):
            self.select(bar.current + 1, drop=False)
        elif event.matches("down", "enter"):
            await self._choose_bar(bar.current)
        elif event.char and not event.ctrl:
            index = bar.hotkey(event.char)
            if index >= 0:
                bar.current = index
                await self._choose_bar(index)
        return True

    # -- the mouse -----------------------------------------------------------------------

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if event.button != "left" or event.is_wheel:
            return True
        bx, by = self._bar_origin()
        if event.y == by and bx <= event.x < bx + self.bar.width:
            index = self.bar.entry_at(event.x - bx)
            if index >= 0 and event.action != "release" and (
                index != self.bar.current or not self.boxes
            ):
                self.select(index, drop=True)
            elif index >= 0 and event.action == "release":
                if not isinstance(self.bar.entries()[index], SubMenu):
                    await self._choose_bar(index)
            return True
        for box in reversed(self.boxes):
            if box.contains(event.x, event.y):
                row = box.entry_at(event.y - box.y)
                inside = box.x + 2 <= event.x < box.x + box.width - 2
                if row >= 0 and inside and box.selectable(row):
                    if event.action == "release":
                        await self.choose(box, row)
                    else:
                        box.current = row
                return True
        if event.action == "press":
            self.bar.close()
        return True

    # -- painting ------------------------------------------------------------------------

    def render_tree(self, surface: Surface) -> None:
        """Each box over its own shadow, the boxes in the order they opened.

        Every :class:`MenuBox` casts a shadow (``Widget.shadow``), painted as
        part of painting that box, so a nested box shades its parent as Turbo
        Vision's did.  Overridden only so that the session itself, a modal,
        paints nothing and dims nothing.
        """
        if not self.visible:
            return
        own = surface.view(self.x, self.y, self.width, self.height)
        for box in self.boxes:
            box.render_tree(own)


def _letter(entries: list, char: str) -> int:
    """The entry whose marked letter is *char*, or -1."""
    char = char.lower()
    for index, entry in enumerate(entries):
        if isinstance(entry, MenuLine):
            continue
        if parse_shortcut(entry.text)[2] == char:
            return index
    return -1
