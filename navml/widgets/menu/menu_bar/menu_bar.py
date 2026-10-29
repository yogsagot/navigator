"""The menu bar: Turbo Vision's ``TMenuBar``, and the menus it opens.

The bar's entries are its children -- :class:`SubMenu` and :class:`MenuItem`
blocks in markup -- and it paints them the way ``TMenuBar.Draw`` does: from
column 1, each caption with a space either side, the selected one in the
*Selected* slot across all three.

**While a menu is open it holds all input**, as Turbo Vision's
``TMenuView.Execute`` did by running modally: :meth:`open` overlays a
:class:`~navml.widgets.menu.menu_bar.menu_session.MenuSession` over the whole
screen, which paints the open boxes and their shadows and takes every key and
every click until it closes.  **Choosing an entry closes the menu first and
asks for the command second**, so the command starts from the widget that had
the keyboard before the menu took it -- exactly where its key would have.

**A window can put menus of its own on the bar** while it is the one in use:
:attr:`MenuBar.context` holds a widget, and every :class:`SubMenu` among its
children joins the bar at the place its ``before``/``after`` names.  Whoever
owns the bar binds ``context`` -- Navigator's shell binds it to the desktop's
active window -- so the entries come and go with the activation.  They are
shown and chosen like the bar's own, and their commands start from the focus
as every menu command does, which is inside that window.

**A caption's tooltip is its entry's** ``tooltip`` -- what the menu holds --
and the Alt+letter that drops it, ``Alt-F``; a window's menus bring their
own.  Not Turbo Vision's, which had none.
"""

from __future__ import annotations

from typing import Any

from navkit import keyboard
from navkit.bidi import display_width
from navkit.events import KeyEvent, MouseClickEvent
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.tooltip import with_keys
from navkit.widget import Widget

from navml.component import take_declared
from navml.widgets.dialog.control.control import parse_shortcut, shortcut_runs
from navml.widgets.menu.menu_item.menu_item import MenuNode
from navml.widgets.menu.sub_menu.sub_menu import MenuContainer, SubMenu


class MenuBar(MenuContainer, Widget):
    """A row of menu captions, and the menus they open.

    Changed from Python like any submenu -- see
    :class:`~navml.widgets.menu.sub_menu.MenuContainer` -- so a plugin can put
    a menu of its own on the bar with :meth:`add_submenu`.
    """

    #: A caption, and its marked letter.  Both take ``:selected`` and
    #: ``:disabled``.
    parts = ("item", "hotkey")

    #: Which entry is highlighted, as an index into :meth:`entries`; -1 while
    #: the menu is closed.
    current: int = reactive(-1)

    #: The widget whose own :class:`SubMenu` children join the bar, or None.
    context: Any = reactive(None)

    #: The cells at the bar's right end that something floating over it
    #: covers -- Navigator's clock -- which a crowded bar keeps clear of.
    reserve: int = reactive(0)

    def __init__(self, **kwargs: Any) -> None:
        take_declared(self, kwargs)
        super().__init__(**kwargs)
        #: The open menu, or None.
        self.session: Any = None

    def entries(self) -> list[MenuNode]:
        """The entries the bar shows: its own, with the context's spliced in.

        Only this list carries the contributed ones.  ``all_entries()`` and
        everything that changes the bar stay the bar's own, so a plugin can
        neither anchor on a window's menu nor remove it by accident.  An
        anchor naming no entry of the bar raises, as an ``add_*`` anchor does.
        """
        own = super().entries()
        context = self.context
        if context is None:
            return own
        for menu in context.children:
            if not isinstance(menu, SubMenu) or menu.hidden or _is_context(menu):
                continue
            if menu.before and menu.after:
                raise ValueError(
                    f"{menu.text!r} goes before one entry or after one, not both"
                )
            anchor = menu.before or menu.after
            if not anchor:
                own.append(menu)
                continue
            target = self._find(anchor)
            index = own.index(target) if target in own else len(own)
            own.insert(index + (1 if menu.after and target in own else 0), menu)
        return own

    def layout(self, width: int, height: int) -> None:
        """Take the size offered and hand none of it on: the entries are data."""
        from navkit.reactive import is_bound

        if not is_bound(self, Widget.width):
            self.width = width
        if not is_bound(self, Widget.height):
            self.height = height

    # -- geometry ----------------------------------------------------------------

    def tight(self) -> bool:
        """Whether the captions, a blank either side, would run into
        :attr:`reserve`: then each keeps only the blank before it, one
        between captions rather than two.  A departure, for Chinese and
        Japanese, whose ``ファイル(F)`` is two cells to a character and would
        push *Window* under the clock or off an 80-column bar."""
        end = 1 + sum(display_width(parse_shortcut(entry.text)[0]) + 2 for entry in self.entries())
        return end > self.width - self.reserve

    def item_span(self, index: int) -> tuple[int, int]:
        """Where entry *index* sits on the bar: ``(start, width)``, as
        ``TMenuBar.GetItemRect`` -- the caption plus a space either side, or
        before it only while the bar is :meth:`tight`."""
        x = 1
        blanks = 1 if self.tight() else 2
        for position, entry in enumerate(self.entries()):
            length = display_width(parse_shortcut(entry.text)[0]) + blanks
            if position == index:
                return x, length
            x += length
        return x, 0

    def tooltip_at(self, x: int, y: int) -> str:
        """The entry's own tooltip, and the Alt+letter that opens it."""
        index = self.entry_at(x)
        if index < 0:
            return super().tooltip_at(x, y)
        entry = self.entries()[index]
        letter = parse_shortcut(entry.text)[2]
        # Only a letter a keyboard types: ``≡`` has none but F10.  A Hebrew
        # or Arabic one is typed on its own layout, and on a US one by the
        # key in its place (:meth:`hotkey`), which is said too.
        keys = []
        if letter.isalnum():
            keys.append(f"Alt-{letter.upper()}")
            latin = keyboard.latin(letter)
            if latin is not None:
                keys.append(f"Alt-{latin.upper()}")
        return with_keys(entry.tooltip, keys)

    def entry_at(self, column: int) -> int:
        """The entry under *column* of the bar, or -1."""
        for index in range(len(self.entries())):
            start, length = self.item_span(index)
            if start <= column < start + length:
                return index
        return -1

    def hotkey(self, letter: str) -> int:
        """The entry whose marked letter is *letter*, or -1 -- or, for a Latin
        *letter*, whose Hebrew or Arabic letter is typed by that key on its own
        layout (:mod:`navkit.keyboard`): a translated menu opens with Alt+E on
        a US keyboard where its caption marks ק."""
        letter = letter.lower()
        marked = [parse_shortcut(entry.text)[2] for entry in self.entries()]
        if letter in marked:
            return marked.index(letter)
        return next((index for index, mark in enumerate(marked) if keyboard.same_key(letter, mark)), -1)

    # -- painting ------------------------------------------------------------------

    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, 1, " ", self.style)
        for index, entry in enumerate(self.entries()):
            start, length = self.item_span(index)
            if start + length - 1 >= self.width:
                break
            states = {"selected": index == self.current, "disabled": entry.disabled}
            style = self.part_style("item", **states)
            caption, mark, _ = parse_shortcut(entry.text)
            after = [(" ", style)] if length > display_width(caption) + 1 else []
            surface.draw_runs(start, 0, [(" ", style), *shortcut_runs(
                caption, mark, style, self.part_style("hotkey", **states)), *after])

    # -- opening and closing ----------------------------------------------------------

    @property
    def is_open(self) -> bool:
        return self.session is not None

    def hint(self) -> str:
        """What the highlighted entry says of itself while the menu is open:
        the top box's current row's tooltip and why it is greyed
        (:meth:`MenuBox.hint`), else the highlighted caption's tooltip; ``""``
        while closed.  Turbo Vision's ``THintStatusLine``, which showed the
        current item's hint on the status line -- so a menu read from the
        keyboard says what the pointer would."""
        session = self.session
        if session is None:
            return ""
        boxes = session.boxes
        if boxes:
            box = boxes[-1]
            entries = box.entries()
            if 0 <= box.current < len(entries):
                return box.hint(entries[box.current])
            return ""
        entries = self.entries()
        return entries[self.current].tooltip if 0 <= self.current < len(entries) else ""

    def open(self, index: int = 0, *, drop: bool = False) -> None:
        """Take the input and highlight entry *index*; *drop* opens its box.

        F10 highlights the first entry and drops nothing, as ``cmMenu`` did;
        Alt+letter and a click drop the box straight away.
        """
        from navml.widgets.menu.menu_bar.menu_session import MenuSession

        app = self.application
        if app is None or not self.entries():
            return
        if self.session is None:
            behind = app.focused
            self.session = MenuSession(self, behind)
            app.overlay(self.session)
        self.session.select(index, drop=drop)

    def close(self) -> None:
        """Put the menu away and give the keyboard back."""
        session, self.session = self.session, None
        self.current = -1
        if session is not None and session.parent is not None:
            session.parent.remove(session)

    async def open_hotkey(self, event: KeyEvent) -> bool:
        """Alt+letter: drop the entry whose marked letter it is.

        For whoever holds the bar to call from its ``on_key``: the letters are
        read off the captions, so they cannot be a key table, which is fixed
        when its class is made.
        """
        if not event.alt or event.ctrl or len(event.key) != 1:
            return False
        index = self.hotkey(event.key)
        if index < 0:
            return False
        self.open(index, drop=True)
        return True

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """A press on a caption opens its menu there and then."""
        if event.action != "press" or event.button != "left":
            return False
        index = self.entry_at(event.x)
        if index < 0:
            return False
        self.open(index, drop=True)
        return True


def _is_context(menu: SubMenu) -> bool:
    """Whether *menu* is a widget's context menu, which never joins the bar.

    Imported here rather than at the top: the context menu's module imports
    the popup, which imports this group's boxes.
    """
    from navml.widgets.menu.context_menu.context_menu import ContextMenu

    return isinstance(menu, ContextMenu)
