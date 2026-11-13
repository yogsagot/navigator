"""Emitting the ``.pyi`` that stands for both halves.

``navml/stubs.py``.  A stub replaces its module for a type checker, so what is
asserted here is that it says everything the module offers -- the generated
surface and the hand-written one -- and says each thing exactly once.
"""

from __future__ import annotations

import ast

import pathlib

import pytest

from navml.generator import MARKER
from navml.parser import parse, parse_file
from navml.resolve import resolve
from navml.sibling import Sibling
from navml.stubs import stub

SHIPPED = ["static_text", "label", "button", "modal", "window", "dialog"]

def shipped(stem: str, suffix: str) -> str:
    """One file of a shipped component.

    A component is a directory whose files repeat its name, so every path in
    here goes through this rather than being spelled out.  A component may sit
    in a group directory, so it is found by name rather than by a fixed depth.
    """
    return next(
        str(path) for path in sorted(pathlib.Path("navml/widgets").rglob(f"{stem}{suffix}"))
        if path.parent.name == stem
    )


def build(stem: str) -> str:
    document = parse_file(shipped(stem, ".nml"))
    return stub(
        resolve(
            document,
            package=f"navml.widgets.{stem}",
            sibling=Sibling.read(shipped(stem, ".py")),
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
    """Both halves of *this* component, which is not the same as both bases.

    An inherited member is not restated: ``disabled`` is declared by
    ``Control`` and a checker reads it from there, so what this stub owes is
    the markup's ids and properties plus the hand-written half's own methods.
    """
    source = build("button")
    assert "caption: StaticText" in source          # the markup's
    assert "text: str" in source                    # the markup's, too
    assert "async def press(self) -> bool: ..." in source   # the Python half's
    assert "class Button(Control, _Component):" in source   # and the base it names


def test_the_event_class_beside_a_component_is_part_of_the_module():
    assert "class ClickEvent(Event): ..." in build("button")


def test_a_hand_written_constructor_wins():
    assert "def __init__(self, text: str = ..., **kwargs: Any)" in build("button")


def test_a_derived_component_keeps_both_bases():
    assert "class Dialog(Modal, _Component):" in build("dialog")


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
        "from navml.widgets.dialog.label import Label\n\n"
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


# -- a hand-written half split into mixins -----------------------------------


def _with_mixin(tmp_path, mixin: str, own: str = "") -> str:
    (tmp_path / "copying.py").write_text(mixin, encoding="utf-8")
    (tmp_path / "widget.py").write_text(
        "from .copying import Copying\n"
        "from navkit.widget import Widget\n"
        f"{own}"
        "class Panel(Copying, Widget):\n"
        "    def own(self) -> int: ...\n",
        encoding="utf-8",
    )
    return stub(
        resolve(
            parse("Panel:\n", filename="widget.nml"),
            sibling=Sibling.read(tmp_path / "widget.py"),
        )
    )


def test_a_stub_lists_a_mixin_s_methods_as_the_class_s_own(tmp_path):
    """Flattened: the stub keeps one base, so a mixin typed against it has no cycle."""
    text = _with_mixin(
        tmp_path,
        "from pathlib import Path\n"
        "class Copying:\n"
        "    async def copy_files(self, target: Path) -> None: ...\n",
    )
    ast.parse(text)
    assert "async def copy_files(self, target: Path) -> None: ..." in text
    assert "def own(self) -> int: ..." in text
    assert "from pathlib import Path" in text
    assert "Copying" not in text


def test_a_mixin_may_not_import_a_name_as_something_else(tmp_path):
    with pytest.raises(ValueError, match="have to agree"):
        _with_mixin(
            tmp_path,
            "from os import path as Path\nclass Copying:\n    pass\n",
            own="from pathlib import Path\n",
        )


def test_a_mixin_may_not_shadow_a_name_the_module_imports(tmp_path):
    """``from .terminal import Terminal`` after a command ``Terminal`` rebinds it for the whole module."""
    (tmp_path / "terminal.py").write_text("class Terminal:\n    pass\n", encoding="utf-8")
    (tmp_path / "widget.py").write_text(
        "from commands import Terminal\n"
        "from .terminal import Terminal\n"
        "from navkit.widget import Widget\n"
        "class Panel(Terminal, Widget):\n    pass\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="shadow"):
        Sibling.read(tmp_path / "widget.py")


def test_a_stub_keeps_a_constant_moved_out_with_its_mixin(tmp_path):
    text = _with_mixin(
        tmp_path,
        "class Copying:\n    LIMIT = 3\n    MODE: str = 'fast'\n    def copy(self) -> None: ...\n",
    )
    assert "    LIMIT: _Any" in text
    assert "    MODE: str" in text
