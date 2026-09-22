"""Compiling the text right of a ``:``.

``navml/expression.py`` alone: a string in, a string out.  No document, no
widget tree, no imports of anything a document might name -- the compiler is
told what the widget declares and what ids exist, rather than looking them up.
"""

from __future__ import annotations

import pytest

from navml.errors import MarkupError
from navml.expression import compile_expression, compile_handler


def compiled(source, **kwargs):
    """The emitted right-hand side of a property line."""
    return compile_expression(source, **kwargs).value


# -- the resolution table ----------------------------------------------------


def test_self_is_the_owner():
    assert compiled("self.width // 3") == "_bind(lambda _o: _o.width // 3)"


def test_root_is_the_component():
    assert compiled("root.left_path") == "_bind(lambda _o: self.left_path)"


def test_parent_is_an_attribute_of_the_owner():
    assert compiled("parent.width // 2") == "_bind(lambda _o: _o.parent.width // 2)"


def test_a_declared_attribute_is_an_attribute_of_the_owner():
    assert compiled("entries", own={"entries"}) == "_bind(lambda _o: _o.entries)"


def test_an_id_is_an_attribute_of_the_component():
    assert compiled("left.width", ids={"left"}) == "_bind(lambda _o: self.left.width)"


def test_anything_else_is_left_to_the_module():
    assert compiled("max(0, 3)") == "max(0, 3)"


def test_the_widget_s_own_property_wins_over_an_id():
    """So adding an id elsewhere cannot change what an expression already meant."""
    assert (
        compiled("cursor", own={"cursor"}, ids={"cursor"})
        == "_bind(lambda _o: _o.cursor)"
    )


def test_only_the_leftmost_name_of_a_chain_is_rewritten():
    assert compiled("parent.width.bit_length()") == (
        "_bind(lambda _o: _o.parent.width.bit_length())"
    )


def test_an_assignment_target_is_not_rewritten():
    # Reachable only through a handler body; the ctx check is what stops it.
    assert compile_handler(
        "self.text = text", owner="_w1", own={"text"}
    ) == "_w1.text = _w1.text"


# -- scopes the expression opens itself --------------------------------------


def test_a_comprehension_target_stays_its_own():
    assert compiled("', '.join(e.name for e in entries)", own={"entries"}) == (
        "_bind(lambda _o: ', '.join((e.name for e in _o.entries)))"
    )


def test_a_nested_lambda_argument_shadows_a_property():
    assert compiled("(lambda entries: entries)(cursor)", own={"entries", "cursor"}) == (
        "_bind(lambda _o: (lambda entries: entries)(_o.cursor))"
    )


def test_a_walrus_target_is_a_local():
    """Even at the top level, where the prototype had no scope to record it."""
    result = compile_expression("(width := 3) + width", own={"width"})
    assert result.expression == "(width := 3) + width"
    assert result.rewritten is False


def test_a_comprehension_condition_is_inside_the_scope():
    assert compiled("[e for e in entries if e.name]", own={"entries"}) == (
        "_bind(lambda _o: [e for e in _o.entries if e.name])"
    )


# -- what the emitter decides by ---------------------------------------------


def test_a_literal_is_a_literal():
    result = compile_expression("0")
    assert (result.constant, result.rewritten) == (True, False)
    assert result.value == "0"


def test_an_expression_reading_nothing_is_not_a_binding():
    """A mutable default: a declaration makes it a ``factory``, a line a value."""
    result = compile_expression("[]")
    assert (result.constant, result.rewritten) == (False, False)
    assert result.value == "[]"


def test_reading_the_component_counts_as_a_read():
    assert compile_expression("root.width").rewritten is True


def test_the_binding_spelling_is_the_generated_module_s():
    assert compile_expression("parent.width").binding == (
        "_bind(lambda _o: _o.parent.width)"
    )


# -- handlers ----------------------------------------------------------------


def test_a_handler_closes_over_its_widget():
    assert compile_handler(
        "self.text = event.key", owner="self.caption", own={"text"}
    ) == "self.caption.text = event.key"


def test_the_event_is_the_one_name_the_handler_binds():
    assert compile_handler(
        "self.text = event.key", owner="_w1", own={"event", "text"}
    ) == "_w1.text = event.key"


def test_a_handler_body_reaches_the_component_through_root():
    assert compile_handler(
        "await root.show_info(event)", owner="self.info"
    ) == "await self.show_info(event)"


def test_a_handler_names_an_id_the_same_way_a_property_does():
    assert compile_handler(
        "self.text = left.path", owner="_w1", own={"text"}, ids={"left"}
    ) == "_w1.text = self.left.path"


def test_two_statements_are_refused():
    with pytest.raises(MarkupError) as caught:
        compile_handler("a = 1; b = 2", owner="_w1", line=12, filename="button.nml")
    assert str(caught.value) == "button.nml:12: a handler is one statement"


# -- failures name the document ----------------------------------------------


def test_a_malformed_expression_names_its_markup_line():
    with pytest.raises(MarkupError) as caught:
        compile_expression("parent.", line=7, filename="panel.nml")
    assert caught.value.line == 7
    assert caught.value.filename == "panel.nml"
