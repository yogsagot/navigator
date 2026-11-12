"""``when COND:`` blocks: a widget's lines that differ while a condition holds.

``navml/states.py`` folds each block into the lines it overrides, beside the
anchors it may carry, before the generator sees the document.  Here: what is
written, what is refused (with its line), and the geometry following the
condition across a resize.
"""

from __future__ import annotations

import pytest

from navml.checks import check
from navml.errors import MarkupError
from navml.generator import generate
from navml.parser import parse
from navml.resolve import resolve

PRELUDE = (
    "from navml.widgets.dialog.label import Label\n"
    "from navml.widgets.layout.horizontal_layout import HorizontalLayout\n\n"
)


def lines(text: str) -> dict[str, dict[str, str]]:
    document = parse(PRELUDE + text, filename="widget.nml")
    return {
        (block.id or "root"): {p.name: p.expression for p in block.properties}
        for block in document.root.walk()
    }


def refused(text: str) -> MarkupError:
    with pytest.raises(MarkupError) as caught:
        check(resolve(parse(PRELUDE + text, filename="widget.nml")))
    return caught.value


def built(text: str, **kwargs):
    namespace: dict = {"__name__": "generated"}
    source = generate(resolve(parse(PRELUDE + text, filename="widget.nml")))
    exec(compile(source, "widget_nml.py", "exec"), namespace)
    return namespace["Widget_"](**kwargs)


# -- what is written ---------------------------------------------------------------


def test_a_property_line_is_replaced_while_the_condition_holds():
    got = lines("""Widget_:
    Label:
        id: a
        x: 35
        y: 12
        when parent.width < 67:
            x: 30
""")["a"]
    assert got == {"x": "(30) if (parent.width < 67) else (35)", "y": "12"}


def test_an_anchor_replaces_the_widget_s_on_its_side_alone():
    """``bottom`` replaced, ``top`` kept: the list still stretches between them."""
    got = lines("""Widget_:
    Label:
        id: a
        anchors:
            left: 1
            top: 1
            bottom: 4
        when parent.width < 82:
            anchors:
                bottom: 6
""")["a"]
    assert got["x"] == "1"
    assert got["y"] == "1"
    assert got["height"] == (
        "(max(0, parent.height - 7)) if (parent.width < 82) else (max(0, parent.height - 5))"
    )


def test_the_first_block_whose_condition_holds_wins():
    got = lines("""Widget_:
    Label:
        id: a
        x: 3
        when parent.width < 40:
            x: 1
        when parent.width < 67:
            x: 2
""")["a"]
    assert got["x"] == "(1) if (parent.width < 40) else ((2) if (parent.width < 67) else (3))"


def test_a_block_that_changes_nothing_writes_nothing_extra():
    got = lines("""Widget_:
    Label:
        id: a
        x: 3
        when parent.width < 67:
            x: 3
""")["a"]
    assert got == {"x": "3"}


def test_center_loses_the_axis_a_when_edge_names():
    got = lines("""Widget_:
    Label:
        id: a
        width: 10
        height: 2
        anchors:
            center: both
        when parent.width < 30:
            anchors:
                left: 0
""")["a"]
    assert got["x"] == "(0) if (parent.width < 30) else (max(0, (parent.width - self.width) // 2))"
    assert got["y"] == "max(0, (parent.height - self.height) // 2)"


# -- what is refused ------------------------------------------------------------------


@pytest.mark.parametrize(
    "body, line, words",
    [
        ("x: 1\n        when:\n            x: 2\n", 8, "needs a condition"),
        ("x: 1\n        when parent.width <:\n            x: 2\n", 8, "the when condition"),
        ("x: 1\n        when parent.width < 9:\n", 8, "says nothing"),
        ("x: 1\n        when parent.width < 9:\n            id: b\n", 9, "property lines alone"),
        ("x: 1\n        when parent.width < 9:\n            on_click: pass\n", 9, "property lines alone"),
        ("x: 1\n        when parent.width < 9:\n            style:\n                bold: true\n", 9,
         "an anchors block"),
        ("x: 1\n        when parent.width < 9:\n            when root.x:\n                x: 2\n", 9,
         "inside a when block"),
        ("x: 1\n        when parent.width < 9:\n            x: 2\n            x: 3\n", 10, "a second 'x'"),
        ("x: 1\n        when parent.width < 9:\n            y: 2\n", 9, "no line for"),
        # A written x and an end edge stretch the width -- which the widget has no line for.
        ("x: 1\n        when parent.width < 9:\n            anchors:\n                right: 2\n", 10,
         "gives width a value"),
    ],
)
def test_a_mistake_is_refused_on_its_line(body, line, words):
    error = refused(f"""Widget_:
    Label:
        id: a
        {body}""")
    assert words in str(error)
    assert error.line == line


# -- the geometry it gives -----------------------------------------------------------


DOCUMENT = """Widget_:
    Label:
        id: unit
        x: 35
        y: 12
        width: max(0, parent.width - 38)
        height: 1
        when parent.width < 67:
            x: 30
            y: 13
            width: max(0, parent.width - 32)
    Label:
        id: button
        width: 10
        height: 2
        anchors:
            right: 47
            bottom: 1
        when parent.width < 82:
            anchors:
                right: 25
                bottom: 3
"""


def test_the_geometry_follows_the_condition_across_a_resize_both_ways():
    root = built(DOCUMENT, width=100, height=24)
    assert (root.unit.x, root.unit.y, root.unit.width) == (35, 12, 62)
    assert (root.button.x, root.button.y) == (43, 21)
    root.width = 70                                  # narrow for the button only
    assert (root.unit.x, root.unit.y) == (35, 12)
    assert (root.button.x, root.button.y) == (35, 19)
    root.width = 60                                  # narrow for both
    assert (root.unit.x, root.unit.y, root.unit.width) == (30, 13, 28)
    root.width = 100                                 # and back
    assert (root.unit.x, root.unit.y, root.button.x, root.button.y) == (35, 12, 43, 21)
