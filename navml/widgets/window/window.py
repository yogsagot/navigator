"""The painting and the key routing behind ``window.nml``.

Two things live here that a dialog would otherwise each have to repeat.

**The frame**, which is a ``draw_box`` and a centred title, and which takes a
double border by default because that is what DOS Navigator draws and what
``[33]`` is a colour for.  A window re-declares ``border`` with the *same*
vocabulary and a different default, which navkit permits explicitly -- the
registry holds the type and the words, not the default.

**The shortcut walk.**  ``dispatch_key`` walks the focus path *upward*, from
whatever holds the keyboard to the widget the walk was started on -- so a
window is offered every key its own controls did not claim, and it is the
right place to go looking for whichever control a ``~A~`` names.  That is the
downward half of the same question, and it needs no broadcast: Turbo Vision
broadcasts because it has no focus path to walk, and navkit has one.
"""

from __future__ import annotations

from typing import Iterator

from navkit.events import KeyEvent, MouseClickEvent
from navkit.glyphs import BOX_CHARSETS
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.widget import Widget

from navml.widgets.control import Control

#: What the corner icon is drawn as.  One cell of content between brackets,
#: the way Turbo Vision draws it, so it survives an ASCII terminal unchanged.
CLOSE_ICON = "[■]"
ASCII_CLOSE_ICON = "[x]"


class Window(Widget):
    """A framed box with a title."""

    #: A window's frame is double in the original; everything else navkit
    #: draws is single.  Re-declared rather than set in a sheet so that the
    #: default travels with the widget, which is what a sheet then overrides.
    border = StyleProperty("double", values=tuple(BOX_CHARSETS))

    #: The title across the top edge, and the close icon beside it.
    parts = ("title", "icon")

    def controls(self) -> Iterator[Control]:
        """Every :class:`Control` under this window, in tree order."""

        def walk(widget: Widget) -> Iterator[Control]:
            for child in widget.children:
                if not child.visible:
                    continue
                if isinstance(child, Control):
                    yield child
                yield from walk(child)

        return walk(self)

    async def activate_shortcut(self, letter: str) -> bool:
        """Give *letter* to the first control that answers to it."""
        for control in self.controls():
            if control.shortcut_match(letter):
                return await control.activate(letter)
        return False

    async def on_key(self, event: KeyEvent) -> bool:
        # Alt and one letter, and nothing else.  Turbo Vision also accepts a
        # bare letter when no input line holds the focus, and reproducing that
        # would mean asking the focused control whether it eats printable
        # keys -- an implicit coupling between every control and every
        # container.  `KeyEvent.is_printable' is already false when alt is
        # set, so an InputLine never has to think about this.
        if event.alt and not event.ctrl and len(event.key) == 1 and event.key.isalpha():
            return await self.activate_shortcut(event.key)
        return False

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if not self.closable or event.action != "press" or event.button != "left":
            return False
        if event.y == 0 and self.width - 5 <= event.x < self.width - 2:
            self.close()
            return True
        return False

    def close(self) -> None:
        """Take this window out of the tree.  A dialog overrides it to answer."""
        if self.parent is not None:
            self.parent.remove(self)

    def render(self, surface: Surface) -> None:
        if self.width < 2 or self.height < 2:
            return
        surface.draw_box(
            0, 0, self.width, self.height, self.style,
            charset=self.box_charset(), fill=" ",
        )
        if self.title:
            label = f" {self.title} "[: max(0, self.width - 2)]
            surface.draw_text(
                max(1, (self.width - len(label)) // 2), 0, label,
                self.part_style("title"),
            )
        if self.closable and self.width >= 8:
            icon = CLOSE_ICON if self.glyphs > 1 else ASCII_CLOSE_ICON
            surface.draw_text(self.width - 5, 0, icon, self.part_style("icon"))
