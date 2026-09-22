"""What a document can only get wrong against a live class.

``navml/resolve.py`` and ``navml/checks.py``.  Every case here parses cleanly --
the parser has no complaint about any of them -- and fails only once the types
the document names are real objects, or once the hand-written half beside it has
been read.  Each refusal asserts the line as well as the message, the discipline
``tests/test_nml_parser.py`` sets.
"""

from __future__ import annotations

import sys
import uuid

import pytest

from navml.checks import check
from navml.errors import MarkupError
from navml.parser import parse
from navml.resolve import resolve
from navml.sibling import Sibling

PRELUDE = "from navml.widgets.button import Button\n" \
          "from navml.widgets.label import Label\n\n"


@pytest.fixture
def module(tmp_path, monkeypatch):
    """Write an importable module, for widgets the library does not have."""
    monkeypatch.syspath_prepend(str(tmp_path))

    def write(source: str) -> str:
        name = "m" + uuid.uuid4().hex
        (tmp_path / f"{name}.py").write_text(source, encoding="utf-8")
        yield_name = name
        sys.modules.pop(name, None)
        return yield_name

    return write


@pytest.fixture
def checked(tmp_path):
    """Parse, resolve and check one document, with an optional ``.py``."""

    def run(text: str, *, sibling: str | None = None, name: str = "widget"):
        path = None
        if sibling is not None:
            path = tmp_path / f"{name}.py"
            path.write_text(sibling, encoding="utf-8")
        document = parse(text, filename=f"{name}.nml")
        resolved = resolve(
            document, sibling=Sibling.read(path) if path else None
        )
        check(resolved)
        return resolved

    return run


def refused(checked, text, **kwargs) -> MarkupError:
    with pytest.raises(MarkupError) as caught:
        checked(text, **kwargs)
    return caught.value


# -- resolving what the document names ---------------------------------------


def test_a_type_the_document_did_not_import_is_refused(checked):
    error = refused(checked, "Widget:\n    Label:\n        id: a\n")
    assert error.line == 2
    assert "Label is not imported" in error.message


def test_something_that_is_not_a_widget_is_refused(checked):
    error = refused(
        checked, "from pathlib import Path\n\nWidget:\n    Path:\n        id: p\n"
    )
    assert error.line == 4
    assert "Path is not a widget class" in error.message


def test_the_shared_base_may_not_be_named_as_a_base(checked):
    """``class X(Component, _Component)`` is a duplicate base, not a class."""
    error = refused(
        checked, "from navml.component import Component\n\nPanel(Component):\n"
    )
    assert "write a bare Panel:" in error.message


def test_an_import_that_does_not_import_names_its_line(checked):
    error = refused(checked, "from nowhere_at_all import Thing\n\nPanel:\n")
    assert error.line == 1
    assert "nowhere_at_all" in error.message


# -- what the root block declares --------------------------------------------


def test_a_property_may_not_shadow_the_base(checked):
    error = refused(checked, "Panel:\n    property width: 0\n")
    assert error.line == 2
    assert "width is already an attribute of Component" in error.message


def test_an_id_may_not_shadow_the_base(checked):
    error = refused(
        checked, PRELUDE + "Panel:\n    Label:\n        id: width\n"
    )
    assert error.line == 6
    assert "width is already an attribute" in error.message


def test_a_style_property_that_disagrees_with_an_existing_one(checked):
    error = refused(checked, "Panel:\n    style_property border: 3 | 4\n")
    assert error.line == 2
    assert "already declared, and differently" in error.message


def test_a_style_property_that_agrees_is_fine(checked):
    checked("Panel:\n    style_property border: single | ascii | double | round\n")


# -- aliases -----------------------------------------------------------------


def test_an_alias_to_a_plain_attribute_is_refused(checked):
    error = refused(
        checked,
        PRELUDE + "Panel:\n    alias t: cap.is_mounted\n\n    Label:\n        id: cap\n",
    )
    assert error.line == 5
    assert "not a reactive attribute of Label" in error.message


def test_an_alias_to_a_computed_is_refused(checked):
    error = refused(
        checked,
        PRELUDE
        + "Panel:\n    alias t: cap.effective_stylesheet\n\n    Label:\n        id: cap\n",
    )
    assert "is computed" in error.message


def test_an_alias_to_a_reactive_attribute_is_fine(checked):
    checked(PRELUDE + "Panel:\n    alias t: cap.text\n\n    Label:\n        id: cap\n")


# -- what a child block constructs -------------------------------------------


def test_a_widget_with_a_required_argument_cannot_appear(checked, module):
    name = module(
        "from navkit.widget import Widget\n"
        "class Needy(Widget):\n"
        "    def __init__(self, path, **kwargs):\n"
        "        super().__init__(**kwargs)\n"
    )
    error = refused(
        checked, f"from {name} import Needy\n\nPanel:\n    Needy:\n        id: n\n"
    )
    assert error.line == 4
    assert "requires path at construction" in error.message


def test_a_widget_whose_argument_has_a_default_may_appear(checked, module):
    name = module(
        "from navkit.widget import Widget\n"
        "class Fine(Widget):\n"
        "    def __init__(self, path='.', **kwargs):\n"
        "        super().__init__(**kwargs)\n"
    )
    checked(f"from {name} import Fine\n\nPanel:\n    Fine:\n        id: n\n")


# -- what a property line lands on -------------------------------------------


def test_a_computed_target_is_refused(checked):
    error = refused(
        checked,
        PRELUDE + "Panel:\n    Label:\n        id: a\n        effective_stylesheet: 1\n",
    )
    assert error.line == 7
    assert "is computed" in error.message


def test_a_style_property_is_not_assigned(checked):
    error = refused(
        checked, PRELUDE + "Panel:\n    Label:\n        id: a\n        border: double\n"
    )
    assert "authored in a sheet" in error.message


def test_a_binding_onto_something_undeclared_is_refused(checked):
    """The failure whose only symptom is the ``<unassigned binding ...>`` repr."""
    error = refused(
        checked,
        PRELUDE + "Panel:\n    Label:\n        id: a\n        depth: parent.width\n",
    )
    assert "does not declare depth" in error.message


def test_a_literal_onto_a_plain_attribute_is_allowed(checked):
    checked(PRELUDE + "Panel:\n    Label:\n        id: a\n        depth: 3\n")


# -- the style block ---------------------------------------------------------


def test_an_unknown_style_property_names_its_line(checked):
    error = refused(
        checked, PRELUDE + "Panel:\n    style:\n        bgx: red\n"
    )
    assert error.line == 6


def test_a_variable_survives_to_run_time(checked):
    checked(PRELUDE + "Panel:\n    style:\n        bg: $surface\n")


# -- handler lines -----------------------------------------------------------


def test_a_handler_nothing_raises_is_refused(checked):
    error = refused(
        checked, PRELUDE + "Panel:\n    Label:\n        id: a\n        on_bogus: self.text = ''\n"
    )
    assert "nothing raises on_bogus" in error.message


def test_a_handler_landing_on_a_class_that_implements_it(checked):
    error = refused(
        checked,
        PRELUDE + "Panel:\n    Button:\n        id: b\n        on_key: self.text = ''\n",
    )
    assert "Button already implements on_key" in error.message


def test_a_root_handler_landing_on_the_hand_written_half(checked):
    error = refused(
        checked,
        "Panel:\n    on_click: self.done()\n",
        sibling="class Panel:\n    async def on_click(self, event): ...\n",
    )
    assert "already implements on_click" in error.message


def test_a_handler_may_land_on_a_child_that_only_emits(checked):
    checked(
        PRELUDE
        + "Panel:\n    Button:\n        id: b\n        on_click: self.text = ''\n"
    )


# -- the hand-written half ---------------------------------------------------


def test_awaiting_something_that_is_not_async(checked):
    error = refused(
        checked,
        PRELUDE
        + "Panel:\n    Button:\n        id: b\n        on_click: await root.done(event)\n",
        sibling="class Panel:\n    def done(self, event): ...\n",
    )
    assert "is not async, so it cannot be awaited" in error.message


def test_calling_something_async_without_await(checked):
    error = refused(
        checked,
        PRELUDE
        + "Panel:\n    Button:\n        id: b\n        on_click: root.done(event)\n",
        sibling="class Panel:\n    async def done(self, event): ...\n",
    )
    assert "builds a coroutine and drops it" in error.message


def test_an_event_declared_in_both_halves(checked):
    error = refused(
        checked,
        "Panel:\n    event Accepted\n",
        sibling=(
            "from navkit.events import Event\n"
            "class Accepted(Event): ...\n"
            "class Panel: ...\n"
        ),
    )
    assert error.line == 2
    assert "declared in widget.py too" in error.message


def test_a_composed_name_naming_no_id(checked):
    """What keeps renaming an ``id`` from silently orphaning its handler."""
    error = refused(
        checked,
        PRELUDE + "Panel:\n    Button:\n        id: ok\n",
        sibling="class Panel:\n    async def on_cancel_click(self, event): ...\n",
    )
    assert "cancel is not an id in this document" in error.message


def test_a_composed_name_that_does_name_an_id_is_fine(checked):
    checked(
        PRELUDE + "Panel:\n    Button:\n        id: ok\n",
        sibling="class Panel:\n    async def on_ok_click(self, event): ...\n",
    )


def test_a_handler_of_navkit_s_own_is_not_read_as_composed(checked):
    """``on_mouse_click`` is an event's handler, not ``mouse`` plus a click."""
    checked(
        PRELUDE + "Panel:\n    Button:\n        id: ok\n",
        sibling="class Panel:\n    async def on_mouse_click(self, event): ...\n",
    )


def test_a_reactive_the_markup_cannot_see_is_reported(checked):
    error = refused(
        checked,
        "Panel:\n    property enabled: True\n",
        sibling=(
            "from navkit.reactive import reactive\n"
            "class Panel:\n    enabled: bool = reactive(True)\n"
        ),
    )
    assert "declares enabled, which this document declares too" in error.message
