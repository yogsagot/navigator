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

**A caller can add buttons** (``buttons=("left", "right")``), as a context
menu does: then a press with that button, a drag along the entries and a
release on one chooses it.  The release of the click that opened the box does
not choose, because the box may have opened under the pointer.

**A caller can add keys** (``keys=("ctrl+up",)``): one of them closes the box
answering with the entry selected in the top box, enabled or not, and :attr:`PopupMenu.pressed`
names the key -- so the caller can act on that entry and open the box again,
as the bookmarks' box does to move one.  In a submenu the entry is the
submenu's, and **the box can open again with it dropped**
(``submenu=(index, current)``: the first box's entry *index* opened, *current*
selected in it), so a key acting on a submenu's entry keeps the user there.

**The first box can carry a title** (``title="Bookmarks"``), centred in its
top frame; :meth:`measure` takes the same title so the caller places a box as
wide as the one shown.  A **footer** (``footer="To /tmp"``) goes in its bottom
frame the same way.

**A filterable submenu filters as it is typed in** (``SubMenu.filterable``),
a departure for long lists of names with no letter marked: the first
printable key shows a filter line under the top frame -- hidden until then
-- and the box keeps the entries whose caption holds the text, in any case.
A ``centred`` submenu's box opens in the middle of the screen's height, still
beside its entry, and stays there as the filter fits it.
Backspace edits it, Esc or a click on its ``×`` empties it (Esc closes the
box only once it is empty), and the box grows by the line's row while it
shows and fits to what is left; the terminal's caret sits at the text's end.

**An entry need not ask for a command.**  A bar's item without one is greyed
until its feature exists; a popup's entries are usually choices its caller
reads off the answer, so here an item is enabled unless it is ``disabled``,
and only one that does name a command is asked whether it would run.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Sequence

from navkit import keyboard
from navkit.bidi import display_width, fit_cells
from navkit.events import KeyEvent, MouseClickEvent
from navkit.glyphs import GLYPHS_UNICODE
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
    """A :class:`MenuBox` whose command-less items are choices, not stubs;
    one for a ``filterable`` submenu filters them as it is typed in."""

    #: What the filter's line clears it with, and its ASCII stand-in.
    CLEAR = "×"
    CLEAR_ASCII = "x"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        #: The text typed into the filter; empty hides its line.
        self.filter = ""
        #: The height the box opened with, and the most it may grow to: what
        #: :meth:`set_filter` fits it between.  Set by whoever drops it.
        self.opened_height = self.height if isinstance(self.height, int) else 0
        self.room = self.opened_height

    @property
    def filterable(self) -> bool:
        return bool(getattr(self.menu, "filterable", False))

    def enabled(self, entry: MenuNode) -> bool:
        if isinstance(entry, MenuItem) and entry.command is None:
            return not entry.disabled
        return super().enabled(entry)

    def entries(self) -> list[MenuNode]:
        """The submenu's entries; while filtering, those whose caption holds
        the filter (lines dropped)."""
        entries = super().entries()
        if not self.filter:
            return entries
        wanted = self.filter.casefold()
        return [entry for entry in entries if not isinstance(entry, MenuLine)
                and wanted in parse_shortcut(entry.text)[0].casefold()]

    def head(self) -> int:
        return 1 if self.filter else 0

    def set_filter(self, text: str) -> None:
        """Filter by *text*: the selection kept on its entry if it is still
        shown, else the first; the box fitted to what is shown."""
        before = super().entries() if not self.filter else self.entries()
        was = before[self.current] if 0 <= self.current < len(before) else None
        self.filter = text
        entries = self.entries()
        if text:
            self.height = max(3, min(self.room, len(entries) + 3))
        else:
            self.height = self.opened_height
        if getattr(self.menu, "centred", False) and self.parent is not None:
            self.y = max(0, (self.parent.height - self.height) // 2)
        self.top = 0
        if was is not None and was in entries:
            self.current = entries.index(was)
        else:
            self.current = -1
            self.step(1)
        self.invalidate()

    def clear_at(self, x: int, y: int) -> bool:
        """Whether *x*, *y* (the box's own) is the filter line's ``×``."""
        return bool(self.filter) and y == 1 and self.width - 5 <= x <= self.width - 3

    def caret(self) -> tuple[int, int] | None:
        """Where the caret goes, in the box's coordinates: the filter's end."""
        if not self.filter:
            return None
        return min(3 + display_width(self.filter), self.width - 6), 1

    def render(self, surface: Surface) -> None:
        super().render(surface)
        if not self.filter:
            return
        vertical = self.box_charset()[5]
        row = self.part_style("item")
        # The whole row, the margin outside the frame too, as every row of the box.
        surface.draw_text(0, 1, " " + vertical, self.style)
        surface.draw_text(2, 1, " " * max(0, self.width - 4), row)
        surface.draw_text(self.width - 2, 1, vertical + " ", self.style)
        shown = self.filter
        room = max(0, self.width - 9)
        if display_width(shown) > room:
            # The end of what is typed, where the caret is.
            while shown and display_width(shown) > room:
                shown = shown[1:]
        surface.draw_text(3, 1, fit_cells(shown, room), row)
        clear = self.CLEAR if self.glyphs >= GLYPHS_UNICODE else self.CLEAR_ASCII
        surface.draw_text(self.width - 4, 1, clear, self.part_style("hotkey"))


class PopupMenu(Widget):
    """*menu*'s entries in a box at *x*, *y*, the entry *current* selected."""

    def __init__(self, menu: SubMenu | None = None, x: int = 0, y: int = 0, *,
                 current: int = -1, behind: Widget | None = None,
                 keys: tuple[str, ...] = (), title: str = "", footer: str = "",
                 buttons: tuple[str, ...] = ("left",), submenu: tuple[int, int] | None = None,
                 hints: Sequence[tuple[str, str]] = (), **kwargs: Any) -> None:
        super().__init__(**kwargs)
        #: A submenu of the first box to open as the box opens, and the entry
        #: to select in it: ``(index, current)``; see the module.
        self.submenu = submenu
        self.menu = menu if menu is not None else SubMenu()
        #: The caption in the first box's top frame; empty for none.
        self.title = title
        #: The caption in the first box's bottom frame; empty for none.
        self.footer = footer
        #: What the key bar says while the first box is up: the *keys* it
        #: takes, as ``(label, caption)`` -- a submenu's own
        #: :attr:`~navml.widgets.menu.sub_menu.SubMenu.hints` while it is open.
        self.hints = tuple(hints)
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
        #: The mouse buttons that choose; a context menu adds ``right``.
        self.buttons = buttons
        #: Whether a button has pressed or moved onto an entry since the box
        #: opened.  Until it has, its release chooses nothing:
        #: the release of the right click that opened a context menu would
        #: otherwise choose whatever the box put under the pointer.
        self._dragged = False
        #: Which of :attr:`keys` closed it, or None if it was not one of them.
        self.pressed: str | None = None
        #: The index of the entry selected when the box closed.
        self.selected = -1
        self.box: PopupBox | None = None
        self._pending: asyncio.Future[Any] | None = None
        self.modal = True
        self.can_focus = True
        # The layer covers its parent, all four sides bound, as a menu's does.
        self.fill_parent()

    def layout(self, width: int, height: int) -> None:
        """The boxes are placed by :meth:`_drop`, never by a cascade."""

    @property
    def boxes(self) -> list[PopupBox]:
        """The open boxes, the first one first and the one taking keys last."""
        return [child for child in self.children if isinstance(child, PopupBox)]

    def key_hints(self) -> Sequence[tuple[str, str]]:
        """The keys the box taking keys takes: its submenu's hints, if it has
        any, else the popup's own (:attr:`hints`)."""
        for box in reversed(self.boxes):
            if box is not getattr(self, "box", None) and getattr(box.menu, "hints", ()):
                return box.menu.hints
        return self.hints

    @staticmethod
    def measure(menu: SubMenu, app: Application | None = None,
                behind: Widget | None = None, title: str = "",
                footer: str = "") -> tuple[int, int]:
        """The ``(width, height)`` the box for *menu* takes, titled *title*
        with *footer* below."""
        return MenuBox.measure(menu, app, behind, title, footer)

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
        self.box = self._drop(self.menu, *self.at, self.start, self.title, self.footer)
        if self.submenu is not None:
            index, current = self.submenu
            entries = self.box.entries()
            if 0 <= index < len(entries) and isinstance(entries[index], SubMenu):
                self.choose(index, self.box)
                inner = self.boxes[-1]
                if inner is not self.box and inner.selectable(current):
                    inner.current = current

    def _drop(self, menu: SubMenu, x: int, y: int, current: int = -1,
              title: str = "", footer: str = "") -> PopupBox:
        """A box for *menu* with its corner at *x*, *y*, kept on the screen."""
        width, height = self.measure(menu, self.application, self.behind, title, footer)
        width = min(width, max(10, self.width))
        height = min(height, max(3, self.height))
        x = max(0, min(x, self.width - width))
        if getattr(menu, "centred", False):
            y = (self.height - height) // 2
        y = max(0, min(y, self.height - height))
        box = PopupBox(menu, title=title, footer=footer, x=x, y=y, width=width, height=height)
        box.opened_height = height
        # A filter's line takes a row: the box may grow by it, as far as the screen.
        # A centred box moves up to make that room.
        below = self.height if getattr(menu, "centred", False) else self.height - y
        box.room = max(height, min(height + 1, below))
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
            self._drop(entry, box.x + 2, box.y + index - box.top + box.head() + 2, footer=entry.footer)
        elif isinstance(entry, MenuItem):
            self.close(entry)

    # -- input --------------------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        boxes = self.boxes
        if not boxes:
            return True
        box = boxes[-1]
        if box.filterable and self._filter_key(box, event):
            return True
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

    def _filter_key(self, box: PopupBox, event: KeyEvent) -> bool:
        """A key a filterable box takes for its filter; whether it was one."""
        if event.matches("escape") and box.filter:
            box.set_filter("")
        elif event.matches("backspace") and box.filter:
            box.set_filter(box.filter[:-1])
        elif event.char and event.char.isprintable() and not event.ctrl and not event.alt \
                and (event.char != " " or box.filter):
            box.set_filter(box.filter + event.char)
        else:
            return False
        return True

    def cursor_position(self) -> tuple[int, int] | None:
        """The caret at the end of the top box's filter, while it has one."""
        boxes = self.boxes
        caret = boxes[-1].caret() if boxes else None
        if caret is None:
            return None
        return boxes[-1].x + caret[0], boxes[-1].y + caret[1]

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        boxes = self.boxes
        if not boxes:
            return True
        if event.button in ("wheel_up", "wheel_down"):
            boxes[-1].move(-1 if event.button == "wheel_up" else 1)
            return True
        if event.is_wheel or event.button == "none":
            return True
        if event.button not in self.buttons:
            # Any other button pressed outside still closes, as a click does.
            box = next((b for b in boxes if b.contains(event.x, event.y)), None)
            if event.action == "press" and box is None:
                self.close(None)
            return True
        box = next((b for b in reversed(boxes) if b.contains(event.x, event.y)), None)
        if box is not None:
            if event.action == "press":
                for later in boxes[boxes.index(box) + 1:]:
                    self.remove(later)
                if box.clear_at(event.x - box.x, event.y - box.y):
                    box.set_filter("")
                    return True
            row = box.entry_at(event.y - box.y)
            inside = box.x + 2 <= event.x < box.x + box.width - 2
            if row >= 0 and inside and box.selectable(row):
                if event.action == "release":
                    if event.button == "left" or self._dragged:
                        self.choose(row, box)
                else:
                    # A press or a drag onto an entry, after the opening click.
                    self._dragged = True
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
    """The entry whose marked letter is *char*, or -1 -- else the one whose
    letter is typed by *char*'s key on another layout (Hebrew or Arabic and
    Latin, :func:`navkit.keyboard.same_key`): a Latin S~S~H with a Hebrew
    layout on, or a Hebrew menu's letter on a US keyboard."""
    char = char.lower()
    for index, entry in enumerate(entries):
        if isinstance(entry, MenuLine):
            continue
        if parse_shortcut(entry.text)[2] == char:
            return index
    for index, entry in enumerate(entries):
        if not isinstance(entry, MenuLine) and keyboard.same_key(char, parse_shortcut(entry.text)[2]):
            return index
    return -1
