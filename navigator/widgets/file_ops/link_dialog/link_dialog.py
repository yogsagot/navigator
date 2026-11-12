"""The handlers behind ``link_dialog.nml``: what it opens on, and what OK means.

Seeded as the Copy dialog is -- the other panel's directory, a single file's
name after it, that directory in the history -- because a link is most often
wanted where a copy would have gone.  The kind (symbolic or hard) and
*Relative link* are remembered for the session, as Copy's mode and options
are.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from navkit.events import Event
from navkit.i18n import tr, tr_n
from navkit.reactive import effect

from navml.history import HISTORY
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.file_ops.filecopy import shown
from navigator.lib.file_ops.filelink import LinkRequest
from navigator.widgets.file_ops.copy_dialog.copy_dialog import target_for

#: The *Relative link* box as the last accepted dialog left it.
_session = {"relative": False, "hard": False}

#: The check box's bit.
RELATIVE = 0x01
#: The kind radio's items.
SYMBOLIC, HARD = 0, 1


def prompt_for(entries: Sequence[Any], hard: bool = False) -> str:
    """``Create symlink to file NAME in``, ``… Directory NAME …``, ``… 3 files …``;
    ``Create hard link …`` for *hard*."""
    if hard:
        if len(entries) != 1:
            return tr_n("Create hard ~l~ink to ~{n} file~ in", "Create hard ~l~inks to ~{n} files~ in", len(entries))
        return tr("Create hard ~l~ink to file ~{name}~ in").format(name=escape_caption(entries[0].name))
    if len(entries) != 1:
        return tr_n("Create ~s~ymlink to ~{n} file~ in", "Create ~s~ymlink to ~{n} files~ in", len(entries))
    entry = entries[0]
    name = escape_caption(entry.name)
    if entry.is_dir:
        return tr("Create ~s~ymlink to Directory ~{name}~ in").format(name=name)
    return tr("Create ~s~ymlink to file ~{name}~ in").format(name=name)


class LinkDialog(Dialog):
    """*Create link* (Shift+F5): where the links go, what kind, and what they hold."""

    def __init__(
        self,
        entries: Sequence[Any] = (),
        here: Path | None = None,
        other: Path | None = None,
        hidden: bool = True,
        relative: bool | None = None,
        hard: bool | None = None,
        can_hard: bool = True,
        **kwargs: Any,
    ) -> None:
        """*entries* are the panel's selection in *here*; *other* is the passive panel's directory.
        *relative* ticks *Relative link* or not, *hard* picks *Hard link*; None
        leaves either as the session had it.  *can_hard* false greys *Hard
        link*: the drive cannot hold one."""
        super().__init__(**kwargs)
        self._entries = list(entries)
        from navigator.lib.drives import Location

        self._here = Location.of(here if here is not None else Path.cwd())
        self._hidden = hidden
        if other is not None and Location.of(other) != self._here:
            HISTORY.add("link", str(other).rstrip("/") + "/")
        self.target.value = target_for(self._entries, self._here, other, move=False)
        self.target.entry.select_all()
        if relative is None:
            relative = _session["relative"]
        self.options.value = RELATIVE if relative else 0
        if hard is None:
            hard = _session["hard"]
        if not can_hard:
            hard = False
            self.kind.enable_mask = 1 << SYMBOLIC
        self.kind.value = HARD if hard else SYMBOLIC
        self.kind.sel = self.kind.value
        self.prompt_caption.text = prompt_for(self._entries, hard)

    def mounted(self) -> None:
        super().mounted()
        effect(self, LinkDialog._follow_kind)

    def _follow_kind(self) -> None:
        """The kind chosen: the prompt says it, and *Relative link* is greyed
        for a hard link, which holds no path."""
        hard = self.kind.value == HARD
        self.prompt_caption.text = prompt_for(self._entries, hard)
        self.options.enable_mask = 0 if hard else -1

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.abandon, self.tree, self.help)

    def accept(self) -> LinkRequest | None:
        """The request, or ``None`` for an empty line -- what Cancel says."""
        target = self.target.value.strip()
        if not target:
            return None
        relative = bool(self.options.value & RELATIVE)
        hard = self.kind.value == HARD
        _session["relative"] = relative
        _session["hard"] = hard
        return LinkRequest(
            sources=[shown(entry.path_in(self._here)) for entry in self._entries],
            target=target,
            relative=relative and not hard,
            hard=hard,
        )

    # -- the buttons -----------------------------------------------------------

    async def on_pick_click(self, event: Event) -> bool:
        self.record_history()
        self.close(self.accept())
        return True
