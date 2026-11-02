"""What the box does: the line seeded with the link's target, *Relative
link* rewriting it in place, and OK answering the target typed."""

from __future__ import annotations

import posixpath
from typing import Any

from navkit.i18n import tr
from navkit.reactive import effect, peek
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.file_ops.filelink import absolute_target, relative_target

#: The check box's bit, as Create symlink's.
RELATIVE = 0x01


class LinkTargetDialog(Dialog):
    """The link *name*'s *target* in the line, all selected; *base* is the
    directory a relative target is read from (:func:`filelink.link_base`)."""

    def __init__(self, name: str = "", target: str = "", base: str = "/", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._base = base
        self.caption = tr("~L~ink {name} points to").format(name=escape_caption(name))
        self.line.value = target
        self.line.entry.select_all()
        self.options.value = 0 if posixpath.isabs(target) or not target else RELATIVE

    def mounted(self) -> None:
        super().mounted()
        effect(self, LinkTargetDialog._follow_relative)

    def _follow_relative(self) -> None:
        """The box ticked or not: the line, if it says otherwise, rewritten
        to reach the same place.  Typing in the line wakes nothing."""
        relative = bool(self.options.value & RELATIVE)
        text = peek(self.line, type(self.line).value)
        if not text:
            return
        new = relative_target(self._base, text) if relative else absolute_target(self._base, text)
        if new != text:
            self.line.value = new

    def accept(self) -> Any:
        """The target typed, or ``None`` for an empty line, as Cancel answers."""
        return self.line.value or None
