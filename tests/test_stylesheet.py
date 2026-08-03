"""The stylesheet language and its lookup engine.

The parsing tests pin the grammar; the resolution tests pin the four channels a
widget's style can come from and the order they sit in.  Where a test exists
because a design decision could plausibly have gone the other way, it says so.
"""

from __future__ import annotations

import pytest
from conftest import RecordingWidget, run_app, settle

from navkit.application import Application
from navkit.reactive import reactive
from navkit.style import Style
from navkit.stylesheet import (
    EMPTY,
    PartRequest,
    StylesheetError,
    load,
    parse,
    register_property,
)
from navkit.widget import Widget

register_property("border")


class Panel(Widget):
    """Matched by name, so the class has to be called this.

    ``active`` is reactive because that is what makes ``Panel:active`` restyle
    rather than merely match -- see
    :func:`test_a_state_on_a_plain_attribute_matches_but_does_not_restyle`.
    """

    active: bool = reactive(False)


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
        ("P { fg: mauve }", "cannot read value"),
        ("P { fg red }", "not a declaration"),
        ("P { fg: 300 }", "above 255"),
        ("P { fg: $nope }", "undefined variable"),
        ("$a: $b; $b: $a; P { fg: red }", "defined in terms of itself"),
        ("P > { fg: red }", "ends with '>'"),
        ("A::row B { fg: red }", "only appear on the last compound"),
    ],
)
def test_bad_input_fails_with_a_line(source, expected):
    with pytest.raises(StylesheetError) as caught:
        parse(source, filename="scheme.nss")
    assert expected in str(caught.value)
    assert str(caught.value).startswith("scheme.nss:")


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
    assert app.root.style_property("border") == "double"
    assert label.style_property("border") is None


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
    assert Label().stylesheet is EMPTY
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
