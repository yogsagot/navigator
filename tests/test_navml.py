"""The two halves of a component, and the import machinery that joins them.

A component is markup, or Python, or both, and nothing importing one can tell
which.  These tests pin that interchangeability first, because it is the
property every other decision in ``navml/DESIGN.md`` was taken to protect, and
then the guards -- each of which exists because the failure it catches is
silent rather than loud.

The four components under ``navml/widgets`` are one per shape: ``Spacer`` is
Python alone, ``Label`` is markup alone, ``Button`` is both, and
``FramedButton`` is both *and* derived from a component that is itself both.
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
from navkit.reactive import declarations
from navkit.stylesheet import parse
from navkit.widget import Widget
from navml._merge import ComponentError, ComponentFinder
from navml.widgets import Button, FramedButton, Label, Spacer
from navml.widgets import button as button_module
from navml.widgets import label as label_module
from navml.widgets import spacer as spacer_module


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
        ("navml.widgets.label", "Label"),         # markup alone
        ("navml.widgets.button", "Button"),       # both
        ("navml.widgets.framed_button", "FramedButton"),
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
    assert button_module.__loader__.get_source("navml.widgets.button")
    assert button_module.__loader__.get_code("navml.widgets.button") is not None
    assert inspect.getsource(Button).startswith("class Button(Widget):")


def test_a_markup_only_component_is_sourced_from_its_generated_half():
    """``inspect`` resolves a class through ``sys.modules[__module__].__file__``.

    So the public module has to point at the file that really holds the class,
    and the class has to be re-homed onto the public name.
    """
    assert label_module.__file__.endswith("label_nml.py")
    assert Label.__module__ == "navml.widgets.label"
    assert inspect.getsource(Label).startswith("class Label(_Widget):")


# -- what the splice produces ------------------------------------------------


def test_the_generated_class_is_the_base():
    """Both halves are called ``Button``; only the module names differ.

    Keeping the name means a sheet's ``Button { }`` reads the same whether or
    not a component has a hand-written half.
    """
    generated = importlib.import_module("navml.widgets.button_nml")
    assert [c.__name__ for c in Button.__mro__] == [
        "Button", "Button", "Widget", "object"
    ]
    assert Button.__mro__[1] is generated.Button
    assert Button is not generated.Button


def test_ids_are_live_before_any_hand_written_line_runs():
    """``super().__init__()`` builds the tree, so the next line may use it."""
    button = Button(text="OK", width=20, height=3)
    assert isinstance(button.caption, Label)
    assert button.caption.text == "OK"          # the hand-written __init__ set it
    assert button.caption.width == 18           # and the markup's binding followed


def test_a_binding_written_in_markup_keeps_following():
    button = Button(text="OK", width=20, height=3)
    button.text = "Cancel"
    assert button.caption.text == "Cancel"
    button.width = 40
    assert button.caption.width == 38


def test_declarations_spans_both_halves():
    """The rewriter's ``own`` set and ``unbind``/``is_bound`` both need this."""
    found = declarations(Button)
    assert "text" in found                       # declared by the markup half
    assert "pressed" in found                    # declared by the hand-written half
    assert "width" in found                      # inherited from Widget


# -- inheritance -------------------------------------------------------------


def test_a_component_may_derive_from_a_component():
    assert [c.__name__ for c in FramedButton.__mro__] == [
        "FramedButton", "FramedButton", "Button", "Button", "Widget", "object"
    ]


def test_each_half_of_each_level_builds_its_tree_exactly_once():
    """The reason the children are constructed in ``__init__``.

    A shared ``_build()`` would resolve to the *derived* class from the base's
    constructor, so the base's children would never be built and the derived
    one's would be built twice.  ``super().__init__()`` chaining gets the order
    right with no mechanism at all.
    """
    framed = FramedButton(text="Save", width=30, height=4)
    assert len(framed.children) == 2
    assert framed.children[0] is framed.caption   # the base's tree, first
    assert framed.children[1] is framed.hint      # then the derived one's
    assert framed.caption.text == "Save"
    assert framed.hint.text == "[enter]"


def test_a_type_selector_reaches_through_the_splice():
    """Two classes named ``Button`` sit in the MRO; a sheet must not notice.

    ``_is_a`` walks the MRO matching ``__name__``, and ``any()`` short-circuits,
    so the duplicate matches once rather than twice -- and a rule written for
    the base component still reaches the derived one.
    """
    framed = FramedButton(width=10, height=4)
    framed._stylesheet = parse("Button { bg: blue }")
    assert framed.style.bg == 4


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


def _imports_of_markup(source: str) -> dict[str, str]:
    """The same, for a document -- whose import block ends at the root block.

    Read with Python's own grammar rather than a grammar of navml's: the lines
    are Python and the generator copies them through untouched.
    """
    bound: dict[str, str] = {}
    for line in source.splitlines():
        if not line.strip():
            continue
        try:
            node = ast.parse(line).body[0]
        except SyntaxError:
            break  # the root block: `Button(Widget):' is not Python
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            break
        bound |= _bound(node)
    return bound


@pytest.mark.parametrize("component", ["label", "button", "framed_button"])
def test_the_markup_imports_what_its_generated_half_imports(component):
    """The two halves must not drift while the generator is a stand-in.

    A document's imports are copied into the generated module verbatim, so the
    document's bound names are exactly the generated module's non-underscored
    ones.
    """
    markup = _imports_of_markup((WIDGETS / f"{component}.nml").read_text())
    generated = _imports_of_python((WIDGETS / f"{component}_nml.py").read_text())
    supplied = {n for n in generated if n.startswith("_")}
    assert set(markup) == set(generated) - supplied - {"annotations"}


@pytest.mark.parametrize("component", ["label", "button", "framed_button"])
def test_the_generator_s_machinery_is_underscored(component):
    """So that a document may import any name at all -- there is no reserved word.

    Markup never names ``Widget``: a bare ``Label:`` head is what asks for it,
    and ``Label(X):`` names something the document imported.  So the generator
    takes ``_Widget`` for itself along with the rest of its machinery, and a
    document that imports its own ``Widget`` gets exactly that.
    """
    bound = _imports_of_python((WIDGETS / f"{component}_nml.py").read_text())
    assert "_Widget" in bound
    supplied = {"Widget", "bind", "reactive", "is_bound", "Any", "Surface"}
    assert not supplied & set(bound)


@pytest.mark.parametrize("component", ["label", "button", "framed_button"])
def test_every_markup_line_reference_points_at_a_real_line(component):
    """The trailing ``# button.nml:12`` is how a reader gets back to the markup.

    It is also the thing an edit to the markup silently invalidates, which is
    why it is checked rather than trusted.
    """
    lines = (WIDGETS / f"{component}.nml").read_text().splitlines()
    generated = (WIDGETS / f"{component}_nml.py").read_text()
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
    """
    script = (
        "import sys, importlib\n"
        "importlib.import_module('navml.widgets.label')\n"
        "print(' '.join(sorted(m for m in sys.modules "
        "if m.startswith('navml.widgets.'))))\n"
    )
    loaded = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    ).stdout.split()
    assert loaded == ["navml.widgets.label", "navml.widgets.label_nml"]


def test_a_component_still_pulls_in_the_ones_it_really_uses():
    script = (
        "import sys, importlib\n"
        "importlib.import_module('navml.widgets.framed_button')\n"
        "print(' '.join(sorted(m for m in sys.modules "
        "if m.startswith('navml.widgets.'))))\n"
    )
    loaded = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    ).stdout.split()
    assert "navml.widgets.button" in loaded      # FramedButton's base
    assert "navml.widgets.label" in loaded       # and the Label both use
    assert "navml.widgets.spacer" not in loaded  # but nothing it does not


def test_the_lazy_re_exports_are_transparent():
    assert navml.widgets.Spacer is Spacer
    assert "Spacer" in dir(navml.widgets)
    assert navml.widgets.__all__ == ["Button", "FramedButton", "Label", "Spacer"]
    with pytest.raises(AttributeError, match="Nonexistent"):
        navml.widgets.Nonexistent


def test_the_finder_declines_everything_it_is_not_asked_about():
    """It sits on ``sys.meta_path``, so it is consulted for every import."""
    finder = ComponentFinder()
    assert finder.find_spec("json", None) is None
    assert finder.find_spec("navkit.widget", ["navkit"]) is None
    assert finder.find_spec("navml.widgets.button_nml", ["navml/widgets"]) is None
