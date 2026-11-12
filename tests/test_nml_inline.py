"""The inline child form: ``MenuItem: text='~A~bout', command=About``.

A child's head line may carry its property values as keywords.  Each becomes
the property line it stands for, at the head's line, so the generated code is
the block form's -- captions translated, expressions bound -- and an indented
body may still follow.
"""

from __future__ import annotations

import re

import pytest

from navml.checks import check
from navml.errors import MarkupError
from navml.generator import generate
from navml.parser import parse
from navml.resolve import resolve

PRELUDE = (
    "from navml.widgets.dialog.label import Label\n"
    "from navml.widgets.layout.horizontal_layout import HorizontalLayout\n\n"
    "Widget_(HorizontalLayout):\n"
)


def generated(body: str) -> str:
    resolved = resolve(parse(PRELUDE + body, filename="widget.nml"))
    check(resolved)
    # Source-map comments name lines, which the two forms place differently.
    return re.sub(r" +# widget\.nml:\d+", "", generate(resolved))


def refused(body: str) -> MarkupError:
    with pytest.raises(MarkupError) as caught:
        check(resolve(parse(PRELUDE + body, filename="widget.nml")))
    return caught.value


def properties(body: str) -> list[tuple[str, str, int]]:
    document = parse(PRELUDE + body, filename="widget.nml")
    (child,) = document.root.children
    return [(p.name, p.expression, p.line) for p in child.properties]


def test_the_head_carries_property_lines_at_its_own_line():
    assert properties("    Label: text='~N~ame', width=parent.width - 2, align='left'\n") == [
        ("text", "'~N~ame'", 5),
        ("width", "parent.width - 2", 5),
        ("align", "'left'", 5),
    ]


def test_it_generates_what_the_block_form_does():
    inline = generated("    Label: text='~N~ame', width=parent.width - 2\n        id: caption\n")
    block = generated(
        "    Label:\n        id: caption\n        text: '~N~ame'\n        width: parent.width - 2\n"
    )
    assert inline == block
    assert "_tr('~N~ame')" in inline


def test_a_body_may_follow():
    assert properties("    Label: text='a'\n        id: caption\n        x: 2\n") == [
        ("text", "'a'", 5),
        ("x", "2", 7),
    ]


def test_a_colon_inside_a_value_is_the_values():
    assert properties("    Label: text='a: b'\n") == [("text", "'a: b'", 5)]


def test_a_doc_comment_above_the_head_is_the_widgets():
    document = parse(PRELUDE + "    #: The caption.\n    Label: text='a'\n", filename="widget.nml")
    assert document.root.children[0].doc == ("The caption.",)


def test_a_property_line_with_keywords_in_its_value_is_still_a_property_line():
    # Lower case is a property, and ``f(a=1)`` is an expression on its own.
    document = parse(PRELUDE + "    Label:\n        text: str(object='x')\n", filename="widget.nml")
    (child,) = document.root.children
    assert [(p.name, p.expression) for p in child.properties] == [("text", "str(object='x')")]


@pytest.mark.parametrize(
    ("body", "says"),
    [
        ("    Label: id='caption'\n", "an id is a line of its own"),
        ("    Label: on_click=root.close()\n", "is a handler"),
        ("    Label: style='bg: red'\n", "is a block"),
        ("    Label: text='a', text='b'\n", "a second 'text'"),
        ("    Label: text='a'\n        text: 'b'\n", "a second 'text'"),
        ("    Label: text=1 +\n", "cannot read"),
    ],
)
def test_what_an_inline_head_cannot_say(body, says):
    error = refused(body)
    assert says in str(error)


def test_the_root_has_no_inline_form():
    with pytest.raises(MarkupError):
        parse(
            "from navml.widgets.dialog.label import Label\n\nWidget_(Label): text='x'\n",
            filename="widget.nml",
        )
