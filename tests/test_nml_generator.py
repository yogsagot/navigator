"""Emitting the Python a document becomes.

``navml/generator.py``.  Every test here generates a module, executes it, and
asks the result questions -- the emitter's output is Python, so the honest way
to check it is to run it.  Byte equality against the files in
``navml/widgets/`` is not asserted here; that is ``navml build --check``'s job
once the shipped artefacts have been regenerated.
"""

from __future__ import annotations

import re

import pytest

from navkit.events import emitted
from navkit.reactive import declarations, is_bound
from navkit.widget import Widget

from navml.component import Component
from navml.generator import MARKER, generate
from navml.parser import parse, parse_file
from navml.resolve import resolve
from navml.sibling import Sibling

SHIPPED = ["label", "button", "framed_button", "dialog"]

def shipped(stem: str, suffix: str) -> str:
    """One file of a shipped component.

    A component is a directory whose files repeat its name, so every path in
    here goes through this rather than being spelled out -- the next layout
    question then has one place to answer.
    """
    return f"navml/widgets/{stem}/{stem}{suffix}"


def build(stem: str):
    """Generate one of the documents the repository ships."""
    document = parse_file(shipped(stem, ".nml"))
    resolved = resolve(
        document,
        package=f"navml.widgets.{stem}",
        sibling=Sibling.read(shipped(stem, ".py")),
    )
    return generate(resolved)


def run(source: str, filename: str = "<generated>") -> dict:
    """Execute a generated module and hand back its namespace."""
    namespace: dict = {"__name__": "generated"}
    exec(compile(source, filename, "exec"), namespace)
    return namespace


@pytest.fixture
def generated():
    """Generate one document written inline, with no hand-written half."""

    def make(text: str, name: str = "widget"):
        document = parse(text, filename=f"{name}.nml")
        source = generate(resolve(document))
        return source, run(source, f"{name}_nml.py")

    return make


# -- the documents the repository ships --------------------------------------


@pytest.mark.parametrize("stem", SHIPPED)
def test_every_shipped_document_generates_and_runs(stem):
    assert build(stem).startswith(MARKER)
    run(build(stem), f"{stem}_nml.py")


@pytest.mark.parametrize("stem", SHIPPED)
def test_the_module_says_which_class_the_loader_wants(stem):
    namespace = run(build(stem))
    name = namespace["__navml_component__"]
    assert name in namespace["__all__"]
    assert isinstance(namespace[name], type)


@pytest.mark.parametrize("stem", SHIPPED)
def test_the_generated_class_says_where_it_came_from(stem):
    namespace = run(build(stem))
    component = namespace[namespace["__navml_component__"]]
    assert component.__navml_source__ == f"{stem}.nml"


def test_a_bare_head_extends_the_shared_base():
    namespace = run(build("label"))
    assert namespace["Label"].__bases__ == (Component,)


def test_a_named_base_keeps_the_shared_base_beside_it():
    """A component derived from a Python-only widget still needs it."""
    from navml.widgets.button import Button

    namespace = run(build("framed_button"))
    assert namespace["FramedButton"].__bases__ == (Button, Component)


def test_generation_is_stable():
    """``--check`` compares text, so twice must mean once."""
    assert build("dialog") == build("dialog")


# -- the tree it builds ------------------------------------------------------


def test_ids_are_live_by_the_time_the_constructor_returns():
    from navml.widgets.label import Label

    button = run(build("button"))["Button"]()
    assert isinstance(button.caption, Label)
    assert button.caption.parent is button


def test_a_binding_keeps_following():
    button = run(build("button"))["Button"](width=40)
    assert button.caption.width == 38
    button.width = 10
    assert button.caption.width == 8


def test_a_literal_is_not_a_binding():
    """Which it can be, now that a generated class does not cascade its size."""
    button = run(build("button"))["Button"]()
    assert not is_bound(button.caption, Widget.height)
    assert button.caption.height == 1


def test_every_widget_is_constructed_before_any_property_is_installed():
    source = build("dialog")
    body = source.split("def __init__")[1]
    constructions = [i for i, l in enumerate(body.splitlines()) if "(parent=" in l]
    installs = [i for i, l in enumerate(body.splitlines()) if ".x = " in l]
    assert max(constructions) < min(installs)


# -- what a child's event reaches --------------------------------------------


def test_a_stub_is_written_for_every_id_and_event():
    dialog = run(build("dialog"))["Dialog"]
    assert dialog.on_ok_click.__name__ == "on_ok_click"
    assert dialog.on_cancel_click.__name__ == "on_cancel_click"


def test_an_explicit_markup_line_suppresses_the_stub():
    dialog = run(build("dialog"))["Dialog"]
    assert not hasattr(dialog, "on_info_click")


def test_a_stub_declines():
    import asyncio

    dialog = run(build("dialog"))["Dialog"]()
    assert asyncio.run(dialog.on_ok_click(None)) is False


def test_the_stub_is_wired_to_the_child():
    dialog = run(build("dialog"))["Dialog"]()
    assert dialog.ok.on_click == dialog.on_ok_click


def test_every_generated_handler_is_async():
    """navkit refuses a synchronous one, and checks at class creation."""
    import inspect

    dialog = run(build("dialog"))["Dialog"]
    assert inspect.iscoroutinefunction(dialog.on_ok_click)


# -- the declarations --------------------------------------------------------


def test_a_property_becomes_a_reactive_declaration(generated):
    _, namespace = generated("Panel:\n    property text: \"\"\n")
    assert "text" in declarations(namespace["Panel"])
    assert namespace["Panel"]().text == ""


def test_a_mutable_default_is_a_factory(generated):
    """Two instances must not share one list."""
    _, namespace = generated("Panel:\n    property entries: []\n")
    first, second = namespace["Panel"](), namespace["Panel"]()
    assert first.entries is not second.entries


def test_a_derived_property_is_a_binding_installed_in_init(generated):
    source, namespace = generated("Panel:\n    property half: self.width // 2\n")
    assert "half = _reactive()" in source
    panel = namespace["Panel"](width=40)
    assert panel.half == 20


def test_a_doc_comment_survives_the_move_into_markup(generated):
    source, _ = generated(
        "Panel:\n    #: Whether the console is up.\n    property shown: False\n"
    )
    assert "#: Whether the console is up." in source


def test_a_style_property_is_declared_as_one(generated):
    source, namespace = generated(
        "Panel:\n    style_property icons: auto | none\n"
    )
    assert "_StyleProperty('auto', values=('auto', 'none'))" in source
    assert namespace["Panel"]().icons == "auto"


def test_an_alias_forwards(generated):
    _, namespace = generated(
        "from navml.widgets.label import Label\n\n"
        "Panel:\n    alias title: cap.text\n\n    Label:\n        id: cap\n"
    )
    panel = namespace["Panel"]()
    panel.title = "Files"
    assert panel.cap.text == "Files"


def test_an_event_declared_in_markup_lands_beside_the_component(generated):
    _, namespace = generated("Panel:\n    event Accepted\n")
    assert emitted(namespace["Panel"]) == frozenset({namespace["Accepted"]})
    assert namespace["Accepted"].handler == "on_accepted"


def test_a_style_block_becomes_one_inline_style(generated):
    _, namespace = generated("Panel:\n    style:\n        bg: red\n        fg: white\n")
    assert namespace["Panel"]().inline_style == "bg: red; fg: white"


# -- what the markup handler compiles to -------------------------------------


def test_a_markup_handler_is_a_one_statement_async_def(generated):
    source, namespace = generated(
        "from navml.widgets.label import Label\n\n"
        "Panel:\n    Label:\n        id: cap\n        on_key: self.text = event.key\n"
    )
    assert "async def _on_key(event):" in source
    assert "self.cap.text = event.key" in source


def test_a_markup_handler_always_consumes(generated):
    import asyncio

    from navkit.events import KeyEvent

    _, namespace = generated(
        "from navml.widgets.label import Label\n\n"
        "Panel:\n    Label:\n        id: cap\n        on_key: self.text = event.key\n"
    )
    panel = namespace["Panel"]()
    assert asyncio.run(panel.cap.on_key(KeyEvent("a", char="a"))) is True
    assert panel.cap.text == "a"


# -- the source map ----------------------------------------------------------


@pytest.mark.parametrize("stem", SHIPPED)
def test_every_line_reference_points_at_a_real_line(stem):
    document = open(shipped(stem, ".nml")).read().splitlines()
    cited = re.findall(rf"# {stem}\.nml:(\d+)", build(stem))
    assert cited
    for number in cited:
        assert 1 <= int(number) <= len(document)
        assert document[int(number) - 1].strip()


@pytest.mark.parametrize("stem", SHIPPED)
def test_the_generated_module_imports_what_the_document_imports(stem):
    document = parse_file(shipped(stem, ".nml"))
    namespace = run(build(stem))
    bare = {
        name
        for name in namespace
        if not name.startswith("_") and name not in {"annotations"}
    }
    assert set(document.bound) <= bare


@pytest.mark.parametrize("stem", SHIPPED)
def test_the_generator_s_machinery_is_underscored(stem):
    """So a document may import any name at all and get what it asked for."""
    namespace = run(build(stem))
    for taken in ("Component", "Widget", "bind", "reactive", "Any", "StyleProperty"):
        assert taken not in namespace
    assert "_Component" in namespace
