"""Children in cells, a fixed number of columns wide, filled row by row.

Every column is as wide as every other and every row as tall, give or take
the one cell the trailing-remainder rule in
:func:`~navml.widgets.layout.layout.distribute` hands out, and there are as many rows
as the visible children need.  **There are no spans and no per-track sizes
yet**: a grid of equal cells is what a table of buttons or of check boxes
wants, and a hint language for tracks is a decision better taken against the
first dialog that needs one.  Hints on the children are ignored.
"""

from __future__ import annotations

from navkit.reactive import reactive
from navkit.widget import Widget

from navml.widgets.layout.layout import Layout, distribute
from navml.widgets.layout.layout.layout import Rect


class GridLayout(Layout):
    """Children in equal cells, row-major."""

    #: How many cells to a row.
    columns: int = reactive(1)

    #: Empty cells between two columns, and between two rows.
    spacing: int = reactive(0)

    def plan(self, children: list[Widget]) -> dict[Widget, Rect]:
        columns = max(1, self.columns)
        rows = -(-len(children) // columns)
        spacing = max(0, self.spacing)
        widths = distribute(self.width, [0] * columns, [1] * columns, spacing)
        heights = distribute(self.height, [0] * rows, [1] * rows, spacing)
        lefts = _starts(widths, spacing)
        tops = _starts(heights, spacing)
        plan = {}
        for index, child in enumerate(children):
            row, column = divmod(index, columns)
            plan[child] = (lefts[column], tops[row], widths[column], heights[row])
        return plan


def _starts(sizes: list[int], spacing: int) -> list[int]:
    starts, position = [], 0
    for size in sizes:
        starts.append(position)
        position += size + spacing
    return starts
