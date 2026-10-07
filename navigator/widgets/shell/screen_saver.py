"""DOS Navigator's four built-in screen savers (IDLERS.PAS): ``TStarSkySaver``
(*Star flight*), ``TProjector`` (*Flash-light*), ``TClockSaver`` (*Clock*)
and ``TSSaver`` itself (*Blackness*).

Each is the whole screen, over everything, taking every key and click; the
first one ends it (``TSSaver.Execute``: ``Event.What <> evNothing``).  The
pointer moving alone does not, a report the application keeps rather than
delivers.  The animation is one timer (``Application.call_every``), each
saver keeping DN's own pace off it.

Departures: *Flash-light*'s spot shows the screen as it is now rather than
a copy taken when it began, so a clock under it goes on ticking; the
*Clock*'s colon blinks by being drawn and not, where DN set the blink
attribute.
"""

from __future__ import annotations

import asyncio
import math
import random
import time
from typing import Any

from navkit.events import KeyEvent, MouseClickEvent, PasteEvent
from navkit.reactive import bind
from navkit.screen import Surface
from navkit.style import Style
from navkit.widget import Widget

#: ``StarChars``: a star's character by how far from the centre it has come.
STAR_CHARS = " ·∙•♦☼"
#: ``StarSkyMult``: a star's position is kept in 256ths of a cell.
MULT = 256

#: ``TProjector.Draw``'s ``RR``: for each radius, rows -3 .. 4 of the spot as
#: (cells left of the centre, cells right of it), doubled across; -1 is none.
SPOTS = (
    ((2, 2), (3, 3), (4, 4), (4, 4), (4, 4), (4, 4), (3, 3), (2, 2)),
    ((-1, 0), (2, 1), (3, 2), (4, 3), (4, 3), (4, 3), (3, 2), (2, 1)),
    ((-1, 0), (-1, 0), (1, 1), (2, 2), (3, 3), (3, 3), (2, 2), (1, 1)),
    ((-1, 0), (-1, 0), (1, 0), (2, 1), (3, 2), (2, 1), (1, 0), (-1, 0)),
)

KINDS = ("star_flight", "flash_light", "clock", "blackness")


class ScreenSaver(Widget):
    """One of DN's savers over the whole screen, until a key or a click."""

    #: How often the animation steps.
    TICK = 0.05

    def __init__(self, kind: str = "blackness", *, rng: random.Random | None = None,
                 **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if kind not in KINDS:
            raise ValueError(f"{kind} is not a built-in saver")
        self.kind = kind
        self.modal = True
        self.can_focus = True
        self.dims_behind = False
        self.x = bind(lambda o: 0)
        self.y = bind(lambda o: 0)
        self.width = bind(lambda o: o.parent.width if o.parent is not None else 0)
        self.height = bind(lambda o: o.parent.height if o.parent is not None else 0)
        self._random = rng or random.Random()
        self._done: asyncio.Future[Any] | None = None
        self._stars: list[dict[str, Any] | None] = []
        self._ticks = 0
        self._center: tuple[int, int] | None = None
        self._radius = 4
        self._step = (0, 0)
        self._steps_left = 0
        self._clock: tuple[int, int] | None = None
        self._clock_step = (0, 0)
        self._clock_steps = 0

    async def execute(self, app: Any) -> None:
        """Show it until a key or a click: ``ExecView(SSaver)``."""
        self._done = asyncio.get_running_loop().create_future()
        app.overlay(self)
        self.focus()
        repeat = app.call_every(self.TICK, self._tick)
        try:
            await self._done
        finally:
            repeat.cancel()
            if self.parent is not None:
                self.parent.remove(self)

    def end(self) -> None:
        if self._done is not None and not self._done.done():
            self._done.set_result(None)

    async def on_key(self, event: KeyEvent) -> bool:
        self.end()
        return True

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        self.end()
        return True

    async def on_paste(self, event: PasteEvent) -> bool:
        self.end()
        return True

    # -- the animation ------------------------------------------------------------

    async def _tick(self) -> None:
        self._ticks += 1
        if self.width <= 0 or self.height <= 0:
            return
        if self.kind == "star_flight":
            self._move_stars()
        elif self.kind == "flash_light" and self._ticks % 3 == 0:
            self._move_spot()
        elif self.kind == "clock" and self._ticks % 5 == 0:
            self._move_clock()
        self.invalidate()

    # *Star flight*: ``TStarSkySaver``.

    def _new_star(self) -> dict[str, Any] | None:
        """``InitStar``: from near the centre, outwards at an angle -- one
        time in four, as DN's did, the rest of the slots waiting a step."""
        rnd, width, height = self._random, self.width, self.height
        if rnd.randrange(4) != 3:
            return None
        speed = width // 44 + rnd.randrange(3)
        angle = rnd.randrange(360) * math.pi / 180
        dx, dy = round(MULT * math.cos(angle)), round(MULT * math.sin(angle))
        r = (1 + rnd.randrange(2)) * (1 + 131 // max(1, width))
        return {
            "x": width // 2 * MULT + dx * speed // r, "y": height // 2 * MULT + dy * speed // r,
            "dx": dx, "dy": dy, "stage": 10, "bright": rnd.randrange(5) == 4, "char": STAR_CHARS[1],
        }

    def _move_stars(self) -> None:
        width, height = self.width, self.height
        count = max(8, 2 * width - 64)
        if len(self._stars) != count:
            self._stars = [None] * count
        # Half of them on a screen twice as wide as it is high, as DN's ``K``.
        moving = count // (2 if height * 2 <= width else 1)
        for index in range(moving):
            star = self._stars[index]
            if star is None or (star["dx"] == 0 and star["dy"] == 0):
                self._stars[index] = self._new_star()
                continue
            star["x"] += star["dx"] * star["stage"] // 12
            star["y"] += star["dy"] * star["stage"] // 12
            star["stage"] += 1
            x, y = star["x"] // MULT, star["y"] // MULT
            if not (0 <= x < width and 0 <= y < height):
                self._stars[index] = self._new_star()
                continue
            far = max(8 * abs(x - width // 2) // width + 1, 8 * abs(y - height // 2) // height + 1)
            star["char"] = STAR_CHARS[min(far, len(STAR_CHARS) - 1)]

    # *Flash-light*: ``TProjector``.

    def _move_spot(self) -> None:
        width, height, rnd = self.width, self.height, self._random
        if self._center is None:
            self._center = (width // 2, height // 2)
        cx, cy = self._center
        if self._steps_left <= 0:
            for _ in range(50):
                dx, dy = rnd.randrange(7) - 3, rnd.randrange(7) - 3
                if 0 < cx + dx < width and 0 < cy + dy < height:
                    break
            else:
                dx = dy = 0
            self._step, self._steps_left = (dx, dy), rnd.randrange(20)
        dx, dy = self._step
        cx = max(1, min(width - 1, cx + dx))
        cy = max(1, min(height - 1, cy + dy))
        self._center = (cx, cy)
        self._steps_left -= 1
        far = max(6 * abs(cx - width // 2) // width + 1, 6 * abs(cy - height // 2) // height + 1)
        self._radius = max(1, min(4, far))
        r = self._radius
        if cx <= r or cy <= r or cx >= width - r or cy >= height - r:
            self._steps_left = 0

    # *Clock*: ``TClockSaver``.

    def _move_clock(self) -> None:
        width, height, rnd = self.width, self.height, self._random
        if self._clock is None:
            self._clock = (width // 2 - 3, height // 2)
            self._clock_step, self._clock_steps = (1 - rnd.randrange(3), 1 - rnd.randrange(3)), 3 + rnd.randrange(10)
        x, y = self._clock
        dx, dy = self._clock_step
        x = max(0, min(width - 6, x + dx))
        y = max(0, min(height - 1, y + dy))
        self._clock = (x, y)
        self._clock_steps -= 1
        if self._clock_steps <= 0:
            self._clock_step = (1 - rnd.randrange(3), 1 - rnd.randrange(3))
            self._clock_steps = 3 + rnd.randrange(10)

    # -- painting -----------------------------------------------------------------

    def render(self, surface: Surface) -> None:
        width, height = self.width, self.height
        plain = self.style
        spot: list[tuple[int, int, str, Style]] = []
        if self.kind == "flash_light":
            spot = self._spot_cells(surface)
        surface.fill(0, 0, width, height, " ", plain)
        if self.kind == "star_flight":
            bright = plain.derive(fg=15)
            for star in self._stars:
                if star is None:
                    continue
                x, y = star["x"] // MULT, star["y"] // MULT
                if 0 <= x < width and 0 <= y < height:
                    surface.set_cell(x, y, star["char"], bright if star["bright"] else plain)
        elif self.kind == "flash_light":
            for x, y, char, style in spot:
                surface.set_cell(x, y, char, style)
        elif self.kind == "clock":
            if self._clock is None:
                self._move_clock()
            x, y = self._clock
            now = time.localtime()
            colon = ":" if time.time() % 1 < 0.5 else " "
            surface.draw_text(x, y, f"{now.tm_hour:02d}{colon}{now.tm_min:02d}", plain, 5)

    def _spot_cells(self, surface: Surface) -> list[tuple[int, int, str, Style]]:
        """What the spot shows of the screen under it, read before it is painted over."""
        if self._center is None:
            self._move_spot()
        cx, cy = self._center
        wide = 2 if self.height * 2 <= self.width else 1
        cells = []
        for row, (left, right) in enumerate(SPOTS[self._radius - 1]):
            y = cy + row - 3
            if left < 0 or not 0 <= y < self.height:
                continue
            for x in range(cx + 1 - left * wide, cx + 1 + right * wide):
                if 0 <= x < self.width:
                    char, style = surface.get(x, y)[:2]
                    if char:
                        cells.append((x, y, char, style))
        return cells
