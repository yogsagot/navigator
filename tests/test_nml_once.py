"""``name = expression``: a value set once, and ``first_focus``.

A ``=`` line is evaluated once, when the widget is built, and assigned rather
than bound -- the starting value a property the widget navigates
(``Panel.path``) needs, which ``name: expression`` cannot give because a bound
attribute refuses a write.
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
from navml.widgets.dialog.label import Label

PRELUDE = (
    "from navml.widgets.dialog.label import Label\n"
    "from navml.widgets.layout.horizontal_layout import HorizontalLayout\n\n"
)


def built(text: str, **kwargs):
    resolved = resolve(parse(PRELUDE + text, filename="widget.nml"))
    check(resolved)
    namespace: dict = {"__name__": "generated"}
    exec(compile(generate(resolved), "widget_nml.py", "exec"), namespace)
    return namespace["Widget_"](**kwargs)


def refused(text: str) -> MarkupError:
    with pytest.raises(MarkupError) as caught:
        check(resolve(parse(PRELUDE + text, filename="widget.nml")))
    return caught.value


def test_a_value_set_once_is_read_once_and_not_bound():
    widget = built(
        "Widget_(HorizontalLayout):\n"
        "    property start: 'a'\n"
        "    Label:\n"
        "        id: caption\n"
        "        align = root.start\n",
        start="b",
    )
    assert widget.caption.align == "b"
    assert not is_bound(widget.caption, Label.align)
    widget.start = "c"
    assert widget.caption.align == "b"


def test_python_may_write_it_afterwards():
    widget = built("Widget_(HorizontalLayout):\n    Label:\n        id: caption\n        text = 'one'\n")
    widget.caption.text = "two"
    assert widget.caption.text == "two"


def test_a_caption_set_once_is_translated_once():
    resolved = resolve(parse(
        PRELUDE + "Widget_(HorizontalLayout):\n    Label:\n        text = '~N~ame'\n",
        filename="widget.nml",
    ))
    check(resolved)
    assert "_w1.text = _tr('~N~ame')" in generate(resolved)


def test_the_root_may_set_its_own_once():
    widget = built("Widget_(HorizontalLayout):\n    spacing = 3\n")
    assert widget.spacing == 3


def test_a_colon_in_the_value_is_the_values():
    widget = built("Widget_(HorizontalLayout):\n    Label:\n        id: caption\n        text = {'a': 'x'}['a']\n")
    assert widget.caption.text == "x"


def test_equality_is_still_an_expression():
    document = parse(
        PRELUDE + "Widget_(HorizontalLayout):\n    Label:\n        visible: root.width == 3\n",
        filename="widget.nml",
    )
    (line,) = document.root.children[0].properties
    assert not line.once and line.expression == "root.width == 3"


def test_a_plain_attribute_may_be_set_once():
    """Stored rather than followed is what ``=`` says, so it is not refused."""
    widget = built("Widget_(HorizontalLayout):\n    Label:\n        id: caption\n        tooltip = root.name\n")
    assert widget.caption.tooltip == widget.name


@pytest.mark.parametrize(
    ("body", "says"),
    [
        ("    Label:\n        id = 'x'\n", "an id, a handler and a directive"),
        ("    Label:\n        on_click = root.close()\n", "an id, a handler and a directive"),
        ("    Label:\n        text = 'a'\n        text: 'b'\n", "a second 'text'"),
        (
            "    Label:\n        text = 'a'\n        when root.width < 3:\n            text: 'b'\n",
            "is set once",
        ),
        (
            "    Label:\n        text: 'a'\n        when root.width < 3:\n            text = 'b'\n",
            "not 'name = value'",
        ),
        ("    Label:\n        x = 2\n        anchors:\n            left: 1\n", "x"),
    ],
)
def test_what_a_value_set_once_cannot_be(body, says):
    error = refused("Widget_(HorizontalLayout):\n" + body)
    assert says in str(error)


# -- first_focus ---------------------------------------------------------------


def test_a_dialog_hands_the_keyboard_to_its_first_focus():
    from conftest import run_app

    from navkit.application import Application
    from navml.widgets.dialog.dialog import Dialog

    root = Widget(width=80, height=25)
    app = Application(root)
    seen = []

    def open_dialog(a):
        dialog = Dialog(buttons="yes-no-cancel", prompt="?")
        dialog.first_focus = dialog.cancel
        a.overlay(dialog)

    run_app(app, [open_dialog, lambda a: seen.append(a.focused), lambda a: None])
    assert seen and getattr(seen[0], "text", None) == "~C~ancel"


def test_without_one_the_first_in_the_tab_order_has_it():
    from conftest import run_app

    from navkit.application import Application
    from navml.widgets.dialog.dialog import Dialog

    root = Widget(width=80, height=25)
    app = Application(root)
    seen = []
    run_app(app, [lambda a: a.overlay(Dialog(buttons="yes-no-cancel", prompt="?")),
                  lambda a: seen.append(a.focused), lambda a: None])
    assert seen and seen[0] is not None and getattr(seen[0], "text", None) != "~C~ancel"


def test_a_name_nothing_declares_is_refused():
    """Run as the widget is built, so a bare name has to mean something now."""
    error = refused("Widget_(HorizontalLayout):\n    Label:\n        text = nowhere\n")
    assert "'nowhere' means nothing here" in str(error)
