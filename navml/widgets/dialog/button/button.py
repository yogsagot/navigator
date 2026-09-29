"""The handlers behind ``button.nml``.

This file never names the generated class.  ``class Button(Control)`` is what a
Python-only component would say too, which is what lets a component gain or
lose its markup half without this file changing -- see *Why the generated base
is hidden* in ``navml/DESIGN.md``.  The base repeats the one the markup
declares, and :mod:`navml._merge` refuses the pair if the two disagree.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from navkit.events import Event, KeyEvent, KeyReleaseEvent, MouseClickEvent
from navkit.glyphs import GLYPHS_UNICODE
from navkit.reactive import computed, effect
from navkit.screen import Surface
from navkit.style import Style
from navkit.widget import Widget

from navml.widgets.dialog.control import Control

if TYPE_CHECKING:
    from navkit.application import Repeat

#: The two markers on the button Enter would press, CP437 16 and 17 in the
#: original, and what stands in for them where only ASCII can be shown.
MARKERS = {"dos": "►◄", "ascii": "><"}

#: How long a Space shows the button pressed on a terminal that will not say
#: when the key was let go.  Long enough to be seen, short enough that the
#: click does not feel late.
FLASH = 0.1


@dataclass(frozen=True, slots=True)
class ClickEvent(Event):
    """The button was pressed, by whichever route.

    Declared here, beside the widget that emits it, rather than in navkit:
    navkit knows about terminal input and nothing a widget *means*.  navkit
    derives the handler name from the class -- ``ClickEvent`` -> ``on_click``
    -- so nothing is registered anywhere, and a document that uses a Button
    writes ``on_click:`` without importing this class at all.

    Carrying no fields is what lets two routes raise the same event: a mouse
    press and a keypress are the same click to whoever is listening, and the
    button is what knows they are.
    """


class Button(Control):
    """A pressable box.

    The worked example of a component with an event of its own: several input
    routes, one thing they all mean.  Space and Enter arrive as keys, a left
    press arrives by position, and ``Alt+O`` arrives from a dialog that went
    looking for the letter -- and none of those is what a listener cares
    about, so all of them go through :meth:`press`, which emits one
    :class:`ClickEvent`.  A document using a Button writes ``on_click:`` and
    never learns which route fired.

    **It is drawn as DOS Navigator's ``TButton.DrawState`` draws it.**  The
    face is plain colour, with no brackets.  The button Enter would press --
    the focused one, or else the dialog's default (:attr:`am_default`) --
    carries ``►`` in its first column and ``◄`` in its last.  The shadow is
    two rows of half blocks in the shadow colour: ``▄`` then ``█`` down the
    column to the right, and ``▀`` under the face, one cell in.  So the
    widget is two rows tall and one column wider than its face, and putting
    those cells inside its own rectangle is what lets one be placed anywhere
    without its owner knowing.

    **And the click comes on the release.**  A mouse press puts the button
    :attr:`down` -- the face moves one cell right into its shadow's column,
    and the shadow goes -- and while the button is held it pops up and goes
    down again as the pointer leaves and comes back.  Only letting go over it
    clicks.  Space does the same where the terminal reports a release
    (:attr:`KeyEvent.releases`) and flashes for :data:`FLASH` where it does
    not.  Enter and the ``Alt`` shortcut press at once, as they did in the
    original, which drew the pressed state for the mouse alone.
    """

    #: What this widget emits, read through :func:`navkit.events.emitted`.
    #: The declaration is the public surface: navml's generator checks an
    #: ``on_click:`` line against it, and a reader sees it without reading
    #: :meth:`press`.
    emits = (ClickEvent,)

    #: The drop shadow, ``[46]`` in the original: black half blocks on the
    #: dialog's own background.  A part rather than a colour on the widget
    #: because it is painted *with* the button and is not the button.
    parts = ("shadow",)

    def __init__(self, text: str = "", **kwargs: Any) -> None:
        # The markup half's tree is built by this call, so every id is live
        # from the next line on.
        super().__init__(**kwargs)
        self.text = text
        #: The timer ending a Space's flash, while one is running.
        self._flash: Repeat | None = None

    @computed
    def am_default(self) -> bool:
        """Whether this is the button Enter presses, DOS Navigator's ``AmDefault``.

        The ``default`` button is, unless another button in the same dialog
        holds the keyboard -- that one takes the role while it has it, which
        is what ``TButton`` did with ``cmGrabDefault`` and
        ``cmReleaseDefault``, and what the stylesheet's ``:am_default`` reads.
        """
        if not self.default:
            return False
        app = self.application
        focused = app.focused if app is not None else None
        if focused is None or focused is self or not isinstance(focused, Button):
            return True
        return _dialog_of(focused) is not _dialog_of(self)

    @computed
    def marked(self) -> bool:
        """Whether ``►`` and ``◄`` are drawn: the button Enter would press."""
        return not self.inert and (self.focused or self.am_default)

    async def press(self) -> bool:
        """Emit the click.  False if disabled, or if nothing claimed it."""
        if self.inert:
            return False
        return await self.emit(ClickEvent())

    async def activate(self, letter: str = "") -> bool:
        """What ``Alt+O`` does: take the keyboard, then press.

        Both, and in that order, because the original does both -- a shortcut
        is a faster route to the same button rather than a way of pressing one
        without visiting it.
        """
        self.focus()
        return await self.press()

    async def on_key(self, event: KeyEvent) -> bool:
        if event.name == "enter":
            return await self.press()
        if not _is_space(event):
            return False
        if self.down or self.inert:
            # A key repeat while the first press is still held.
            return True
        if event.releases:
            self.down = True
            return True
        app = self.application
        if app is None:
            # No clock to flash by, so nothing to see either: press at once.
            await self.press()
            return True
        self.down = True
        self._flash = app.call_every(FLASH, self._end_flash)
        return True

    async def on_key_release(self, event: KeyReleaseEvent) -> bool:
        if not (_is_space(event) and self.down) or self._flash is not None:
            return False
        return await self._release()

    async def _end_flash(self) -> None:
        self._stop_flash()
        await self._release()

    def _stop_flash(self) -> None:
        if self._flash is not None:
            self._flash.cancel()
            self._flash = None

    async def _release(self) -> bool:
        """Come back up, and click -- the end of every route that went down."""
        self.down = False
        return await self.press()

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        app = self.application
        if app is not None and app.mouse_capture is self:
            # Tracking a held button.  Over the face or the column it moves
            # into, it is down; anywhere else it pops up and waits.
            over = 0 <= event.x < self.width and 0 <= event.y < self.height - 1
            if event.action == "release":
                if self.down and over:
                    return await self._release()
                self.down = False
                return True
            self.down = over
            return True
        # Up to `Control' first, which takes the keyboard and claims nothing;
        # a press on a button means both things and this is the order they
        # happen in.
        await super().on_mouse_click(event)
        width, height = self.face
        if (
            event.action == "press"
            and event.button == "left"
            and not self.inert
            and event.x < width
            and event.y < height
        ):
            self._stop_flash()
            self.down = True
            if app is not None:
                app.capture_mouse(self)
            return True
        return False

    def mounted(self) -> None:
        super().mounted()
        effect(self, Button._pop_up_on_blur)

    def _pop_up_on_blur(self) -> None:
        """A Space held down, and the keyboard gone elsewhere: up, no click.

        The release would reach whatever has the focus now, so this button
        would otherwise stay pressed for good.  A mouse press is left alone --
        it holds the capture, and its own release ends it.
        """
        if self.down and not self.focused:
            app = self.application
            if app is None or app.mouse_capture is not self:
                self._stop_flash()
                self.down = False

    def unmounting(self) -> None:
        # Gone mid-press: no click, and no timer left to deliver one.
        self._stop_flash()
        self.down = False

    @property
    def face(self) -> tuple[int, int]:
        """The width and height of the button itself, shadow excluded."""
        return max(0, self.width - 1), max(0, self.height - 1)

    def render(self, surface: Surface) -> None:
        width, height = self.face
        if width < 1 or height < 1:
            return
        style = self.style
        shadow: Style = self.part_style("shadow")
        unicode = self.glyphs >= GLYPHS_UNICODE
        left = 1 if self.down else 0
        surface.fill(left, 0, width, height, " ", style)
        if self.marked and width >= 2:
            first, last = MARKERS["dos" if unicode else "ascii"]
            surface.draw_text(left, 0, first, style)
            surface.draw_text(left + width - 1, 0, last, style)
        if self.down:
            # The face has moved into its shadow: what it left is blank.
            surface.fill(0, 0, 1, height, " ", shadow)
            surface.fill(0, height, width + 1, 1, " ", shadow)
            return
        if not unicode:
            # No half blocks to draw with, so whole cells in the shadow's
            # own colour, one step coarser than the original.
            solid = Style(bg=shadow.fg)
            surface.fill(width, 0, 1, height, " ", solid)
            surface.fill(0, height, 1, 1, " ", shadow)
            surface.fill(1, height, width, 1, " ", solid)
            return
        surface.draw_text(width, 0, "▄", shadow)
        surface.fill(width, 1, 1, height - 1, "█", shadow)
        surface.draw_text(0, height, " ", shadow)
        surface.fill(1, height, width, 1, "▀", shadow)


def _is_space(event: KeyEvent | KeyReleaseEvent) -> bool:
    """A bare Space.  The key is ``" "``; ``"space"`` is how Ctrl+Space comes."""
    return event.key in (" ", "space") and not (event.ctrl or event.alt or event.shift)


def _dialog_of(widget: Widget) -> Widget | None:
    """The nearest modal ancestor, the group ``cmGrabDefault`` was broadcast to."""
    node: Widget | None = widget
    while node is not None and not node.modal:
        if node.parent is None:
            return node
        node = node.parent
    return node
