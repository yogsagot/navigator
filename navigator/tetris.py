"""≡ > Game: DOS Navigator's *Navigator's game* (TETRIS.PAS), Tetris and
Pentix, the rules alone -- the window is
:class:`navigator.widgets.shell.game_window.GameWindow`.

Transcribed: the glass twelve wide and nineteen deep (``Shi``, ``Vis``) with
a wall round it; the 27 figures, the first seven Tetris's and all of them
Pentix's, each with its cell count (``ColPo``) and the size of the square it
turns in (``CRot``); the colour a figure is drawn in, ``15 - n mod 7``; a
level's delay in hundredths of a second (``LevelDelay``); and the scoring --
for a figure set down, for each line taken, for an empty glass, and less
with the preview on -- and the climb through the levels as lines are made.

The time is the caller's: :meth:`Game.tick` is told how many hundredths
have passed, and the figure falls a row whenever a level's delay has.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

#: The glass's width and depth in cells.
SHI, VIS = 12, 19

#: ``Figures``: each figure's cells as ``(row, column)``, up to five, from 1.
FIGURES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((1, 3), (2, 3), (3, 3), (3, 2)),
    ((1, 2), (2, 2), (3, 2), (3, 3)),
    ((1, 2), (2, 2), (3, 2), (4, 2)),
    ((2, 2), (2, 3), (3, 2), (3, 3)),
    ((1, 2), (2, 2), (2, 3), (3, 2)),
    ((1, 2), (2, 2), (2, 3), (3, 3)),
    ((1, 3), (2, 3), (2, 2), (3, 2)),
    ((1, 1),),
    ((1, 1), (2, 1)),
    ((1, 2), (2, 2), (3, 2)),
    ((1, 1), (2, 1), (2, 2)),
    ((1, 3), (2, 3), (3, 3), (4, 3), (5, 3)),
    ((1, 2), (2, 1), (2, 2), (2, 3), (3, 2)),
    ((2, 2), (2, 3), (3, 2), (3, 3), (3, 4)),
    ((2, 2), (2, 3), (3, 1), (3, 2), (3, 3)),
    ((1, 1), (1, 3), (2, 1), (2, 2), (2, 3)),
    ((1, 1), (2, 1), (2, 2), (3, 2), (3, 3)),
    ((1, 2), (2, 2), (3, 2), (3, 3), (4, 3)),
    ((1, 3), (2, 3), (3, 2), (3, 3), (4, 2)),
    ((1, 1), (1, 2), (2, 2), (3, 2), (3, 3)),
    ((1, 2), (1, 3), (2, 2), (3, 1), (3, 2)),
    ((1, 1), (2, 1), (2, 2), (2, 3), (3, 2)),
    ((1, 3), (2, 1), (2, 2), (2, 3), (3, 2)),
    ((1, 1), (1, 2), (1, 3), (2, 2), (3, 2)),
    ((1, 2), (2, 2), (2, 3), (3, 2), (4, 2)),
    ((1, 3), (2, 2), (2, 3), (3, 3), (4, 3)),
    ((1, 1), (2, 1), (3, 1), (3, 2), (3, 3)),
)
#: ``CRot``: the side of the square each figure turns in.
TURNS = (4, 4, 4, 4, 3, 4, 4, 1, 2, 3, 2, 5, 3, 4, 4, 3, 3, 4, 4, 3, 3, 3, 3, 3, 4, 4, 3)
#: How many figures each style draws from: Tetris's seven, or all of Pentix's.
TETRIS_FIGURES, PENTIX_FIGURES = 7, len(FIGURES)
#: ``LevelDelay``: hundredths of a second between one row's fall and the next.
DELAYS = {1: 80, 2: 60, 3: 50, 4: 30, 5: 25, 6: 20, 7: 15, 8: 10, 9: 5, 10: 4}
#: The levels' names in *Setup game*.
LEVEL_NAMES = ("Baby", "Little fella", "Big child", "It's easy", "Never mind", "I'm powerful !",
               "Insanity coming", "So what ?..", "Madness", "Sanitarium")


def colour_of(figure: int) -> int:
    """The VGA colour a figure is drawn in: ``15 - CurFig mod 7``."""
    return 15 - figure % 7


@dataclass
class Game:
    """``TGameView``'s state: the glass, the falling figure, the next one,
    and the score."""

    start_level: int = 5
    pentix: bool = False
    preview: bool = False
    rng: random.Random = field(default_factory=random.Random)

    def __post_init__(self) -> None:
        self.new_game()

    # -- the glass ------------------------------------------------------------------

    def new_game(self) -> None:
        """``NewGame``: an empty glass, a figure at the top, and the score at 0."""
        self.figures = PENTIX_FIGURES if self.pentix else TETRIS_FIGURES
        #: Each cell's colour, 0 for empty; the walls and the floor are 1,
        #: rows above the glass empty (``Glass[-2..Vis+2, -1..Shi+2]``).
        self.glass = {(row, col): int(col < 1 or col > SHI or row > VIS - 1)
                      for row in range(-2, VIS + 3) for col in range(-1, SHI + 3)}
        self.current = self.rng.randrange(self.figures)
        self.cells = list(FIGURES[self.current])
        self.x, self.y = SHI // 2 - 2, 0
        self.next = self.rng.randrange(self.figures)
        self.score = self.lines = 0
        self.level = self.start_level
        self.stopped = False
        self.over = False
        self._waited = 0

    @property
    def delay(self) -> int:
        return DELAYS[self.level]

    def valid(self, dx: int = 0, dy: int = 0, cells: list[tuple[int, int]] | None = None) -> bool:
        """``ValidMove``: whether the figure fits *dx*, *dy* from where it is."""
        return all(self.glass.get((row + self.y + dy, col + self.x + dx + 1), 1) == 0
                   for row, col in (cells if cells is not None else self.cells))

    def falling(self) -> list[tuple[int, int]]:
        """The falling figure's cells in the glass, ``(row, column)``, columns from 1."""
        return [(row + self.y, col + self.x + 1) for row, col in self.cells]

    # -- moves ----------------------------------------------------------------------

    def move(self, dx: int) -> bool:
        """Left and Right: ``MoveFig``."""
        if self.stopped or not self.valid(dx, 0):
            return False
        self.x += dx
        return True

    def rotate(self) -> bool:
        """Up: the figure turned a quarter in its square, if it fits there."""
        if self.stopped:
            return False
        turn = TURNS[self.current]
        turned = [(turn + 1 - col, row) for row, col in self.cells]
        if not self.valid(0, 0, turned):
            return False
        self.cells = turned
        return True

    def drop(self) -> None:
        """Down and Space: straight down as far as it goes; it sets with the
        next fall, as DN's did."""
        while not self.stopped and self.valid(0, 1):
            self.y += 1
        self._waited = 0

    def tick(self, hundredths: int) -> bool:
        """``Update``: *hundredths* more passed; a row's fall once the
        level's delay has.  Whether anything changed."""
        if self.stopped:
            return False
        self._waited += hundredths
        if self._waited <= self.delay:
            return False
        self._waited = 0
        self.fall()
        return True

    def fall(self) -> None:
        """``MoveDown``: a row down, or set down where it is -- lines taken,
        the score counted, the next figure in, and the game over if it does
        not fit."""
        if self.stopped:
            return
        if self.valid(0, 1):
            self.y += 1
            return
        colour = colour_of(self.current)
        for cell in self.falling():
            self.glass[cell] = colour
        weight = 10 - 3 * int(self.preview)
        self.score += ((VIS - self.y) * 2 + self.level * 6) * weight // 10
        taken = empty = 0
        for row in range(VIS):
            full = all(self.glass[(row, col)] != 0 for col in range(1, SHI + 1))
            empty += all(self.glass[(row, col)] == 0 for col in range(1, SHI + 1))
            if full:
                for above in range(row, 0, -1):
                    for col in range(1, SHI + 1):
                        self.glass[(above, col)] = self.glass[(above - 1, col)]
                        self.glass[(above - 1, col)] = 0
                self.score += (taken + VIS - row) * 30
                self.lines += 1
                taken += 1
        if empty == VIS:
            self.score += self.level * 300 * weight // 10
        self.current = self.next
        self.cells = list(FIGURES[self.current])
        self.next = self.rng.randrange(self.figures)
        self.x, self.y = SHI // 2 - 2, -self.cells[0][0]
        threshold = 90 - (9 - self.start_level) * 10
        if self.lines > threshold:
            self.level = max(self.start_level, min(10, 1 + (self.lines - threshold) // 20 + self.start_level))
        if not self.valid(0, 0):
            for cell in self.falling():
                self.glass[cell] = colour_of(self.current)
            self.stopped = self.over = True

    # -- the buttons ------------------------------------------------------------------

    def pause(self) -> None:
        """F3, *Pause*: ``cmStop`` -- not once the game is over."""
        if not self.over:
            self.stopped = not self.stopped

    def level_up(self) -> None:
        """Gray +: ``cmTetrisIncLevel``."""
        self.level = min(10, self.level + 1)


# -- the Top Ten ------------------------------------------------------------------------

#: What a name is, left alone: ``sAnonymous``.
ANONYMOUS = "Anonymous"


def top_ten(style: str) -> list:
    """*style*'s Top Ten, best first (:class:`~navigator.models.tetris_score.TetrisScore`)."""
    from navigator.models.tetris_score import TetrisScore

    return TetrisScore.where(style=style).order("-score", "seq").limit(10).all()


def place_for(style: str, score: int) -> int | None:
    """``CheckHiScores``: the place, from 0, *score* takes in *style*'s Top
    Ten -- above the first it beats, or in an empty one -- or None."""
    table = top_ten(style)
    for index, entry in enumerate(table):
        if entry.score < score:
            return index
    return len(table) if len(table) < 10 and score > 0 else None


def enter(style: str, name: str, start: int, end: int, score: int) -> None:
    """*name*'s game into *style*'s Top Ten, and the eleventh out."""
    from navkit.database import DATABASE

    from navigator.models.tetris_score import TetrisScore

    with DATABASE.transaction():
        newest = TetrisScore.query().order("-seq").first()
        TetrisScore.create(style=style, name=name[:30] or ANONYMOUS, start=start, end=end, score=score,
                           seq=1 if newest is None else newest.seq + 1)
        for entry in TetrisScore.where(style=style).order("-score", "seq").offset(10).all():
            entry.delete()


def score_line(entry, highlight: bool = False) -> str:
    """One Top Ten line, as ``ShowScores`` wrote it: the name filled with dots
    to 30, then the levels and the score right-aligned on dots."""
    name = f"~{entry.name}~" if highlight else entry.name
    dots = "." * max(0, 30 - len(entry.name))
    return f"{name}{dots} {str(entry.start).rjust(5, '.')} {str(entry.end).rjust(5, '.')} {str(entry.score).rjust(10, '.')}"
