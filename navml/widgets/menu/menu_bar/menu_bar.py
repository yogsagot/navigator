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
"""

from __future__ import annotations

from typing import Any

from navkit.events import KeyEvent, MouseClickEvent
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.widget import Widget

from navml.component import take_declared
from navml.widgets.dialog.control.control import parse_shortcut
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
            if not isinstance(menu, SubMenu) or menu.hidden:
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

    def item_span(self, index: int) -> tuple[int, int]:
        """Where entry *index* sits on the bar: ``(start, width)``, as
        ``TMenuBar.GetItemRect`` -- the caption plus a space either side."""
        x = 1
        for position, entry in enumerate(self.entries()):
            length = len(parse_shortcut(entry.text)[0]) + 2
            if position == index:
                return x, length
            x += length
        return x, 0

    def entry_at(self, column: int) -> int:
        """The entry under *column* of the bar, or -1."""
        for index in range(len(self.entries())):
            start, length = self.item_span(index)
            if start <= column < start + length:
                return index
        return -1

    def hotkey(self, letter: str) -> int:
        """The entry whose marked letter is *letter*, or -1."""
        letter = letter.lower()
        for index, entry in enumerate(self.entries()):
            if parse_shortcut(entry.text)[2] == letter:
                return index
        return -1

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
            surface.draw_text(start, 0, f" {caption} ", style)
            if 0 <= mark < len(caption):
                surface.draw_text(
                    start + 1 + mark, 0, caption[mark],
                    self.part_style("hotkey", **states),
                )

    # -- opening and closing ----------------------------------------------------------

    @property
    def is_open(self) -> bool:
        return self.session is not None

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

