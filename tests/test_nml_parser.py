"""Reading a ``.nml`` document, and refusing one that cannot be read.

The parser is the half of the toolchain that imports nothing: it answers what a
document says about itself and leaves every question needing a live class to
the code generator.  So these tests need no widget tree, no application and no
components -- a string in, a node graph or a :class:`~navml.errors.MarkupError`
out.

Two things are pinned harder than the rest, because they are the ones a later
change could break silently.  The four shipped documents under
``navml/widgets`` must parse into exactly the structure their hand-written
``*_nml.py`` halves were written from, and **every ``# button.nml:12`` comment
in those files must name a line the parser actually found a node at** -- that
convention is how a reader gets from a traceback back to the markup, and it is
worthless if the two drift.  The refusals each assert a line number as well as
a message, because a message with the wrong line sends its reader to the wrong
place.
"""

from __future__ import annotations

import pathlib
import re

import pytest

from navml.errors import MarkupError
from navml.parser import (
    AliasDecl,
    EventDecl,
    PropertyDecl,
    StylePropertyDecl,
    imports_of,
    parse,
    parse_file,
)

WIDGETS = pathlib.Path(__file__).resolve().parent.parent / "navml" / "widgets"

SHIPPED = ["label", "button", "framed_button", "dialog"]


def fails(text: str) -> MarkupError:
    """The error *text* raises, for a test that wants to read it."""
    with pytest.raises(MarkupError) as caught:
        parse(text, filename="t.nml")
    return caught.value


# -- the documents the repository ships -------------------------------------


@pytest.mark.parametrize("component", SHIPPED)
def test_every_shipped_document_parses(component):
    """The four are one per shape, and they are the only real markup there is."""
    document = parse_file(WIDGETS / f"{component}.nml")
    assert document.filename == f"{component}.nml"
    assert document.root.type


def test_the_root_block_declares_a_component():
    """A bare head extends ``Widget``; a parenthesised one names what it extends."""
    assert parse_file(WIDGETS / "button.nml").root.base is None
    assert parse_file(WIDGETS / "framed_button.nml").root.base == "Button"


def test_the_dialog_is_read_the_way_its_generated_half_was_written():
    """The richest document, against the file hand-written from it.

    ``dialog_nml.py`` is the agreed output, so matching it is the strongest
    regression available before the generator exists.
    """
    document = parse_file(WIDGETS / "dialog.nml")
    assert [line.names for line in document.imports] == [("Button",), ("Label",)]
    assert [d.name for d in document.root.declarations] == ["prompt"]
    assert list(document.ids()) == ["message", "ok", "cancel", "info"]

    blocks = {block.id: block for block in document.root.walk() if block.id}
    assert [b.type for b in document.root.children] == ["Label", "Button", "Button", "Button"]
    assert dict(
        (p.name, p.expression) for p in blocks["message"].properties
    ) == {
        "x": "1",
        "y": "1",
        "width": "max(0, parent.width - 2)",
        "height": "1",
        "text": "parent.prompt",
        "align": '"left"',
    }
    # Only ``info`` carries a handler: the other two reach the hand-written
    # half through the ``on_<id>_<event>`` convention, which is the generator's
    # to emit and says nothing in the markup.
    assert [h.name for h in blocks["info"].handlers] == ["on_click"]
    assert blocks["info"].handlers[0].body == "await root.show_info(event)"
    assert all(not b.handlers for b in (blocks["ok"], blocks["cancel"]))


@pytest.mark.parametrize("component", SHIPPED)
def test_the_generated_half_cites_lines_the_parser_found(component):
    """Every ``# x.nml:N`` in a generated file names a node, not a blank line.

    The stand-ins were written by hand against the markup, so this is where the
    parser and the file it will one day replace have to agree.  A block head, a
    property, a handler and an ``id:`` directive are the four kinds of line a
    reference can point at -- the ``id:`` line is what a child's wired-up
    handler is named after, which is why the block carries its own.
    """
    document = parse_file(WIDGETS / f"{component}.nml")
    found = set()
    for line in document.imports:
        found.add(line.line)
    for block in document.root.walk():
        found.add(block.line)
        if block.id_line is not None:
            found.add(block.id_line)
        found.update(p.line for p in block.properties)
        found.update(h.line for h in block.handlers)
        found.update(d.line for d in block.declarations)
        if block.style is not None:
            found.update(d.line for d in block.style.declarations)

    generated = (WIDGETS / f"{component}_nml.py").read_text()
    cited = {
        int(number)
        for name, number in re.findall(r"#\s*(\w+)\.nml:(\d+)", generated)
        if name == component
    }
    assert cited, "the generated half cites no markup at all"
    assert cited <= found


def test_imports_of_reads_the_block_without_reading_the_document():
    """What ``navml build`` orders a cold build by.

    The edges of the import graph have to be readable before anything has been
    generated, so this stops at the root block and never looks further.
    """
    lines = imports_of(WIDGETS / "dialog.nml")
    assert [line.modules for line in lines] == [
        ("navml.widgets.button",),
        ("navml.widgets.label",),
    ]
    assert [line.source for line in lines] == [
        "from navml.widgets.button import Button",
        "from navml.widgets.label import Label",
    ]


# -- the import block -------------------------------------------------------


def test_an_import_is_read_with_pythons_own_grammar():
    """Every form round-trips, because navml invents no grammar here."""
    document = parse(
        "import navkit\n"
        "from pathlib import Path as P\n"
        "from . import sibling\n"
        "from ..widgets.label import Label, Spacer\n"
        "\n"
        "Panel:\n",
        filename="t.nml",
    )
    assert document.bound == {
        "navkit": "",
        "P": "pathlib",
        "sibling": ".",
        "Label": "..widgets.label",
        "Spacer": "..widgets.label",
    }
    assert document.imports[3].modules == ("..widgets.label",)


@pytest.mark.parametrize(
    "line, says",
    [
        ("from x import *", "'import *' is refused"),
        ("from __future__ import annotations", "__future__"),
        ("from x import event", "reserved"),
        ("from x import y as event", "reserved"),
    ],
)
def test_an_import_that_cannot_be_allowed(line, says):
    """Three refusals, each naming its line: two would break the generator's
    own module, and the third would shadow a handler's one argument."""
    error = fails(f"{line}\n\nPanel:\n")
    assert says in error.message
    assert error.line == 1


def test_an_import_after_the_root_block():
    """Blocks are made by indentation, so an import inside one means nothing."""
    error = fails("Panel:\n    width: 1\nfrom x import y\n")
    assert error.line == 3
    assert "before the root block" in error.message


def test_an_indented_import():
    error = fails("Panel:\n    from x import y\n")
    assert error.line == 2
    assert "left margin" in error.message


# -- lexical rules ----------------------------------------------------------


def test_a_comment_is_a_hash_and_a_space():
    """And a value is not, which is what ``#rrggbb`` costs.

    A ``style:`` block is written in the ``.nss`` value grammar, where a hex
    colour is a literal -- so ``#`` introduces a comment only when a space, an
    end of line or a ``:`` follows it.
    """
    document = parse(
        "Panel:\n"
        "    # a whole line\n"
        "    width: 1  # and a trailing one\n"
        '    title: "# 1"\n'
        "    style:\n"
        "        bg: #1e1e2e  # the base\n",
        filename="t.nml",
    )
    values = {p.name: p.expression for p in document.root.properties}
    assert values == {"width": "1", "title": '"# 1"'}
    assert document.root.style.text() == "bg: #1e1e2e"


def test_a_hash_inside_a_string_is_not_a_comment():
    """Including the f-string form, where the inner quotes are the same."""
    document = parse("Panel:\n    title: f\"{d['#']}\"\n", filename="t.nml")
    assert document.root.properties[0].expression == "f\"{d['#']}\""


def test_doc_comments_are_captured_for_the_generator():
    """``#:`` is what ``navigator/__main__.py`` writes beside every reactive
    attribute it declares, and the reason one exists is worth carrying over."""
    document = parse(
        "Panel:\n"
        "    #: Whether a listing shows a Nerd Font glyph.\n"
        "    #: ``auto`` means whenever the terminal can draw one.\n"
        "    style_property icons: auto | none\n"
        "\n"
        "    #: dropped: a blank line ends the run\n"
        "\n"
        "    property count: 0\n",
        filename="t.nml",
    )
    icons, count = document.root.declarations
    assert icons.doc == (
        "Whether a listing shows a Nerd Font glyph.",
        "``auto`` means whenever the terminal can draw one.",
    )
    assert count.doc == ()


def test_a_tab_in_the_indentation():
    error = fails("Panel:\n\twidth: 1\n")
    assert error.line == 2
    assert "tab" in error.message


def test_an_expression_continues_inside_brackets():
    """Python's own implicit continuation, and nothing else -- so an indent
    goes on meaning exactly one thing."""
    document = parse(
        "Panel:\n"
        "    footer_text: ', '.join(\n"
        "        e.name\n"
        "        for e in entries\n"
        "    )\n"
        "    width: 2\n",
        filename="t.nml",
    )
    assert [p.name for p in document.root.properties] == ["footer_text", "width"]
    assert document.root.properties[0].expression == "', '.join( e.name for e in entries )"
    assert document.root.properties[0].line == 2


def test_a_bracket_that_never_closes():
    error = fails("Panel:\n    width: max(1,\n")
    assert error.line == 2
    assert "never ends" in error.message


def test_a_string_that_never_closes():
    error = fails('Panel:\n    title: "open\n')
    assert error.line == 2
    assert "never closes" in error.message


# -- blocks -----------------------------------------------------------------


def test_only_the_root_block_names_a_base():
    """A child block constructs a type; the root declares one."""
    error = fails("Panel:\n    Label(Widget):\n        x: 1\n")
    assert error.line == 2
    assert "only the root block" in error.message


def test_a_base_is_a_single_name():
    """``import navml.widgets`` binds ``navml``, so a dotted head is no use."""
    error = fails("Panel(navml.widgets.Button):\n    x: 1\n")
    assert error.line == 1
    assert "single name" in error.message


def test_a_document_declares_one_component():
    error = fails("Panel:\n    x: 1\nOther:\n    x: 1\n")
    assert error.line == 3
    assert "one component" in error.message


def test_a_document_with_no_component():
    error = fails("from x import y\n")
    assert "declares none" in error.message


def test_an_indent_that_matches_nothing():
    error = fails("Panel:\n    Label:\n        x: 1\n  y: 2\n")
    assert error.line == 4
    assert "unexpected indent" in error.message


def test_a_widget_with_nothing_to_say_is_legal():
    """A spacer declares no property and is not thereby an error."""
    document = parse("Panel:\n    Spacer:\n", filename="t.nml")
    assert document.root.children[0].type == "Spacer"


# -- ids --------------------------------------------------------------------


def test_an_id_is_a_name_a_generated_module_can_carry():
    document = parse("Panel:\n    Label:\n        id: header\n", filename="t.nml")
    assert document.ids()["header"].type == "Label"
    assert document.root.children[0].id_line == 3


@pytest.mark.parametrize(
    "id_, says, line",
    [
        ("2left", "Python identifier", 3),
        ("class", "keyword", 3),
        ("parent", "reserved", 3),
        ("event", "reserved", 3),
    ],
)
def test_an_id_that_cannot_be_one(id_, says, line):
    """The reserved row is the one both ancestors got wrong, in the same
    direction: QML shadows ``parent`` and Kivy shadows in two directions at
    once depending on where the name is read."""
    error = fails(f"Panel:\n    Label:\n        id: {id_}\n")
    assert says in error.message
    assert error.line == line


def test_two_ids_of_one_name():
    error = fails(
        "Panel:\n"
        "    Label:\n"
        "        id: left\n"
        "    Label:\n"
        "        id: left\n"
    )
    assert error.line == 4
    assert "already" in error.message


def test_two_ids_on_one_widget():
    error = fails("Panel:\n    Label:\n        id: a\n        id: b\n")
    assert error.line == 4
    assert "second id" in error.message


def test_the_root_block_takes_no_id():
    """It is named ``root`` in every expression in the document already, and a
    second name for it would be a second way to say the same thing."""
    error = fails("Panel:\n    id: desktop\n")
    assert error.line == 2
    assert "root" in error.message


def test_an_id_colliding_with_a_declared_property():
    """Both become ``self.<name>``, and ``Reactive`` is a data descriptor, so
    the declaration wins the tie and the widget is written into a cell."""
    error = fails("Panel:\n    property left: 0\n    Label:\n        id: left\n")
    assert error.line == 3
    assert "self.left" in error.message


# -- declarations -----------------------------------------------------------


def test_the_four_directives():
    document = parse(
        "Panel:\n"
        "    property console_visible: False\n"
        "    style_property icons: auto | none\n"
        "    alias title: header.text\n"
        "    event SelectionChanged\n"
        "\n"
        "    Label:\n"
        "        id: header\n",
        filename="t.nml",
    )
    declared = document.root.declarations
    assert isinstance(declared[0], PropertyDecl)
    assert declared[0].expression == "False"
    assert isinstance(declared[1], StylePropertyDecl)
    assert (declared[1].default, declared[1].values) == ("auto", ("auto", "none"))
    assert isinstance(declared[2], AliasDecl)
    assert (declared[2].target, declared[2].attribute) == ("header", "text")
    assert isinstance(declared[3], EventDecl)
    assert declared[3].name == "SelectionChanged"


@pytest.mark.parametrize("directive", ["property x: 1", "style_property x: auto",
                                       "alias x: header.text", "event Clicked"])
def test_a_directive_under_a_child_block(directive):
    """Each becomes a descriptor on the class the root block declares, and
    every other block is an instance of a class that already exists."""
    error = fails(f"Panel:\n    Label:\n        id: header\n        {directive}\n")
    assert error.line == 4
    assert "root block only" in error.message


@pytest.mark.parametrize("line", ["property console_visible", "alias title",
                                  "style_property icons"])
def test_a_declaration_with_no_value(line):
    """Never quietly ``reactive(None)``: a value is required."""
    error = fails(f"Panel:\n    {line}\n")
    assert error.line == 2
    assert "value is required" in error.message


def test_a_style_property_narrows_its_default_form():
    """Nothing spells a type: the default's own form is it, and ``|`` narrows."""
    document = parse(
        "Panel:\n"
        "    style_property margin: 0\n"
        "    style_property indent: 2 | 4 | 8\n"
        "    style_property scrollbar: true\n",
        filename="t.nml",
    )
    margin, indent, scrollbar = document.root.declarations
    assert (margin.default, margin.values) == (0, None)
    assert (indent.default, indent.values) == (2, (2, 4, 8))
    assert (scrollbar.default, scrollbar.values) == (True, None)


def test_a_style_property_whose_alternatives_disagree():
    error = fails("Panel:\n    style_property indent: 2 | wide\n")
    assert error.line == 2
    assert "same kind" in error.message


def test_a_style_property_cannot_read_a_variable():
    """There is no sheet loaded when a class body runs, so a default that
    needed one would be a different mechanism wearing the same syntax."""
    error = fails("Panel:\n    style_property icons: $icons\n")
    assert error.line == 2
    assert "variable" in error.message


def test_an_alias_is_one_property_deep():
    """Chaining is how reach goes further, and each hop is then a declaration
    the component in the middle made."""
    error = fails("Panel:\n    alias title: header.child.text\n")
    assert error.line == 2
    assert "one property deep" in error.message


def test_an_alias_naming_no_id():
    error = fails("Panel:\n    alias title: header.text\n")
    assert error.line == 2
    assert "not one" in error.message


def test_an_alias_naming_a_reserved_word():
    error = fails("Panel:\n    alias title: parent.width\n")
    assert error.line == 2
    assert "declared in this document" in error.message


def test_an_event_carries_no_value():
    """Markup says what a component emits, Python says what it emits about."""
    error = fails("Panel:\n    event ClickEvent: 1\n")
    assert error.line == 2
    assert "carries no value" in error.message


def test_an_event_that_collides_with_an_import():
    """A declared event is a name of the generated module, where the
    document's own imports land too."""
    error = fails("from x import ClickEvent\n\nPanel:\n    event ClickEvent\n")
    assert error.line == 4
    assert "already imported" in error.message


# -- handlers ---------------------------------------------------------------


def test_a_handler_is_one_line():
    document = parse(
        "Panel:\n    on_key: self.title = event.key\n", filename="t.nml"
    )
    handler = document.root.handlers[0]
    assert (handler.name, handler.body) == ("on_key", "self.title = event.key")


def test_a_handler_body_that_is_a_block():
    """Anything longer is a method in the hand-written half, and the message
    says so rather than leaving the author to find that out."""
    error = fails("Panel:\n    on_key: await self.a()\n        await self.b()\n")
    assert error.line == 3
    assert ".py half" in error.message


def test_an_indented_line_under_a_property():
    error = fails("Panel:\n    width: 1\n        + 2\n")
    assert error.line == 3
    assert "only inside brackets" in error.message


def test_two_handlers_for_one_event_on_one_widget():
    error = fails("Panel:\n    on_key: self.a()\n    on_key: self.b()\n")
    assert error.line == 3
    assert "second 'on_key'" in error.message


def test_two_assignments_of_one_property():
    error = fails("Panel:\n    width: 1\n    width: 2\n")
    assert error.line == 3
    assert "second 'width'" in error.message


# -- the style block --------------------------------------------------------


def test_a_style_block_is_a_stylesheet_fragment():
    """``$name`` is meaningful here and nowhere else in a document: the block
    is the boundary between two languages, and resolution stays at run time so
    a theme swap reaches markup-authored styles."""
    document = parse(
        "Panel:\n"
        "    style:\n"
        "        bg: $surface\n"
        "        fg: white\n",
        filename="t.nml",
    )
    assert [(d.name, d.value) for d in document.root.style.declarations] == [
        ("bg", "$surface"),
        ("fg", "white"),
    ]
    assert document.root.style.text() == "bg: $surface; fg: white"


def test_a_style_block_on_a_child():
    document = parse(
        "Panel:\n    Label:\n        style:\n            bold: true\n",
        filename="t.nml",
    )
    assert document.root.children[0].style.text() == "bold: true"


def test_a_style_block_that_says_nothing():
    error = fails("Panel:\n    style:\n    width: 1\n")
    assert error.line == 2
    assert "says nothing" in error.message


def test_a_style_line_that_is_not_a_declaration():
    error = fails("Panel:\n    style:\n        bold\n")
    assert error.line == 3
    assert "not a declaration" in error.message


def test_two_style_blocks_on_one_widget():
    error = fails(
        "Panel:\n    style:\n        bold: true\n    style:\n        bg: red\n"
    )
    assert error.line == 4
    assert "second style block" in error.message


# -- the two things a document can be syntactically wrong about -------------


def test_a_property_expression_has_to_be_an_expression():
    """Asked here rather than left to the generator, because a binding's
    failure is lazy and cached: a malformed expression left to run time
    surfaces at the first read, arbitrarily far from the line that wrote it."""
    error = fails("Panel:\n    width: parent.width //\n")
    assert error.line == 2
    assert "cannot read the value of 'width'" in error.message


def test_where_the_two_comment_rules_differ_and_where_they_do_not():
    """``#`` without a space is not navml's comment, and mostly does not have
    to be.

    The right of a ``:`` is Python, whose *own* reader takes ``#`` as a comment
    however it is spaced -- so a property expression is unharmed either way,
    and the text kept here loses it at the generator's ``unparse``.  The rule
    earns its keep in the one place the right of a ``:`` is not Python: a
    ``style:`` block, where ``#1e1e2e`` is a colour and Python's rule would
    eat it.
    """
    document = parse(
        "Panel:\n"
        "    width: 1 #comment\n"
        "    style:\n"
        "        bg: #1e1e2e\n",
        filename="t.nml",
    )
    assert document.root.properties[0].expression == "1 #comment"
    assert document.root.style.text() == "bg: #1e1e2e"


def test_a_handler_body_may_await():
    """It compiles into an ``async def``, so it is read as one."""
    document = parse("Panel:\n    on_key: await self.quit()\n", filename="t.nml")
    assert document.root.handlers[0].body == "await self.quit()"


def test_a_handler_body_joined_by_semicolons():
    """One line is one statement; semicolons are two wearing one line."""
    error = fails("Panel:\n    on_key: a = 1; b = 2\n")
    assert error.line == 2
    assert "one statement" in error.message


def test_a_declared_property_value_has_to_be_an_expression():
    error = fails("Panel:\n    property count: 1 +\n")
    assert error.line == 2
    assert "cannot read the value of 'count'" in error.message
