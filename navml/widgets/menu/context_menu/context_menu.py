"""A widget's own menu, opened where the user points at it.

**A departure: DOS Navigator had no context menu.**  Its right button meant
something different in each place: a panel selected with it, and a dialog
pressed its default button.  Turbo Vision had no local menu either.  This is
the modern convention, added as a framework feature: a right click, the Menu
key, or Shift+F10 opens a box of the most common things the widget under the
pointer, or holding the keyboard, can do.

Two pieces:

* :class:`ContextMenu` is a :class:`SubMenu` declared as a child of the widget
  it belongs to, its entries written as any menu's are::

      FileEditor:
          ContextMenu:
              MenuItem:
                  text: "Cu~t~"
                  command: ClipboardCut

  It never joins the menu bar, even when it is a child of the window the bar
  takes its contributed menus from (``MenuBar.entries`` skips it).

* :class:`ContextMenuHost` is the mixin that opens it.  It answers navkit's
  :class:`~navkit.events.ContextMenuEvent`, the second delivery of a right
  press, and the :class:`ShowContextMenu` command, the keyboard's way in.
  :meth:`~ContextMenuHost.context_menu` is the hook: by default the first
  visible ``ContextMenu`` child, overridden by a host whose entries depend on
  what it shows (a file panel's, on what is under the cursor).

**The chosen command runs from the host**, not from whatever has the
keyboard: ``app.run_command(item.command, start=host)``.  It is greyed from
the same point of view, because the box is opened with ``behind=host``.  A
right click in a panel that is not the active one therefore copies *that*
panel's files.

The box is run with ``spawn``, as every dialog is.  A handler starts it and
returns; the choice is acted on once it closes.
"""

from __future__ import annotations

from typing import Any

from navkit.events import ContextMenuEvent
from navkit.widget import Widget

from navml.widgets.menu.commands import ShowContextMenu
from navml.widgets.menu.popup_menu.popup_menu import PopupMenu
from navml.widgets.menu.sub_menu.sub_menu import SubMenu


class ContextMenu(SubMenu):
    """The entries a host's context menu shows; never a part of the menu bar."""


class ContextMenuHost:
    """Mix into a :class:`~navkit.widget.Widget` that offers a context menu.

    A host may override:

    * :meth:`context_menu`, which returns the menu to show now, or None;
    * :meth:`prepare_context`, which moves the host's own cursor to the click
      before the box opens;
    * :meth:`context_point`, which is where the keyboard opens the box.

    A host that gives the right button another meaning (a setting chose it)
    declines by returning None from :meth:`context_menu` for a click, or by
    claiming the press itself.  It must not claim this event.
    """

    #: Whether opening the menu gives this widget the keyboard.  The console
    #: says no: it shows what the command line runs, and the keys stay there.
    context_focus = True

    def context_menu(self) -> SubMenu | None:
        """The menu to show now: the first visible :class:`ContextMenu` child."""
        for child in self.children:  # type: ignore[attr-defined]
            if isinstance(child, ContextMenu) and not child.hidden:
                return child
        return None

    def prepare_context(self, x: int, y: int) -> None:
        """Get ready for a menu asked for at *x*, *y*, in this widget's coordinates.

        Called only for a click, before :meth:`context_menu`.  A list moves
        its cursor to the row clicked, and an editor its caret.  Does nothing
        by default.
        """

    def context_point(self) -> tuple[int, int]:
        """Where the keyboard opens the box, in this widget's coordinates.

        One row under the caret if the widget shows one, so the box does not
        cover what it acts on.  Otherwise just inside the top-left corner.
        """
        return default_point(self)  # type: ignore[arg-type]

    async def on_context_menu(self, event: ContextMenuEvent) -> bool:
        """A right click: move to it, then open the menu at the pointer."""
        return open_on_click(self, event)

    async def on_show_context_menu(self, command: ShowContextMenu) -> bool:
        """The Menu key or Shift+F10: open the menu at :meth:`context_point`."""
        return open_on_key(self)


# -- for a host that cannot take the mixin --------------------------------------
#
# A component's hand-written half has exactly one base, its markup's (see
# *The merge is one line* in the navml-components skill), so ``InputLine``
# cannot list ``ContextMenuHost`` beside ``Control``.  It defines the hooks and
# the two handlers itself, and the handlers call these.


def open_on_click(host: Any, event: ContextMenuEvent) -> bool:
    """What ``on_context_menu`` does: prepare, then open at the pointer.

    False, so the event goes on outward, when *host* has no menu to show.
    """
    if event.button != "right":
        return False
    host.prepare_context(event.x, event.y)
    menu = host.context_menu()
    if menu is None:
        return False
    open_context(host, menu, event.x, event.y)
    return True


def open_on_key(host: Any) -> bool:
    """What ``on_show_context_menu`` does: open at the host's context point."""
    menu = host.context_menu()
    if menu is None:
        return False
    open_context(host, menu, *host.context_point())
    return True


def default_point(widget: Widget) -> tuple[int, int]:
    """:meth:`ContextMenuHost.context_point`'s answer, for any widget."""
    caret = widget.cursor_position()
    if caret is not None:
        return caret[0], caret[1] + 1
    return 1, 1


def open_context(host: Widget, menu: SubMenu, x: int, y: int) -> None:
    """Give *host* the keyboard, then start *menu*'s box at its local *x*, *y*.

    Started, not awaited: the caller is an event handler.
    """
    if getattr(host, "context_focus", True) and host.can_focus and not host.focused:
        host.focus()
    dx, dy = host.offset()
    host.spawn(_run(host, menu, dx + host.x + x, dy + host.y + y))


async def _run(host: Widget, menu: SubMenu, x: int, y: int) -> None:
    """Show the box, then run the command chosen from *host*."""
    app = host.application
    if app is None:
        return
    popup = PopupMenu(menu, x, y, behind=host, buttons=("left", "right"))
    chosen = await popup.execute(app)
    if chosen is not None and chosen.command is not None and host.application is app:
        await app.run_command(chosen.command, start=host)


__all__ = [
    "ContextMenu",
    "ContextMenuHost",
    "default_point",
    "open_context",
    "open_on_click",
    "open_on_key",
]
