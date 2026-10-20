"""The handlers behind ``links_dialog.nml``: the list, and what each button does to it.

The profiles are copied in (:class:`navigator.lib.drives.profiles.Entry`)
and edited here; OK answers ``("ok", entries)``, *Connect* ``("connect",
entries, index)``, and the caller writes them back
(:func:`navigator.lib.drives.profiles.store`).  Cancel answers None, and
nothing is changed.  Each link is edited in its protocol's own box -- the
one F2 opens in the *Link* list (``ConnectDialog(editing=True)``) -- which
needs none of the protocol's packages.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from navkit.events import Event
from navkit.i18n import tr

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.drives.profiles import Entry
from navigator.widgets.drives.commands import AddLink, DeleteLink, EditLink, MoveLinkDown, MoveLinkUp

#: The name column's width in a row.
NAME_WIDTH = 24


class LinksDialog(Dialog):
    """*Saved links*: the profiles, edited, kept on OK."""

    def __init__(self, entries: list[Entry] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        #: The links as they stand in the box, the list's order.
        self.entries: list[Entry] = [replace(entry) for entry in entries or ()]
        self.hint.text = tr("{add} Add  {edit} Edit  {delete} Delete  {move} Move").format(
            add="Ins", edit="F2", delete="Del", move="Ctrl+↑↓")
        self._refresh(0)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.connect, self.edit, self.append, self.delete, self.pick, self.abandon)

    # -- the list -------------------------------------------------------------------

    @staticmethod
    def row_text(entry: Entry) -> str:
        """``name  SFTP user@host:port``: the protocol before the place, as the
        *Link* list shows it."""
        from navigator.lib.drives import sessions

        who = f"{entry.user}@" if entry.user else ""
        port = f":{entry.port}" if entry.port else ""
        name = entry.name if len(entry.name) <= NAME_WIDTH else entry.name[:NAME_WIDTH - 1] + "…"
        return escape_caption(f"{name:<{NAME_WIDTH}} {sessions.protocol_sign(entry.scheme)} {who}{entry.host}{port}")

    def _refresh(self, cursor: int) -> None:
        self.links.items = [self.row_text(entry) for entry in self.entries]
        self.links.cursor = max(0, min(cursor, len(self.entries) - 1))

    @property
    def current(self) -> int | None:
        """The focused link's index, or None for an empty list."""
        cursor = self.links.cursor
        return cursor if 0 <= cursor < len(self.entries) else None

    def _put(self, entry: Entry, at: int, *, replacing: int | None = None) -> int:
        """*entry* in at *at* (over *replacing*, being edited); another link of
        its name goes, as ``profiles.replace`` drops it.  Answers where it is."""
        kept = [(index, each) for index, each in enumerate(self.entries)
                if index != replacing and each.name != entry.name]
        before = sum(1 for index, _ in kept if index < at)
        rest = [each for _, each in kept]
        rest.insert(before, entry)
        self.entries = rest
        return before

    # -- the buttons and their keys ---------------------------------------------------

    def accept(self) -> tuple[str, list[Entry]]:
        return "ok", list(self.entries)

    async def on_pick_click(self, event: Event) -> bool:
        self.close(self.accept())
        return True

    async def on_connect_click(self, event: Event) -> bool:
        index = self.current
        if index is None:
            return True
        self.close(("connect", list(self.entries), index))
        return True

    async def on_edit_click(self, event: Event) -> bool:
        self.spawn(self.edit_link())
        return True

    async def on_edit_link(self, event: EditLink) -> bool:
        self.spawn(self.edit_link())
        return True

    async def edit_link(self) -> None:
        """The focused link in its protocol's box; its answer in its place."""
        index = self.current
        if index is None:
            return
        entry = self.entries[index]
        answer = await self._ask(entry, entry.scheme)
        if answer is not None:
            self._refresh(self._put(answer, index, replacing=index))
        self.links.focus()

    async def on_append_click(self, event: Event) -> bool:
        self.spawn(self.add_link())
        return True

    async def on_add_link(self, event: AddLink) -> bool:
        self.spawn(self.add_link())
        return True

    async def add_link(self) -> None:
        """Which protocol, from a menu at *Add*, then its box: the new link
        after the focused one."""
        from navml.widgets.menu.popup_menu import PopupMenu
        from navml.widgets.menu.sub_menu import SubMenu

        app = self.application
        menu = SubMenu()
        # The protocols, as the *Link* list's *New* items name them.
        schemes = {id(menu.add_item(caption)): scheme for caption, scheme in (
            (tr("~N~ew SSH link (SFTP)..."), "sftp"), (tr("New ~F~TP link..."), "ftp"),
            (tr("New S~M~B link (Windows share)..."), "smb"), (tr("New S~3~ link (Amazon S3)..."), "s3"))}
        ox, oy = self.append.offset()
        chosen = await PopupMenu(menu, ox + self.append.x, oy + self.append.y + self.append.height, current=0,
                                 behind=self, title=tr("New link")).execute(app)
        scheme = schemes.get(id(chosen))
        if scheme is not None:
            answer = await self._ask(None, scheme)
            if answer is not None:
                index = self.current
                self._refresh(self._put(answer, len(self.entries) if index is None else index + 1))
        self.links.focus()

    async def _ask(self, entry: Entry | None, scheme: str) -> Entry | None:
        from navigator.widgets.drives.connect_dialog import ConnectDialog, ConnectRequest

        request = None
        if entry is not None:
            request = ConnectRequest(entry.scheme, entry.host, entry.user, entry.port, entry.path, entry.name, True)
        answer = await ConnectDialog(request, editing=True, scheme=scheme).execute(self.application)
        if answer is None:
            return None
        return Entry(answer.name or answer.host, answer.scheme, answer.host, answer.user, answer.port, answer.path)

    async def on_delete_click(self, event: Event) -> bool:
        self.spawn(self.delete_link())
        return True

    async def on_delete_link(self, event: DeleteLink) -> bool:
        self.spawn(self.delete_link())
        return True

    async def delete_link(self) -> None:
        """The focused link gone, once asked."""
        index = self.current
        if index is None:
            return
        name = self.entries[index].name
        answer = await Dialog(title=tr("Confirm"),
                              prompt=tr('Delete the link "{name}"?').format(name=escape_caption(name)),
                              buttons="yes-no").execute(self.application)
        if answer is True:
            del self.entries[index]
            self._refresh(index)
        self.links.focus()

    async def on_move_link_up(self, event: MoveLinkUp) -> bool:
        self.move(-1)
        return True

    async def on_move_link_down(self, event: MoveLinkDown) -> bool:
        self.move(1)
        return True

    def move(self, by: int) -> None:
        """The focused link *by* places along, the cursor with it."""
        index = self.current
        if index is None or not 0 <= index + by < len(self.entries):
            return
        entries = list(self.entries)
        entries[index], entries[index + by] = entries[index + by], entries[index]
        self.entries = entries
        self._refresh(index + by)
