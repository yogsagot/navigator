"""The two halves of a component, and the import machinery that joins them.

A component is markup, or Python, or both, and nothing importing one can tell
which.  These tests pin that interchangeability first, because it is the
property every other decision in ``navml/DESIGN.md`` was taken to protect, and
then the guards -- each of which exists because the failure it catches is
silent rather than loud.

The components under ``navml/widgets`` are one per shape: ``Spacer`` is
Python alone, ``Field`` is markup alone, ``Button`` is both, and
``Dialog`` is both *and* derived from ``Modal``, which is itself both.
``Dialog`` is a fifth, on a different axis: it is the one whose *children*
raise the events its hand-written half handles, and it pins the
``on_<id>_<event>`` convention the generator has to emit for them.
"""

from __future__ import annotations

import ast
import importlib
import importlib.machinery
import importlib.util
import inspect
import pathlib
import re
import subprocess
import sys
import textwrap
from types import SimpleNamespace
from uuid import uuid4

import pytest

import navml
import navml.widgets
from navml import Component
from navkit.events import KeyEvent, MouseClickEvent, emitted
from navkit.reactive import declarations
from navkit.stylesheet import parse
from navkit.widget import Widget
from navml._merge import ComponentError, ComponentFinder
from navml.parser import imports_of
from conftest import awaited
from navml.widgets import (
    Button, Dialog, Field, Label, Modal, Spacer, StaticText, Window,
)
# The *component modules*, not their packages: a component is a directory whose
# `__init__.py' re-exports the class, so the questions these tests ask about a
# module -- its `__file__', its loader, where a class is re-homed -- are about
# the module one level in.
from navml.widgets.button import button as button_module
from navml.widgets.field import field as field_module
from navml.widgets.spacer import spacer as spacer_module


@pytest.fixture(autouse=True)
def _import_state():
    """Keep one test's import machinery out of the next one's.

    ``sys.path_importer_cache`` matters as much as the other two: ``FileFinder``
    caches a directory listing, so a package written after one has been taken is
    invisible until the cache is dropped.
    """
    meta_path, path = sys.meta_path[:], sys.path[:]
    registered = set(navml._merge._REGISTERED)
    yield
    sys.meta_path[:] = meta_path
    sys.path[:] = path
    for name in [n for n in sys.modules if n.startswith("navml_t")]:
        del sys.modules[name]
    navml._merge._REGISTERED.clear()
    navml._merge._REGISTERED.update(registered)
    sys.path_importer_cache.clear()
    importlib.invalidate_caches()


@pytest.fixture
def package(tmp_path, monkeypatch):
    """A throwaway component package, with a name no other test can reuse.

    A unique name rather than a purge: a leaked ``sys.modules`` entry then
    cannot satisfy the next test's import, which is cheaper than proving the
    purge was complete.
    """
    name = f"navml_t{uuid4().hex[:8]}"
    root = tmp_path / name
    root.mkdir()
    (root / "__init__.py").write_text("import navml\nnavml.register(__name__)\n")
    monkeypatch.syspath_prepend(str(tmp_path))

    def write(filename: str, source: str) -> None:
        (root / filename).write_text(textwrap.dedent(source).lstrip())

    def load(module: str):
        sys.path_importer_cache.clear()
        importlib.invalidate_caches()
        return importlib.import_module(f"{name}.{module}")

    return SimpleNamespace(name=name, path=root, write=write, load=load)


# -- the three shapes are one shape from outside -----------------------------


@pytest.mark.parametrize(
    "module, component",
    [
        ("navml.widgets.spacer", "Spacer"),       # Python alone
        ("navml.widgets.field", "Field"),         # markup alone
        ("navml.widgets.label", "Label"),         # both
        ("navml.widgets.button", "Button"),       # both
        ("navml.widgets.window", "Window"),
    ],
)
def test_every_shape_imports_the_same_way(module, component):
    """The consumer's line does not know which shape it is looking at."""
    imported = getattr(importlib.import_module(module), component)
    assert isinstance(imported, type) and issubclass(imported, Widget)
    assert imported.__name__ == component
    assert imported(width=10, height=3).width == 10


def test_a_python_only_component_is_not_navml_s_at_all():
    """No markup half, so the finder declines and the stock loader runs.

    This is the strongest form of the promise: an ordinary ``Widget`` subclass
    already is a component, and gaining a ``.nml`` later would not change a
    line of it.
    """
    assert type(spacer_module.__loader__) is importlib.machinery.SourceFileLoader
    assert Spacer.__mro__ == (Spacer, Widget, object)


def test_a_merged_component_keeps_one_truthful_source_file():
    """``__file__`` and friends name the file a human wrote, not a synthesis.

    This is what a loader executing two sources into one namespace gives up,
    and it is why the loader delegates to the real source loader instead.
    """
    assert button_module.__file__.endswith("button.py")
    assert button_module.__spec__.origin == button_module.__file__
    assert button_module.__loader__.get_source("navml.widgets.button.button")
    assert button_module.__loader__.get_code("navml.widgets.button.button") is not None
    assert inspect.getsource(Button).startswith("class Button(Control):")


def test_a_markup_only_component_is_sourced_from_its_generated_half():
    """``inspect`` resolves a class through ``sys.modules[__module__].__file__``.

    So the public module has to point at the file that really holds the class,
    and the class has to be re-homed onto the public name.
    """
    assert field_module.__file__.endswith("field_nml.py")
    assert Field.__module__ == "navml.widgets.field.field"
    assert inspect.getsource(Field).startswith("class Field(_Component):")


# -- what the splice produces ------------------------------------------------


def test_the_generated_class_is_the_base():
    """Both halves are called ``Button``; only the module names differ.

    Keeping the name means a sheet's ``Button { }`` reads the same whether or
    not a component has a hand-written half.
    """
    generated = importlib.import_module("navml.widgets.button.button_nml")
    assert [c.__name__ for c in Button.__mro__] == [
        "Button", "Button", "Control", "Component", "Widget", "object"
    ]
    assert Button.__mro__[1] is generated.Button
    assert Button is not generated.Button


def test_ids_are_live_before_any_hand_written_line_runs():
    """``super().__init__()`` builds the tree, so the next line may use it."""
    button = Button(text="OK", width=20, height=3)
    assert isinstance(button.caption, StaticText)
    assert button.caption.text == "OK"          # the hand-written __init__ set it
    assert button.caption.width == 17           # and the markup's binding followed


def test_a_binding_written_in_markup_keeps_following():
    button = Button(text="OK", width=20, height=3)
    button.text = "Cancel"
    assert button.caption.text == "Cancel"
    button.width = 40
    assert button.caption.width == 37


def test_declarations_spans_both_halves():
    """The rewriter's ``own`` set and ``unbind``/``is_bound`` both need this."""
    found = declarations(Button)
    assert "text" in found                       # declared by the markup half
    assert "disabled" in found                   # declared by the base, Control
    assert "width" in found                      # inherited from Widget


# -- inheritance -------------------------------------------------------------


def test_a_component_may_derive_from_a_component():
    """And ``Component`` appears once, however deep the chain gets.

    Every generated class names it, so a component derived from a component
    names it twice over -- and C3 puts it in one place, below the whole
    inheritance chain and above ``Widget``.  That is what makes it safe for the
    generator to emit it unconditionally, which it must: a component derived
    from a *Python-only* widget has no other way to stop ``Widget.layout``
    cascading into children the markup placed.
    """
    assert [c.__name__ for c in Dialog.__mro__] == [
        "Dialog", "Dialog", "Modal", "Modal",
        "Component", "Widget", "object",
    ]


def test_each_half_of_each_level_builds_its_tree_exactly_once():
    """The reason the children are constructed in ``__init__``.

    A shared ``_build()`` would resolve to the *derived* class from the base's
    constructor, so the base's children would never be built and the derived
    one's would be built twice.  ``super().__init__()`` chaining gets the order
    right with no mechanism at all.
    """
    dialog = Dialog(prompt="Save?", modal_width=40, modal_height=10)
    assert len(dialog.children) == 4
    assert dialog.children[0] is dialog.message   # the derived document's own
    assert dialog.children[1] is dialog.ok
    assert dialog.message.text == "Save?"

    # Modal declares no children at all, so this is also the proof that a
    # base with an empty tree costs the derived one nothing.
    assert dialog.title == ""


def test_a_type_selector_reaches_through_the_splice():
    """Two classes named ``Button`` sit in the MRO; a sheet must not notice.

    ``_is_a`` walks the MRO matching ``__name__``, and ``any()`` short-circuits,
    so the duplicate matches once rather than twice -- and a rule written for
    the base component still reaches the derived one.
    """
    dialog = Dialog(modal_width=20, modal_height=8)
    dialog.stylesheet = parse("Modal { bg: blue }")
    assert dialog.style.bg == 4


# -- the guards --------------------------------------------------------------


BASES = """
    from navkit.widget import Widget
    class Mid(Widget): pass
    class Other(Widget): pass
"""


def _markup_half(package, component="Thing", base="Mid"):
    package.write("bases.py", BASES)
    package.write(
        "thing_nml.py",
        f"""
        from {package.name}.bases import Mid, Other
        __navml_component__ = "{component}"
        class {component}({base}):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.built = True
        """,
    )


def test_a_loose_ancestor_is_allowed(package):
    """``Widget`` where the markup says ``Mid`` splices to the same MRO.

    So the rule that the hand-written half repeats the markup's base is a
    convention -- for interchangeability and for completion while the handlers
    are being written -- rather than something the mechanism can enforce.
    """
    _markup_half(package)
    package.write(
        "thing.py",
        """
        from navkit.widget import Widget
        class Thing(Widget): pass
        """,
    )
    Thing = package.load("thing").Thing
    assert [c.__name__ for c in Thing.__mro__[:4]] == ["Thing", "Thing", "Mid", "Widget"]
    assert Thing().built is True


def test_an_unrelated_base_is_refused(package):
    """CPython would not refuse it -- it drops the base and says nothing.

    Assigning ``__bases__`` over an unrelated class succeeds and leaves no
    trace of it in the MRO, which is the worst shape this failure can take, so
    the loader asks the question CPython does not.
    """
    _markup_half(package)
    package.write(
        "thing.py",
        f"""
        from {package.name}.bases import Other
        class Thing(Other): pass
        """,
    )
    with pytest.raises(ComponentError) as caught:
        package.load("thing")
    assert "Other" in str(caught.value) and "Mid" in str(caught.value)


def test_a_hand_written_half_with_no_widget_base_is_refused(package):
    """``class Thing:`` cannot be spliced at all.

    A class based only on ``object`` has a different solid base from one in the
    ``Widget`` lineage, so CPython rejects the assignment outright.  The message
    it gives says 'deallocator differs from object', which is true and useless;
    this is where it becomes advice.
    """
    _markup_half(package)
    package.write("thing.py", "class Thing: pass\n")
    with pytest.raises(ComponentError) as caught:
        package.load("thing")
    assert "class Thing(Mid)" in str(caught.value)


def test_a_hand_written_half_missing_the_component_is_refused(package):
    """Not a silent fall back to the markup-only shape."""
    _markup_half(package)
    package.write("thing.py", "VALUE = 1\n")
    with pytest.raises(ComponentError) as caught:
        package.load("thing")
    assert "does not define 'Thing'" in str(caught.value)


def test_a_generated_half_must_name_its_component(package):
    package.write("thing_nml.py", "from navkit.widget import Widget\n")
    package.write(
        "thing.py",
        """
        from navkit.widget import Widget
        class Thing(Widget): pass
        """,
    )
    with pytest.raises(ComponentError) as caught:
        package.load("thing")
    assert "__navml_component__" in str(caught.value)


def test_without_the_hook_the_hand_written_half_is_a_plain_widget(package):
    """What a by-path load gets, and how loudly it says so.

    pytest's assertion rewriter consults ``PathFinder`` directly and bypasses
    ``sys.meta_path``, so this is reachable -- which is why a component module
    must never be a test module, a ``conftest.py`` or a plugin.
    """
    _markup_half(package)
    package.write(
        "thing.py",
        f"""
        from {package.name}.bases import Mid
        class Thing(Mid):
            def caption_text(self):
                return self.caption.text
        """,
    )
    package.load("bases")
    spec = importlib.util.spec_from_file_location("raw", package.path / "thing.py")
    raw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(raw)

    assert raw.Thing.__mro__[1].__name__ == "Mid"     # no markup half underneath
    with pytest.raises(AttributeError):
        raw.Thing().caption_text()


# -- the markup-only shape, built from scratch -------------------------------


def test_a_markup_only_component_needs_no_hand_written_file(package):
    package.write(
        "leaf_nml.py",
        """
        from navkit.widget import Widget
        __navml_component__ = "Leaf"
        __all__ = ["Leaf"]
        class Leaf(Widget):
            pass
        """,
    )
    module = package.load("leaf")
    assert module.Leaf.__name__ == "Leaf"
    assert module.__file__.endswith("leaf_nml.py")
    assert module.Leaf.__module__ == f"{package.name}.leaf"
    assert module.__all__ == ["Leaf"]


def test_reloading_a_merged_component_splices_again(package):
    _markup_half(package)
    package.write(
        "thing.py",
        f"""
        from {package.name}.bases import Mid
        class Thing(Mid): pass
        """,
    )
    module = package.load("thing")
    reloaded = importlib.reload(module)
    assert [c.__name__ for c in reloaded.Thing.__mro__[:3]] == ["Thing", "Thing", "Mid"]


# -- what a document imports, and what the generator supplies ---------------


WIDGETS = pathlib.Path(navml.widgets.__file__).parent


def shipped(stem: str, suffix: str) -> pathlib.Path:
    """One file of a shipped component.

    A component is a directory whose files repeat its name, so the paths in
    here go through this rather than being spelled out.
    """
    return WIDGETS / stem / f"{stem}{suffix}"


def _bound(node: ast.Import | ast.ImportFrom) -> dict[str, str]:
    """The names one import statement binds.

    ``alias.asname or alias.name.split(".")[0]`` is the whole rule, and it is
    Python's: ``import navml.widgets`` binds ``navml``, which is why a document
    wanting ``Label:`` as a block head writes ``from ... import Label``.
    """
    where = getattr(node, "module", None) or ""
    return {alias.asname or alias.name.split(".")[0]: where for alias in node.names}


def _imports_of_python(source: str) -> dict[str, str]:
    """Every name the import block of a generated module binds."""
    bound: dict[str, str] = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue  # the module docstring
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            break
        bound |= _bound(node)
    return bound


def _imports_of_markup(path: pathlib.Path) -> dict[str, str]:
    """The same, for a document -- whose import block ends at the root block.

    Through the parser rather than a miniature of it kept here: ``imports_of``
    exists because ``navml build`` has to order a cold build by the import
    graph without executing anything, and a document's bound names are what
    that reads.  The lines are Python either way -- the generator copies them
    through untouched -- but there is now one reader of them.
    """
    return {name: line.module for line in imports_of(path) for name in line.names}


@pytest.mark.parametrize(
    "component", ["field", "label", "button", "static_text", "modal", "window", "dialog"]
)
def test_the_markup_imports_what_its_generated_half_imports(component):
    """The two halves must not drift while the generator is a stand-in.

    A document's imports are copied into the generated module verbatim, so the
    document's bound names are exactly the generated module's non-underscored
    ones.
    """
    markup = _imports_of_markup(shipped(component, ".nml"))
    generated = _imports_of_python(shipped(component, "_nml.py").read_text())
    supplied = {n for n in generated if n.startswith("_")}
    assert set(markup) == set(generated) - supplied - {"annotations"}


@pytest.mark.parametrize(
    "component", ["field", "label", "button", "static_text", "modal", "window", "dialog"]
)
def test_the_generator_s_machinery_is_underscored(component):
    """So that a document may import any name at all -- there is no reserved word.

    Markup never names the base a bare head asks for: ``Label:`` is what asks
    for it, and ``Label(X):`` names something the document imported.  So the
    generator takes ``_Component`` for itself along with the rest of its
    machinery, and a document that imports its own ``Component`` -- or its own
    ``Widget`` -- gets exactly that.
    """
    bound = _imports_of_python(shipped(component, "_nml.py").read_text())
    assert "_Component" in bound
    supplied = {"Component", "Widget", "bind", "reactive", "is_bound", "Any", "Surface"}
    assert not supplied & set(bound)


@pytest.mark.parametrize(
    "component", ["field", "label", "button", "static_text", "modal", "window", "dialog"]
)
def test_every_markup_line_reference_points_at_a_real_line(component):
    """The trailing ``# button.nml:12`` is how a reader gets back to the markup.

    It is also the thing an edit to the markup silently invalidates, which is
    why it is checked rather than trusted.
    """
    lines = (shipped(component, ".nml")).read_text().splitlines()
    generated = shipped(component, "_nml.py").read_text()
    found = re.findall(rf"# {component}\.nml:(\d+)", generated)
    assert found, "no markup references at all"
    for number in found:
        assert 1 <= int(number) <= len(lines), f"{component}.nml:{number} does not exist"
        assert lines[int(number) - 1].strip(), f"{component}.nml:{number} is blank"


# -- the package re-exports lazily ------------------------------------------


def test_importing_one_component_does_not_load_the_library(package):
    """What a cold build needs, and the regression that would break it.

    The generator reads ``declarations(cls)`` off the classes a document names,
    so generating a component really imports the ones it uses.  If the package
    re-exported eagerly, importing any one would import every one, and nothing
    could be generated until everything already had been.

    Three entries per component, not one: a component is a directory, so its
    package, its module and its generated module each get a slot.  **What this
    pins is the absence** -- ``button``, ``dialog``, ``window`` and
    ``spacer`` -- and that is untouched by the count going up.
    """
    script = (
        "import sys, importlib\n"
        "importlib.import_module('navml.widgets.field')\n"
        "print(' '.join(sorted(m for m in sys.modules "
        "if m.startswith('navml.widgets.'))))\n"
    )
    loaded = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    ).stdout.split()
    assert loaded == [
        "navml.widgets.control",          # the base both of Field's children
        "navml.widgets.control.control",  # derive from
        "navml.widgets.field",
        "navml.widgets.field.field",
        "navml.widgets.field.field_nml",
        "navml.widgets.input_line",
        "navml.widgets.input_line.input_line",
        "navml.widgets.input_line.input_line_nml",
        "navml.widgets.label",
        "navml.widgets.label.label",
        "navml.widgets.label.label_nml",
        "navml.widgets.static_text",      # Label's shortcut painter
        "navml.widgets.static_text.static_text",
        "navml.widgets.static_text.static_text_nml",
    ]


def test_a_component_still_pulls_in_the_ones_it_really_uses():
    script = (
        "import sys, importlib\n"
        "importlib.import_module('navml.widgets.dialog')\n"
        "print(' '.join(sorted(m for m in sys.modules "
        "if m.startswith('navml.widgets.'))))\n"
    )
    loaded = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    ).stdout.split()
    assert "navml.widgets.button" in loaded      # Dialog's buttons
    assert "navml.widgets.modal" in loaded       # and the base it derives
    assert "navml.widgets.spacer" not in loaded  # but nothing it does not


def test_the_lazy_re_exports_are_transparent():
    assert navml.widgets.Spacer is Spacer
    assert "Spacer" in dir(navml.widgets)
    assert navml.widgets.__all__ == [
        "Button", "CheckBoxes", "Cluster", "Control", "Desktop", "Dialog",
        "Field", "InputLine", "Label", "ListViewer", "Modal", "RadioButtons",
        "ScrollBar", "Spacer", "StaticText", "Window",
    ]
    with pytest.raises(AttributeError, match="Nonexistent"):
        navml.widgets.Nonexistent


def test_the_finder_declines_everything_it_is_not_asked_about():
    """It sits on ``sys.meta_path``, so it is consulted for every import."""
    finder = ComponentFinder()
    assert finder.find_spec("json", None) is None
    assert finder.find_spec("navkit.widget", ["navkit"]) is None
    assert finder.find_spec(
        "navml.widgets.button.button_nml", ["navml/widgets/button"]
    ) is None


def test_registering_a_library_covers_the_components_inside_it(package):
    """One ``navml.register`` call per widget library, not per component.

    A component is a directory, so the package a component module lives in is
    the component's own and never the one anybody registered.  The finder
    walks up the dotted name to find the library above it, which is what lets
    a component directory's ``__init__.py`` be a re-export and nothing else.
    """
    component = package.path / "leaf"
    component.mkdir()
    (component / "__init__.py").write_text(
        f"from {package.name}.leaf.leaf import Leaf\n", encoding="utf-8"
    )
    (component / "leaf_nml.py").write_text(
        "__navml_component__ = 'Leaf'\n"
        "__all__ = ['Leaf']\n"
        "from navkit.widget import Widget\n"
        "class Leaf(Widget):\n    pass\n",
        encoding="utf-8",
    )
    module = package.load("leaf")
    assert issubclass(module.Leaf, Widget)
    assert module.Leaf.__module__ == f"{package.name}.leaf.leaf"


def test_the_finder_never_claims_a_package(package):
    """**A component is a module.**

    A stale flat ``leaf_nml.py`` left beside a ``leaf/`` directory -- an
    untracked copy, or a native package upgrade that adds files without
    removing them -- would otherwise make the finder rebase whatever the
    directory re-exported onto a generated class from before the move.  CPython
    gives no warning for that; declining does.
    """
    component = package.path / "leaf"
    component.mkdir()
    (component / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    (package.path / "leaf_nml.py").write_text(
        "__navml_component__ = 'Leaf'\n__all__ = []\n", encoding="utf-8"
    )
    module = package.load("leaf")
    assert module.VALUE == 1          # the package, loaded by PathFinder
    assert hasattr(module, "__path__")


# -- a component with an event of its own -----------------------------------


def test_a_button_declares_the_event_it_emits():
    """The public surface navml's generator will check an ``on_click:`` line
    against, and the one a reader consults instead of hunting for emit calls."""
    from navml.widgets.button import ClickEvent

    assert emitted(Button) == {ClickEvent}
    assert ClickEvent.handler == "on_click"


@pytest.mark.parametrize("key", ["enter", "space"])
def test_both_keys_reach_the_same_handler(key):
    """Two routes, one thing they mean: a listener never learns which fired."""
    root = Widget()
    button = root.add(Button("OK"))
    seen = []

    async def on_click(event):
        seen.append(event)
        return True

    button.on_click = on_click
    assert awaited(button.on_key(KeyEvent(key))) is True
    assert len(seen) == 1


def test_a_mouse_press_reaches_the_same_handler_as_the_keys():
    root = Widget()
    button = root.add(Button("OK"))
    seen = []

    async def on_click(event):
        seen.append(event)
        return True

    button.on_click = on_click
    assert awaited(button.on_mouse_click(MouseClickEvent(0, 0, "left", "press"))) is True
    assert len(seen) == 1


def test_a_click_bubbles_to_an_ancestor_that_never_named_the_button():
    """Why an alias to a widget is not needed: a container catches what its
    children emit without reaching through them to connect anything."""
    from navml.widgets.button import ClickEvent

    root = Widget()
    box = root.add(Widget())
    button = box.add(Button("OK"))
    seen = []

    async def on_click(event):
        seen.append(type(event))
        return True

    root.on_click = on_click
    assert awaited(button.press()) is True
    assert seen == [ClickEvent]


def test_a_disabled_button_emits_nothing():
    """State is reactive, what happened is an event -- the division the whole
    mechanism rests on, with the two meeting in one method."""
    root = Widget()
    button = root.add(Button("OK"))
    seen = []

    async def on_click(event):
        seen.append(event)
        return True

    button.on_click = on_click
    button.disabled = True
    assert awaited(button.press()) is False
    assert seen == []


def test_a_derived_component_keeps_the_event_its_base_emits():
    """Through the four-deep merged MRO, which is the case only this repo has:
    Dialog, Dialog, Modal, Modal, then the shared base."""
    from navml.widgets.button import ClickEvent

    assert emitted(Button) == {ClickEvent}
    assert [c.__name__ for c in Dialog.__mro__][:5] == [
        "Dialog", "Dialog", "Modal", "Modal", "Component",
    ]


# -- a child's event reaches the hand-written half -------------------------
#
# ``Dialog`` has three buttons in it and never asks which one spoke: the
# generated half wires each id'd child to an ``on_<id>_<event>`` method, so the
# question is answered by the time ``dialog.py`` runs.  See *Which child it was
# is a question the generator answers* in navml/DESIGN.md.


def test_a_child_event_reaches_the_method_its_id_names():
    """``ok`` raises a ClickEvent and ``on_ok_click`` is what runs.

    The name is composed from the ``id:`` line and the handler navkit derives
    from the event class -- no registry, and no second naming rule.
    """
    dialog = Dialog()
    assert awaited(dialog.ok.press()) is True
    assert dialog.result is True


def test_an_unoverridden_stub_declines_and_the_click_carries_on():
    """The property the whole convention rests on.

    ``dialog.py`` overrides ``on_ok_click`` and leaves ``on_cancel_click``
    alone, so the generated stub answers for Cancel, returns False, and
    ``emit`` walks on to the dialog's own ``on_click``.  A stub nobody
    overrides costs nothing, which is what makes it safe for the generator to
    write one for every child without being told which are wanted.
    """
    dialog = Dialog()
    assert awaited(dialog.cancel.press()) is True
    assert dialog.result is None


def test_the_stub_is_on_the_generated_half_and_the_override_on_the_other():
    """Which is what makes the override work, and is the merge direction.

    The generated class is always the *base*, so a hand-written method of the
    same name wins without either half naming the other -- the same fact that
    lets a hand-written ``__init__`` call ``super().__init__()`` and find every
    id live.
    """
    handwritten = Dialog
    (generated,) = handwritten.__bases__

    assert "on_cancel_click" in vars(generated)
    assert "on_cancel_click" not in vars(handwritten)
    assert "on_ok_click" in vars(generated)
    assert "on_ok_click" in vars(handwritten)
    assert awaited(generated.on_ok_click(Dialog(), None)) is False


def test_an_explicit_markup_handler_suppresses_the_convention():
    """``info`` carries an ``on_click:`` line, so no stub is generated for it.

    Both would have assigned to ``self.info.on_click`` and one would have won
    silently, so the generator emits only the markup's.
    """
    dialog = Dialog()

    assert not hasattr(dialog, "on_info_click")
    assert dialog.info.on_click.__qualname__.endswith("__init__.<locals>._on_click")
    assert dialog.ok.on_click == dialog.on_ok_click


def test_a_markup_handler_consumes_whatever_its_body_returns():
    """``show_info`` returns None; the generated function supplies the True."""
    dialog = Dialog()

    assert awaited(dialog.show_info(None)) is None
    assert awaited(dialog.info.press()) is True
    assert dialog.prompt == "Enter accepts, Escape dismisses."


def test_every_generated_handler_is_async():
    """navkit refuses a synchronous one, and for a generated stub it refuses
    at class creation -- ``check_handlers`` scans ``vars(cls)`` for ``on_*``.
    That free check is what the ``on_*`` spelling buys here, and is why the
    *routed* method the markup calls is deliberately not spelled that way."""
    import asyncio

    (generated,) = Dialog.__bases__
    handlers = [
        value
        for name, value in vars(generated).items()
        if name.startswith("on_") and callable(value)
    ]
    assert handlers
    assert all(asyncio.iscoroutinefunction(h) for h in handlers)


def test_the_markup_names_every_composed_handler_the_python_half_defines():
    """The orphan check, run against the shipped component.

    A renamed ``id:`` would leave an ``on_<id>_<event>`` in ``dialog.py`` that
    nothing calls -- the method still there, the button silently dead.  The
    generator is specified to refuse that by parsing the sibling ``.py``; this
    asserts the shipped pair is consistent, which is the same question asked
    of the one document that exists.
    """
    markup = (shipped("dialog", ".nml")).read_text()
    ids = set(re.findall(r"^\s+id: (\w+)$", markup, re.M))
    assert ids == {"message", "ok", "cancel", "info"}

    source = (shipped("dialog", ".py")).read_text()
    composed = re.findall(r"async def on_(\w+)_click\(", source)
    assert composed, "the example is supposed to have one"
    for stem in composed:
        assert stem in ids, f"on_{stem}_click names no id in dialog.nml"


# -- the base every generated class shares ----------------------------------
#
# `navml/DESIGN.md`'s *Whether the generated half gets a base of its own* is
# answered yes, and these are the three things it holds.  The second is the
# one that unblocked the `Manager' conversion: `Widget.__init__' is
# keyword-only and closed, so without it a component could not be handed
# anything it declares.


def test_every_generated_class_shares_the_base():
    """And a Python-only component does not, which is the asymmetry.

    ``Component`` answers *built from markup*, never *is a component* --
    ``Spacer`` is a component and is not one.  It matters outside Python too:
    a type selector matches by class name walking the MRO, so ``Component { }``
    is a live ``.nss`` selector with exactly this membership.
    """
    assert issubclass(Label, Component) and issubclass(Dialog, Component)
    assert issubclass(Window, Component)
    assert not issubclass(Spacer, Component)


def test_the_generated_half_says_which_document_it_came_from():
    """Provenance had nowhere to live until the base existed."""
    assert Dialog.__navml_source__ == "dialog.nml"
    assert Label.__navml_source__ == "label.nml"
    assert not hasattr(Spacer, "__navml_source__")  # not a Component at all


def test_a_component_is_handed_what_it_declares_by_keyword():
    """A component's parameters are the properties it declares.

    Markup has no parameter list and grows none, so this is how a value gets
    in from outside -- and it has to happen before ``Widget.__init__``, which
    accepts none of them and would refuse the lot.
    """
    dialog = Dialog(prompt="Overwrite?", modal_width=30, modal_height=6)
    assert dialog.prompt == "Overwrite?"
    assert (dialog.width, dialog.height) == (30, 6)
    assert dialog.message.text == "Overwrite?"      # the markup binding followed


def test_a_keyword_naming_nothing_still_raises():
    """The split hands the mistakes on to the constructor that refuses them,
    so a typo fails at the call rather than being set as an attribute."""
    with pytest.raises(TypeError) as caught:
        Dialog(promt="Overwrite?")
    assert "promt" in str(caught.value)


def test_a_declared_property_reaches_through_the_splice(package):
    """Declared in markup, set by keyword, read from the hand-written half.

    The whole chain in one test, because each link was written separately: the
    generated class declares it, the shared base peels it out of ``kwargs``,
    and the hand-written half -- which is the *derived* class -- sees it live.
    """
    package.write(
        "thing_nml.py",
        """
        from typing import Any as _Any

        from navkit.reactive import reactive as _reactive

        from navml.component import Component as _Component

        __navml_component__ = "Thing"

        class Thing(_Component):
            caption: str = _reactive("")
            __navml_source__ = "thing.nml"
        """,
    )
    package.write(
        "thing.py",
        """
        from navkit.widget import Widget

        class Thing(Widget):
            def shout(self) -> str:
                return self.caption.upper()
        """,
    )
    thing = package.load("thing").Thing(caption="ready", width=4)
    assert thing.shout() == "READY"
    assert thing.width == 4


def test_the_base_sizes_only_itself():
    """``Widget.layout`` cascades into every child whose size is not bound,
    which is what a hand-written widget wants and what a generated one must
    not have -- markup has already said where each child goes."""
    button = Button()
    button.layout(80, 24)
    assert (button.width, button.height) == (80, 24)
    assert (button.caption.height) == 1        # its own, from markup

    # And the other half of the rule: a size the markup *bound* is stepped
    # around rather than overwritten, which is what stops a dialog becoming
    # full-screen the moment `overlay' adds it.
    dialog = Dialog()
    dialog.layout(80, 24)
    assert (dialog.width, dialog.height) == (50, 10)


def test_a_widget_markup_constructs_needs_no_constructor_argument():
    """A child block compiles to ``Type(parent=self)`` and nothing else, so a
    required positional argument is what keeps a widget out of a document."""
    for component in (Label, Button, Dialog, Modal, Window, StaticText, Spacer):
        assert component(parent=None) is not None
