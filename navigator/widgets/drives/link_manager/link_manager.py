"""The handlers behind ``link_manager.nml``: one protocol's connections kept,
and the one to connect to.

The box is given one protocol family's kept connections (its schemes'
profiles, read on a thread by the caller, :func:`entries_for`).  Two states,
after FileZilla's Site Manager: with nothing chosen
(:attr:`LinkManagerDialog.chosen` None) the lines are a one-off connection,
kept by nothing; with a connection chosen they *are* that connection,
*changed* once they differ from it, and kept by *Save*.  *New* makes a
connection at once -- empty, under a placeholder name ready to be typed over,
or from the one-off lines -- and *Delete* takes one away; each writes on a
thread through :mod:`navigator.lib.drives.profiles` and reads the list back.
Leaving a changed connection asks whether to save it.  *Connect* answers a
:class:`~navigator.widgets.drives.connect_dialog.ConnectRequest`, Cancel None.

What differs between protocols is :data:`FAMILIES`' and :meth:`LinkManagerDialog._dress`'s:
the schemes listed, the captions, the TLS box (FTP's ``ftps``, S3's
``s3``/``s3+http``), S3's endpoint to start from, the share or bucket as the
first name of SMB's and S3's directory, and GVfs/KIO's single URI line.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
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
from navigator.widgets.drives.commands import DeleteLinkEntry, NewLinkEntry, SaveLinkEntry
from navigator.widgets.drives.connect_dialog.connect_dialog import ConnectRequest, split_host, titles


@dataclass(frozen=True)
class Family:
    """One protocol's manager: what it lists and how its lines read."""

    #: The family's name, its menu item's scheme: ``sftp``, ``ftp``, ``smb``,
    #: ``s3`` or ``gvfs``.
    key: str
    #: The schemes it lists and writes; GVfs/KIO's are the backend's (:func:`schemes_of`).
    schemes: tuple[str, ...] = ()
    #: The scheme with the TLS box ticked and unticked, for a family that has one.
    secure: tuple[str, str] | None = None
    #: The first name of the directory is the share or the bucket: a leading ``/``.
    rooted: bool = False
    #: What its lines' histories are called: ``{prefix}_name``, ``{prefix}_host``...
    history: str = ""


#: Every family, by its key.
FAMILIES: dict[str, Family] = {
    "sftp": Family("sftp", ("sftp",), history="ssh"),
    "ftp": Family("ftp", ("ftp", "ftps"), secure=("ftps", "ftp"), history="ftp"),
    "smb": Family("smb", ("smb",), rooted=True, history="smb"),
    "s3": Family("s3", ("s3", "s3+http"), secure=("s3", "s3+http"), rooted=True, history="s3"),
    "gvfs": Family("gvfs", history="gvfs"),
}


def family_of(scheme: str) -> str:
    """The family a scheme's connections are kept in: ``ftps`` is FTP's."""
    for family in FAMILIES.values():
        if scheme in family.schemes:
            return family.key
    return "gvfs"


def schemes_of(family: str) -> tuple[str, ...]:
    """The schemes *family* lists: GVfs/KIO's those the desktop's backend
    reaches that are not Navigator's own (``sftp://`` is SSH link's)."""
    if family != "gvfs":
        return FAMILIES[family].schemes
    from navigator.lib.drives import sessions
    from navigator.lib.system import desktop

    return tuple(scheme for scheme in desktop.link_schemes() if scheme not in sessions.SCHEMES)


def entries_for(family: str) -> list[Entry]:
    """*family*'s kept connections, in the user's order -- on a thread, it reads the database."""
    schemes = set(schemes_of(family))
    return [entry for entry in profiles.entries() if entry.scheme in schemes]


def sftp_entries() -> list[Entry]:
    """The kept SSH connections (:func:`entries_for` ``"sftp"``)."""
    return entries_for("sftp")


def site_of(entry: Entry) -> Site:
    return Site(entry.scheme, entry.user, entry.host, entry.port)


def uri_of(entry: Entry) -> str:
    """*entry* as GVfs/KIO's line writes it: ``mtp://Phone/DCIM``."""
    if not entry.scheme:
        return ""
    return str(Location(site_of(entry), PurePosixPath(entry.path or "/")))


def unique_name(base: str, taken: set[str]) -> str:
    """*base*, or ``base 2``, ``base 3``... -- the first not in *taken*."""
    name, number = base, 1
    while name in taken:
        number += 1
        name = f"{base} {number}"
    return name


class LinkManagerDialog(Dialog):
    """Utilities > *SSH link*, *FTP link*, *SMB link*, *S3 link*, *GVfs/KIO link*
    and *Remote shell*: one protocol's connection manager."""

    def __init__(self, entries: list[Entry] | None = None, *, family: str = "sftp", mode: str = "panel",
                 select: Location | None = None, missing: str | None = None,
                 **kwargs: Any) -> None:
        """*entries* are *family*'s kept connections (:func:`entries_for`).
        *mode* is what *Connect* is for: ``"panel"`` sends the panel there,
        ``"shell"`` (SSH's alone) opens ``ssh`` -- which needs no paramiko,
        so *missing* (why the protocol cannot be used) stops *Connect* only in
        ``"panel"``.  *select* is where the active panel is: the kept
        connection to that server chosen, or the one-off lines filled from it
        when none is."""
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        self.family = FAMILIES[family]
        #: The schemes this family's lines may name (GVfs/KIO's the backend's).
        self.schemes = schemes_of(family)
        self.mode = mode
        self._dress()
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
            self._fill_lines(Entry("", site.scheme, site.host, site.user, site.port, here))
        else:
            self._fill_lines(self._blank())
        #: The cursor the lines last followed: the effect acts only when the
        #: user moves it, not when it first runs or a re-read puts it back.
        self._followed = self.links.cursor
        self.links.on_choose = self._choose
        self.links.on_activate = self._activate
        self._show_state()

    def mounted(self) -> None:
        super().mounted()
        effect(self, LinkManagerDialog._follow_cursor)
        effect(self, LinkManagerDialog._follow_lines)
        # The list shows its cursor only while it has the keyboard, so with
        # nothing chosen the keyboard starts on the top line, Name: no row
        # looks chosen while the lines are a one-off.  A chosen one starts on
        # the list, on it.
        (self.links if self.chosen is not None else self.label.entry).focus()

    def _dress(self) -> None:
        """The protocol's title, captions, histories and TLS box."""
        key = self.family.key
        self.title = tr("GVfs/KIO link") if key == "gvfs" else titles(key)[0]
        prefix = self.family.history
        for line, name in ((self.label, "name"), (self.host, "host"), (self.user, "login"),
                           (self.port, "port"), (self.directory, "directory")):
            line.history_id = f"{prefix}_{name}"
        if key == "sftp":
            self.options.visible = True
            self.options.entry.tooltip = tr(
                "Added to Remote shell's ssh command, after Communications' own (-Y); "
                "SSH link's panel reads ~/.ssh/config alone")
        if key == "smb":
            self.directory.label_text = tr("Sh~a~re/dir")
        if key == "s3":
            self.host.label_text = tr("End~p~oint")
            self.user.label_text = tr("Access ~k~ey")
            self.directory.label_text = tr("~B~ucket/dir")
        if self.family.secure is not None:
            self.secure.visible = True
            self.secure.items = [tr("Encr~y~pt with TLS (HTTPS)") if key == "s3" else tr("Encr~y~pt with TLS (FTPS)")]
        if key == "gvfs":
            for line in (self.host, self.user, self.port, self.directory):
                line.visible = False
            self.uri.visible = True
            # Under the URI, not below the four lines it stands in for.
            self.missing.y = self.uri.y + 2
            from navigator.lib.system import desktop

            # The backend's own spellings, as the old URI box's caption had them.
            self.uri.entry.tooltip = (
                tr("For example mtp://Phone/, webdav://host/dir or gdrive://you@gmail.com/")
                if desktop.link_name() == "KIO"
                else tr("For example mtp://Phone/, dav://host/dir or google-drive://you@gmail.com/"))

    def _blank(self) -> Entry:
        """The lines of a connection not yet written: S3's endpoint, and the
        TLS box ticked where the protocol has one -- what ``ConnectDialog``
        started from."""
        if self.family.key == "s3":
            from navigator.lib.drives.s3 import AWS_HOST

            return Entry("", "s3", AWS_HOST)
        scheme = self.family.secure[1] if self.family.key == "ftp" else self.family.key
        return Entry("", "" if self.family.key == "gvfs" else scheme, "")

    def key_hints(self) -> list[tuple[str, str]]:
        return [("Ins", tr("New")), ("F2", tr("Save")), ("Del", tr("Delete"))]

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.create, self.save, self.delete, self.connect, self.abandon)

    # -- the state ----------------------------------------------------------------------

    def _values(self) -> tuple[str, ...]:
        """Every line, the TLS box and the URI: what *changed* compares."""
        return (self.label.value, self.host.value, self.user.value, self.port.value, self.directory.value,
                str(self.secure.value & 1), self.uri.value, self.options.value)

    @property
    def changed(self) -> bool:
        """The lines are a chosen connection's, and differ from it."""
        return self.chosen is not None and self._values() != self._baseline

    def _follow_lines(self) -> None:
        """Every keystroke in a line: the state shown again (an effect).

        The values are read first, every run, whatever the state: an
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

    def _unchoose(self) -> None:
        """Back to a one-off: nothing chosen, the lines as the box opens."""
        self.chosen = None
        self._fill_lines(self._blank())
        self._baseline = ()
        self._show_state()

    def _fill_lines(self, entry: Entry) -> None:
        self.label.value = entry.name
        self.host.value = entry.host
        self.user.value = entry.user
        self.port.value = str(entry.port) if entry.port else ""
        self.directory.value = entry.path
        if self.family.secure is not None:
            self.secure.value = 1 if entry.scheme == self.family.secure[0] else 0
        self.uri.value = uri_of(entry) if self.family.key == "gvfs" else ""
        self.options.value = entry.options

    def _entry(self, fallback: str = "") -> Entry:
        """What the lines say, as a connection, host or none -- named by
        *Name*, else *fallback*, else the host.

        A user or port written into the Host line (``user@host:port``) wins
        over the Login and Port lines.  The TLS box picks the scheme; SMB's
        share and S3's bucket are the directory's first name; GVfs/KIO's URI
        is all of it."""
        if self.family.key == "gvfs":
            return self._uri_entry(fallback)
        user, host, port = split_host(self.host.value)
        typed = self.port.value.strip()
        if not port and typed.isdigit():
            port = int(typed)
        name = self.label.value.strip() or fallback or host
        scheme = self.family.key
        if self.family.secure is not None:
            scheme = self.family.secure[0] if self.secure.value & 1 else self.family.secure[1]
        directory = self.directory.value.strip()
        if self.family.rooted and directory and not directory.startswith("/"):
            directory = "/" + directory
        options = self.options.value.strip() if self.family.key == "sftp" else ""
        return Entry(name, scheme, host, user or self.user.value.strip(), port, directory, options)

    def _uri_entry(self, fallback: str) -> Entry:
        """GVfs/KIO's line as a connection: no scheme for an empty or local one."""
        text = self.uri.value.strip()
        target = Location.parse(text) if text else None
        if target is None or target.is_local:
            return Entry(self.label.value.strip() or fallback, "", "")
        site = target.site
        path = "" if str(target.path) == "/" else str(target.path)
        return Entry(self.label.value.strip() or fallback or site.host, site.scheme, site.host, site.user,
                     site.port, path)

    def problem(self) -> str:
        """Why the lines cannot be connected to or kept: no host, or a URI
        nothing reaches -- else ``""``."""
        if self.family.key != "gvfs":
            return "" if self._entry().host else tr("Type a host to connect to")
        text = self.uri.value.strip()
        if not text:
            return tr("Type a URI to connect to")
        if self._uri_entry("").scheme in self.schemes:
            return ""
        from navigator.lib.system import desktop

        known = ", ".join(f"{scheme}://" for scheme in self.schemes)
        prompt = (tr("{uri} is no place KIO reaches. It knows {schemes}") if desktop.link_name() == "KIO"
                  else tr("{uri} is no place GVfs reaches. It knows {schemes}"))
        return escape_caption(prompt.format(uri=text, schemes=known))

    def _first_line(self) -> Any:
        """The line a problem sends the keyboard to."""
        return self.uri.entry if self.family.key == "gvfs" else self.host.entry

    def lines(self) -> Entry | None:
        """What the lines say, as a connection, or None when it cannot be one."""
        return None if self.problem() else self._entry()

    async def _reread(self, name: str | None) -> None:
        """The list read back from the database, *name* chosen (None: nothing)."""
        self.entries = await asyncio.to_thread(entries_for, self.family.key)
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
        return ConnectRequest(entry.scheme, entry.host, entry.user, entry.port, entry.path, options=entry.options)

    async def on_connect_click(self, event: Event) -> bool:
        self.spawn(self.connect_to())
        return True

    async def connect_to(self) -> None:
        """*Connect*: the lines answered, a changed connection settled first."""
        if self._missing:
            return
        problem = self.problem()
        if problem:
            self._say(problem)
            self._first_line().focus()
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

    async def on_new_link_entry(self, event: NewLinkEntry) -> bool:
        self.spawn(self.new_link())
        return True

    async def new_link(self) -> None:
        """*New*: a connection made and kept at once, chosen, its name ready
        to be typed over -- the one-off lines, if a host is typed there, else
        an empty one under a placeholder name."""
        if not await self._settle():
            return
        if self.family.key == "gvfs" and (self.chosen is not None or self.problem()):
            # A GVfs/KIO place is its URI: kept with no scheme it would be in
            # no family's list.  So *New* starts a one-off to type it into,
            # and keeps it once there is one.
            if self.chosen is not None:
                self._unchoose()
                self._say(tr("Type its URI, then New keeps it"))
            else:
                self._say(self.problem())
            self.uri.entry.focus()
            return
        self.record_history()
        taken = {entry.name for entry in self.entries}
        if self.chosen is None and self.lines() is not None:
            entry = self._entry()
        else:
            entry = replace(self._blank(), name=tr("New connection"))
        entry = replace(entry, name=unique_name(entry.name, taken))
        await asyncio.to_thread(profiles.save, entry.name, entry.scheme, entry.host, entry.user, entry.port,
                                entry.path, entry.options)
        await self._reread(entry.name)
        if self.chosen is not None:
            self._fill(self.chosen)
        self.label.entry.focus()
        self.label.entry.select_all()

    async def on_save_click(self, event: Event) -> bool:
        self.spawn(self.save_link())
        return True

    async def on_save_link_entry(self, event: SaveLinkEntry) -> bool:
        self.spawn(self.save_link())
        return True

    async def save_link(self) -> bool:
        """*Save*: the chosen connection made what the lines say, renamed in
        its place.  A name another connection has is refused.  True once kept."""
        if self.chosen is None or not 0 <= self.chosen < len(self.entries):
            return False
        old = self.entries[self.chosen].name
        entry = self._entry(fallback=old)
        if self.family.key == "gvfs" and self.uri.value.strip() and self.problem():
            self._say(self.problem())
            self.uri.entry.focus()
            return False
        if not entry.scheme:
            # GVfs/KIO's with no URI yet: still its own, under the scheme it had.
            entry = replace(entry, scheme=self.entries[self.chosen].scheme)
        if entry.name != old and any(each.name == entry.name for each in self.entries):
            self._say(tr('Another connection is named "{name}"').format(name=escape_caption(entry.name)))
            self.label.entry.focus()
            return False
        self.record_history()
        await asyncio.to_thread(profiles.replace, old, entry.name, entry.scheme, entry.host, entry.user,
                                entry.port, entry.path, entry.options)
        await self._reread(entry.name)
        if self.chosen is not None:
            self._fill(self.chosen)
        self._say(tr('"{name}" saved').format(name=escape_caption(entry.name)))
        return True

    async def on_delete_click(self, event: Event) -> bool:
        self.spawn(self.delete_link())
        return True

    async def on_delete_link_entry(self, event: DeleteLinkEntry) -> bool:
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
        self._unchoose()
        self._say(tr('"{name}" deleted').format(name=escape_caption(name)))
        self.label.entry.focus()


def location_of(request: ConnectRequest) -> Location:
    """Where *request* opens: its directory, or the home directory there."""
    return Location(Site(request.scheme, request.user, request.host, request.port),
                    PurePosixPath(request.path) if request.path else profiles.HOME)


__all__ = ["FAMILIES", "Family", "LinkManagerDialog", "entries_for", "family_of", "location_of", "schemes_of",
           "sftp_entries"]
