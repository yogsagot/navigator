"""Emitting the ``.pyi`` that stands for both halves.

``navml/stubs.py``.  A stub replaces its module for a type checker, so what is
asserted here is that it says everything the module offers -- the generated
surface and the hand-written one -- and says each thing exactly once.
"""

from __future__ import annotations

import ast

import pytest

from navml.generator import MARKER
from navml.parser import parse, parse_file
from navml.resolve import resolve
from navml.sibling import Sibling
from navml.stubs import stub

SHIPPED = ["label", "button", "framed_button", "dialog"]


def build(stem: str) -> str:
    document = parse_file(f"navml/widgets/{stem}.nml")
    return stub(
        resolve(
            document,
            package="navml.widgets",
            sibling=Sibling.read(f"navml/widgets/{stem}.py"),
        )
    )


@pytest.fixture
def written():
    def make(text: str, name: str = "widget") -> str:
        return stub(resolve(parse(text, filename=f"{name}.nml")))

    return make


# -- every shipped component -------------------------------------------------


@pytest.mark.parametrize("stem", SHIPPED)
def test_a_stub_is_python(stem):
    ast.parse(build(stem))


@pytest.mark.parametrize("stem", SHIPPED)
def test_a_stub_says_it_was_generated(stem):
    assert build(stem).splitlines()[0] == MARKER


@pytest.mark.parametrize("stem", SHIPPED)
def test_a_name_is_declared_once(stem):
    tree = ast.parse(build(stem))
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        names = [
            entry.name
            for entry in node.body
            if isinstance(entry, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        assert len(names) == len(set(names))


# -- the three shapes --------------------------------------------------------


def test_a_markup_only_component_is_its_generated_surface():
    """The only thing a checker can see for that module name."""
    source = build("label")
    assert "text: str" in source
    assert "align: str" in source
    assert "def __init__(self, **kwargs: _Any) -> None: ..." in source


def test_a_merged_component_carries_both_halves():
    source = build("button")
    assert "caption: Label" in source          # the markup's
    assert "enabled: bool" in source           # the hand-written half's
    assert "async def press(self) -> bool: ..." in source


def test_the_event_class_beside_a_component_is_part_of_the_module():
    assert "class ClickEvent(Event): ..." in build("button")


def test_a_hand_written_constructor_wins():
    assert "def __init__(self, text: str = ..., **kwargs: Any)" in build("button")


def test_a_derived_component_keeps_both_bases():
    assert "class FramedButton(Button, _Component):" in build("framed_button")


# -- the composed handlers ---------------------------------------------------


def test_an_unoverridden_stub_is_declared():
    assert "async def on_cancel_click(self, event: _Event) -> bool: ..." in build(
        "dialog"
    )


def test_an_overridden_stub_is_declared_with_the_override_s_signature():
    source = build("dialog")
    assert "async def on_ok_click(self, event: Event) -> bool: ..." in source
    assert "async def on_ok_click(self, event: _Event)" not in source


def test_a_child_with_an_explicit_handler_gets_no_stub():
    assert "on_info_click" not in build("dialog")


# -- the declarations --------------------------------------------------------


def test_an_alias_is_annotated_with_the_target_s_type(written):
    source = written(
        "from navml.widgets.label import Label\n\n"
        "Panel:\n    alias title: cap.text\n\n    Label:\n        id: cap\n"
    )
    assert "title: str" in source


def test_a_style_property_is_annotated_by_its_default(written):
    assert "icons: str" in written("Panel:\n    style_property icons: auto | none\n")


def test_a_property_with_no_literal_default_is_unchecked(written):
    """Which is what the generated module says about it too."""
    assert "entries: _Any" in written("Panel:\n    property entries: []\n")


def test_an_event_declared_in_markup_is_not_an_attribute(written):
    source = written("Panel:\n    event Accepted\n")
    assert "Accepted:" not in source
