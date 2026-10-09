"""An entry that opens a box of entries: Turbo Vision's ``SubMenu``.

Also :class:`MenuContainer`, what the bar and every submenu share: a list of
entries that Python can change after the markup has built it.  That is the
plugin's way in -- find a menu by its ``id`` on the document that declared it
(``app.shell.menu.file``), then add to it::

    menu.file.add_item("~Z~ip...", ZipFiles, key="Alt-Z", after=MakeDirectory)
    menu.add_submenu("~P~lugins", before="Window")

**An anchor** -- ``before=`` or ``after=``, and what :meth:`entry` and
:meth:`remove_entry` take -- is an entry itself, its caption (tildes and case
ignored: ``"Make directory"``), or a command class or instance, which names
the item that asks for it.  An anchor that names nothing raises, since a
plugin placing its item next to one that has moved should hear about it.

**The entries are not reactive; their flags are.**  Adding, removing and
reordering take effect the next time a box opens -- an open box keeps the
size it was measured at -- while ``hidden`` and ``disabled`` are reactive, so
toggling one repaints an open menu straight away.
"""

from __future__ import annotations

from typing import Any

from navkit.commands import Command, command_of
from navkit.i18n import tr_plain
from navkit.reactive import reactive

from navml.widgets.dialog.control.control import parse_shortcut
from navml.widgets.menu.menu_item.menu_item import MenuItem, MenuNode
from navml.widgets.menu.menu_line.menu_line import MenuLine

#: What names an entry: the entry, its caption, or the command it asks for.
Anchor = Any


class MenuContainer:
    """A widget whose children are menu entries, and the ways to change them.

    A mixin rather than a base, because the two things it is mixed into are
    unrelated otherwise: a :class:`~navml.widgets.menu.menu_bar.MenuBar` is a
    visible widget painted as a row, a :class:`SubMenu` an invisible node.
    """

    children: list[Any]

    # -- reading ------------------------------------------------------------------

    def all_entries(self) -> list[MenuNode]:
        """Every entry, hidden ones included, in order."""
        return [child for child in self.children if isinstance(child, MenuNode)]

    def entries(self) -> list[MenuNode]:
        """The entries a menu shows: every one that is not ``hidden``."""
        return [entry for entry in self.all_entries() if not entry.hidden]

    def entry(self, anchor: Anchor) -> MenuNode | None:
        """The entry directly in this menu that *anchor* names, or None."""
        for entry in self.all_entries():
            if _names(anchor, entry):
                return entry
        return None

    def item_for(self, command: Any) -> MenuItem | None:
        """The item asking for *command*, searched through every submenu."""
        for entry in self.all_entries():
            if isinstance(entry, MenuItem) and _names(command, entry):
                return entry
            if isinstance(entry, MenuContainer):
                found = entry.item_for(command)
                if found is not None:
                    return found
        return None

    # -- changing -------------------------------------------------------------------

    def add_item(
        self,
        text: str,
        command: Any = None,
        key: str = "",
        *,
        before: Anchor = None,
        after: Anchor = None,
    ) -> MenuItem:
        """Add an item asking for *command*; at the end unless anchored."""
        item = MenuItem(text=text, command=command, key=key)
        return self.add_entry(item, before=before, after=after)

    def add_submenu(
        self, text: str, *, before: Anchor = None, after: Anchor = None
    ) -> SubMenu:
        """Add an empty submenu, to be filled with its own ``add_*`` calls."""
        return self.add_entry(SubMenu(text=text), before=before, after=after)

    def add_line(self, *, before: Anchor = None, after: Anchor = None) -> MenuLine:
        """Add a separator."""
        return self.add_entry(MenuLine(), before=before, after=after)

    def add_entry(
        self, entry: MenuNode, *, before: Anchor = None, after: Anchor = None
    ) -> Any:
        """Put *entry* in this menu -- at the end, or next to an anchor."""
        if before is not None and after is not None:
            raise ValueError("an entry goes before one anchor or after one, not both")
        anchor = before if before is not None else after
        target = self._find(anchor) if anchor is not None else None
        self.add(entry)
        if target is not None:
            self.children.remove(entry)
            index = self.children.index(target) + (1 if after is not None else 0)
            self.children.insert(index, entry)
        self.invalidate()
        return entry

    def remove_entry(self, anchor: Anchor) -> MenuNode:
        """Take the entry *anchor* names out of this menu, and return it."""
        entry = self._find(anchor)
        self.remove(entry)
        return entry

    def move_entry(
        self, anchor: Anchor, *, before: Anchor = None, after: Anchor = None
    ) -> MenuNode:
        """Move an entry of this menu next to another one."""
        entry = self.remove_entry(anchor)
        return self.add_entry(entry, before=before, after=after)

    def clear(self) -> None:
        """Take every entry out of this menu."""
        for entry in self.all_entries():
            self.remove(entry)

    def _find(self, anchor: Anchor) -> MenuNode:
        entry = self.entry(anchor)
        if entry is None:
            captions = ", ".join(
                repr(parse_shortcut(getattr(e, "text", ""))[0] or "---")
                for e in self.all_entries()
            )
            raise LookupError(f"no entry {anchor!r} in this menu; it has {captions}")
        return entry


class SubMenu(MenuContainer, MenuNode):
    """Its children are the entries of the box it opens."""

    #: The caption, with its hotkey marked: ``~F~ile``.
    text: str = reactive("")
    #: Where this submenu goes when it is *contributed* to a bar -- a child of
    #: the widget a :class:`~navml.widgets.menu.menu_bar.MenuBar` holds as its
    #: ``context`` -- rather than being one of the bar's own: before or after
    #: the bar entry with this caption (tildes and case ignored), or at the
    #: end with neither.  Read nowhere else.
    before: str = reactive("")
    after: str = reactive("")
    #: A command that opens this submenu's entries some other way -- a box of
    #: their own -- whose key is shown beside the caption, before the arrow,
    #: read off the key tables as an item's is.  Only shown: choosing the
    #: entry still opens the submenu.  :attr:`key` is the caption to show
    #: while nothing binds it.
    key_command: Any = reactive(None)
    key: str = reactive("")


def _names(anchor: Anchor, entry: MenuNode) -> bool:
    """Whether *anchor* names *entry*: itself, its caption, or its command."""
    if anchor is entry:
        return True
    if isinstance(anchor, str):
        # The caption is in the current language and the anchor is English, so
        # the anchor is translated too; an untranslated one still matches.
        caption = parse_shortcut(getattr(entry, "text", ""))[0].casefold()
        return bool(caption) and caption in (
            anchor.replace("~", "").casefold(), tr_plain(anchor).casefold()
        )
    if isinstance(entry, MenuItem) and entry.command is not None:
        if isinstance(anchor, type) and issubclass(anchor, Command):
            mine = entry.command
            return mine is anchor or isinstance(mine, anchor)
        if isinstance(anchor, Command):
            return command_of(entry.command) == anchor
    return False
