"""``anchors:`` blocks, and the ButtonRow they place.

``navml/anchors.py`` turns an ``anchors:`` block into the geometry property
lines that used to be written by hand, before the generator sees the document.
Here: the lines each form expands to, the mistakes refused at build time with
the line they sit on, and the geometry the generated bindings give, followed
across a resize.  The last section is ``ButtonRow``.
"""

from __future__ import annotations

import pytest

from navkit.reactive import is_bound
from navkit.widget import Widget

from navml.checks import check
from navml.errors import MarkupError
from navml.generator import generate
from navml.parser import parse
from navml.resolve import resolve
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.button_row import ButtonRow

PRELUDE = (
    "from navml.widgets.dialog.label import Label\n"
    "from navml.widgets.layout.horizontal_layout import HorizontalLayout\n\n"
)


def lines(text: str) -> dict[str, dict[str, str]]:
    """Every block's property lines, by id (the root as ``root``)."""
    document = parse(PRELUDE + text, filename="widget.nml")
    return {
        (block.id or "root"): {p.name: p.expression for p in block.properties}
        for block in document.root.walk()
    }


def refused(text: str) -> MarkupError:
    with pytest.raises(MarkupError) as caught:
        document = parse(PRELUDE + text, filename="widget.nml")
        check(resolve(document))
    return caught.value


def built(text: str, **kwargs):
    """Generate *text*, run it, and construct the component."""
    document = parse(PRELUDE + text, filename="widget.nml")
    namespace: dict = {"__name__": "generated"}
    exec(compile(generate(resolve(document)), "widget_nml.py", "exec"), namespace)
    return namespace["Widget_"](**kwargs)


def geometry(widget: Widget) -> tuple[int, int, int, int]:
    return widget.x, widget.y, widget.width, widget.height


# -- what each form writes ---------------------------------------------------


def test_an_end_edge_alone_pins_the_widgets_own_size():
    got = lines("""Widget_:
    Label:
        id: a
        width: 11
        anchors:
            right: 2
            bottom: 3
""")["a"]
    assert got["x"] == "max(0, parent.width - 2 - self.width)"
    assert got["y"] == "max(0, parent.height - 3 - self.height)"
    assert got["width"] == "11"


def test_two_literal_insets_read_as_the_line_they_replace():
    got = lines("""Widget_:
    Label:
        id: a
        anchors:
            left: 2
            right: 2
""")["a"]
    assert got == {"x": "2", "width": "max(0, parent.width - 4)"}


def test_center_is_modals_own_binding():
    got = lines("""Widget_:
    anchors:
        center: both
""")["root"]
    assert got == {
        "x": "max(0, (parent.width - self.width) // 2)",
        "y": "max(0, (parent.height - self.height) // 2)",
    }


def test_a_zero_inset_writes_no_subtraction():
    got = lines("""Widget_:
    Label:
        id: a
        anchors:
            left: 0
            right: 0
""")["a"]
    assert got["width"] == "max(0, parent.width)"


def test_a_sibling_start_and_a_parent_end_stretch_between_them():
    got = lines("""Widget_:
    Label:
        id: a
        width: 10
    Label:
        id: b
        anchors:
            after: a + 1
            right: 2
""")["b"]
    assert got["x"] == "root.a.x + root.a.width + 1"
    assert got["width"] == "max(0, parent.width - 2 - self.x)"


def test_a_list_of_siblings_takes_the_first_one_shown():
    got = lines("""Widget_:
    Label:
        id: mark
    Label:
        id: clock
    Label:
        id: a
        anchors:
            before: mark, clock + 1
""")["a"]
    assert got["x"] == (
        "max(0, (root.mark.x - 1 if root.mark.visible and root.mark.width else root.clock.x - 1) - self.width)"
    )


def test_a_parent_edge_beside_a_sibling_is_the_fallback():
    got = lines("""Widget_:
    Label:
        id: options
    Label:
        id: a
        anchors:
            left: 2
            before: options + 1
            right: 1
""")["a"]
    assert got["x"] == "2"
    assert got["width"] == (
        "max(0, (root.options.x - 1 if root.options.visible and root.options.width "
        "else parent.width - 1) - 2)"
    )


def test_a_lone_sibling_stays_unconditional():
    got = lines("""Widget_:
    Label:
        id: a
    Label:
        id: b
        anchors:
            after: a + 1
""")["b"]
    assert got["x"] == "root.a.x + root.a.width + 1"


def test_a_sibling_named_like_one_of_the_widget_s_own_properties_is_still_the_sibling():
    """A field ``id: text`` beside a ``Label``, whose own ``text`` is its caption:
    bare, ``text`` would be the caption string -- the Find dialog met this."""
    root = built("""Widget_:
    Label:
        id: text
        y: 2
        height: 1
    Label:
        id: below_it
        height: 1
        anchors:
            below: text + 1
""", width=40, height=10)
    assert root.below_it.y == 4


# -- what is refused -----------------------------------------------------------


@pytest.mark.parametrize(
    "body, line, words",
    [
        ("x: 1\n        anchors:\n            left: 2\n", 11, "x is written"),
        ("width: 5\n        anchors:\n            left: 2\n            right: 2\n",
         12, "width is written"),
        ("anchors:\n            after: other, other\n", 10, "one sibling twice"),
        ("anchors:\n            center: horizontal\n            right: 2\n", 11,
         "center horizontal and right"),
        ("anchors:\n            center: both\n            fill: 1\n", 11, "fill"),
        ("anchors:\n            after: nobody\n", 10, "not an id beside"),
        ("anchors:\n            middle: 2\n", 10, "no anchor"),
        ("anchors:\n            after: other * 2\n", 10, "names siblings"),
        ("anchors:\n            after: other + 1, other\n", 10, "names siblings"),
        ("anchors:\n            center: diagonal\n", 10, "it takes"),
        ("anchors:\n            left: 1\n            left: 2\n", 11, "already anchored"),
    ],
)
def test_a_mistake_is_refused_on_its_line(body, line, words):
    error = refused(f"""Widget_:
    Label:
        id: other
    Label:
        id: a
        {body}""")
    assert words in str(error)
    assert error.line == line


def test_the_root_has_no_siblings_to_anchor_to():
    error = refused("""Widget_:
    anchors:
        after: a
    Label:
        id: a
""")
    assert "root block has no siblings" in str(error)


def test_an_empty_block_is_refused():
    assert "says nothing" in str(refused("""Widget_:
    anchors:
    Label:
        id: a
"""))


def test_anchors_under_a_layout_are_refused():
    error = refused("""Widget_:
    HorizontalLayout:
        Label:
            anchors:
                left: 2
""")
    assert "places its children itself" in str(error)
    assert error.line == 7


# -- the geometry it gives ------------------------------------------------------


DOCUMENT = """Widget_:
    Label:
        id: tag
        width: 6
        height: 1
        anchors:
            left: 2
            top: 1
    Label:
        id: entry
        height: 1
        anchors:
            after: tag + 1
            right: 3
            top: 1
    Label:
        id: pinned
        width: 10
        height: 2
        anchors:
            right: 2
            bottom: 1
    Label:
        id: body
        anchors:
            fill: 2
            bottom: 4
    Label:
        id: middle
        width: 20
        height: 3
        anchors:
            center: both
    Label:
        id: tight
        height: 1
        anchors:
            before: pinned + 1
            top: 3
"""


CHAIN = """Widget_:
    Label:
        id: clock
        width: 5
        height: 1
        anchors:
            right: 0
    Label:
        id: mark
        width: 3
        height: 1
        anchors:
            before: clock + 1
            right: 0
    Label:
        id: strip
        height: 1
        anchors:
            left: 10
            before: mark, clock + 1
            right: 1
"""


def test_a_chain_steps_past_what_is_hidden():
    root = built(CHAIN, width=80, height=25)
    assert root.mark.x == 71
    assert (root.strip.x, root.strip.width) == (10, 60)
    root.mark.visible = False
    assert (root.strip.x, root.strip.width) == (10, 64)
    root.clock.visible = False
    assert root.mark.x == 77
    assert (root.strip.x, root.strip.width) == (10, 69)
    root.mark.visible = True
    assert (root.strip.x, root.strip.width) == (10, 66)


def test_an_empty_sibling_counts_as_not_shown():
    root = built(CHAIN, width=80, height=25)
    root.mark.width = 0
    assert root.strip.width == 64


def test_anchored_geometry_follows_a_resize():
    root = built(DOCUMENT, width=80, height=25)
    assert geometry(root.tag) == (2, 1, 6, 1)
    assert geometry(root.entry) == (9, 1, 68, 1)
    assert geometry(root.pinned) == (68, 22, 10, 2)
    assert geometry(root.body) == (2, 2, 76, 19)
    assert geometry(root.middle) == (30, 11, 20, 3)
    assert root.tight.x == 67 - root.tight.width
    root.width, root.height = 60, 20
    assert geometry(root.entry) == (9, 1, 48, 1)
    assert geometry(root.pinned) == (48, 17, 10, 2)
    assert geometry(root.body) == (2, 2, 56, 14)
    assert geometry(root.middle) == (20, 8, 20, 3)


def test_nothing_goes_negative_when_the_parent_is_too_small():
    root = built(DOCUMENT, width=5, height=2)
    assert root.pinned.x == 0
    assert root.body.width == 1
    assert root.body.height == 0
    assert root.middle.x == 0 and root.middle.y == 0


def test_an_anchored_side_is_bound_so_layout_steps_around_it():
    root = built(DOCUMENT, width=80, height=25)
    assert is_bound(root.pinned, Widget.x)
    assert not is_bound(root.tag, Widget.x)


# -- ButtonRow -----------------------------------------------------------------


def row_of(*captions: str, **kwargs) -> ButtonRow:
    row = ButtonRow(width=60, **kwargs)
    for caption in captions:
        Button(parent=row, text=caption)
    row.arrange()
    return row


def test_a_row_centres_its_buttons_at_one_width():
    row = row_of("O~K~", "~C~ancel", "~H~elp")
    assert [b.x for b in row.children] == [11, 24, 37]
    assert {b.width for b in row.children} == {11}
    assert row.height == 2


def test_a_hidden_button_gives_up_its_slot():
    row = row_of("O~K~", "~C~ancel", "~H~elp")
    row.children[2].visible = False
    row.arrange()
    assert [b.x for b in row.children[:2]] == [18, 31]


def test_width_zero_sizes_each_button_by_its_caption():
    row = row_of("O~K~", "~C~ancel", button_width=0)
    assert [b.width for b in row.children] == [7, 11]


def test_a_buttons_own_basis_wins():
    row = ButtonRow(width=60)
    wide = Button(parent=row, text="Wide")
    wide.inline_style = "basis: 20"
    Button(parent=row, text="OK")
    row.arrange()
    assert [b.width for b in row.children] == [20, 11]
