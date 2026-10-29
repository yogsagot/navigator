"""``ShowScores``: the Top Ten's lines, a label each, one bright."""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr

from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.label import Label

from navigator.lib.utilities import tetris
class TopTenDialog(Dialog):
    """*Tetris Top Ten* or *Pentix Top Ten*."""

    def __init__(self, highlight: int | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.message.visible = False
        # The headings, a label a column (``tetris.SCORE_COLUMNS``) as the
        # lines are, so a translation lines up over its column and a mirrored
        # screen moves both; bright as DN's one heading was.  A number's
        # heading also takes the blank before its column, right-aligned.
        self.headings: list[Label] = []
        titles = (tr("Name"), tr("Start"), tr("End"), tr("Score"))
        for column, ((x, width), title) in enumerate(zip(tetris.SCORE_COLUMNS, titles)):
            label = Label(parent=self)
            label.x, label.y, label.height = 2 + x - (column > 0), 2, 1
            label.width = width + (column > 0)
            label.align = "left" if column == 0 else "right"
            label.text = f"~{escape_caption(title)}~"
            self.headings.append(label)
        self.lines: list[list[Label]] = []
        for index, entry in enumerate(tetris.top_ten(self.game_style)):
            cells = tetris.score_cells(entry, highlight=index == highlight)
            line = []
            for column, ((x, width), text) in enumerate(zip(tetris.SCORE_COLUMNS, cells)):
                label = Label(parent=self)
                label.x, label.y, label.width, label.height = 2 + x, 4 + index, width, 1
                label.align = "left" if column == 0 else "right"
                label.text = text
                line.append(label)
            self.lines.append(line)
