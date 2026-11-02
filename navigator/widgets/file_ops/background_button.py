"""The progress boxes' *Background* button (``navigator.lib.system.background``).

A departure: DN's ``TWhileView`` had only *Stop*.  A box whose watcher can
let it go (``Manager._watch_job``'s *background*) is given ``background``,
and its row turns from *Stop* alone into *Background* and *Stop* -- the
dialog's own ``ok`` and ``no`` buttons, the first the default, so Enter
sends the box away and Esc still asks before it stops.  ``no`` answers
False, Esc None, and the watcher takes either as *Stop*.
"""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr
from navkit.reactive import bind, unbind

from navml.widgets.dialog.button import Button


class _Away:
    """What a box answers when *Background* was pressed."""

    def __repr__(self) -> str:
        return "BACKGROUND"


#: The answer of a box sent to the background.
BACKGROUND: Any = _Away()


def wire(box: Any, stop: str) -> None:
    """*box*'s ``ok`` says *stop* (DN's ``dlStop`` or *Cancel*), or
    *Background* once the box has ``background``; ``no`` is then *stop*."""
    unbind(box.ok, Button.text)
    box.ok.text = bind(lambda w: tr("~B~ackground") if box.background else stop)
    unbind(box.no, Button.text)
    box.no.text = stop


def answer(box: Any) -> Any:
    """What ``ok`` answers: :data:`BACKGROUND` while it says so, else what Esc does."""
    return BACKGROUND if box.background else None
