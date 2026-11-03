"""The handlers behind ``ssh_link_dialog.nml``: the SSH connections kept, and
the one to connect to.

The box is given the kept connections (``sftp`` profiles, read on a thread
by the caller, :func:`sftp_entries`).  Two states, after FileZilla's Site
Manager: with nothing chosen (:attr:`SshLinkDialog.chosen` None) the lines
are a one-off connection, kept by nothing; with a connection chosen they
*are* that connection, *changed* once they differ from it, and kept by
*Save*.  *New* makes a connection at once -- empty, under a placeholder name
ready to be typed over, or from the one-off lines -- and *Delete* takes one
away; each writes on a thread through :mod:`navigator.lib.drives.profiles`
and reads the list back.  Leaving a changed connection asks whether to save
it.  *Connect* answers a
:class:`~navigator.widgets.drives.connect_dialog.ConnectRequest`, Cancel None.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import PurePosixPath
from typing import Any

from navkit.events import Event
from navkit.i18n import tr
from navkit.reactive import effect, peek

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.list_viewer import ListViewer

from navigator.lib.drives import profiles
from navigator.lib.drives.location import Location, Site
from navigator.lib.drives.profiles import Entry
from navigator.widgets.drives.commands import DeleteSshLink, NewSshLink, SaveSshLink
from navigator.widgets.drives.connect_dialog.connect_dialog import ConnectRequest, split_host

#: The scheme this box keeps and connects to.
SCHEME = "sftp"


def sftp_entries() -> list[Entry]:
    """The kept SSH connections, in the user's order -- on a thread, it reads the database."""
    return [entry for entry in profiles.entries() if entry.scheme == SCHEME]


def site_of(entry: Entry) -> Site:
    return Site(entry.scheme, entry.user, entry.host, entry.port)


def shown(entry: Entry) -> tuple[str, str, str, str, str]:
    """*entry* as its lines show it: name, host, login, port, directory."""
    return entry.name, entry.host, entry.user, str(entry.port) if entry.port else "", entry.path


def unique_name(base: str, taken: set[str]) -> str:
    """*base*, or ``base 2``, ``base 3``... -- the first not in *taken*."""
    name, number = base, 1
    while name in taken:
        number += 1
        name = f"{base} {number}"
    return name


class SshLinkDialog(Dialog):
    """Utilities > *SSH link (SFTP)* and *Remote shell*: the SSH connection manager."""

    def __init__(self, entries: list[Entry] | None = None, *, mode: str = "panel",
                 select: Location | None = None, missing: str | None = None,
                 **kwargs: Any) -> None:
        """*entries* are the kept SSH connections (:func:`sftp_entries`).
        *mode* is what *Connect* is for: ``"panel"`` sends the panel there,
        ``"shell"`` opens ``ssh`` -- which needs no paramiko, so *missing*
        (why SFTP cannot be used) stops *Connect* only in ``"panel"``.
        *select* is where the active panel is: the kept connection to that
        server chosen, or the one-off lines filled from it when none is."""
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        self.mode = mode
        if mode == "shell":
            self.title = tr("Remote shell")
        self.entries: list[Entry] = [replace(entry) for entry in entries or ()]
        #: The kept connection the lines are, or None: they are a one-off.
        self.chosen: int | None = None
        #: What the lines said when they were last the chosen connection's:
        #: they are *changed* while they differ from it.
        self._baseline: tuple[str, ...] = ()
        #: What a button last did, said until the lines change from
        #: :attr:`_noted`, what they were when it was said.
        self._note = ""
        self._noted: tuple[str, ...] = ()
        self._missing = missing if mode == "panel" else None
        self._list_rows()
        index = self._index_of(select.site) if select is not None else None
        here = "" if select is None or select.path == profiles.HOME else str(select.path)
        if index is not None:
            self.links.cursor = index
            self._fill(index)
            # Where the panel is, rather than where the connection opens: the
            # shell starts beside the files being looked at -- and that is not
            # a change to the connection, so nothing asks to save it.
            self.directory.value = here
            self._baseline = self._values()
        elif select is not None:
            site = select.site
            self._fill_lines(Entry("", SCHEME, site.host, site.user, site.port, here))
        #: The cursor the lines last followed: the effect acts only when the
        #: user moves it, not when it first runs or a re-read puts it back.
        self._followed = self.links.cursor
        self.links.on_choose = self._choose
        self.links.on_activate = self._activate
        self._show_state()

    def mounted(self) -> None:
        super().mounted()
        effect(self, SshLinkDialog._follow_cursor)
        effect(self, SshLinkDialog._follow_lines)
        # The list shows its cursor only while it has the keyboard, so with
        # nothing chosen the keyboard starts on the top line, Name: no row
        # looks chosen while the lines are a one-off.  A chosen one starts on
        # the list, on it.
        (self.links if self.chosen is not None else self.label.entry).focus()

    def key_hints(self) -> list[tuple[str, str]]:
        return [("Ins", tr("New")), ("F2", tr("Save")), ("Del", tr("Delete"))]

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.create, self.save, self.delete, self.connect, self.abandon)

    # -- the state ----------------------------------------------------------------------

    def _values(self) -> tuple[str, ...]:
        return (self.label.value, self.host.value, self.user.value, self.port.value, self.directory.value)

    @property
    def changed(self) -> bool:
        """The lines are a chosen connection's, and differ from it."""
        return self.chosen is not None and self._values() != self._baseline

    def _follow_lines(self) -> None:
        """Every keystroke in a line: the state shown again (an effect).

        The five values are read first, every run, whatever the state: an
        effect depends only on what its last run read, and a run that
        short-circuited past them would never run again."""
        values = self._values()
        if self._note and values != self._noted:
            self._note = ""
        self._show_state()

    def _show_state(self) -> None:
        """*Save* and *Delete*, the changed row's ``*`` and the line under the
        lines, from the state."""
        changed = self.changed
        self.save.disabled = not changed
        self.delete.disabled = self.chosen is None
        items = [escape_caption(entry.name) for entry in self.entries]
        if changed and self.chosen is not None and self.chosen < len(items):
            items[self.chosen] += " *"
        if items != peek(self.links, ListViewer.items):
            self.links.items = items
        if self._missing:
            text = self._missing
        elif self._note:
            text = self._note
        elif changed:
            text = tr("Changed — Save keeps it")
        elif self.chosen is None:
            text = tr("Not saved — New keeps it")
        else:
            text = ""
        self.missing.text = text

    def _say(self, text: str) -> None:
        self._note, self._noted = text, self._values()
        self._show_state()

    # -- the list and the lines -------------------------------------------------------

    def _list_rows(self) -> None:
        self.links.items = [escape_caption(entry.name) for entry in self.entries]
        self.links.cursor = max(0, min(self.links.cursor, len(self.entries) - 1))

    def _index_of(self, site: Site) -> int | None:
        """The first kept connection to *site*: the same host, and the same
        user and port where *site* names them."""
        for index, entry in enumerate(self.entries):
            if (entry.host == site.host and (not site.user or entry.user == site.user)
                    and (not site.port or entry.port == site.port)):
                return index
        return None

    def _follow_cursor(self) -> None:
        """The cursor moved onto a row: that connection chosen (an effect)."""
        cursor = self.links.cursor
        if cursor == self._followed:
            return
        self._choose(cursor)

    def _choose(self, index: int) -> None:
        """Row *index* chosen -- by the cursor, a click or Space.  Leaving a
        changed connection asks first; the cursor stays on it meanwhile."""
        if not 0 <= index < len(self.entries) or index == self.chosen and self.changed:
            self._put_cursor(self.chosen if self.chosen is not None else index)
            return
        if not self.changed:
            self._fill(index)
            return
        self._put_cursor(self.chosen)
        self.spawn(self._choose_asking(index))

    def _activate(self, index: int) -> None:
        """A row double-clicked: *Connect* to it -- once its first click has
        made it the chosen one.  While leaving a changed connection is still
        being asked about, it is not, and the double click does nothing more."""
        if index == self.chosen:
            self.spawn(self.connect_to())

    async def _choose_asking(self, index: int) -> None:
        if await self._settle() and 0 <= index < len(self.entries):
            self._fill(index)

    def _put_cursor(self, index: int | None) -> None:
        if index is not None:
            self.links.cursor = index
            self._followed = index

    def _fill(self, index: int) -> None:
        self.chosen = index
        self._put_cursor(index)
        self._fill_lines(self.entries[index])
        self._baseline = self._values()
        self._note = ""
        self._show_state()

    def _fill_lines(self, entry: Entry) -> None:
        self.label.value, self.host.value, self.user.value, self.port.value, self.directory.value = shown(entry)

    def _entry(self, fallback: str = "") -> Entry:
        """What the lines say, as a connection, host or none -- named by
        *Name*, else *fallback*, else the host.

        A user or port written into the Host line (``user@host:port``) wins
        over the Login and Port lines."""
        user, host, port = split_host(self.host.value)
        typed = self.port.value.strip()
        if not port and typed.isdigit():
            port = int(typed)
        name = self.label.value.strip() or fallback or host
        return Entry(name, SCHEME, host, user or self.user.value.strip(), port, self.directory.value.strip())

    def lines(self) -> Entry | None:
        """What the lines say, as a connection, or None with no host."""
        entry = self._entry()
        return entry if entry.host else None

    async def _reread(self, name: str | None) -> None:
        """The list read back from the database, *name* chosen (None: nothing)."""
        self.entries = await asyncio.to_thread(sftp_entries)
        index = next((i for i, entry in enumerate(self.entries) if entry.name == name), None)
        self.chosen = index
        self.links.items = [escape_caption(entry.name) for entry in self.entries]
        self._put_cursor(index if index is not None else max(0, min(self.links.cursor, len(self.entries) - 1)))

    async def _settle(self) -> bool:
        """Leaving the chosen connection: if it is changed, *Save changes?* --
        Yes saves, No puts the lines back, Cancel stays.  False to stay."""
        if not self.changed:
            return True
        name = self.entries[self.chosen].name
        answer = await Dialog(title=tr("Save changes"),
                              prompt=tr('Save changes to "{name}"?').format(name=escape_caption(name)),
                              buttons="yes-no-cancel").execute(self.application)
        if answer is None:
            return False
        if answer is True:
            return await self.save_link()
        self._fill(self.chosen)
        return True

    # -- the buttons and their keys ---------------------------------------------------

    def accept(self) -> ConnectRequest | None:
        if self._missing:
            return None
        entry = self.lines()
        if entry is None:
            return None
        return ConnectRequest(SCHEME, entry.host, entry.user, entry.port, entry.path)

    async def on_connect_click(self, event: Event) -> bool:
        self.spawn(self.connect_to())
        return True

    async def connect_to(self) -> None:
        """*Connect*: the lines answered, a changed connection settled first."""
        if self._missing:
            return
        if self.lines() is None:
            self._say(tr("Type a host to connect to"))
            self.host.entry.focus()
            return
        if not await self._settle():
            return
        self.record_history()
        self.close(self.accept())

    def must_ask(self) -> bool:
        """Esc and the close icon ask about a changed connection."""
        return self.changed

    async def ask_to_close(self) -> bool:
        return await self._settle()

    async def on_abandon_click(self, event: Event) -> bool:
        self.spawn(self._cancel())
        return True

    async def _cancel(self) -> None:
        if await self._settle():
            self.close(None)

    async def on_create_click(self, event: Event) -> bool:
        self.spawn(self.new_link())
        return True

    async def on_new_ssh_link(self, event: NewSshLink) -> bool:
        self.spawn(self.new_link())
        return True

    async def new_link(self) -> None:
        """*New*: a connection made and kept at once, chosen, its name ready
        to be typed over -- the one-off lines, if a host is typed there, else
        an empty one under a placeholder name."""
        if not await self._settle():
            return
        self.record_history()
        taken = {entry.name for entry in self.entries}
        if self.chosen is None and self.lines() is not None:
            entry = self._entry()
        else:
            entry = Entry(tr("New connection"), SCHEME, "")
        entry = replace(entry, name=unique_name(entry.name, taken))
        await asyncio.to_thread(profiles.save, entry.name, SCHEME, entry.host, entry.user, entry.port, entry.path)
        await self._reread(entry.name)
        if self.chosen is not None:
            self._fill(self.chosen)
        self.label.entry.focus()
        self.label.entry.select_all()

    async def on_save_click(self, event: Event) -> bool:
        self.spawn(self.save_link())
        return True

    async def on_save_ssh_link(self, event: SaveSshLink) -> bool:
        self.spawn(self.save_link())
        return True

    async def save_link(self) -> bool:
        """*Save*: the chosen connection made what the lines say, renamed in
        its place.  A name another connection has is refused.  True once kept."""
        if self.chosen is None or not 0 <= self.chosen < len(self.entries):
            return False
        old = self.entries[self.chosen].name
        entry = self._entry(fallback=old)
        if entry.name != old and any(each.name == entry.name for each in self.entries):
            self._say(tr('Another connection is named "{name}"').format(name=escape_caption(entry.name)))
            self.label.entry.focus()
            return False
        self.record_history()
        await asyncio.to_thread(profiles.replace, old, entry.name, SCHEME, entry.host, entry.user,
                                entry.port, entry.path)
        await self._reread(entry.name)
        if self.chosen is not None:
            self._fill(self.chosen)
        self._say(tr('"{name}" saved').format(name=escape_caption(entry.name)))
        return True

    async def on_delete_click(self, event: Event) -> bool:
        self.spawn(self.delete_link())
        return True

    async def on_delete_ssh_link(self, event: DeleteSshLink) -> bool:
        self.spawn(self.delete_link())
        return True

    async def delete_link(self) -> None:
        """The chosen connection gone, once asked; the lines then empty, a
        one-off, as the box opens."""
        if self.chosen is None or not 0 <= self.chosen < len(self.entries):
            return
        name = self.entries[self.chosen].name
        answer = await Dialog(title=tr("Confirm"),
                              prompt=tr('Delete the link "{name}"?').format(name=escape_caption(name)),
                              buttons="yes-no").execute(self.application)
        if answer is not True:
            return
        await asyncio.to_thread(profiles.remove, name)
        await self._reread(None)
        self._fill_lines(Entry("", SCHEME, ""))
        self._baseline = ()
        self._say(tr('"{name}" deleted').format(name=escape_caption(name)))
        self.label.entry.focus()


def location_of(request: ConnectRequest) -> Location:
    """Where *request* opens: its directory, or the home directory there."""
    return Location(Site(request.scheme, request.user, request.host, request.port),
                    PurePosixPath(request.path) if request.path else profiles.HOME)


__all__ = ["SshLinkDialog", "location_of", "sftp_entries"]
