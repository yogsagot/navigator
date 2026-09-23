"""The handlers behind ``label.nml``.

A label is the one control that never takes the keyboard and still wants a
shortcut: pressing its letter focuses something *else*.  That is what
``activate()`` is virtual for, and it is why `accepts_focus' is a class fact
rather than an instance one -- no label ever changes its mind about it.

``selected`` is a computed rather than a flag anybody sets, so
``Label:selected`` in a sheet lights the caption whenever its control holds
the focus, with nothing keeping the two in step by hand.
"""

from __future__ import annotations

from navkit.reactive import computed
from navkit.screen import Surface
from navkit.widget import Widget

from navml.widgets.control import Control, parse_shortcut
from navml.widgets.static_text import draw_caption


class Label(Control):
    """A caption that belongs to the control beside it."""

    #: The marked letter.  ``[40] Label shortcut`` in the original.
    parts = ("shortcut",)

    #: A caption is never in the tab order: Turbo Vision's ``TLabel`` is not
    #: selectable either, and a Tab stop on a piece of text that cannot do
    #: anything is a stop the user has to press past.
    accepts_focus = False

    @computed
    def selected(self) -> bool:
        """Whether the control this caption names holds the keyboard.

        A computed, so ``Label:selected`` is a stylesheet state for free --
        the same trick ``Widget.focused`` plays, and for the same reason.
        """
        link = self.link
        return isinstance(link, Widget) and link.focused

    async def activate(self, letter: str = "") -> bool:
        """Do to the linked control what its own shortcut would.

        Delegating rather than merely focusing, because ``~N~ame`` beside a
        field has to mean the same thing as ``~N~`` on the field itself --
        which for an ``InputLine`` includes selecting what is already there,
        so that typing replaces it.  A link that is not a ``Control`` is
        simply focused.
        """
        link = self.link
        if isinstance(link, Control):
            return await link.activate(letter)
        return link.focus() if isinstance(link, Widget) else False

    async def on_mouse_click(self, event) -> bool:
        """A click on a caption means its control, which is what a user means."""
        if event.action == "press" and event.button == "left" and not self.disabled:
            return await self.activate()
        return False

    def render(self, surface: Surface) -> None:
        caption, _, _ = parse_shortcut(self.text)
        if self.align == "right":
            x = max(0, self.width - len(caption))
        elif self.align == "center":
            x = max(0, (self.width - len(caption)) // 2)
        else:
            x = 0
        draw_caption(
            surface, x, 0, self.text, self.style,
            self.part_style("shortcut"), self.width - x,
        )
