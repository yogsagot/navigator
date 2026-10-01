"""The handlers behind ``attr_dialog.nml``: what it opens on, and what OK means.

The dialog opens on :func:`navigator.fileattr.survey` of the selection: the
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

**Up and Down move between the lines** -- Octal, User, Group, Date, Time, in
that order, passing over one that is disabled -- since the grid and the
radio buttons each keep their arrows for themselves and the lines had no
use for them.  At either end they stay where they are.  Date and Time keep
them: there they step the date or time, carrying as a calendar does.
"""

from __future__ import annotations

import stat
from pathlib import Path
from typing import Any, Sequence

from navkit.events import KeyEvent, MouseClickEvent
from navkit.reactive import effect, untracked

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator import fileattr

#: The grid's twelve items.
ALL_ITEMS = (1 << len(fileattr.BITS)) - 1

#: The keys that press a box in the cursor's column, and its row there.
ROW_KEYS = {"r": 0, "w": 1, "x": 2}

#: The grid's columns of read/write/execute: owner, group, others.
RWX_COLUMNS = 3


def name_for(entries: Sequence[Any]) -> str:
    """``File notes.txt``, ``Directory src``, ``3 files, 1 directory``."""
    if len(entries) == 1:
        entry = entries[0]
        kind = "Directory" if entry.is_dir else "File"
        return f"{kind} ~{escape_caption(entry.name)}~"
    dirs = sum(1 for entry in entries if entry.is_dir)
    files = len(entries) - dirs
    parts = []
    if files:
        parts.append(f"{files} file" + ("s" if files != 1 else ""))
    if dirs:
        parts.append(f"{dirs} director" + ("ies" if dirs != 1 else "y"))
    return "~" + ", ".join(parts) + "~"


def info_for(survey: fileattr.Survey) -> str:
    """A lone entry's kind and size, and where a link points; nothing for several."""
    st = survey.single
    if st is None:
        return ""
    mode = st.st_mode
    if stat.S_ISDIR(mode):
        text = "directory"
    elif stat.S_ISREG(mode):
        text = f"{st.st_size:,} bytes"
    elif stat.S_ISLNK(mode):
        text = "broken link"
    elif stat.S_ISFIFO(mode):
        text = "named pipe"
    elif stat.S_ISSOCK(mode):
        text = "socket"
    elif stat.S_ISCHR(mode) or stat.S_ISBLK(mode):
        text = "device"
    else:
        text = "special file"
    if survey.link_target is not None:
        text = f"link to {survey.link_target}, {text}"
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


class AttrDialog(Dialog):
    """*File Attributes* (Alt+E): the mode, owner, group and time of the selection."""

    def __init__(
        self,
        entries: Sequence[Any] = (),
        here: Path | None = None,
        **kwargs: Any,
    ) -> None:
        """*entries* are the panel's selection in *here*."""
        super().__init__(**kwargs)
        self.message.visible = False
        self._entries = list(entries)
        self._here = Path(here) if here is not None else Path.cwd()
        self._paths = [self._here / entry.name for entry in self._entries]
        self.survey = fileattr.survey(self._paths)
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

        self.user.value = "" if survey.uid is None else fileattr.user_name(survey.uid)
        self.user.choices = with_current(fileattr.users(), self.user.value)
        self.user.disabled = not fileattr.can_chown_user()
        self.group.value = "" if survey.gid is None else fileattr.group_name(survey.gid)
        self.group.choices = with_current(fileattr.assignable_groups(), self.group.value)
        self.date.value = fileattr.date_text(survey.mtime)
        self.clock.value = fileattr.time_text(survey.mtime)

        self.recurse.disabled = not survey.dirs
        self.recurse_caption.disabled = not survey.dirs

        #: What the dialog opened on, which dismissing it compares against.
        self._opened_on = self._state()

        self.symbolic.on_mouse_click = self._on_symbolic_click

        # In front of the grid's own keys, which still has the arrows and Space.
        self._grid_keys = self.bits.on_key
        self.bits.on_key = self._on_bits_key

    def mounted(self) -> None:
        super().mounted()
        effect(self, AttrDialog._grid_changed)
        effect(self, AttrDialog._octal_changed)

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
        )

    def must_ask(self) -> bool:
        """Changed from what it opened on -- a box pressed back is no change."""
        return self._state() != self._opened_on

    async def ask_to_close(self) -> bool:
        answer = await Dialog(
            title="Warning",
            prompt="Changes will be lost. Are you sure?",
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
        mtime = fileattr.parse_mtime(self.date.value, self.clock.value, survey.mtime)
        recurse = fileattr.RECURSE[self.recurse.value] if survey.dirs else fileattr.NONE
        return fileattr.AttrRequest(
            sources=list(self._paths),
            set_bits=set_bits,
            clear_bits=clear_bits,
            uid=None if uid == survey.uid else uid,
            gid=None if gid == survey.gid else gid,
            mtime=mtime,
            recurse=recurse,
        )

    def valid(self) -> bool:
        """``Valid(cmOK)``: a mode, owner, group or time that cannot be read keeps the dialog up."""
        try:
            self._request = self.build()
        except ValueError as error:
            self._request = None
            if self.application is not None:
                box = Dialog(title="Error", prompt=escape_caption(str(error)), buttons="ok")
                self.spawn(box.execute(self.application))
            return False
        return True

    def accept(self) -> fileattr.AttrRequest | None:
        """The request, or ``None`` when it would change nothing -- what Cancel says."""
        request = self._request if self._request is not None else self.build()
        return None if request.changes_nothing else request
