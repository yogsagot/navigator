"""``class NAME: VALUE`` lines, and the ``default_height`` they were made for.

A ``class`` line overrides a plain class attribute the base already has, as a
class-level expression: the generated class body carries ``NAME = VALUE``.
``Widget.default_height`` is the first such attribute: the height a widget
starts with when its constructor is given none, 1 for the single-row
controls, so a document need not say ``height: 1`` under each of them.
"""

from __future__ import annotations

import pytest

from navkit.reactive import is_bound
from navkit.widget import Widget

from navml.checks import check
from navml.errors import MarkupError
from navml.generator import generate
from navml.parser import ClassAttrDecl, parse
from navml.resolve import resolve
from navml.stubs import stub
from navml.widgets.dialog.choice_field import ChoiceField
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.input_line import InputLine
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.masked_field import MaskedField
from navml.widgets.dialog.static_text import StaticText
from navml.widgets.progress_bar import ProgressBar

PRELUDE = (
    "from navml.widgets.dialog.label import Label\n"
    "from navml.widgets.layout.horizontal_layout import HorizontalLayout\n\n"
)


def refused(text: str) -> MarkupError:
    with pytest.raises(MarkupError) as caught:
        check(resolve(parse(PRELUDE + text, filename="widget.nml")))
    return caught.value


def built(text: str, **kwargs):
    document = parse(PRELUDE + text, filename="widget.nml")
    resolved = resolve(document)
    check(resolved)
    namespace: dict = {"__name__": "generated"}
    exec(compile(generate(resolved), "widget_nml.py", "exec"), namespace)
    return namespace["Widget_"]


# -- the directive -----------------------------------------------------------


def test_a_class_line_is_read_as_a_declaration():
    document = parse(PRELUDE + "Widget_(HorizontalLayout):\n    class default_height: 2\n")
    (declaration,) = document.root.declarations
    assert declaration == ClassAttrDecl("default_height", "2", 5)


def test_a_class_line_becomes_a_class_attribute():
    cls = built("Widget_(HorizontalLayout):\n    class default_height: 2\n")
    assert cls.__dict__["default_height"] == 2
    assert cls().height == 2
    assert cls(height=5).height == 5


def test_the_value_is_a_class_level_expression_over_the_imports():
    text = (
        "from navml.widgets.dialog.label import Label\n"
        "from navml.widgets.layout.horizontal_layout import HorizontalLayout\n"
        "from navkit.widget import Widget\n\n"
        "Widget_(HorizontalLayout):\n    class default_height: Widget.default_height + 2\n"
    )
    resolved = resolve(parse(text, filename="widget.nml"))
    check(resolved)
    namespace: dict = {"__name__": "generated"}
    exec(compile(generate(resolved), "widget_nml.py", "exec"), namespace)
    assert namespace["Widget_"].default_height == 2


def test_the_stub_leaves_the_attribute_to_the_base():
    resolved = resolve(parse(PRELUDE + "Widget_(HorizontalLayout):\n    class default_height: 2\n",
                             filename="widget.nml"))
    assert "default_height" not in stub(resolved)


def test_a_child_cannot_carry_one():
    error = refused("Widget_(HorizontalLayout):\n    Label:\n        class default_height: 2\n")
    assert error.line == 6


@pytest.mark.parametrize(
    ("line", "says"),
    [
        ("class no_such_thing: 1", "has no class attribute"),
        ("class height: 1", "not a plain class attribute"),
        ("class layout: 1", "not a plain class attribute"),
        ("class default_height: self.width", "'self' is not imported"),
        ("class default_height: 1 // 0", "failed to evaluate"),
    ],
)
def test_what_a_class_line_cannot_say(line, says):
    error = refused(f"Widget_(HorizontalLayout):\n    {line}\n")
    assert says in str(error)
    assert error.line == 5


def test_a_class_line_and_an_id_cannot_share_a_name():
    with pytest.raises(MarkupError):
        parse(PRELUDE + "Widget_(HorizontalLayout):\n    class default_height: 1\n"
              "    Label:\n        id: default_height\n")


# -- default_height ------------------------------------------------------------


def test_a_plain_widget_still_starts_with_no_height():
    assert Widget().height == 0


@pytest.mark.parametrize(
    "cls", [Label, InputLine, StaticText, ProgressBar, Field, MaskedField, ChoiceField]
)
def test_a_single_row_control_starts_one_row_high(cls):
    assert cls().height == 1
    assert cls(height=4).height == 4


def test_the_default_is_an_assignment_and_not_a_binding():
    """``Widget.height`` names the same declaration on every class, so a
    layout's ``is_bound(child, Widget.height)`` still answers for a Label."""
    label = Label()
    assert not is_bound(label, Widget.height)


def test_a_document_need_not_say_height_under_a_label():
    cls = built("Widget_(HorizontalLayout):\n    Label:\n        id: caption\n        width: 5\n")
    assert cls().caption.height == 1
