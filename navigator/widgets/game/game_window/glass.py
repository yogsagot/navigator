"""``TGameView``'s drawing and keys: the glass, framed, two columns a cell."""

from __future__ import annotations

from typing import Any

from navkit import glyphs
from navkit.events import KeyEvent
from navkit.screen import Surface
from navkit.style import Style
from navkit.widget import Widget

from navigator.tetris import SHI, VIS, Game, colour_of

#: A cell's character, ``#219``, drawn twice across.
BLOCK = "█"
#: What the glass is drawn on: DN's ``$0`` -- black, which no theme changes.
EMPTY = Style(fg=0, bg=0)


class Glass(Widget):
    """The glass, a frame round it (``ofFramed``), and the falling figure.

    Twelve cells by nineteen inside a single frame: 26 columns by 21 rows.
    Its keys are ``TGameView.HandleEvent``'s: Left and Home move left,
    Right and PgUp right, Up turns, Down and Space drop.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.can_focus = True
        self.game: Game | None = None

    async def on_key(self, event: KeyEvent) -> bool:
        game = self.game
        if game is None or event.ctrl or event.alt:
            return False
        if event.key in ("left", "home"):
            game.move(-1)
        elif event.key in ("right", "pageup"):
            game.move(1)
        elif event.key == "up":
            game.rotate()
        elif event.key in ("down", "space"):
            game.drop()
        else:
            return False
        self.invalidate()
        return True

    def render(self, surface: Surface) -> None:
        surface.draw_box(0, 0, SHI * 2 + 2, VIS + 2, self.style, charset=glyphs.charset("single", self.glyphs))
        game = self.game
        if game is None:
            return
        for row in range(VIS):
            for col in range(1, SHI + 1):
                colour = game.glass[(row, col)]
                style = Style(fg=colour, bg=0) if colour else EMPTY
                surface.draw_text(1 + (col - 1) * 2, 1 + row, BLOCK * 2 if colour else "  ", style, 2)
        if not game.stopped or game.over:
            style = Style(fg=colour_of(game.current), bg=0)
            for row, col in game.falling():
                if 0 <= row < VIS:
                    surface.draw_text(1 + (col - 1) * 2, 1 + row, BLOCK * 2, style, 2)
