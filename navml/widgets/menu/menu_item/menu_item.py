"""One entry in a menu: a caption, the command it asks for, and a key.

Also :class:`MenuNode`, what every entry in a menu tree is: a widget that is
never shown.  A menu is written as blocks in markup, and a block is a widget,
so the entries are widgets -- but they are *data*, read by the
:class:`~navml.widgets.menu.menu_bar.MenuBar` and the boxes it opens and
painted by them as rows, the way a listing paints its entries.  So a node is
invisible from its constructor on, which also takes it out of every walk that
would otherwise find it: painting, hit-testing, focus.
"""

from __future__ import annotations

from typing import Any

from navkit.reactive import reactive
from navkit.widget import Widget

from navml.component import take_declared


class MenuNode(Widget):
    """An entry in a menu tree: laid out nowhere, painted by its menu.

    Two flags a program may set on any entry, both reactive so an open menu
    repaints: ``hidden`` leaves it out of its menu altogether, and
    ``disabled`` -- ``Widget``'s own -- greys it whatever its command says.
    ``visible`` is not the way to hide one: every node is invisible already,
    because a node is never painted as a widget.
    """

    #: Left out of its menu: not shown, not counted, not reachable by letter.
    hidden: bool = reactive(False)

    def __init__(self, **kwargs: Any) -> None:
        take_declared(self, kwargs)
        super().__init__(**kwargs)
        self.visible = False

    def layout(self, width: int, height: int) -> None:
        """Nothing to fit: a node has no rectangle of its own."""


class MenuItem(MenuNode):
    """Asks for :attr:`command` when chosen; greyed while it cannot run."""

    #: The caption, with its hotkey marked Turbo Vision's way: ``~M~ake``.
    text: str = reactive("")
    #: A command class or instance, or None for an entry whose feature does
    #: not exist yet -- which is shown, and disabled, like any command nobody
    #: handles.
    command: Any = reactive(None)
    #: The key to show when no key table binds the command: DOS Navigator's
    #: own caption for it.  A key that *is* bound is read off the binding
    #: instead, so the menu cannot claim a key that does something else.
    key: str = reactive("")
