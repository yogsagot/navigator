"""navml's ``GroupBox``: Turbo Vision's ``ofFramed`` view with a label on its frame."""

from __future__ import annotations

from navkit.screen import ScreenBuffer

from navml.widgets.dialog.group_box import GroupBox
from navml.widgets.dialog.static_text import StaticText


def rows(buffer: ScreenBuffer) -> list[str]:
    return ["".join(buffer.get(x, y)[0] or " " for x in range(buffer.width)) for y in range(buffer.height)]


def test_a_single_frame_with_its_caption_two_cells_in_and_its_children_inside():
    box = GroupBox(title="~M~emory")
    box.x, box.y, box.width, box.height = 0, 0, 20, 4
    text = StaticText(parent=box, text="Total : 1K")
    text.x, text.y, text.width, text.height = 2, 1, 16, 2
    buffer = ScreenBuffer(20, 4)
    box.render_tree(buffer)
    assert rows(buffer) == [
        "┌─ Memory ─────────┐",
        "│ Total : 1K       │",
        "│                  │",
        "└──────────────────┘",
    ]


def test_no_caption_is_a_plain_frame_and_a_long_one_is_cut_inside_the_corners():
    box = GroupBox()
    box.width, box.height = 8, 3
    buffer = ScreenBuffer(8, 3)
    box.render_tree(buffer)
    assert rows(buffer)[0] == "┌──────┐"
    box.title = "A very long caption"
    buffer = ScreenBuffer(8, 3)
    box.render_tree(buffer)
    assert rows(buffer)[0] == "┌─ A v─┐"
