"""The handlers behind ``attr_dialog.nml``: what it opens on, and what OK means.

The dialog opens on :func:`navigator.lib.file_ops.fileattr.survey` of the selection: the
bits every file has ticked, the bits they disagree on ``[?]``, and the owner,
group and time where they all agree -- blank where they do not.  Blank, and a
``[?]`` nobody moved, are *leave it as it is*.

**Only what the user touched is applied.**  A bit counts once it is pressed,
even pressed back, and an octal digit that changes anything claims all three
of its bits, so that ``0644`` typed means 644 on every file it reaches; a bit
nobody moved goes in neither of the request's masks.  It matters under a recursed
directory -- the directory's own ``755`` must not give every file in it an
execute bit because the grid happened to show one.

**The octal line and the grid follow each other, a digit at a time.**  The
line is a :class:`MaskedLine` of four places in base eight, so it takes the
digits 0 to 7 and nothing else, and Up and Down step the mode as an octal
number.  Each of its digits that is one sets the three boxes it stands for
and clears their ``[?]``; a ``?`` or a blank place leaves them as they are.
Pressing a box rewrites the line, unless the line has the keyboard -- then
it is tidied when the keyboard leaves it, so a blanked place is not filled
back in under the user's fingers.

**A click on the ``rwxr-xr-x`` beside the octal line presses that box**: its
nine letters are the grid's first nine items in the same order, so a click
does what Space on the box would, a ``?`` cycling as it does there.  The
special bits show in the execute letters (``s``, ``t``) but are pressed in
the grid; a click there presses the execute bit.

**R, W and X press a box in the grid's current column** -- Read, Write or
Exec of whichever of owner, group and others the cursor is in, and the cursor
goes to it -- as ``r``/``w``/``x`` did in Midnight Commander's *Advanced
chown*.  In the special column, which has none of the three, they do nothing.

**Dismissing it with something changed asks first** -- Esc or the close icon --
*Changes will be lost. Are you sure?*, and only *Yes* lets it go.  The Cancel
button does not ask: pressing it is already the answer.
Changed means differing from what it opened on, so a box pressed and pressed
back, or a line typed into and restored, asks nothing.

**ACL, Xattrs and Flags are pages behind tabs** (a departure, asked for):
what every file shares is listed or ticked, what they disagree on is ``???``,
``‹differs›`` or ``[?]``, and only what the user added, changed or removed
goes in the request -- the same edit to every file, under *Recurse* too
(:mod:`navigator.lib.file_ops.acl` has the ACL's rules).  Ins, Enter and Del
on either list are *Add*, *Edit* and *Delete*; whom an ACL entry names is
picked from the passwd or group database (``AclEntryDialog``).  A page that
cannot apply -- another drive, a file system without flags -- is inert and
says why.

**Up and Down move between the lines** -- Octal, User, Group, Date, Time, in
that order, passing over one that is disabled -- since the grid and the
radio buttons each keep their arrows for themselves and the lines had no
use for them.  At either end they stay where they are.  Date and Time keep
them: there they step the date or time, carrying as a calendar does.
"""

from __future__ import annotations

import os

import stat
from pathlib import Path
from typing import Any, Sequence

from navkit.events import KeyEvent, MouseClickEvent
from navkit.i18n import tr, tr_n
from navkit.reactive import bind, effect, unbind, untracked
from navkit.widget import Widget

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.config import country
from navigator.lib.file_ops import acl, fileattr, fsflags

#: The grid's twelve items.
ALL_ITEMS = (1 << len(fileattr.BITS)) - 1

#: The keys that press a box in the cursor's column, and its row there.
ROW_KEYS = {"r": 0, "w": 1, "x": 2}

#: The grid's columns of read/write/execute: owner, group, others.
RWX_COLUMNS = 3

#: The flags grid's twelve items.
ALL_FLAGS = (1 << len(fsflags.EDITABLE)) - 1

#: An ACL row's key: whether it is the default ACL's, then the entry's own
#: key (:meth:`navigator.lib.file_ops.acl.Acl.entries`).
AclRow = tuple[bool, str, "int | None"]


def name_for(entries: Sequence[Any]) -> str:
    """``File notes.txt``, ``Directory src``, ``3 files, 1 directory``."""
    if len(entries) == 1:
        entry = entries[0]
        if entry.is_dir:
            return tr("Directory ~{name}~").format(name=escape_caption(entry.name))
        return tr("File ~{name}~").format(name=escape_caption(entry.name))
    dirs = sum(1 for entry in entries if entry.is_dir)
    files = len(entries) - dirs
    parts = []
    if files:
        parts.append(tr_n("{n} file", "{n} files", files))
    if dirs:
        parts.append(tr_n("{n} directory", "{n} directories", dirs))
    return "~" + ", ".join(parts) + "~"


def info_for(survey: fileattr.Survey) -> str:
    """A lone entry's kind and size, and where a link points; nothing for several."""
    st = survey.single
    if st is None:
        return ""
    mode = st.st_mode
    if stat.S_ISDIR(mode):
        text = tr("directory")
    elif stat.S_ISREG(mode):
        text = tr_n("{n:,} byte", "{n:,} bytes", st.st_size)
    elif stat.S_ISLNK(mode):
        text = tr("broken link")
    elif stat.S_ISFIFO(mode):
        text = tr("named pipe")
    elif stat.S_ISSOCK(mode):
        text = tr("socket")
    elif stat.S_ISCHR(mode) or stat.S_ISBLK(mode):
        text = tr("device")
    else:
        text = tr("special file")
    if survey.link_target is not None:
        text = tr("link to {target}, {kind}").format(target=survey.link_target, kind=text)
    return escape_caption(text[0].upper() + text[1:])


def with_current(choices: list[str], current: str) -> list[str]:
    """*choices*, with *current* among them, so the list opens on it.

    A file's group need not be one of the user's, and an owner or group may
    have no name -- but keeping what a file has is always allowed, so it is
    always offered, and the list is never opened on an entry that is not it.
    """
    if not current or current in choices:
        return choices
    return sorted([*choices, current])


def gather(paths: Sequence[Path]) -> dict[str, Any]:
    """Everything the dialog shows that has to be asked of the system.

    Every file's ``stat``, and the user and group names and lists -- which
    NSS may fetch from a directory server -- in one call a thread can make
    (``Manager.change_attributes``), so the screen does not wait for them.
    """
    survey = fileattr.survey(paths)
    if paths and not isinstance(paths[0], (str, os.PathLike)) and not paths[0].is_local:
        # On another drive: its ids mean nothing in this system's passwd, so
        # they are numbers, and changed only where the drive can.
        from navigator.lib.drives import drive_of

        drive = drive_of(paths[0])
        can = drive.can("chown")
        return {
            "survey": survey,
            "user": "" if survey.uid is None else str(survey.uid), "users": [], "can_chown_user": can,
            "group": "" if survey.gid is None else str(survey.gid), "groups": [], "can_chown_group": can,
            "all_users": [], "all_groups": [], "names": acl_names(survey, numbers=True),
            "can_xattr": drive.can("xattr"), "can_flags": drive.can("fsflags"),
        }
    return {
        "survey": survey,
        "user": "" if survey.uid is None else fileattr.user_name(survey.uid),
        "users": fileattr.users(),
        "can_chown_user": fileattr.can_chown_user(),
        "group": "" if survey.gid is None else fileattr.group_name(survey.gid),
        "groups": fileattr.assignable_groups(),
        # An ACL may name anyone, where only root may give a file away.
        "all_users": fileattr.users(),
        "all_groups": fileattr.groups(),
        "names": acl_names(survey),
        "can_xattr": True, "can_flags": True,
    }


def acl_names(survey: fileattr.Survey, numbers: bool = False) -> dict[tuple[str, int], str]:
    """The name of everyone the selection's ACLs name, asked here, on
    :func:`gather`'s thread; their numbers alone with *numbers*."""
    names = {}
    for key in (*survey.acl, *survey.default_acl):
        kind, ident = key
        if ident is None or key in names:
            continue
        if numbers:
            names[key] = str(ident)
        else:
            names[key] = fileattr.user_name(ident) if kind == acl.KIND_USER else fileattr.group_name(ident)
    return names


class AttrDialog(Dialog):
    """*File Attributes* (Alt+E): the mode, owner, group and time of the selection."""

    def __init__(
        self,
        entries: Sequence[Any] = (),
        here: Path | None = None,
        facts: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """*entries* are the panel's selection in *here*; *facts* is what
        :func:`gather` found of them, asked for here if not given."""
        super().__init__(**kwargs)
        self.message.visible = False
        # OK and Cancel a row lower than a dialog's, their shadow on the row
        # above the frame, as *Settings* has them: a blank row under *Recurse*.
        unbind(self.row, Widget.y)
        self.row.y = bind(lambda r: max(0, self.height - 3))
        self._entries = list(entries)
        from navigator.lib.drives import Location
        from navigator.lib.file_ops.filecopy import shown

        self._here = Location.of(here if here is not None else Path.cwd())
        self._paths = [shown(entry.path_in(self._here)) for entry in self._entries]
        if facts is None:
            facts = gather(self._paths)
        self.survey = facts["survey"]
        #: The bits the user has pressed, as grid items.
        self.touched = 0
        self._request: fileattr.AttrRequest | None = None

        survey = self.survey
        self.name_row.text = name_for(self._entries)
        self.info_row.text = info_for(survey)
        self._initial = fileattr.to_items(survey.mode)
        self._initial_mixed = fileattr.to_items(survey.mixed)
        self.bits.value = self._initial
        self.bits.mixed = self._initial_mixed
        self.bits.tristate = self._initial_mixed
        self._seen = (self._initial, self._initial_mixed)
        self.octal.value = fileattr.octal(survey.mode, survey.mixed)
        self.symbolic.text = fileattr.symbolic(survey.mode, survey.mixed)

        self.user.value = facts["user"]
        self.user.choices = with_current(facts["users"], self.user.value)
        self.user.disabled = not facts["can_chown_user"]
        self.group.value = facts["group"]
        self.group.choices = with_current(facts["groups"], self.group.value)
        if "can_chown_group" in facts:
            self.group.disabled = not facts["can_chown_group"]
        # *Country support*'s order, where a mask can hold it (country.typed_date_format).
        self.date.date_format = country.typed_date_format()
        self.date.value = fileattr.date_text(survey.mtime, self.date.date_format)
        self.clock.time_format = country.typed_time_format()
        self.clock.value = fileattr.time_text(survey.mtime, self.clock.time_format)

        self.recurse.disabled = not survey.dirs
        self.recurse_caption.disabled = not survey.dirs

        elsewhere = bool(self._paths) and not self._here.is_local
        self._all_users = list(facts.get("all_users", ()))
        self._all_groups = list(facts.get("all_groups", ()))
        #: Who each ACL key names, for its row; keys added get theirs as added.
        self._names: dict[tuple[str, int], str] = dict(facts.get("names", {}))
        can_xattr = facts.get("can_xattr", True) and survey.xattrs_supported

        #: The ACL rows as they are now, and as the dialog opened on them.
        self._acl: dict[AclRow, int | None] = {}
        if can_xattr:
            self._acl = {(False, *key): perm for key, perm in survey.acl.items()}
            self._acl.update({(True, *key): perm for key, perm in survey.default_acl.items()})
        self._acl_initial = dict(self._acl)
        self._acl_rows: list[AclRow] = []
        self._refresh_acl()
        #: Extended attributes as they are now, and as the dialog opened on them.
        self._xattrs: dict[str, bytes | None] = dict(survey.xattrs) if can_xattr else {}
        self._xattrs_initial = dict(self._xattrs)
        self._xattr_rows: list[str] = []
        self._refresh_xattrs()
        if not can_xattr:
            why = (tr("Not on this drive") if elsewhere or not facts.get("can_xattr", True)
                   else tr("Not supported by this file system"))
            self._inert(why, self.acl_note, self.acl_caption, self.acl_list, self.acl_add, self.acl_edit,
                        self.acl_delete, self.acl_clear)
            self._inert(why, self.xattr_note, self.xattr_caption, self.xattr_list, self.xattr_add,
                        self.xattr_edit, self.xattr_delete)

        #: The flags pressed, as grid items, as ``touched`` is the mode's.
        self.flags_touched = 0
        self._initial_flags = fsflags.to_items(survey.flags)
        self._initial_flags_mixed = fsflags.to_items(survey.flags_mixed)
        self.flags.value = self._initial_flags
        self.flags.mixed = self._initial_flags_mixed
        self.flags.tristate = self._initial_flags_mixed
        self._flags_seen = (self._initial_flags, self._initial_flags_mixed)
        self.lsattr.text = "lsattr  " + fsflags.lsattr(survey.flags, survey.flags_mixed)
        if not (facts.get("can_flags", True) and survey.flags_supported):
            why = (tr("Not on this drive") if elsewhere or not facts.get("can_flags", True)
                   else tr("Not supported by this file system"))
            self.lsattr.text = ""
            self._inert(why, self.flags_note, self.flags_caption, self.flags)

        #: What the dialog opened on, which dismissing it compares against.
        self._opened_on = self._state()

        self.symbolic.on_mouse_click = self._on_symbolic_click

        # In front of the grid's own keys, which still has the arrows and Space.
        self._grid_keys = self.bits.on_key
        self.bits.on_key = self._on_bits_key
        # Ins, Enter and Del on the two lists.
        self._acl_keys = self.acl_list.on_key
        self.acl_list.on_key = self._on_acl_key
        self.acl_list.choose = self._choose_acl
        self._xattr_keys = self.xattr_list.on_key
        self.xattr_list.on_key = self._on_xattr_key
        self.xattr_list.choose = self._choose_xattr

    def mounted(self) -> None:
        super().mounted()
        effect(self, AttrDialog._grid_changed)
        effect(self, AttrDialog._octal_changed)
        effect(self, AttrDialog._flags_changed)

    def key_hints(self) -> list[tuple[str, str]]:
        """The grid's R, W and X (``_on_bits_key``), which no caption marks,
        while the grid has the keyboard; the lists' Ins and Del while one has."""
        if self.bits.focused:
            return [("R W X", tr("Read Write Exec"))]
        if self.acl_list.focused or self.xattr_list.focused:
            return [("Ins", tr("Add")), ("Enter", tr("Edit")), ("Del", tr("Delete"))]
        return []

    @staticmethod
    def _inert(why: str, note: Any, *controls: Any) -> None:
        """A page that cannot apply: its controls disabled, *note* saying *why*."""
        note.text = escape_caption(why)
        for control in controls:
            control.disabled = True

    # -- Up and Down between the lines ----------------------------------------

    @property
    def lines(self) -> tuple[Any, ...]:
        """The lines Up and Down step through, top to bottom."""
        return (self.octal.entry, self.user.entry, self.group.entry, self.date.entry, self.clock.entry)

    async def on_key(self, event: KeyEvent) -> bool:
        if event.matches("up", "down"):
            lines = self.lines
            app = self.application
            focused = app.focused if app is not None else None
            if focused in lines:
                step = -1 if event.matches("up") else 1
                index = lines.index(focused) + step
                while 0 <= index < len(lines):
                    if lines[index].can_focus and lines[index].focus():
                        break
                    index += step
                return True
        return await super().on_key(event)

    # -- the symbolic text, clicked ----------------------------------------------

    async def _on_symbolic_click(self, event: MouseClickEvent) -> bool:
        """A press on one of ``rwxr-xr-x``'s letters presses its box."""
        if event.action != "press" or event.button != "left" or self.bits.inert:
            return False
        if event.y == 0 and 0 <= event.x < 9:
            self.bits.sel = event.x
            self.bits.toggle(event.x)
            return True
        return False

    # -- the grid's letters ----------------------------------------------------

    async def _on_bits_key(self, event: KeyEvent) -> bool:
        """R, W or X: that box in the cursor's column, pressed."""
        row = ROW_KEYS.get(event.key)
        if row is None or event.ctrl or event.alt or self.bits.inert:
            return await self._grid_keys(event)
        column = self.bits.sel // 3
        if column < RWX_COLUMNS:
            index = column * 3 + row
            self.bits.sel = index
            self.bits.toggle(index)
        return True

    # -- the grid and the line, each following the other -----------------------

    def _grid_changed(self) -> None:
        value, mixed = self.bits.value, self.bits.mixed
        editing = self.octal.entry.focused
        with untracked():
            old_value, old_mixed = self._seen
            self.touched |= (value ^ old_value) | (mixed ^ old_mixed)
            self._seen = (value, mixed)
            mode = fileattr.from_items(value)
            unknown = fileattr.from_items(mixed)
            self.symbolic.text = fileattr.symbolic(mode, unknown)
            text = fileattr.octal(mode, unknown)
            if not editing and self.octal.value != text:
                self.octal.value = text

    def _octal_changed(self) -> None:
        text = self.octal.value
        with untracked():
            if len(text) != 4:
                return
            value, mixed = self.bits.value, self.bits.mixed
            claimed = 0
            for char, shift in zip(text, (9, 6, 3, 0)):
                if char not in "01234567":
                    continue
                # The three boxes this digit stands for, and what it says of them.
                boxes = fileattr.to_items(0o7 << shift)
                want = fileattr.to_items(int(char) << shift)
                if (value & boxes, mixed & boxes) != (want, 0):
                    claimed |= boxes
                value = (value & ~boxes) | want
                mixed &= ~boxes
            self.touched |= claimed
            if (value, mixed) != (self.bits.value, self.bits.mixed):
                # Mixed first, so a box leaving ``[?]`` is never painted off.
                self.bits.mixed = mixed
                self.bits.value = value

    # -- the flags ---------------------------------------------------------------

    def _flags_changed(self) -> None:
        value, mixed = self.flags.value, self.flags.mixed
        with untracked():
            old_value, old_mixed = self._flags_seen
            self.flags_touched |= (value ^ old_value) | (mixed ^ old_mixed)
            self._flags_seen = (value, mixed)
            if not self.lsattr.text:
                return
            survey = self.survey
            shown = (survey.flags & ~fsflags.EDITABLE_MASK) | fsflags.from_items(value)
            unknown = (survey.flags_mixed & ~fsflags.EDITABLE_MASK) | fsflags.from_items(mixed)
            self.lsattr.text = "lsattr  " + fsflags.lsattr(shown, unknown)

    # -- the ACL -------------------------------------------------------------------

    def _acl_name(self, row: AclRow) -> str:
        _, kind, ident = row
        if ident is None:
            return ""
        return self._names.get((kind, ident), str(ident))

    def _acl_text(self, row: AclRow) -> str:
        default, kind, ident = row
        perm = self._acl[row]
        if kind == acl.MASK_KEY[0] and self._mask_follows(default):
            spelled = tr("auto")
        else:
            spelled = acl.spell(perm)
        label = ("default:" if default else "") + kind
        return f"{label:<14}{self._acl_name(row)[:20]:<21}{spelled}"

    def _mask_follows(self, default: bool) -> bool:
        """Whether the mask will be worked out again on OK: a named entry of
        that ACL changed, and the mask was not set here."""
        mask = (default, *acl.MASK_KEY)
        if self._acl.get(mask) != self._acl_initial.get(mask) or mask not in self._acl_initial:
            return False
        rows = {row for row in self._acl.keys() | self._acl_initial.keys()
                if row[0] == default and row[1] != acl.MASK_KEY[0]}
        return any(self._acl.get(row) != self._acl_initial.get(row) for row in rows)

    def _refresh_acl(self, at: AclRow | None = None) -> None:
        def order(row: AclRow) -> tuple[Any, ...]:
            default, kind, _ = row
            return default, ("user", "group", "mask").index(kind), self._acl_name(row)

        self._acl_rows = sorted(self._acl, key=order)
        self.acl_list.items = [self._acl_text(row) for row in self._acl_rows]
        if at in self._acl_rows:
            self.acl_list.cursor = self._acl_rows.index(at)
        else:
            self.acl_list.cursor = max(0, min(self.acl_list.cursor, len(self._acl_rows) - 1))
        has_rows = bool(self._acl_rows) and not self.acl_list.disabled
        self.acl_edit.disabled = self.acl_delete.disabled = self.acl_clear.disabled = not has_rows

    def _acl_row(self) -> AclRow | None:
        index = self.acl_list.cursor
        return self._acl_rows[index] if 0 <= index < len(self._acl_rows) else None

    async def _on_acl_key(self, event: KeyEvent) -> bool:
        if not self.acl_list.inert and not event.ctrl and not event.alt:
            if event.matches("insert"):
                self.spawn(self.add_acl_entry())
                return True
            if event.matches("delete"):
                self.delete_acl_entry()
                return True
        return await self._acl_keys(event)

    async def _choose_acl(self) -> bool:
        if self._acl_row() is None:
            return False
        self.spawn(self.edit_acl_entry())
        return True

    async def on_acl_add_click(self, event: Any) -> bool:
        self.spawn(self.add_acl_entry())
        return True

    async def on_acl_edit_click(self, event: Any) -> bool:
        self.spawn(self.edit_acl_entry())
        return True

    async def on_acl_delete_click(self, event: Any) -> bool:
        self.delete_acl_entry()
        return True

    async def on_acl_clear_click(self, event: Any) -> bool:
        """``setfacl -b``: every row gone, on every file."""
        self._acl = {}
        self._refresh_acl()
        self.acl_list.focus()
        return True

    async def add_acl_entry(self) -> None:
        from navigator.widgets.file_ops.acl_entry_dialog import AclEntryDialog

        box = AclEntryDialog(self._all_users, self._all_groups, can_default=bool(self.survey.dirs))
        answer = await box.execute(self.application)
        if answer is None:
            return
        default, kind, ident, perms = answer
        row = (default, kind, ident)
        if ident is not None:
            self._names[(kind, ident)] = box.who.value.strip()
        self._acl = {**self._acl, row: perms}
        self._refresh_acl(at=row)
        self.acl_list.focus()

    async def edit_acl_entry(self) -> None:
        from navigator.widgets.file_ops.acl_entry_dialog import AclEntryDialog

        row = self._acl_row()
        if row is None:
            return
        default, kind, _ = row
        perm = self._acl[row]
        box = AclEntryDialog(
            self._all_users, self._all_groups, kind=kind, name=self._acl_name(row),
            perms=perm or 0, default=default, can_default=default, editing=True,
            mask=kind == acl.MASK_KEY[0],
        )
        answer = await box.execute(self.application)
        if answer is None:
            return
        self._acl = {**self._acl, row: answer[3]}
        self._refresh_acl(at=row)
        self.acl_list.focus()

    def delete_acl_entry(self) -> None:
        row = self._acl_row()
        if row is None:
            return
        self._acl = {key: perm for key, perm in self._acl.items() if key != row}
        self._refresh_acl()

    # -- the extended attributes -------------------------------------------------------

    def _xattr_text(self, name: str) -> str:
        value = self._xattrs[name]
        spelled = tr("<differs>") if value is None else fileattr.spell_value(value)
        return f"{name[:22]:<23}{spelled}"

    def _refresh_xattrs(self, at: str | None = None) -> None:
        self._xattr_rows = sorted(self._xattrs)
        self.xattr_list.items = [self._xattr_text(name) for name in self._xattr_rows]
        if at in self._xattr_rows:
            self.xattr_list.cursor = self._xattr_rows.index(at)
        else:
            self.xattr_list.cursor = max(0, min(self.xattr_list.cursor, len(self._xattr_rows) - 1))
        has_rows = bool(self._xattr_rows) and not self.xattr_list.disabled
        self.xattr_edit.disabled = self.xattr_delete.disabled = not has_rows

    def _xattr_row(self) -> str | None:
        index = self.xattr_list.cursor
        return self._xattr_rows[index] if 0 <= index < len(self._xattr_rows) else None

    async def _on_xattr_key(self, event: KeyEvent) -> bool:
        if not self.xattr_list.inert and not event.ctrl and not event.alt:
            if event.matches("insert"):
                self.spawn(self.add_xattr())
                return True
            if event.matches("delete"):
                self.delete_xattr()
                return True
        return await self._xattr_keys(event)

    async def _choose_xattr(self) -> bool:
        if self._xattr_row() is None:
            return False
        self.spawn(self.edit_xattr())
        return True

    async def on_xattr_add_click(self, event: Any) -> bool:
        self.spawn(self.add_xattr())
        return True

    async def on_xattr_edit_click(self, event: Any) -> bool:
        self.spawn(self.edit_xattr())
        return True

    async def on_xattr_delete_click(self, event: Any) -> bool:
        self.delete_xattr()
        return True

    async def add_xattr(self) -> None:
        from navigator.widgets.file_ops.xattr_entry_dialog import XattrEntryDialog

        answer = await XattrEntryDialog().execute(self.application)
        if answer is None:
            return
        name, value = answer
        self._xattrs = {**self._xattrs, name: value}
        self._refresh_xattrs(at=name)
        self.xattr_list.focus()

    async def edit_xattr(self) -> None:
        from navigator.widgets.file_ops.xattr_entry_dialog import XattrEntryDialog

        name = self._xattr_row()
        if name is None:
            return
        answer = await XattrEntryDialog(name, self._xattrs[name], editing=True).execute(self.application)
        if answer is None:
            return
        self._xattrs = {**self._xattrs, name: answer[1]}
        self._refresh_xattrs(at=name)
        self.xattr_list.focus()

    def delete_xattr(self) -> None:
        name = self._xattr_row()
        if name is None:
            return
        self._xattrs = {key: value for key, value in self._xattrs.items() if key != name}
        self._refresh_xattrs()

    # -- what dismissing it loses -----------------------------------------------

    def _state(self) -> tuple[Any, ...]:
        """Every value the user can change, to compare with what it opened on."""
        return (
            self.bits.value,
            self.bits.mixed,
            self.octal.value,
            self.user.value,
            self.group.value,
            self.date.value,
            self.clock.value,
            self.recurse.value,
            self.flags.value,
            self.flags.mixed,
            tuple(sorted(self._acl.items(), key=repr)),
            tuple(sorted(self._xattrs.items(), key=repr)),
        )

    def must_ask(self) -> bool:
        """Changed from what it opened on -- a box pressed back is no change."""
        return self._state() != self._opened_on

    async def ask_to_close(self) -> bool:
        answer = await Dialog(
            title=tr("Warning"),
            prompt=tr("Changes will be lost. Are you sure?"),
            buttons="yes-no",
        ).execute(self.application)
        return answer is True

    # -- what OK means -----------------------------------------------------------

    def build(self) -> fileattr.AttrRequest:
        """The request the dialog says, or ``ValueError`` naming what is wrong."""
        survey = self.survey
        value, mixed = self.bits.value, self.bits.mixed
        changed = self.touched & ~mixed & ALL_ITEMS
        set_bits = fileattr.from_items(changed & value)
        clear_bits = fileattr.from_items(changed & ~value)
        uid = fileattr.parse_user(self.user.value) if not self.user.disabled else None
        gid = fileattr.parse_group(self.group.value)
        mtime = fileattr.parse_mtime(self.date.value, self.clock.value, survey.mtime,
                                     self.date.date_format, self.clock.time_format)
        recurse = fileattr.RECURSE[self.recurse.value] if survey.dirs else fileattr.NONE
        request = fileattr.AttrRequest(
            sources=list(self._paths),
            set_bits=set_bits,
            clear_bits=clear_bits,
            uid=None if uid == survey.uid else uid,
            gid=None if gid == survey.gid else gid,
            mtime=mtime,
            recurse=recurse,
        )
        for row in self._acl_initial.keys() - self._acl.keys():
            (request.default_remove if row[0] else request.acl_remove).add(row[1:])
        for row, perm in self._acl.items():
            if perm is not None and self._acl_initial.get(row) != perm:
                (request.default_set if row[0] else request.acl_set)[row[1:]] = perm
        request.xattr_remove = set(self._xattrs_initial.keys() - self._xattrs.keys())
        request.xattr_set = {name: value for name, value in self._xattrs.items()
                             if value is not None and self._xattrs_initial.get(name) != value}
        flags_value, flags_mixed = self.flags.value, self.flags.mixed
        changed = self.flags_touched & ~flags_mixed & ALL_FLAGS
        request.flags_set = fsflags.from_items(changed & flags_value)
        request.flags_clear = fsflags.from_items(changed & ~flags_value)
        return request

    def valid(self) -> bool:
        """``Valid(cmOK)``: a mode, owner, group or time that cannot be read keeps the dialog up."""
        try:
            self._request = self.build()
        except ValueError as error:
            self._request = None
            if self.application is not None:
                box = Dialog(title=tr("Error"), prompt=escape_caption(str(error)), buttons="ok")
                self.spawn(box.execute(self.application))
            return False
        return True

    def accept(self) -> fileattr.AttrRequest | None:
        """The request, or ``None`` when it would change nothing -- what Cancel says."""
        request = self._request if self._request is not None else self.build()
        return None if request.changes_nothing else request
