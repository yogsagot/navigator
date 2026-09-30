"""One open submenu, painted the way Turbo Vision's ``TMenuBox.Draw`` does.

Every measurement here is ``MENUS.PAS``'s:

* **A box is framed one column in**: a space, the frame, the entries, the
  frame, a space -- ``' ┌─┐ '``, ``' │ │ '`` and ``' └─┘ '`` are its three
  line shapes, and a :class:`MenuLine` is ``' ├─┤ '``.
* **An entry's colour fills the whole row inside the frame**, so the
  selection bar runs from frame to frame; its caption starts at column 3, and
  its key is right-aligned three columns in from the far edge.  A submenu gets
  ``►`` where the key would go.
* **A toggle that is on is ticked** in the column between the frame and the
  caption -- ``√``, or ``+`` with no Unicode -- which Turbo Vision left blank,
  so a tick costs no width.  Whether it is on is the command's to say, through
  :meth:`navkit.widget.Widget.checks`.
* **Width is the widest entry plus six**, plus the key and two spaces, or plus
  three for a submenu's arrow; never under ten.  Height is one row per entry
  and two for the frame.

The frame uses the widget's ``border`` like any other frame, so a terminal
with no box-drawing characters gets ``+-+`` rather than replacement boxes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from navkit import commands
from navkit.glyphs import GLYPHS_ASCII, GLYPHS_UNICODE, SCROLLBARS
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.widget import Widget

from navml.widgets.dialog.control.control import parse_shortcut
from navml.widgets.menu.menu_item.menu_item import MenuItem, MenuNode
from navml.widgets.menu.menu_line.menu_line import MenuLine
from navml.widgets.menu.sub_menu.sub_menu import SubMenu

if TYPE_CHECKING:
    from navkit.application import Application


class MenuBox(Widget):
    """A framed column of entries, one of them selected."""

    #: An entry's row and its marked letter.  Both take ``:selected`` and
    #: ``:disabled``, which are the four combinations the Colors dialog's
    #: *Menus* group has a slot for.
    parts = ("item", "hotkey")

    #: A dropped box casts Turbo Vision's shadow, as every menu box did.
    shadow: bool = True

    #: What ticks a toggle that is on, and its ASCII stand-in -- the same two
    #: characters Navigator's panel tags a file with.
    CHECK = "√"
    CHECK_ASCII = "+"

    #: Which entry is selected, as an index into :meth:`entries`; -1 for none.
    current: int = reactive(-1)

    def __init__(self, menu: SubMenu | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        #: The submenu this box shows.
        self.menu = menu
        #: The widget whose point of view decides what is enabled -- the one
        #: that had the keyboard before the menu took it.  Set by whoever
        #: opens the box; None asks from wherever the focus is.
        self.behind: Widget | None = None

    def layout(self, width: int, height: int) -> None:
        """Keep the size it was opened with.

        A box is measured from its entries and placed by whoever opens it;
        ``Widget.add`` would otherwise lay it out into its parent's size the
        moment it joined, and a menu layer covers the whole screen.
        """

    def entries(self) -> list[MenuNode]:
        return self.menu.entries() if self.menu is not None else []

    @staticmethod
    def measure(menu: SubMenu, app: Application | None = None,
                behind: Widget | None = None) -> tuple[int, int]:
        """The ``(width, height)`` a box for *menu* takes, as ``TMenuBox.Init``."""
        width, height = 10, 2
        for entry in menu.entries():
            height += 1
            if isinstance(entry, MenuLine):
                continue
            length = len(parse_shortcut(entry.text)[0]) + 6
            if isinstance(entry, SubMenu):
                length += 3
            else:
                key = key_caption(entry, app, behind)
                if key:
                    length += len(key) + 2
            width = max(width, length)
        return width, height

    # -- what an entry is --------------------------------------------------------

    def enabled(self, entry: MenuNode) -> bool:
        """Whether choosing *entry* would do anything.

        Not if it is ``disabled``; otherwise a submenu always opens, and an
        item runs when its command would.
        """
        if entry.disabled:
            return False
        if isinstance(entry, SubMenu):
            return True
        if not isinstance(entry, MenuItem) or entry.command is None:
            return False
        app = self.application
        return app is not None and app.command_enabled(entry.command, self.behind)

    def checked(self, entry: MenuNode) -> bool:
        """Whether *entry* is a toggle that is on now."""
        if not isinstance(entry, MenuItem) or entry.command is None:
            return False
        app = self.application
        return app is not None and app.command_checked(entry.command, self.behind) is True

    def selectable(self, index: int) -> bool:
        """Every entry but a line can hold the selection, a disabled one too."""
        entries = self.entries()
        return 0 <= index < len(entries) and not isinstance(entries[index], MenuLine)

    def step(self, delta: int) -> None:
        """Move the selection by one, skipping lines and wrapping round."""
        entries = self.entries()
        if not entries:
            return
        index = self.current
        for _ in entries:
            index = (index + delta) % len(entries)
            if self.selectable(index):
                self.current = index
                return

    def entry_at(self, row: int) -> int:
        """The entry on *row* of this box, or -1 for the frame."""
        index = row - 1
        return index if 0 <= index < len(self.entries()) else -1

    # -- painting ---------------------------------------------------------------

    def render(self, surface: Surface) -> None:
        width, normal = self.width, self.style
        tl, tr, bl, br, horizontal, vertical = self.box_charset()
        left_tee, right_tee = self.box_joins()[:2]
        arrow = SCROLLBARS["dos" if self.glyphs >= GLYPHS_UNICODE else "ascii"][3]
        check = self.CHECK if self.glyphs > GLYPHS_ASCII else self.CHECK_ASCII

        def frame_line(y: int, ends: tuple[str, str], middle: str, style) -> None:
            surface.draw_text(0, y, " " + ends[0], normal)
            surface.draw_text(2, y, middle * max(0, width - 4), style)
            surface.draw_text(width - 2, y, ends[1] + " ", normal)

        frame_line(0, (tl, tr), horizontal, normal)
        for index, entry in enumerate(self.entries()):
            y = index + 1
            if isinstance(entry, MenuLine):
                frame_line(y, (left_tee, right_tee), horizontal, normal)
                continue
            states = {"selected": index == self.current,
                      "disabled": not self.enabled(entry)}
            row = self.part_style("item", **states)
            frame_line(y, (vertical, vertical), " ", row)
            if self.checked(entry):
                surface.draw_text(2, y, check, row)
            caption, start, _ = parse_shortcut(entry.text)
            surface.draw_text(3, y, caption, row, max(0, width - 6))
            if 0 <= start < len(caption):
                surface.draw_text(3 + start, y, caption[start],
                                  self.part_style("hotkey", **states))
            if isinstance(entry, SubMenu):
                surface.draw_text(width - 4, y, arrow, row)
            else:
                key = key_caption(entry, self.application, self.behind)
                if key:
                    surface.draw_text(width - 3 - len(key), y, key, row)
        frame_line(len(self.entries()) + 1, (bl, br), horizontal, normal)


def key_caption(item: MenuItem, app: Application | None,
                behind: Widget | None) -> str:
    """The key shown beside *item*: its live binding, else DOS Navigator's.

    A bound key is read off the key tables, so a menu can never claim a key
    that does something else; an entry nobody has bound yet shows the key the
    original gave it, which is also the key it will get.
    """
    if app is not None and item.command is not None:
        key = commands.key_for(app, item.command, behind)
        if key is not None:
            return commands.key_label(key)
    return item.key
