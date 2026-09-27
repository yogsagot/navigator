"""The layout containers: the hints a child gives, and the rectangles it gets."""

from __future__ import annotations

import pytest

from navkit import stylesheet
from navkit.reactive import bind, reactive
from navkit.widget import Widget

from conftest import mounted, settle
from navml.widgets import (
    DockLayout,
    GridLayout,
    HorizontalLayout,
    StackLayout,
    VerticalLayout,
)
from navml.widgets.layout.layout import distribute


def rect(widget: Widget) -> tuple[int, int, int, int]:
    return widget.x, widget.y, widget.width, widget.height


class Root(Widget):
    """A parent that does not cascade, the way a markup parent does not."""

    across: int = reactive(80)
    down: int = reactive(24)

    def layout(self, width: int, height: int) -> None:
        self.width, self.height = width, height


def hosted(layout: Widget) -> Root:
    """*layout* under a non-cascading root, sized by bindings to it."""
    root = Root()
    root.add(layout)
    layout.width = bind(lambda o: o.parent.across)
    layout.height = bind(lambda o: o.parent.down)
    mounted(root)
    settle()
    return root


# -- distribute --------------------------------------------------------------


def test_the_remainder_goes_to_the_trailing_growers():
    """``W // 2`` and ``W - W // 2``: the panels' own arithmetic."""
    assert distribute(80, [0, 0], [1, 1]) == [40, 40]
    assert distribute(81, [0, 0], [1, 1]) == [40, 41]
    assert distribute(10, [0, 0, 0], [1, 1, 1]) == [3, 3, 4]


def test_bases_are_granted_first_and_clamped_in_order():
    assert distribute(20, [12, 0], [0, 1]) == [12, 8]
    assert distribute(10, [6, 6, 6], [0, 0, 0]) == [6, 4, 0]
    assert distribute(20, [4, 0, 0], [0, 1, 3], spacing=2) == [4, 3, 9]


# -- linear ------------------------------------------------------------------


def test_children_that_say_nothing_share_equally():
    row = HorizontalLayout()
    left, right = Widget(parent=row), Widget(parent=row)
    root = hosted(row)
    assert rect(left) == (0, 0, 40, 24)
    assert rect(right) == (40, 0, 40, 24)
    root.across = 81
    settle()
    assert rect(left) == (0, 0, 40, 24)
    assert rect(right) == (40, 0, 41, 24)


def test_a_fixed_child_beside_a_growing_one():
    row = HorizontalLayout()
    label = Widget(parent=row, inline_style="basis: 12; grow: 0")
    entry = Widget(parent=row)
    hosted(row)
    assert rect(label) == (0, 0, 12, 24)
    assert rect(entry) == (12, 0, 68, 24)


def test_a_vertical_layout_runs_down():
    column = VerticalLayout(spacing=1)
    top = Widget(parent=column, inline_style="basis: 1; grow: 0")
    rest = Widget(parent=column)
    hosted(column)
    assert rect(top) == (0, 0, 80, 1)
    assert rect(rest) == (0, 2, 80, 22)


@pytest.mark.parametrize("justify, start", [("start", 0), ("center", 21), ("end", 43)])
def test_justify_places_children_that_do_not_fill(justify, start):
    """Three 11-column buttons, two apart: 37 of 80, as the dialog lays them."""
    row = HorizontalLayout(spacing=2, justify=justify)
    buttons = [Widget(parent=row, inline_style="basis: 11; grow: 0") for _ in range(3)]
    hosted(row)
    assert [b.x for b in buttons] == [start, start + 13, start + 26]
    assert all(b.width == 11 for b in buttons)


def test_an_unknown_justify_is_refused():
    row = HorizontalLayout(justify="middle")
    Widget(parent=row)
    with pytest.raises(ValueError, match="justify"):
        hosted(row)


def test_a_hidden_child_gives_up_its_slot_and_gets_it_back():
    row = HorizontalLayout(spacing=2, justify="center")
    a, b, c = (Widget(parent=row, inline_style="basis: 11; grow: 0") for _ in range(3))
    hosted(row)
    b.visible = False
    settle()
    assert (a.x, c.x) == ((80 - 24) // 2, (80 - 24) // 2 + 13)
    b.visible = True
    settle()
    assert (a.x, b.x, c.x) == (21, 34, 47)


def test_a_restyled_child_rearranges_its_siblings():
    row = HorizontalLayout()
    label, entry = Widget(parent=row), Widget(parent=row)
    hosted(row)
    label.merge_style("basis: 20; grow: 0")
    settle()
    assert rect(entry) == (20, 0, 60, 24)


def test_hints_come_from_a_sheet_rule_too():
    sheet = stylesheet.parse(".fixed { basis: 5; grow: 0 }")
    row = HorizontalLayout()
    row.stylesheet = sheet
    fixed = Widget(parent=row, classes=frozenset({"fixed"}))
    rest = Widget(parent=row)
    hosted(row)
    assert rect(fixed) == (0, 0, 5, 24)
    assert rect(rest) == (5, 0, 75, 24)


def test_a_bound_side_is_stepped_around():
    row = HorizontalLayout()
    short = Widget(parent=row)
    short.height = bind(lambda o: 2)
    Widget(parent=row)
    hosted(row)
    assert rect(short) == (0, 0, 40, 2)


def test_adding_and_removing_while_mounted_rearranges():
    row = HorizontalLayout()
    first = Widget(parent=row)
    hosted(row)
    assert first.width == 80
    second = Widget()
    row.add(second)
    assert (first.width, second.x, second.width) == (40, 40, 40)
    row.remove(second)
    assert first.width == 80


def test_a_cascading_parent_arranges_through_layout():
    """A hand-written parent calls ``layout()``, and that arranges too."""
    root = Widget()
    row = HorizontalLayout(parent=root)
    left, right = Widget(parent=row), Widget(parent=row)
    root.layout(30, 3)
    assert (rect(left), rect(right)) == ((0, 0, 15, 3), (15, 0, 15, 3))


def test_layouts_nest():
    column = VerticalLayout()
    bar = Widget(parent=column, inline_style="basis: 1; grow: 0")
    row = HorizontalLayout(parent=column)
    left, right = Widget(parent=row), Widget(parent=row)
    root = hosted(column)
    assert rect(bar) == (0, 0, 80, 1)
    assert (rect(left), rect(right)) == ((0, 0, 40, 23), (40, 0, 40, 23))
    root.down = 10
    settle()
    assert rect(right) == (40, 0, 40, 9)


# -- grid --------------------------------------------------------------------


def test_a_grid_fills_row_by_row():
    grid = GridLayout(columns=3, spacing=1)
    cells = [Widget(parent=grid) for _ in range(5)]
    root = hosted(grid)
    root.across, root.down = 32, 9
    settle()
    # 32 - 2 = 30 across three columns, 9 - 1 = 8 down two rows.
    assert [rect(c) for c in cells] == [
        (0, 0, 10, 4), (11, 0, 10, 4), (22, 0, 10, 4),
        (0, 5, 10, 4), (11, 5, 10, 4),
    ]


# -- dock --------------------------------------------------------------------


def test_edges_carve_in_order_and_fills_share_the_rest():
    """Navigator's own screen: two bars and two layers between them."""
    dock = DockLayout()
    menu = Widget(parent=dock, inline_style="dock: top; basis: 1")
    clock = Widget(parent=dock, inline_style="dock: none", x=75, width=5, height=1)
    console = Widget(parent=dock)
    desktop = Widget(parent=dock, inline_style="dock: fill")
    keybar = Widget(parent=dock, inline_style="dock: bottom; basis: 1")
    hosted(dock)
    assert rect(menu) == (0, 0, 80, 1)
    assert rect(clock) == (75, 0, 5, 1)
    assert rect(console) == rect(desktop) == (0, 1, 80, 22)
    assert rect(keybar) == (0, 23, 80, 1)


def test_left_and_right_take_what_top_left():
    dock = DockLayout()
    top = Widget(parent=dock, inline_style="dock: top; basis: 2")
    left = Widget(parent=dock, inline_style="dock: left; basis: 10")
    right = Widget(parent=dock, inline_style="dock: right; basis: 5")
    middle = Widget(parent=dock)
    hosted(dock)
    assert rect(top) == (0, 0, 80, 2)
    assert rect(left) == (0, 2, 10, 22)
    assert rect(right) == (75, 2, 5, 22)
    assert rect(middle) == (10, 2, 65, 22)


def test_an_unknown_dock_is_refused_by_the_sheet():
    with pytest.raises(stylesheet.StylesheetError):
        Widget(inline_style="dock: centre").style_declarations


# -- stack -------------------------------------------------------------------


def test_every_layer_fills_a_stack():
    stack = StackLayout()
    under, over = Widget(parent=stack), Widget(parent=stack)
    hosted(stack)
    assert rect(under) == rect(over) == (0, 0, 80, 24)
