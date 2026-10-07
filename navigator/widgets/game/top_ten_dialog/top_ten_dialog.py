"""``ShowScores``: the Top Ten's lines, a label each, one bright."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.label import Label

from navigator import tetris


class TopTenDialog(Dialog):
    """*Tetris Top Ten* or *Pentix Top Ten*."""

    def __init__(self, highlight: int | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.message.visible = False
        self.lines: list[Label] = []
        for index, entry in enumerate(tetris.top_ten(self.game_style)):
            line = Label(parent=self)
            line.x, line.y, line.width, line.height = 2, 4 + index, 55, 1
            line.text = tetris.score_line(entry, highlight=index == highlight)
            self.lines.append(line)
