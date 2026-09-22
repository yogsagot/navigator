"""Reading the hand-written half without importing it.

``navml/sibling.py`` alone.  Everything here is about *spelling*: the module
resolves nothing and imports nothing, which is what keeps the generated half a
pure function of the markup and what makes a cold build possible.
"""

from __future__ import annotations

import pytest

from navml.sibling import Sibling


@pytest.fixture
def written(tmp_path):
    """Write a ``.py`` and read it back the way the generator would."""

    def write(source: str, name: str = "widget.py") -> Sibling:
        path = tmp_path / name
        path.write_text(source, encoding="utf-8")
        return Sibling.read(path)

    return write


# -- the shipped components --------------------------------------------------


def test_the_component_class_is_found_by_name():
    sibling = Sibling.read("navml/widgets/button.py")
    button = sibling.component("Button")
    assert button.bases == ("Widget",)
    assert button.emits == ("ClickEvent",)


def test_a_helper_class_beside_the_component_is_read_too():
    """Which is how ``event`` declared in both halves is caught."""
    sibling = Sibling.read("navml/widgets/button.py")
    assert "ClickEvent" in sibling.classes


def test_a_handler_says_whether_it_is_async():
    dialog = Sibling.read("navml/widgets/dialog.py").component("Dialog")
    assert dialog.methods["show_info"].is_async is True
    assert dialog.methods["render"].is_async is False


def test_a_reactive_declared_in_the_hand_written_half_is_reported():
    """The markup cannot see these, so a collision has to be reported."""
    button = Sibling.read("navml/widgets/button.py").component("Button")
    assert "enabled" in button.reactive


def test_a_component_with_no_hand_written_half_reads_as_nothing():
    assert Sibling.read("navml/widgets/field.py") is None


# -- the shapes it has to get right ------------------------------------------

def test_the_import_block_is_reported_by_bound_name(written):
    sibling = written(
        "import os.path\n"
        "from navkit.widget import Widget as W\n"
    )
    assert sorted(sibling.imports) == ["W", "os"]


def test_emits_is_read_off_the_class_body(written):
    sibling = written("class A:\n    emits = (ClickEvent, KeyEvent)\n")
    assert sibling.component("A").emits == ("ClickEvent", "KeyEvent")


def test_an_annotated_reactive_is_read(written):
    sibling = written("class A:\n    enabled: bool = reactive(True)\n")
    assert sibling.component("A").reactive == {"enabled": 2}


def test_a_qualified_reactive_is_read(written):
    sibling = written("class A:\n    enabled = navkit.reactive(True)\n")
    assert "enabled" in sibling.component("A").reactive


def test_something_that_is_not_a_reactive_call_is_not_one(written):
    sibling = written("class A:\n    enabled = staticmethod(lambda: True)\n")
    assert sibling.component("A").reactive == {}


def test_a_nested_class_is_not_a_module_level_one(written):
    """Only what the loader could splice is of interest."""
    sibling = written("class A:\n    class Inner:\n        pass\n")
    assert sorted(sibling.classes) == ["A"]


def test_a_missing_file_is_one_of_the_three_shapes(tmp_path):
    assert Sibling.read(tmp_path / "absent.py") is None


def test_a_broken_python_file_complains_as_python(written):
    with pytest.raises(SyntaxError):
        written("class A(:\n")
