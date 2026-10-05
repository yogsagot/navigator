"""A cell that turns while work goes on -- a component written in Python alone.

For work whose end cannot be told, or not yet: a box that says *Reading file*
and shows nothing moving looks the same as one whose program has hung.  DOS
Navigator's ``WriteMsg`` did look like that, and on a 4.77 MHz machine it was
usually honest; the spinner is an addition, and a widget so that whatever
paints it does not have to keep a clock of its own.

It runs as :class:`~navml.widgets.timer.Timer` does, on navkit's
:meth:`~navkit.application.Application.call_every`, and only while mounted.
"""

from __future__ import annotations

from typing import Any

from navkit.glyphs import DEFAULT_SPINNER, SPINNERS, spinner
from navkit.reactive import effect, reactive, untracked
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.widget import Widget


class Spinner(Widget):
    """One cell, a frame of :attr:`frames` that moves on every :attr:`interval` ms."""

    #: Which frame is showing, counting up for ever; the cell shows it modulo
    #: the set's length.
    frame: int = reactive(0)

    #: Milliseconds between frames.  Zero or less stands it still.
    interval: int = reactive(100)

    #: Which characters it turns through.  Not ``chars``, which a gauge and a
    #: scroll bar declare with sets of their own names.
    frames = StyleProperty(DEFAULT_SPINNER, values=tuple(SPINNERS))

    def __init__(self, **kwargs: Any) -> None:
        # Before the base constructor, which may mount and so arm the clock.
        self._repeat: Any = None
        super().__init__(**kwargs)

    def mounted(self) -> None:
        super().mounted()
        effect(self, Spinner._arm)

    def unmounting(self) -> None:
        self._stop()
        super().unmounting()

    def _arm(self) -> None:
        interval = self.interval
        self._stop()
        with untracked():
            app = self.application
        if interval > 0 and app is not None:
            self._repeat = app.call_every(interval / 1000, self._tick)

    def _stop(self) -> None:
        if self._repeat is not None:
            self._repeat.cancel()
            self._repeat = None

    async def _tick(self) -> None:
        self.frame += 1

    def render(self, surface: Surface) -> None:
        if self.width < 1 or self.height < 1:
            return
        cells = spinner(self.frames, self.glyphs)
        surface.fill(0, 0, self.width, self.height, cells[self.frame % len(cells)], self.style)
