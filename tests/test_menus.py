"""Menus: the bar, the boxes it opens, and Turbo Vision's rules for driving them."""

from __future__ import annotations

import pytest

from navkit.application import Application
from navkit.commands import Command
from navkit.events import KeyEvent, MouseClickEvent
from navkit.reactive import bind
from navkit.screen import ScreenBuffer
from navkit.widget import Widget

from navml.widgets.menu.menu_bar import MenuBar, MenuSession
from navml.widgets.menu.menu_box import MenuBox
from navml.widgets.menu.menu_item import MenuItem
from navml.widgets.menu.menu_line import MenuLine
from navml.widgets.menu.sub_menu import SubMenu

from conftest import FakeTerminal, run_app


class Save(Command):
    title = "Save"


class Burn(Command):
    title = "Burn"


class Editor(Widget):
    """Focusable, handles Save but never Burn, and binds Save to F2."""

    keys = {"f2": Save}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.saved = 0
        self.keys_seen: list[str] = []

    async def on_save(self, event):
        self.saved += 1
        return True

    async def on_key(self, event):
        self.keys_seen.append(event.name)
        return True


def build():
    """A bar with File (Save, a line, Burn, a submenu) and Edit, over an editor."""
    root = Widget()
    bar = MenuBar(parent=root)
    bar.x, bar.y = 0, 0
    bar.width = bind(lambda o: o.parent.width)
    bar.height = bind(lambda o: 1)
    file = SubMenu(parent=bar, text="~F~ile")
    MenuItem(parent=file, text="~S~ave", command=Save)
    MenuLine(parent=file)
    MenuItem(parent=file, text="~B~urn", command=Burn, key="Alt-B")
    more = SubMenu(parent=file, text="~M~ore")
    MenuItem(parent=more, text="~A~gain", command=Save)
    edit = SubMenu(parent=bar, text="~E~dit")
    MenuItem(parent=edit, text="~U~ndo")
    editor = Editor(parent=root)
    editor.x, editor.y = 0, 1
    editor.can_focus = True
    app = Application(root, terminal=FakeTerminal(width=40, height=12))
    editor.focus()
    return app, bar, editor


def boxes(app):
    session = app.modal
    return session.boxes if isinstance(session, MenuSession) else []


# -- geometry, from MENUS.PAS ------------------------------------------------------


def test_bar_entries_sit_where_tmenubar_puts_them():
    app, bar, _ = build()
    # From column 1, each caption with a space either side.
    assert [bar.item_span(i) for i in range(2)] == [(1, 6), (7, 6)]
    assert (bar.entry_at(0), bar.entry_at(1), bar.entry_at(7)) == (-1, 0, 1)
    assert (bar.hotkey("E"), bar.hotkey("q")) == (1, -1)


def test_a_box_is_as_wide_as_its_widest_entry_plus_its_key():
    app, bar, editor = build()
    file = bar.entries()[0]
    # "Burn" + 6, plus "Alt-B" and two spaces; five entries and the frame.
    assert MenuBox.measure(file, app, editor) == (4 + 6 + 5 + 2, 6)


def test_a_box_paints_frame_captions_keys_and_the_submenu_arrow(terminal):
    app, bar, editor = build()
    bar.open(0, drop=True)
    (box,) = boxes(app)
    buffer = ScreenBuffer(box.width, box.height)
    box.render_tree(buffer.view(-box.x, -box.y, box.width + box.x, box.height + box.y))
    rows = ["".join(buffer.get(x, y)[0] or " " for x in range(box.width))
            for y in range(box.height)]
    assert rows[0] == " ┌" + "─" * (box.width - 4) + "┐ "
    assert rows[1].startswith(" │ Save") and rows[1].endswith("F2 │ ")
    assert rows[2] == " ├" + "─" * (box.width - 4) + "┤ "
    assert rows[3].rstrip().endswith("Alt-B │")
    assert rows[4].endswith("► │ ")
    assert rows[5] == " └" + "─" * (box.width - 4) + "┘ "


def test_a_toggle_that_is_on_is_ticked_left_of_its_caption(terminal):
    app, bar, editor = build()
    editor.checks = lambda command: True if isinstance(command, Save) else None
    bar.open(0, drop=True)
    (box,) = boxes(app)
    buffer = ScreenBuffer(box.width, box.height)
    box.render_tree(buffer.view(-box.x, -box.y, box.width + box.x, box.height + box.y))
    rows = ["".join(buffer.get(x, y)[0] or " " for x in range(box.width))
            for y in range(box.height)]
    assert rows[1].startswith(" │√Save")
    assert rows[3].startswith(" │ Burn")          # disabled: neither on nor off
    assert MenuBox.measure(bar.entries()[0], app, editor)[0] == box.width
    editor.checks = lambda command: False if isinstance(command, Save) else None
    box.render_tree(buffer.view(-box.x, -box.y, box.width + box.x, box.height + box.y))
    assert "".join(buffer.get(x, 1)[0] or " " for x in range(6)) == " │ Sav"


def test_the_box_drops_one_column_left_of_its_caption_at_its_own_size():
    app, bar, editor = build()
    bar.open(1, drop=True)
    (box,) = boxes(app)
    assert (box.x, box.y) == (bar.item_span(1)[0] - 1, 1)
    # Measured, not laid out into the screen-sized layer it joined.
    assert (box.width, box.height) == MenuBox.measure(bar.entries()[1], app, editor)


# -- what is enabled, and what a key reads ----------------------------------------------


def test_entries_are_judged_from_the_focus_behind_the_menu():
    app, bar, editor = build()
    bar.open(0, drop=True)
    (box,) = boxes(app)
    save, _, burn, more = box.entries()
    assert app.focused is not editor  # the menu has the keyboard now
    assert (box.enabled(save), box.enabled(burn), box.enabled(more)) == (True, False, True)


def test_an_entry_with_no_command_is_disabled():
    app, bar, _ = build()
    bar.open(1, drop=True)
    (box,) = boxes(app)
    assert box.enabled(box.entries()[0]) is False


# -- the keyboard ------------------------------------------------------------------------


def run(app, *keys):
    run_app(app, list(keys))


def test_f10_style_open_highlights_without_dropping_and_down_drops():
    app, bar, _ = build()
    seen = []
    run_app(app, [lambda a: bar.open(0), lambda a: seen.append(len(boxes(a))),
                  KeyEvent("down"), lambda a: seen.append(len(boxes(a)))])
    assert seen == [0, 1]


def test_up_and_down_skip_lines_and_wrap():
    app, bar, _ = build()
    seen = []
    run_app(app, [
        lambda a: bar.open(0, drop=True),
        lambda a: seen.append(boxes(a)[0].current),
        KeyEvent("down"), lambda a: seen.append(boxes(a)[0].current),
        KeyEvent("down"), lambda a: seen.append(boxes(a)[0].current),
        KeyEvent("down"), lambda a: seen.append(boxes(a)[0].current),
        KeyEvent("up"), lambda a: seen.append(boxes(a)[0].current),
    ])
    assert seen == [0, 2, 3, 0, 3]


def test_enter_closes_the_menu_and_runs_the_command_from_the_focus():
    app, bar, editor = build()
    run_app(app, [lambda a: bar.open(0, drop=True), KeyEvent("enter")])
    assert editor.saved == 1
    assert (app.modal, bar.current, app.focused) == (None, -1, editor)


def test_a_letter_chooses_the_entry_it_marks():
    app, bar, editor = build()
    run_app(app, [lambda a: bar.open(0, drop=True), KeyEvent("s", "s")])
    assert editor.saved == 1


def test_a_disabled_entry_does_nothing_and_keeps_the_menu_open():
    app, bar, editor = build()
    seen = []
    run_app(app, [lambda a: bar.open(0, drop=True), KeyEvent("b", "b"),
                  lambda a: seen.append(a.modal is not None)])
    assert seen == [True]


def test_right_opens_a_submenu_and_left_closes_it():
    app, bar, editor = build()
    seen = []
    run_app(app, [
        lambda a: bar.open(0, drop=True),
        KeyEvent("m", "m"), lambda a: seen.append(len(boxes(a))),
        KeyEvent("left"), lambda a: seen.append(len(boxes(a))),
        KeyEvent("end"), KeyEvent("right"), lambda a: seen.append(len(boxes(a))),
        KeyEvent("enter"),
    ])
    assert seen == [2, 1, 2]
    assert editor.saved == 1  # More > Again


def test_right_on_an_item_moves_along_the_bar_and_drops_the_next_box():
    app, bar, _ = build()
    seen = []
    run_app(app, [lambda a: bar.open(0, drop=True), KeyEvent("right"),
                  lambda a: seen.append((bar.current, len(boxes(a))))])
    assert seen == [(1, 1)]


def test_escape_closes_a_nested_box_then_the_whole_menu():
    app, bar, editor = build()
    seen = []
    run_app(app, [
        lambda a: bar.open(0, drop=True), KeyEvent("m", "m"),
        KeyEvent("escape"), lambda a: seen.append(len(boxes(a))),
        KeyEvent("escape"), lambda a: seen.append((a.modal, bar.current)),
    ])
    assert seen == [1, (None, -1)]
    assert app.focused is editor
    assert editor.keys_seen == []  # every key went to the menu


def test_alt_letter_switches_menus_while_one_is_open():
    app, bar, _ = build()
    seen = []
    run_app(app, [lambda a: bar.open(0, drop=True), KeyEvent("e", "e", alt=True),
                  lambda a: seen.append(bar.current)])
    assert seen == [1]


@pytest.mark.parametrize("key", [KeyEvent("e", "e", alt=True), KeyEvent("x", "x", alt=True)])
def test_open_hotkey_answers_only_for_a_letter_on_the_bar(key):
    import asyncio

    app, bar, _ = build()
    opened = asyncio.run(bar.open_hotkey(key))
    assert opened is (key.key == "e")


# -- the mouse ---------------------------------------------------------------------------


def test_a_press_on_the_bar_drops_and_a_release_on_an_entry_chooses_it():
    app, bar, editor = build()
    run_app(app, [
        MouseClickEvent(2, 0, "left"),
        MouseClickEvent(3, 2, "left", action="release"),
    ])
    assert editor.saved == 1
    assert app.modal is None


def test_a_press_outside_every_box_closes_the_menu():
    app, bar, editor = build()
    seen = []
    run_app(app, [MouseClickEvent(2, 0, "left"), MouseClickEvent(35, 10, "left"),
                  lambda a: seen.append(a.modal)])
    assert seen == [None]
    assert editor.saved == 0



# -- changing a menu from Python ------------------------------------------------------


def captions(container):
    from navml.widgets.dialog.control.control import parse_shortcut

    return [parse_shortcut(getattr(e, "text", ""))[0] or "---" for e in container.entries()]


def test_add_item_appends_or_goes_next_to_an_anchor():
    app, bar, _ = build()
    file = bar.entry("File")
    file.add_item("~Z~ip", Burn)
    file.add_item("~F~irst", before="Save")
    file.add_item("~A~fter save", after=Save)       # a command names its item
    file.add_line(before=file.entry("Zip"))
    assert captions(file) == ["First", "Save", "After save", "---", "Burn",
                              "More", "---", "Zip"]


def test_anchors_ignore_tildes_and_case_and_a_missing_one_raises():
    app, bar, _ = build()
    file = bar.entry("~f~ILE")
    assert file is bar.entries()[0]
    with pytest.raises(LookupError, match="no entry 'Nope'.*'Save'"):
        file.add_item("x", after="Nope")
    with pytest.raises(ValueError, match="not both"):
        file.add_item("x", before="Save", after="Burn")


def test_a_plugin_can_put_a_menu_of_its_own_on_the_bar():
    app, bar, editor = build()
    plugins = bar.add_submenu("~P~lugins", before="Edit")
    plugins.add_item("~S~ave twice", Save)
    assert captions(bar) == ["File", "Plugins", "Edit"]
    # Alt+P is read off the new caption: its box drops and Enter runs it.
    run_app(app, [lambda a: bar.open(0), KeyEvent("p", "p", alt=True),
                  KeyEvent("enter")])
    assert editor.saved == 1


def test_remove_and_move_entries():
    app, bar, _ = build()
    file = bar.entry("File")
    removed = file.remove_entry(Burn)
    assert removed.command is Burn and removed.parent is None
    file.move_entry("More", before="Save")
    assert captions(file) == ["More", "Save", "---"]
    file.clear()
    assert file.entries() == []


def test_item_for_searches_every_submenu():
    app, bar, _ = build()
    again = bar.item_for(Save)
    assert again is bar.entry("File").entry("Save")
    bar.entry("File").remove_entry("Save")
    assert bar.item_for(Save).text == "~A~gain"   # found in File > More
    assert bar.item_for(Burn).key == "Alt-B"


def test_a_hidden_entry_is_left_out_and_comes_back():
    app, bar, _ = build()
    file = bar.entry("File")
    file.entry("Burn").hidden = True
    assert captions(file) == ["Save", "---", "More"]
    assert file.entry("Burn") is not None      # still there, only not shown
    file.entry("Burn").hidden = False
    assert "Burn" in captions(file)


def test_a_disabled_entry_is_greyed_and_cannot_be_chosen():
    app, bar, editor = build()
    save = bar.entry("File").entry("Save")
    save.disabled = True
    seen = []
    run_app(app, [lambda a: bar.open(0, drop=True),
                  lambda a: seen.append(boxes(a)[0].enabled(save)),
                  KeyEvent("enter")])
    assert seen == [False]
    assert editor.saved == 0


def test_a_disabled_menu_on_the_bar_does_not_drop():
    app, bar, _ = build()
    bar.entry("Edit").disabled = True
    seen = []
    run_app(app, [lambda a: bar.open(1, drop=True), lambda a: seen.append(len(boxes(a)))])
    assert seen == [0]
