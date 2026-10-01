"""What every drop-down shares: the box a button drops over the line it fills.

``HistoryList``, ``Calendar`` and ``TimePicker`` are three different views --
a list, a month, a clock face -- and one kind of thing: a framed modal window
casting Turbo Vision's shadow, laid over a dialog by ``Application.overlay``,
taken down again by Esc, by a choice, or by a click past it.  They are not
dialogs (a drop-down has no buttons and answers through the button that
dropped it), so ``Dialog``'s handler never reaches them; this is where theirs
lives instead, once.
"""

from __future__ import annotations

from typing import Any

from navkit.events import ClickOutsideEvent
from navkit.reactive import reactive
from navkit.widget import Widget


class DropDown(Widget):
    """A modal box over a dialog's line, closed by Esc or a click past it.

    Mixed in after the view it is (``class HistoryList(ListViewer,
    DropDown)``), so the view's own behaviour comes first and this supplies
    only what the three have in common.
    """

    #: ``THistoryWindow`` was a window, and cast a window's shadow.
    shadow: bool = True

    #: Whether a click outside it closes it, as Esc does: the same property
    #: ``Dialog`` declares in its markup, on by default here because a
    #: drop-down holds nothing a click could lose.
    close_on_outside_click: bool = reactive(True)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.modal = True

    def close(self) -> None:
        """Come down, choosing nothing."""
        if self.parent is not None:
            self.parent.remove(self)

    async def on_click_outside(self, event: ClickOutsideEvent) -> bool:
        if not self.close_on_outside_click:
            return False
        self.close()
        return True
