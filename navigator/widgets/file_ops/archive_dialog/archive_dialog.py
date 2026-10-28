"""The handlers behind ``archive_dialog.nml``: what it opens on, and what OK means.

``ArchiveFiles``' part around ``ExecResource(dlgArchiveFiles)``, the
archive made by the copier (``filecopy._open_target_archive``) as F5 into a
new archive's name makes one.  The line opens on the other panel's
directory and a name after the selection; the type, the level and the boxes
are what they were when the box was last accepted in this session, as DN's
were -- the password never.  The type and the name's ending follow each
other.  A password is asked again, as DN's ``dlgReenterPassword`` asked it,
and an archive there already is added to or replaced, as the user says.
"""

from __future__ import annotations

import asyncio
from pathlib import Path, PurePosixPath
from typing import Any, Sequence

from navkit.events import Event
from navkit.i18n import tr
from navkit.reactive import effect, unbind, untracked

from navml.history import HISTORY
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.drives import Location, drive_of
from navigator.lib.drives import archive
from navigator.lib.file_ops.filecopy import (
    ASK, FOLLOW_LINKS, MOVE, PRESERVE, CopyRequest, shown, target_location,
)
from navigator.settings import SETTINGS
from navigator.widgets.file_ops.commands import ChooseTarget

#: The boxes' bits.
PATHNAMES, MOVE_FILES, FOLLOW = 1, 2, 4

#: What the last accepted box said: the type and level by index, the boxes.
_session = {"kind": 0, "level": archive.LEVEL_NAMES.index("normal"), "options": PATHNAMES}

#: The program each greyed type wants, by ``(kind, compression)``.
_TOOLS = {("7z", ""): "7-Zip", ("tar", "zst"): "zstd", ("rar", ""): "rar"}


def suffix_of(name: str) -> str:
    """The archive ending *name* has -- the longest of :data:`archive.NEW_KINDS` -- or ``""``."""
    lower = name.lower()
    found = [suffix for suffix, _, _ in archive.NEW_KINDS if lower.endswith(suffix) and len(lower) > len(suffix)]
    return max(found, key=len, default="")


def with_suffix(name: str, suffix: str) -> str:
    """*name* with its archive ending, if any, replaced by *suffix*."""
    ending = suffix_of(name)
    return (name[: len(name) - len(ending)] if ending else name) + suffix


def kind_index(name: str) -> int | None:
    """Which of :data:`archive.FORMATS` *name*'s ending is, or None."""
    kind = archive.new_kind(name)
    for index, (_, _, format_kind) in enumerate(archive.FORMATS):
        if format_kind == kind:
            return index
    return None


class ArchiveDialog(Dialog):
    """*Create archive*: its name, type, level, password and options."""

    def __init__(self, entries: Sequence[Any] = (), here: Path | Location | None = None,
                 directory: str = "", stem: str = "archive", hidden: bool = True, **kwargs: Any) -> None:
        """*entries* are the panel's selection in *here*; the line opens on
        *directory* -- the other panel's, when it can be written -- and *stem*
        with the type's ending.  *hidden* is what the Tree follows."""
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        self._entries = list(entries)
        self._here = Location.of(here if here is not None else Path.cwd())
        self._hidden = hidden
        missing = [index for index, (_, _, kind) in enumerate(archive.FORMATS) if archive.format_missing(kind)]
        mask = -1
        for index in missing:
            mask &= ~(1 << index)
        self.kind.enable_mask = mask
        self.note.text = escape_caption("; ".join(
            tr("{format} needs {tool}").format(format=archive.FORMATS[index][0],
                                               tool=_TOOLS.get(archive.FORMATS[index][2], "?"))
            for index in missing))
        kind = _session["kind"] if self.kind.item_enabled(_session["kind"]) else 0
        self.kind.value = self.kind.sel = kind
        self._kind_seen = kind
        if directory:
            directory = directory.rstrip("/") + "/"
            HISTORY.add("copy", directory)
        self.target.value = directory + (stem or "archive") + archive.FORMATS[kind][1]
        self.target.entry.select_all()
        self.level.value = self.level.sel = _session["level"]
        self.options.value = _session["options"]
        self.password.entry.password = True

    def mounted(self) -> None:
        super().mounted()
        effect(self, ArchiveDialog._kind_changed)
        effect(self, ArchiveDialog._name_changed)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.abandon, self.tree, self.help)

    @property
    def format(self) -> tuple[str, str]:
        """The ``(kind, compression)`` the type says."""
        return archive.FORMATS[self.kind.value][2]

    # -- the type, the name and the level following each other ----------------

    def _kind_changed(self) -> None:
        """Another type: the name's ending changed to it, and the levels and
        the password it allows the only ones to be had."""
        index = self.kind.value
        with untracked():
            if index != self._kind_seen:
                self._kind_seen = index
                self.target.value = with_suffix(self.target.value.rstrip(), archive.FORMATS[index][1])
            kind = archive.FORMATS[index][2]
            levels = archive.LEVELS.get(kind, {})
            mask = 0
            for bit, name in enumerate(archive.LEVEL_NAMES):
                if name in levels:
                    mask |= 1 << bit
            self.level.enable_mask = mask
            self.level.disabled = not levels
            self.level_caption.disabled = not levels
            if levels and not self.level.item_enabled(self.level.value):
                normal = archive.LEVEL_NAMES.index("normal")
                self.level.value = self.level.sel = normal
            encrypt = archive.can_encrypt(kind)
            self.password.disabled = not encrypt
            self.password_caption.disabled = not encrypt

    def _name_changed(self) -> None:
        """An ending typed: the type it is chosen, where it can be."""
        text = self.target.value
        with untracked():
            index = kind_index(text.strip())
            if index is not None and index != self.kind.value and self.kind.item_enabled(index):
                self._kind_seen = index
                self.kind.value = self.kind.sel = index

    # -- OK ----------------------------------------------------------------------

    def _request(self, outer: Location, password: str) -> CopyRequest:
        options = self.options.value
        flags = PRESERVE | (FOLLOW_LINKS if options & FOLLOW else 0) | (MOVE if options & MOVE_FILES else 0)
        level = archive.LEVEL_NAMES[self.level.value]
        root = str(Location(archive.ARCHIVE_SITE, PurePosixPath("/"), outer=outer))
        return CopyRequest(
            sources=[shown(entry.path_in(self._here)) for entry in self._entries],
            target=root if root.endswith("/") else root + "/",
            mode=ASK,
            options=flags,
            flush=SETTINGS.system.flush_buffers,
            flatten=not options & PATHNAMES,
            archive=archive.ArchiveOptions(level=level, password=password),
        )

    async def on_pick_click(self, event: Event) -> bool:
        self.spawn(self.confirm())
        return True

    async def confirm(self) -> None:
        """The name made whole, the password asked again, an archive there
        already added to or replaced -- and the request answered."""
        app = self.application
        name = self.target.value.strip()
        if app is None or not name:
            return
        if not suffix_of(name):
            name = with_suffix(name, archive.FORMATS[self.kind.value][1])
        password = self.password.value if not self.password.disabled else ""
        if password and not await self._password_again(password):
            return
        outer = target_location(name, self._here)
        try:
            there = await asyncio.to_thread(lambda: drive_of(outer.parent).lexists(outer))
        except OSError:
            there = False  # said by the copy, which fails the same way
        if there:
            answer = await ask_add_or_replace(app, shown(outer))
            if answer is None:
                return
            if answer == "replace":
                try:
                    await asyncio.to_thread(lambda: drive_of(outer.parent).unlink(outer))
                except OSError as error:
                    await Dialog(title=tr("Error"), buttons="ok", prompt=tr("Cannot replace {path}: {error}").format(
                        path=escape_caption(str(shown(outer))),
                        error=escape_caption(error.strerror or str(error)))).execute(app)
                    return
        self.target.value = name
        self.record_history()
        _session.update(kind=self.kind.value, level=self.level.value, options=self.options.value)
        self.close(self._request(outer, password))

    async def _password_again(self, password: str) -> bool:
        """DN's ``dlgReenterPassword``: whether the same password was typed."""
        from navigator.widgets.drives.password_dialog import PasswordDialog

        app = self.application
        again = await PasswordDialog(title=tr("Re-enter Password"), prompt=tr("Type the password again")).execute(app)
        if again is None:
            return False
        if again[0] != password:
            await Dialog(title=tr("Error"), buttons="ok",
                         prompt=tr("The passwords do not match.")).execute(app)
            self.password.entry.focus()
            return False
        return True

    # -- Tree ----------------------------------------------------------------------

    async def on_tree_click(self, event: Event) -> bool:
        self.spawn(self.choose_target())
        return True

    async def on_choose_target(self, event: ChooseTarget) -> bool:
        self.spawn(self.choose_target())
        return True

    async def choose_target(self) -> None:
        """*Choose Directory*, and the archive's name kept after it."""
        from navigator.widgets.file_ops.copy_dialog.copy_dialog import choose_target_line

        text = self.target.value.strip()
        name = text.rsplit("/", 1)[-1] if text else ""
        if text and not text.endswith("/"):
            self.target.value = text[: len(text) - len(name)]
        await choose_target_line(self, self._here, self._hidden)
        value = self.target.value
        if name and value.endswith("/"):
            self.target.value = value + name
        elif name and not value:
            self.target.value = name


async def ask_add_or_replace(app: Any, path: Any) -> str | None:
    """*PATH already exists*: ``"add"`` the files to it, ``"replace"`` it, or None."""
    box = Dialog(title=tr("Create archive"), buttons="yes-no-cancel",
                 prompt=tr("{path} already exists.").format(path=escape_caption(str(path))))
    unbind(box.ok, Button.text)
    box.ok.text = tr("~A~dd to it")
    unbind(box.no, Button.text)
    box.no.text = tr("~R~eplace")
    answer = await box.execute(app)
    if answer is None:
        return None
    return "add" if answer else "replace"


__all__ = ["ArchiveDialog", "ask_add_or_replace", "kind_index", "suffix_of", "with_suffix"]
