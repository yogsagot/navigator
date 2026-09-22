"""The descriptor an ``alias`` line compiles to.

``navml/_alias.py`` alone: no document, no generator, no markup.  Every widget
here is built by hand, the way the generated ``__init__`` would build it, so a
failure in this file is a failure of the forwarding itself.
"""

from __future__ import annotations

import pytest

from navkit.reactive import (
    Binding,
    ReactiveError,
    ReactiveTypeError,
    bind,
    computed,
    effect,
    is_bound,
    peek,
    reactive,
    unbind,
)
from navkit.widget import Widget

from navml._alias import _Alias


class Label(Widget):
    text: str = reactive("")
    align: str = reactive("left")

    @computed
    def shouted(self) -> str:
        return self.text.upper()


class Panel(Widget):
    """The shape a generated component has: an id, and an alias through it."""

    title: str = _Alias("header", "text")
    heading: str = _Alias("header", "shouted")
    label_align: str = _Alias("header", "align")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.header = Label(parent=self)


class Outer(Widget):
    """An alias onto a component that itself aliases -- one hop further."""

    caption: str = _Alias("inner", "title")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.inner = Panel(parent=self)


# -- the forwarding ----------------------------------------------------------


def test_a_read_reaches_the_target():
    panel = Panel()
    panel.header.text = "Files"
    assert panel.title == "Files"


def test_a_write_reaches_the_target():
    panel = Panel()
    panel.title = "Files"
    assert panel.header.text == "Files"


def test_a_read_through_an_alias_is_tracked():
    """The target's descriptor captures the dependency, so nothing here does."""
    panel = Panel()
    seen = []
    effect(panel, lambda p: seen.append(p.title))
    panel.header.text = "Files"
    from navkit.reactive import flush_effects

    flush_effects()
    assert seen == ["", "Files"]


def test_an_alias_reaches_through_another_alias():
    outer = Outer()
    outer.caption = "Files"
    assert outer.inner.header.text == "Files"
    assert outer.caption == "Files"


def test_a_write_keeps_the_target_s_type_check():
    panel = Panel()
    with pytest.raises(ReactiveTypeError) as caught:
        panel.title = 3
    assert "Panel.title -> header.text" in str(caught.value)


def test_the_class_attribute_is_the_declaration():
    # What `unbind(panel, Panel.title)' and its two siblings check.
    assert isinstance(Panel.title, _Alias)
    assert Panel.title.name == "title"
    assert Panel.title.declaring_class is Panel


# -- bindings ----------------------------------------------------------------


def test_a_binding_is_called_with_the_aliasing_widget():
    """The whole reason :meth:`Binding.owned_by` exists.

    Both widgets have a ``width``, so an expression handed the wrong one
    computes a number rather than raising.
    """
    panel = Panel(width=40)
    panel.header.width = 4
    panel.title = bind(lambda o: f"{o.width}")
    assert panel.header.text == "40"


def test_a_binding_through_an_alias_recomputes():
    panel = Panel(width=40)
    panel.title = bind(lambda o: f"{o.width}")
    panel.width = 12
    assert panel.header.text == "12"


def test_a_binding_through_a_chain_is_owned_by_the_outermost():
    outer = Outer(width=7)
    outer.inner.width = 3
    outer.inner.header.width = 1
    outer.caption = bind(lambda o: f"{o.width}")
    assert outer.inner.header.text == "7"


def test_the_comparator_comes_along():
    calls = []

    def same(a, b):
        calls.append((a, b))
        return a == b

    panel = Panel(width=40)
    panel.title = Binding(lambda o: f"{o.width}", same)
    assert panel.header.text == "40"
    panel.width = 40
    assert panel.header.text == "40"
    assert calls


def test_is_bound_and_unbind_reach_the_target_s_cell():
    panel = Panel()
    assert not is_bound(panel, Panel.title)
    panel.title = bind(lambda o: "bound")
    assert is_bound(panel, Panel.title)
    assert is_bound(panel.header, Label.text)
    unbind(panel, Panel.title)
    assert not is_bound(panel, Panel.title)
    assert panel.header.text == "bound"


def test_peek_reads_without_subscribing():
    panel = Panel()
    panel.header.text = "Files"
    assert peek(panel, Panel.title) == "Files"


# -- what it refuses, and how it says so -------------------------------------


def test_a_computed_target_refuses_a_write_naming_both_ends():
    """navkit's own refusal, restated.

    It is an ``AttributeError`` rather than a ``ReactiveError`` because that is
    what ``Computed.__set__`` raises, and the type is carried through rather
    than flattened: the alias adds the two names and nothing else.  The
    generator refuses this pair when the document is compiled, so reaching it
    at run time means somebody wrote the alias by hand.
    """
    panel = Panel()
    with pytest.raises(AttributeError) as caught:
        panel.heading = "Files"
    assert "Panel.heading -> header.shouted" in str(caught.value)


def test_an_attribute_that_is_not_reactive_says_so():
    class Bare(Widget):
        title: str = _Alias("header", "not_reactive")

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.header = Label(parent=self)

    bare = Bare()
    with pytest.raises(ReactiveError) as caught:
        is_bound(bare, Bare.title)
    assert "not_reactive is not a reactive attribute of Label" in str(caught.value)
    assert "Bare.title -> header.not_reactive" in str(caught.value)


def test_a_target_that_is_not_there_yet_says_that():
    class Early(Widget):
        title: str = _Alias("header", "text")

    early = Early()
    with pytest.raises(ReactiveError) as caught:
        early.title
    assert "Early.title -> header.text" in str(caught.value)
    assert "__init__" in str(caught.value)


def test_the_repr_names_both_ends():
    assert repr(Panel.title) == "<alias Panel.title -> header.text>"
