"""``TGameInfo``: the *Info* box, *Next*, and the *Best* of the Top Ten."""

from __future__ import annotations

from typing import Any

from navkit.screen import Surface
from navkit.style import Style
from navkit.widget import Widget

from navigator.tetris import FIGURES, Game, colour_of

#: A preview cell, as the glass draws one.
BLOCK = "█"


class GameInfo(Widget):
    """Score, lines and level; the next figure under *Next*; the best entry
    of the Top Ten under *Best*.  23 columns by 15 rows."""

    parts = ("info", "info-bright", "best", "best-bright")

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.game: Game | None = None
        #: The best entry: ``(name, score)``, kept by the window.
        self.best: tuple[str, int] = ("Anonymous", 0)

    def _line(self, surface: Surface, y: int, text: str, part: str, edges: str = "││", fill: str = " ") -> None:
        """One row of a box: *edges* at its ends, *text* in it with ``~``
        around what is bright, centred when *fill* is a rule."""
        width = self.width
        plain, bright = self.part_style(part), self.part_style(f"{part}-bright")
        surface.draw_text(0, y, fill * width, plain, width)
        shown = text.replace("~", "")
        x = (width - len(shown)) // 2 if fill != " " else 1
        on = False
        for piece in text.split("~"):
            if piece:
                surface.draw_text(x, y, piece, bright if on else plain, max(0, width - 1 - x))
                x += len(piece)
            on = not on
        surface.draw_text(0, y, edges[0], plain, 1)
        surface.draw_text(width - 1, y, edges[1], plain, 1)

    def render(self, surface: Surface) -> None:
        game = self.game
        if game is None:
            return
        self._line(surface, 0, " ~Info~ ", "info", "┌┐", "─")
        self._line(surface, 1, f"Score: ~{game.score}~", "info")
        self._line(surface, 2, f"Lines: ~{game.lines}~", "info")
        self._line(surface, 3, f"Level: ~{game.level}~", "info")
        self._line(surface, 4, " ~Next~ ", "info", "├┤", "─")
        for y in range(5, 10):
            self._line(surface, y, "", "info")
            surface.fill(1, y, self.width - 2, 1, " ", Style(fg=7, bg=0))
        if not game.stopped and game.preview:
            style = Style(fg=colour_of(game.next), bg=0)
            for row, col in FIGURES[game.next]:
                surface.draw_text(col * 2 + 3, 4 + row, BLOCK * 2, style, 2)
        self._line(surface, 10, "", "info", "└┘", "─")
        name, score = self.best
        self._line(surface, 11, " ~Best~ ", "best", "┌┐", "─")
        self._line(surface, 12, f"~Name:~ {name}", "best")
        self._line(surface, 13, f"~Score:~ {score}", "best")
        self._line(surface, 14, "", "best", "└┘", "─")
