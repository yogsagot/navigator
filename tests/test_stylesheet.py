"""The stylesheet language and its lookup engine.

The parsing tests pin the grammar; the resolution tests pin the four channels a
widget's style can come from and the order they sit in.  Where a test exists
because a design decision could plausibly have gone the other way, it says so.
"""

from __future__ import annotations

import pytest
from conftest import RecordingWidget, run_app, settle

from navkit import glyphs
from navkit.application import Application
from navkit.reactive import reactive
from navkit.style import Style
from navkit.stylesheet import (
    EMPTY,
    PartRequest,
    PropertySpec,
    StyleProperty,
    StylesheetError,
    check_declarations,
    declared_property,
    load,
    parse,
    read,
    register_property,
)
from navkit.stylesheet import parts_of
from navkit.widget import Widget


class Panel(Widget):
    """Matched by name, so the class has to be called this.

    ``active`` is reactive because that is what makes ``Panel:active`` restyle
    rather than merely match -- see
    :func:`test_a_state_on_a_plain_attribute_matches_but_does_not_restyle`.
    """

    active: bool = reactive(False)
    #: Declared because `part_style' refuses a part its widget does not paint.
    parts = ("row", "title")


class Label(Widget):
    pass


class Manager(Widget):
    pass


@pytest.fixture
def app_with(terminal):
    """An application carrying *sheet*, with a root already attached."""

    def make(sheet_text, root=None):
        app = Application(
            root or Manager(), terminal=terminal, stylesheet=parse(sheet_text)
        )
        return app

    return make


# -- parsing ----------------------------------------------------------------


def test_a_rule_is_selector_and_declarations():
    sheet = parse("Panel { fg: white; bg: blue }")
    assert len(sheet.rules) == 1
    assert sheet.rules[0].declarations == {"fg": 15, "bg": 4}


def test_every_colour_form_lands_on_the_existing_color_type():
    sheet = parse(
        "A { fg: light_cyan } B { fg: 33 } C { fg: #0088ff } "
        "D { fg: rgb(0, 136, 255) } E { fg: default } F { bold: true }"
    )
    assert [r.declarations for r in sheet.rules] == [
        {"fg": 14},
        {"fg": 33},
        {"fg": (0, 136, 255)},
        {"fg": (0, 136, 255)},
        {"fg": None},
        {"bold": True},
    ]


def test_comments_do_not_disturb_line_numbers():
    sheet = parse("/* a\n   comment */\nPanel { fg: white }")
    assert sheet.rules[0].line == 3


def test_a_group_shares_its_declarations():
    sheet = parse("MenuBar, KeyBar { bg: cyan }")
    assert len(sheet.rules) == 2
    assert all(r.declarations == {"bg": 6} for r in sheet.rules)


@pytest.mark.parametrize(
    "source, expected",
    [
        ("P { bordr: red }", "unknown property"),
        # The value half of a declaration, checked against what the widget
        # declaring the key said it accepts -- see `border' on Widget.
        ("P { border: dubble }", "not a valid border"),
        ("P { border: true }", "expected a keyword"),
        ("P { border: 2 }", "expected a keyword"),
        ("P { fg: mauve }", "cannot read value"),
        ("P { fg red }", "not a declaration"),
        ("P { fg: 300 }", "above 255"),
        ("P { fg: $nope }", "undefined variable"),
        ("$a: $b; $b: $a; P { fg: red }", "defined in terms of itself"),
        ("P > { fg: red }", "ends with '>'"),
        ("A::row B { fg: red }", "only appear on the last compound"),
        # Braces are found before selectors are, so a stray one lands in the
        # selector rather than in a check of its own -- it still has to fail.
        ("} P { fg: red }", "cannot read selector"),
        ("P { { }", "cannot read selector"),
        ("P { fg: red", "stray text"),
    ],
)
def test_bad_input_fails_with_a_line(source, expected):
    with pytest.raises(StylesheetError) as caught:
        parse(source, filename="scheme.nss")
    assert expected in str(caught.value)
    assert str(caught.value).startswith("scheme.nss:")


def test_a_big_sheet_parses_in_linear_time():
    """A sheet that is mostly declarations must not cost quadratic time.

    The palette themes are exactly that shape -- hundreds of variables and no
    rules at all -- and the first version of the block regex led with an
    unanchored ``[^{}]*``, which gives the engine no literal to seek: it
    retried at every character and rescanned to the end each time.  A 17 kB
    theme took 1.2 s to parse, so every one of the eleven cost more than the
    whole test suite.

    Timed rather than counted because there is nothing to count, and with a
    thousandfold margin: the linear version does this in about a millisecond
    and the quadratic one needs minutes.
    """
    import time

    sheet = "\n".join(f"$name-{i}: red;" for i in range(4000)) + "\nP { fg: $name-0 }"
    assert len(sheet) > 50_000
    start = time.perf_counter()
    parsed = parse(sheet)
    elapsed = time.perf_counter() - start

    assert len(parsed.rules) == 1
    assert len(parsed.variables) == 4000
    assert elapsed < 1.0, f"parsing {len(sheet)} bytes took {elapsed:.1f}s"


def test_default_is_only_meaningful_on_a_colour():
    # A flag turns off with `false`; allowing `default` would put None into a
    # field declared bool, which sgr() would silently tolerate.
    with pytest.raises(StylesheetError, match="only meaningful on fg and bg"):
        parse("P { dim: default }")


# -- specificity ------------------------------------------------------------


def test_specificity_columns_do_not_add():
    sheet = parse("#a { fg: red } .b.c.d.e.f { fg: blue }")
    by_name, by_classes = sheet.rules
    assert by_name.selector.specificity > by_classes.selector.specificity


def test_a_part_counts_as_a_type():
    sheet = parse("Panel:active::row.selected { fg: red }")
    assert sheet.rules[0].selector.specificity == (0, 2, 2)


def test_the_cascade_is_per_property_not_per_rule():
    # The name rule wins overall, yet fg still comes from the state rule
    # because the winner never mentioned fg.  A per-rule cascade would drop it.
    sheet = parse(
        "Panel { fg: cyan; bg: blue } Panel:active { fg: white } #p { bg: red }"
    )
    panel = Panel(name="p")
    panel.active = True
    assert sheet.declarations_for(panel) == {"fg": 15, "bg": 1}


def test_a_later_rule_wins_an_equal_specificity_tie():
    sheet = parse("Panel { fg: red } Panel { fg: blue }")
    assert sheet.declarations_for(Panel()) == {"fg": 4}


# -- selectors --------------------------------------------------------------


def test_a_type_selector_matches_subclasses():
    class Special(Panel):
        pass

    assert parse("Panel { fg: red }").declarations_for(Special()) == {"fg": 1}


def test_a_child_combinator_does_not_match_a_grandchild():
    sheet = parse("Manager > Panel { fg: red }")
    root = Manager()
    child = Panel(parent=root)
    grandchild = Panel(parent=Panel(parent=root))
    assert sheet.declarations_for(child) == {"fg": 1}
    assert sheet.declarations_for(grandchild) == {}


def test_a_descendant_combinator_does_match_a_grandchild():
    sheet = parse("Manager Panel { fg: red }")
    root = Manager()
    assert sheet.declarations_for(Panel(parent=Panel(parent=root))) == {"fg": 1}


def test_a_state_matches_a_truthy_attribute():
    sheet = parse("Panel:active { fg: red }")
    panel = Panel()
    panel.active = False
    assert sheet.declarations_for(panel) == {}
    panel.active = True
    assert sheet.declarations_for(panel) == {"fg": 1}


def test_a_part_is_only_matched_when_it_is_asked_for():
    sheet = parse("Panel { fg: cyan } Panel::row { fg: white }")
    panel = Panel()
    assert sheet.declarations_for(panel) == {"fg": 6}
    assert sheet.declarations_for(panel, PartRequest("row")) == {"fg": 15}


# -- variables --------------------------------------------------------------


def test_a_variable_is_substituted():
    assert parse("$a: cyan; P { fg: $a }").declarations_for(Panel()) == {}
    sheet = parse("$a: cyan; Panel { fg: $a }")
    assert sheet.declarations_for(Panel()) == {"fg": 6}


def test_a_variable_may_name_another():
    sheet = parse("$blue: blue; $surface: $blue; Panel { bg: $surface }")
    assert sheet.declarations_for(Panel()) == {"bg": 4}


def test_a_later_sheet_redefines_a_variable_the_first_ones_rules_use():
    # This is the whole theming mechanism: a theme redefines names rather than
    # forking every rule, and load order alone decides.
    default = "$accent: cyan; Panel { fg: $accent }"
    sheet = load([("default.nss", default), ("dark.nss", "$accent: light_cyan;")])
    assert sheet.declarations_for(Panel()) == {"fg": 14}


# -- resolution on a widget -------------------------------------------------


def test_appearance_inherits_from_the_parent():
    app = Application(Manager(), stylesheet=parse("Manager { fg: white; bg: blue }"))
    label = Label(parent=app.root)
    assert label.style == Style(fg=15, bg=4)


def test_a_widget_property_does_not_inherit():
    # An inherited border would hand a frame to every child of a framed widget,
    # which is why the split sits at the Style boundary.
    app = Application(Panel(), stylesheet=parse("Panel { border: double }"))
    label = Label(parent=app.root)
    assert app.root.border == "double"
    assert label.border == "single"  # the declaration's default, not the parent's
    assert label.style_property("border") is None  # nothing cascaded onto it at all


def test_a_declared_property_reads_the_cascade_through_its_attribute():
    app = Application(Panel(), stylesheet=parse("Panel { border: round }"))
    assert app.root.border == "round"
    assert Panel().border == "single"  # no sheet: the declaration answers


def test_a_declared_property_is_authored_in_a_sheet_and_not_assigned():
    panel = Panel()
    with pytest.raises(AttributeError, match="merge_style"):
        panel.border = "double"
    panel.merge_style("border: double")
    assert panel.border == "double"


def test_a_property_takes_the_type_of_its_default():
    """The default's own form is the type, which is what lets ints and flags in."""

    class Gauge(Widget):
        margin = StyleProperty(0)
        wrap = StyleProperty(True)

    app = Application(Gauge(), stylesheet=parse("Gauge { margin: 3; wrap: false }"))
    assert (app.root.margin, app.root.wrap) == (3, False)
    with pytest.raises(StylesheetError, match="expected a number"):
        parse("Gauge { margin: wide }")
    # `true' is an int in Python and must not pass for one here.
    with pytest.raises(StylesheetError, match="expected a number"):
        parse("Gauge { margin: true }")


def test_a_property_is_redeclared_by_default_but_not_by_vocabulary():
    """A subclass may want another default frame; it may not want another word."""

    class Framed(Widget):
        border = StyleProperty("double", values=tuple(glyphs.BOX_CHARSETS))

    assert Framed().border == "double"
    assert Panel().border == "single"

    with pytest.raises(ValueError, match="import order"):

        class Odd(Widget):
            border = StyleProperty("fancy", values=("fancy", "plain"))


def test_the_bare_registration_declares_a_name_and_nothing_about_its_value():
    """The route for a property no attribute is held for -- a name, checked."""
    register_property("gutter-hint")
    assert parse("P { gutter-hint: 4 }").rules[0].declarations == {"gutter-hint": 4}
    assert parse("P { gutter-hint: wide }").rules[0].declarations["gutter-hint"] == "wide"
    assert declared_property("gutter-hint") == PropertySpec()
    assert declared_property("nothing-declares-this") is None


def test_a_default_outside_its_own_vocabulary_is_refused():
    with pytest.raises(ValueError, match="not one of the values"):
        StyleProperty("dotted", values=("single", "double"))


def test_inline_declarations_are_partial_and_beat_every_rule():
    app = Application(Panel(), stylesheet=parse("Panel { fg: cyan; bg: blue }"))
    app.root.inline_style = "bg: red"
    assert app.root.style == Style(fg=6, bg=1)  # fg survives from the rule


def test_an_inline_declaration_does_not_block_inheritance():
    app = Application(Manager(), stylesheet=parse("Manager { fg: white; bg: blue }"))
    label = Label(parent=app.root, inline_style="bg: red")
    # Only bg stops descending; a whole-Style inline would have cut the chain.
    assert label.style == Style(fg=15, bg=1)


def test_merge_style_keeps_what_was_already_authored():
    widget = Label(inline_style="bg: blue")
    widget.merge_style("fg: white")
    assert widget.style == Style(fg=15, bg=4)


def test_a_widget_with_no_application_still_resolves():
    assert Label().effective_stylesheet is EMPTY
    assert Label(inline_style="fg: red").style == Style(fg=1)


# -- parts ------------------------------------------------------------------


def test_a_part_inherits_from_its_owner():
    app = Application(
        Panel(), stylesheet=parse("Panel { fg: cyan; bg: blue } Panel::row { fg: white }")
    )
    assert app.root.part_style("row") == Style(fg=15, bg=4)


def test_a_part_takes_its_state_from_the_widget():
    app = Application(
        Panel(),
        stylesheet=parse(
            "Panel::row { fg: white } Panel::row:selected { fg: black; bg: cyan }"
        ),
    )
    assert app.root.part_style("row", selected=False) == Style(fg=15)
    assert app.root.part_style("row", selected=True) == Style(fg=0, bg=6)


def test_a_state_on_a_plain_attribute_matches_but_does_not_restyle():
    """The sharp edge of matching states by ``getattr``.

    A selector may name any attribute, but only a *reactive* one is read
    through the dependency graph -- so a plain attribute is matched correctly
    the first time and never invalidates the memoised answer afterwards.  This
    pins the behaviour rather than endorsing it: a widget meaning a state to be
    stylable has to declare it reactive.
    """
    app = Application(Label(), stylesheet=parse("Label:busy { fg: red }"))
    app.root.busy = True  # a plain attribute, set before anything resolved
    assert app.root.style.fg == 1  # matching itself works
    app.root.busy = False
    assert app.root.style.fg == 1  # ... but nothing marked the style stale


def test_a_part_state_composes_with_the_owners_state():
    app = Application(
        Panel(), stylesheet=parse("Panel:active::row:selected { fg: red }")
    )
    app.root.part_style("row", selected=True)
    app.root.active = True
    assert app.root.part_style("row", selected=True) == Style(fg=1)


# -- reactivity -------------------------------------------------------------


def test_changing_a_class_restyles_the_widget():
    app = Application(Panel(), stylesheet=parse("Panel.wide { fg: red }"))
    assert app.root.style.fg is None
    app.root.add_class("wide")
    assert app.root.style.fg == 1
    app.root.remove_class("wide")
    assert app.root.style.fg is None


def test_replacing_the_sheet_restyles_the_whole_tree():
    default = "$accent: cyan; Manager { fg: $accent }"
    app = Application(Manager(), stylesheet=parse(default))
    label = Label(parent=app.root)
    assert label.style.fg == 6
    app.stylesheet = load([("d.nss", default), ("t.nss", "$accent: light_cyan;")])
    assert label.style.fg == 14


def test_a_style_pulled_before_attachment_still_picks_up_the_sheet():
    # The application reference is observable precisely so this recovers; with
    # a plain attribute the widget would have memoised "no stylesheet".
    root = Panel()
    assert root.style.fg is None
    Application(root, stylesheet=parse("Panel { fg: red }"))
    assert root.style.fg == 1


def test_restyling_costs_one_frame(terminal):
    root = RecordingWidget()
    app = Application(root, terminal=terminal, stylesheet=parse("Widget { fg: red }"))
    run_app(app, [lambda a: root.add_class("wide")])
    # The initial paint, then one more for the class change -- not one per
    # widget and not one per reactive hop.
    assert root.renders == 2


def test_an_unchanged_resolution_paints_nothing(terminal):
    root = RecordingWidget()
    app = Application(root, terminal=terminal, stylesheet=parse("Widget { fg: red }"))
    run_app(app, [lambda a: root.add_class("irrelevant")])
    # The class changed, so a frame is composed -- but the resolved style did
    # not, so the diff has nothing to send.
    assert len(terminal.frames) == 1


def test_the_part_resolver_is_rebuilt_when_the_sheet_changes():
    app = Application(Panel(), stylesheet=parse("Panel::row { fg: cyan }"))
    assert app.root.part_style("row").fg == 6
    app.stylesheet = parse("Panel::row { fg: white }")
    assert app.root.part_style("row").fg == 15


# -- reading sheets from disk -----------------------------------------------


def test_read_loads_a_file(tmp_path):
    sheet = tmp_path / "scheme.nss"
    sheet.write_text("Panel { fg: white }")
    assert read(sheet).declarations_for(Panel()) == {"fg": 15}


def test_read_reports_a_missing_file_by_name(tmp_path):
    with pytest.raises(StylesheetError, match="cannot read"):
        read(tmp_path / "absent.nss")


def test_read_names_the_file_in_a_parse_error(tmp_path):
    sheet = tmp_path / "scheme.nss"
    sheet.write_text("Panel { fg: white }\nPanel { fg: mauve }")
    with pytest.raises(StylesheetError) as caught:
        read(sheet)
    assert "scheme.nss:2" in str(caught.value)


def test_a_theme_file_redefines_variables_without_repeating_rules(tmp_path):
    default = tmp_path / "default.nss"
    default.write_text("$accent: cyan;\nPanel { fg: $accent; bg: blue }")
    theme = tmp_path / "amber.nss"
    theme.write_text("$accent: yellow;")
    assert read(default).declarations_for(Panel()) == {"fg": 6, "bg": 4}
    # The theme carries no rule at all -- only the variable moves.
    assert read(default, theme).declarations_for(Panel()) == {"fg": 11, "bg": 4}


def test_read_mixes_paths_with_inline_sheets(tmp_path):
    default = tmp_path / "default.nss"
    default.write_text("$accent: cyan;\nPanel { fg: $accent }")
    sheet = read(default, ("override.nss", "$accent: white;"))
    assert sheet.declarations_for(Panel()) == {"fg": 15}


# -- checking declarations before any sheet exists ----------------------------
#
# What a code generator asks of a markup `style:' block.  The property names
# and the value grammar can be checked the moment the widgets are imported,
# but a `$variable' cannot: the sheets do not exist yet, and the reference has
# to survive to run time or a theme swap would never reach these widgets.  See
# *The `style` block* in navml/DESIGN.md.


def test_check_declarations_passes_over_a_variable_it_cannot_resolve():
    register_property("gutter", default=2)
    check_declarations("bg: $surface; fg: white; gutter: $wide")


def test_check_declarations_still_refuses_an_unknown_property():
    with pytest.raises(StylesheetError) as caught:
        check_declarations("bakground: red", line=12, filename="panel.nml")
    assert caught.value.line == 12
    assert caught.value.filename == "panel.nml"
    assert "unknown property 'bakground'" in caught.value.message


def test_check_declarations_still_refuses_a_value_it_cannot_read():
    with pytest.raises(StylesheetError) as caught:
        check_declarations("bg: sideways", line=4, filename="panel.nml")
    assert "cannot read value 'sideways'" in caught.value.message
    assert caught.value.line == 4


def test_check_declarations_holds_a_literal_against_the_declared_vocabulary():
    """The half a variable takes away, kept for the values that stayed."""
    register_property("frame", default="single", values=("single", "double"))
    check_declarations("frame: double")
    with pytest.raises(StylesheetError) as caught:
        check_declarations("frame: triple", line=7, filename="panel.nml")
    assert "not a valid frame" in caught.value.message


def test_check_declarations_names_the_position_it_was_given():
    """Which is what ``parse_declarations`` cannot do: it is for an inline
    string arriving at run time and has no position to name."""
    with pytest.raises(StylesheetError) as caught:
        check_declarations("bold", line=31, filename="dialog.nml")
    assert str(caught.value).startswith("dialog.nml:31: ")


def test_resolving_a_variable_is_still_an_error_on_the_ordinary_path():
    """Deferring is something a caller asks for, not a relaxation."""
    with pytest.raises(StylesheetError) as caught:
        parse("Panel { bg: $nothing }")
    assert "undefined variable $nothing" in caught.value.message


# -- a part has to be declared -----------------------------------------------


def test_a_part_a_widget_does_not_paint_is_refused():
    """The check navkit/DESIGN.md claimed existed, and now does.

    A ``::part`` selector cannot be checked when a sheet is parsed -- it
    matches by class *name*, so the parser has no class to ask and a sheet may
    legally name a type it could not import.  So the check lives where the
    class is in hand, and fires at the first paint.
    """
    with pytest.raises(LookupError) as caught:
        Panel().part_style("rwo")
    assert "Panel paints no part 'rwo'" in str(caught.value)
    assert "row, title" in str(caught.value)


def test_a_widget_that_paints_nothing_says_so():
    with pytest.raises(LookupError, match="it declares none"):
        Label().part_style("anything")


def test_parts_union_down_the_mro():
    """Unlike declarations(), a subclass *adds* to what its base paints."""

    class Listing(Panel):
        parts = ("divider",)

    assert parts_of(Listing) == {"row", "title", "divider"}
    Listing().part_style("divider")   # the base's check does not refuse it
    Listing().part_style("row")
