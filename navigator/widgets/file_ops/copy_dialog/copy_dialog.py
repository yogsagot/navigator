"""The handlers behind ``copy_dialog.nml``: what it opens on, and what OK means.

Everything here is ``FILECOPY.PAS``'s ``CopyDialog``, the part that ran
before the resource was shown and after it closed.  The prompt is built from
what was selected; the line opens on the passive panel's directory; the copy
mode and options are what they were the last time the dialog was accepted in
this session -- DN's ``ccCopyMode``/``ccCopyOpt``, which were typed constants
and so lasted until Navigator quit, and not a moment longer.  *Remove source*
is F6's and never remembered: the key says whether it is ticked.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from navkit.events import Event
from navkit.i18n import tr, tr_n

from navml.history import HISTORY
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.file_ops.commands import ChooseTarget
from navigator.filecopy import ASK, MOVE, PRESERVE, CopyRequest
from navigator.settings import SETTINGS

#: ``ccCopyMode`` and ``ccCopyOpt``: what the last accepted dialog said.  DN
#: began at *Ask* and nothing ticked; *Preserve attributes* begins ticked
#: here, because a copy that loses its time stamps surprises on Linux.
_session = {"mode": ASK, "options": PRESERVE}


def prompt_for(entries: Sequence[Any], move: bool) -> str:
    """``Copy file NAME to``, ``Copy Directory NAME to``, ``Copy 3 files to``.

    DN's ``dlFCCopyTo`` with the object put in after its first word, and
    ``dlFCMoveOr`` in front for F6.  The object is marked so that it is drawn
    highlighted, as DN's ``#0`` trick drew it, and a ``~`` in a name is
    doubled so that it shows as itself.  DN's double space before *to* after a
    count was an accident of the spacing, and is not kept.
    """
    if len(entries) != 1:
        if move:
            return tr_n("~R~ename or move ~{n} file~ to", "~R~ename or move ~{n} files~ to", len(entries))
        return tr_n("~C~opy ~{n} file~ to", "~C~opy ~{n} files~ to", len(entries))
    entry = entries[0]
    name = escape_caption(entry.name)
    if entry.is_dir:
        if move:
            return tr("~R~ename or move Directory ~{name}~ to").format(name=name)
        return tr("~C~opy Directory ~{name}~ to").format(name=name)
    if move:
        return tr("~R~ename or move file ~{name}~ to").format(name=name)
    return tr("~C~opy file ~{name}~ to").format(name=name)


def target_for(entries: Sequence[Any], here: Path, other: Path | None, move: bool) -> str:
    """What the line opens on: ``CopyDialog``'s ``S4``.

    The other panel's directory when it is somewhere else, with a single
    file's name after it; F6 on one entry with nowhere else to go opens on the
    bare name, which renames it in place.  Nothing at all otherwise, as DN
    left it.
    """
    if other is not None and Path(other) != Path(here):
        text = str(other).rstrip("/") + "/"
        if len(entries) == 1 and not entries[0].is_dir:
            text += entries[0].name
        return text
    if move and len(entries) == 1:
        return entries[0].name
    return ""


class CopyDialog(Dialog):
    """*Copy* (F5) or *Rename/move* (F6): where the files go, and how."""

    def __init__(
        self,
        entries: Sequence[Any] = (),
        here: Path | None = None,
        other: Path | None = None,
        hidden: bool = True,
        **kwargs: Any,
    ) -> None:
        """*entries* are the panel's selection in *here*; *other* is the passive panel's directory.

        *hidden* is the panel's ``show_hidden``, which the Tree button's
        directory tree follows as Alt+T's does.
        """
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        self._entries = list(entries)
        self._here = Path(here) if here is not None else Path.cwd()
        self._hidden = hidden
        self.prompt_caption.text = prompt_for(self._entries, self.move)
        # ``cmPushName``: every panel somewhere else puts its directory in
        # the history, so the Down arrow offers it.
        if other is not None and Path(other) != self._here:
            HISTORY.add("copy", str(other).rstrip("/") + "/")
        self.target.value = target_for(self._entries, self._here, other, self.move)
        self.target.entry.select_all()
        self.mode.value = self.mode.sel = _session["mode"]
        options = _session["options"] & ~MOVE
        self.options.value = options | MOVE if self.move else options

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.abandon, self.tree, self.help)

    def accept(self) -> CopyRequest | None:
        """The request, or ``None`` for an empty line -- what Cancel says."""
        target = self.target.value.strip()
        if not target:
            return None
        _session["mode"] = self.mode.value
        _session["options"] = self.options.value
        return CopyRequest(
            sources=[entry.path_in(self._here) for entry in self._entries],
            target=target,
            mode=self.mode.value,
            options=self.options.value,
            flush=SETTINGS.system.flush_buffers,
        )

    # -- the buttons -----------------------------------------------------------

    async def on_pick_click(self, event: Event) -> bool:
        self.record_history()
        self.close(self.accept())
        return True

    async def on_tree_click(self, event: Event) -> bool:
        self.spawn(self.choose_target())
        return True

    async def on_choose_target(self, event: ChooseTarget) -> bool:
        self.spawn(self.choose_target())
        return True

    async def choose_target(self) -> None:
        await choose_target_line(self, self._here, self._hidden)


async def choose_target_line(dialog: Any, here: Path, hidden: bool) -> None:
    """``ExecTree``: *Choose Directory*, and *dialog*'s ``target`` line becomes where it points.

    The tree opens on the directory the line names, if there is one, and on
    *here* otherwise.  Shared with Create symlink, whose line means the same.
    """
    from navigator.widgets.tree.change_dir_dialog import ChangeDirDialog

    typed = Path(dialog.target.value.strip() or ".").expanduser()
    start = typed if typed.is_absolute() else here / typed
    while not start.is_dir() and start != start.parent:
        start = start.parent
    chosen = await ChangeDirDialog(start=start, hidden=hidden).execute(dialog.application)
    if chosen is not None:
        dialog.target.value = str(chosen).rstrip("/") + "/"
        dialog.target.entry.select_all()
    dialog.target.entry.focus()
