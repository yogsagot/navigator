"""Tooltips: a widget's ``tooltip`` shown beside the pointer once it rests, gone
at the next input, and the option strips' items saying what they are."""

from __future__ import annotations

import pytest

from conftest import IDLE, FakeTerminal, RecordingWidget, Until, run_app, settle
from navkit.application import Application
from navkit.events import KeyEvent, MouseClickEvent
from navkit.tooltip import Tooltip, plain
from navkit.widget import Widget

from navigator.settings import SETTINGS


def _motion(x, y):
    return MouseClickEvent(x, y, "none", action="move")


def _row(app, y) -> str:
    buffer = app._front
    return "".join(buffer.get(x, y)[0] or "" for x in range(buffer.width))


def _shown(app):
    return app._tooltip is not None


def _tree():
    root = RecordingWidget(" ")
    left = root.add(RecordingWidget(" ", x=0, y=0, width=20, height=10))
    right = root.add(RecordingWidget(" ", x=20, y=0, width=20, height=10))
    return root, left, right


def _app(root, **kwargs) -> Application:
    return Application(root, terminal=FakeTerminal(), tooltip_delay=50, **kwargs)


def test_resting_on_a_widget_shows_its_tooltip_beside_the_pointer():
    root, left, _right = _tree()
    left.tooltip = "Hello"
    app = _app(root)
    rows = []
    run_app(app, [_motion(3, 2), Until(_shown), lambda a: rows.append(_row(a, 3))])
    assert rows[0][4:11] == " Hello "


def test_the_next_motion_or_key_takes_it_away():
    root, left, _right = _tree()
    left.tooltip = "Hello"
    app = _app(root)
    after = []
    run_app(app, [
        _motion(3, 2), Until(_shown),
        _motion(4, 2), lambda a: after.append((a._tooltip, "Hello" in _row(a, 3))),
        Until(_shown),
        KeyEvent("a"), lambda a: after.append((a._tooltip, "Hello" in _row(a, 3))),
    ])
    assert after == [(None, False), (None, False)]


def test_a_key_or_press_does_not_ask_for_one():
    root, left, _right = _tree()
    left.tooltip = "Hello"
    app = _app(root)
    run_app(app, [_motion(3, 2), KeyEvent("a"), lambda a: None])
    assert app._tooltip is None and app._tooltip_timer is None


def test_nothing_without_a_tooltip_and_the_nearest_ancestors_otherwise():
    root, left, right = _tree()
    child = left.add(RecordingWidget(" ", x=1, y=1, width=5, height=5))
    left.tooltip = "Left"
    app = _app(root)
    texts = []
    run_app(app, [_motion(2, 2), Until(_shown), lambda a: texts.append(a._tooltip.text)])
    assert texts == ["Left"]
    app.pointer, app.hovered = (25, 2), right
    assert app.tooltip_here() == ""
    assert child.tooltip_at(0, 0) == ""


def test_tooltip_at_is_asked_in_the_widgets_own_coordinates():
    asked = []

    class Spot(Widget):
        def tooltip_at(self, x, y):
            asked.append((x, y))
            return "spot"

    root = RecordingWidget(" ")
    holder = root.add(RecordingWidget(" ", x=5, y=2, width=20, height=6))
    spot = holder.add(Spot(x=3, y=1, width=4, height=2))
    app = _app(root)
    app.pointer = (10, 4)
    app.hovered = spot
    assert app.tooltip_here() == "spot"
    assert asked == [(2, 1)]


def test_it_flips_before_the_pointer_at_the_right_and_bottom_edges():
    root, _left, right = _tree()
    right.tooltip = "Hello"
    app = _app(root)
    places = []
    run_app(app, [_motion(38, 9), Until(_shown),
                  lambda a: places.append((a._tooltip.x, a._tooltip.y, a._tooltip.width))])
    assert places == [(38 - 7, 9 - 1, 7)]


def test_several_lines_and_the_screens_width():
    tip = Tooltip("one\nthree")
    root = Widget(width=7, height=10)
    root.add(tip)
    assert tip.lines == ("one", "three")
    assert (tip.width, tip.height) == (7, 2)
    root.width = 4                              # two cells inside the padding: wrapped
    assert tip.lines == ("on", "e", "th", "re", "e")
    assert tip.width == 4


def test_it_shows_over_a_modal_for_what_is_in_it_and_not_outside():
    class Box(RecordingWidget):
        modal = True

    root, left, _right = _tree()
    left.tooltip = "Behind"
    app = _app(root)
    texts = []

    def open_box(a):
        box = a.overlay(Box(" ", x=22, y=2, width=10, height=4))
        box.tooltip = "Box"

    run_app(app, [
        open_box,
        _motion(3, 3), lambda a: texts.append(a.tooltip_here()),
        _motion(24, 3), Until(_shown), lambda a: texts.append(a._tooltip.text),
        lambda a: texts.append("Box" in _row(a, 4)),
    ])
    # Outside the modal nothing is hovered, so nothing says anything.
    assert texts == ["", "Box", True]


def test_a_zero_delay_turns_them_off():
    root, left, _right = _tree()
    left.tooltip = "Hello"
    app = Application(root, terminal=FakeTerminal(), tooltip_delay=0)
    run_app(app, [_motion(3, 2), lambda a: None])
    assert app._tooltip_timer is None


def test_call_later_runs_once_and_not_once_cancelled():
    runs = []
    app = Application(RecordingWidget(), terminal=FakeTerminal())

    async def once():
        runs.append("once")

    async def never():
        runs.append("never")

    app.call_later(0.01, once)
    cancelled = app.call_later(0.01, never)
    cancelled.cancel()
    run_app(app, [Until(lambda a: runs), lambda a: None], settle=0.05)
    assert runs == ["once"]
    with pytest.raises(ValueError):
        app.call_later(0, once)
    with pytest.raises(TypeError):
        app.call_later(1, lambda: None)


# -- the option strips ---------------------------------------------------------


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    for name in ("one", "two"):
        (tmp_path / name).mkdir()
    return tmp_path


def test_a_panels_option_strip_says_what_each_item_is(place):
    from navigator.__main__ import Navigator
    from navigator.widgets.manager.commands import SortBy, ToggleHidden

    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30))
    found = []

    def look(a):
        strip = a.manager.left.options
        spans = {s[2].command: s for s in strip.spans}
        found.append(strip.tooltip_at(spans[ToggleHidden][0], 0))
        found.append(strip.tooltip_at(spans[SortBy][0] + 1, 0))
        found.append(strip.tooltip_at(spans[ToggleHidden][1], 0))  # between two

    run_app(app, [look])
    hidden, sort, between = found
    assert hidden.startswith("Show hidden files (") and hidden.endswith(")")
    assert sort.startswith("Sort order")
    assert between == ""


def test_a_panels_strip_tooltip_shows_when_the_mouse_rests(place):
    from navigator.__main__ import Navigator
    from navigator.widgets.manager.commands import ToggleHidden

    SETTINGS.interface.tooltip_delay = 50
    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30))
    texts = []

    def rest(a):
        strip = a.manager.left.options
        start = next(s for s in strip.spans if s[2].command is ToggleHidden)[0]
        ox, oy = strip.offset()
        a.post_event(_motion(ox + strip.x + start + 1, oy + strip.y))

    run_app(app, [rest, Until(_shown), lambda a: texts.append(a._tooltip.text)])
    assert texts and texts[0].startswith("Show hidden files")


# -- the key bar ----------------------------------------------------------------


def test_a_key_bar_item_says_where_its_command_is_in_the_menus(place):
    from navigator.__main__ import Navigator

    (place / "one" / "a.txt").write_text("hi\n")
    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(130, 30))
    found = {}

    def look(tag):
        def action(a):
            bar = a.shell.keybar
            found[tag] = {key: bar.tooltip_at(start + 1, 0) for key, _c, start, _w in bar.items()}
            found[tag + " gap"] = bar.tooltip_at(bar.width - 1, 0)
        return action

    run_app(app, [look("panel"), KeyEvent("down"), KeyEvent("f4"), IDLE, lambda a: None, look("editor")])
    assert found["panel"]["f7"] == "File > Make directory"
    # Its "..." dropped; greyed with the cursor on "..", and says why.
    assert found["panel"]["f5"] == "File > Copy\nNo files are tagged, and the cursor is on none"
    assert found["panel"]["f1"] == "Help"                  # in no menu: the caption
    assert found["panel gap"] == ""
    # The editor's own menu, joined to the bar, is searched too.
    assert found["editor"]["f2"] == "Editor > File > Save"


def test_a_hint_has_no_tooltip():
    from navigator.widgets.shell.keybar.keybar import Hint, KeyBar

    bar = KeyBar()
    bar.items = lambda: [("Space", Hint("Tag"), 0, 11)]
    assert bar.tooltip_at(3, 0) == ""


# -- the clock -------------------------------------------------------------------


def test_the_clock_says_the_weekday_and_the_date_in_the_countrys_format(monkeypatch):
    from datetime import datetime

    from navigator.widgets.shell.clock import clock as clock_module

    monkeypatch.setattr(clock_module, "now", lambda: datetime(2026, 10, 28, 9, 5))
    SETTINGS.country.date_format = "iso"
    tip = clock_module.Clock().tooltip_at(0, 0)
    assert tip == "Wednesday, 2026-10-28\nClick for the calendar"


# -- the menu bar ----------------------------------------------------------------


def test_a_menu_bar_caption_says_what_its_menu_holds_and_its_key(place):
    from navigator.__main__ import Navigator

    (place / "one" / "a.txt").write_text("hi\n")
    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(130, 30))
    found = {}

    def look(tag):
        def action(a):
            bar = a.shell.menu
            for index, entry in enumerate(bar.entries()):
                start, _width = bar.item_span(index)
                found[(tag, entry.text.replace("~", ""))] = plain(bar.tooltip_at(start + 1, 0))
            found[(tag, "past the end")] = bar.tooltip_at(bar.item_span(len(bar.entries()))[0] + 1, 0)
        return action

    run_app(app, [look("panel"), KeyEvent("down"), KeyEvent("f4"), IDLE, lambda a: None, look("editor")])
    assert found[("panel", "File")] == "View, edit, copy, move, archive and delete files (Alt-F)"
    assert found[("panel", "≡")] == "About, the screen saver, SmartPad, the Trashcan and the game"
    assert found[("panel", "Panel")].endswith("(Alt-P)")
    assert found[("panel", "past the end")] == ""
    # A window's own menu brings its tooltip with it.
    assert found[("editor", "Editor")] == "Editing, the file, search, paragraphs and blocks (Alt-E)"
    # Every caption on the bar says something; only past the last is there nothing.
    assert {key for key, text in found.items() if not text} == {("panel", "past the end"), ("editor", "past the end")}


# -- the menu boxes --------------------------------------------------------------


def test_a_menu_box_row_shows_its_items_tooltip_over_the_open_menu(place):
    from navigator.__main__ import Navigator

    SETTINGS.interface.tooltip_delay = 50
    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30))
    seen = {}

    def open_file_menu(a):
        a.shell.menu.open(a.shell.menu.hotkey("f"), drop=True)

    def rows(a):
        box = a.shell.menu.session.boxes[0]
        captions = [getattr(entry, "text", "").replace("~", "") for entry in box.entries()]
        seen["single"] = box.tooltip_at(3, captions.index("Delete single file") + 1)
        seen["copy"] = box.tooltip_at(3, captions.index("Copy...") + 1)
        seen["frame"] = box.tooltip_at(0, captions.index("Delete single file") + 1)
        seen["line"] = box.tooltip_at(3, captions.index("") + 1)   # the first separator
        row = captions.index("Delete single file") + 1
        a.post_event(_motion(box.x + 4, box.y + row))

    run_app(app, [open_file_menu, rows, Until(_shown), lambda a: seen.update(shown=a._tooltip.text)])
    # Greyed with the cursor on "..": the tooltip, then why.
    assert seen["single"] == "Delete the file at the cursor, not the selection\nThe cursor is on no file"
    assert seen["copy"] == "No files are tagged, and the cursor is on none"   # its caption says the rest
    assert seen["frame"] == ""
    assert seen["line"] == ""
    assert seen["shown"] == seen["single"]   # over the open menu, a modal


# -- dialog buttons --------------------------------------------------------------


def test_a_dialog_button_names_the_keys_that_press_it(place):
    from navigator.__main__ import Navigator

    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30))
    seen = {}

    def look(a):
        dialog = a.modal
        seen["ok"] = plain(dialog.ok.tooltip_at(1, 0))
        seen["cancel"] = plain(dialog.cancel.tooltip_at(1, 0))
        dialog.cancel.tooltip = "Make nothing"
        seen["own"] = plain(dialog.cancel.tooltip_at(1, 0))
        a.post_event(KeyEvent("escape"))

    run_app(app, [KeyEvent("f7"), lambda a: None, look])
    assert seen["ok"] == "Enter, Alt-K"
    assert seen["cancel"] == "Esc, Alt-C"
    assert seen["own"] == "Make nothing (Esc, Alt-C)"


# -- check boxes and radio buttons -----------------------------------------------


def test_a_cluster_item_shows_its_own_tooltip_else_the_clusters():
    from navml.widgets.dialog.check_boxes import CheckBoxes

    boxes = CheckBoxes(width=30, height=3)
    boxes.items = ["~O~ne", "~T~wo", "T~h~ree"]
    boxes.tooltips = ["First", ""]          # the second empty, the third missing
    boxes.tooltip = "All of them"
    assert boxes.tooltip_at(5, 0) == "First"
    assert boxes.tooltip_at(5, 1) == "All of them"
    assert boxes.tooltip_at(5, 2) == "All of them"
    assert boxes.tooltip_at(5, 5) == "All of them"   # below the items


def test_the_setup_pages_check_boxes_say_their_settings_docs_in_step(place):
    from navml.widgets.dialog.cluster import Cluster
    from navigator.__main__ import Navigator
    from navigator.settings import InterfaceData
    from navigator.widgets.shell.commands import Settings as OpenSettings

    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30))
    seen = {}

    def look(a):
        dialog = a.modal
        stack, clusters = [dialog], []
        while stack:
            widget = stack.pop()
            if isinstance(widget, Cluster) and widget.tooltips:
                clusters.append(widget)
            stack.extend(widget.children)
        seen["clusters"] = clusters
        page = dialog.interface
        rows = page.options._rows()
        index = InterfaceData.OPTIONS.index("esc_user_screen")
        x = page.options.column_x(index // rows) + 1
        seen["esc"] = page.options.tooltip_at(x, index % rows)
        seen["tabs"] = page.settings_tabs.tooltip_at(1, 0)
        a.post_event(KeyEvent("escape"))

    run_app(app, [lambda a: a.spawn(a.run_command(OpenSettings)), lambda a: None, look])
    assert len(seen["clusters"]) >= 13
    # One doc an item, never more: a longer list would put a doc on the wrong box.
    for cluster in seen["clusters"]:
        assert len(cluster.tooltips) == len(cluster.items), (type(cluster.parent).__name__, cluster.items)
    assert seen["esc"] == "Esc on an empty command line toggles the console"
    assert seen["tabs"].startswith("Where Options > Settings shows its tabs")


# -- input lines -----------------------------------------------------------------


def test_an_input_line_shows_its_whole_text_only_while_it_is_cut():
    from navml.widgets.dialog.input_line import InputLine

    line = InputLine(width=12, height=1)
    line.value = "short"
    assert line.tooltip_at(3, 0) == ""
    line.value = "/home/juris/development/navigator"
    assert line.tooltip_at(3, 0) == "/home/juris/development/navigator"
    line.tooltip = "Where to"
    assert line.tooltip_at(3, 0) == "Where to\n/home/juris/development/navigator"
    line.password = True
    assert line.tooltip_at(3, 0) == "Where to"     # never a password's text


def test_a_fields_line_says_what_the_field_does():
    from navml.widgets.dialog.masked_field import MaskedField

    field = MaskedField(width=20, height=1)
    field.tooltip = "How many"
    assert field.entry.tooltip_at(1, 0) == "How many"


def test_a_long_tooltip_line_wraps_inside_the_screen():
    from navkit.tooltip import _wrap

    root = Widget(width=14, height=10)
    tip = root.add(Tooltip("/home/juris/development/navigator and more"))
    assert all(len(line) <= 12 for line in tip.lines)
    assert "".join(tip.lines).replace(" ", "") == "/home/juris/development/navigatorandmore"
    assert tip.width <= 14
    assert _wrap("two words", 5) == ["two", "words"]


def test_a_setup_pages_fields_say_their_settings_docs(place):
    from navigator.__main__ import Navigator
    from navigator.widgets.shell.commands import InterfaceSetup

    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30))
    seen = {}

    def look(a):
        page = a.modal.interface
        seen["entry"] = page.history_size.entry.tooltip_at(1, 0)
        # The label has none of its own: the lookup climbs to the field.
        caption = page.history_size.caption
        ox, oy = caption.offset()
        a.pointer, a.hovered = (ox + caption.x + 1, oy + caption.y), caption
        seen["label"] = a.tooltip_here()
        seen["language"] = page.language.tooltip
        a.post_event(KeyEvent("escape"))

    run_app(app, [lambda a: a.spawn(a.run_command(InterfaceSetup)), lambda a: None, look])
    doc = "Entries kept per history list: input lines, viewed and edited files"
    assert seen["entry"] == doc and seen["label"] == doc
    assert seen["language"].startswith("The language captions and messages are in")


# -- list boxes ------------------------------------------------------------------


def test_a_list_row_shows_its_whole_text_only_while_it_is_cut():
    from navml.widgets.dialog.list_viewer import ListViewer

    lines = ListViewer(width=12, height=5)
    lines.items = ["short", "/home/juris/development/navigator"]
    lines.tooltip = "Pick one"
    top = lines.inset + lines.header
    assert lines.tooltip_at(3, top) == "Pick one"                      # fits: the list's own
    assert lines.tooltip_at(3, top + 1) == "/home/juris/development/navigator"
    assert lines.tooltip_at(3, top + 3) == "Pick one"                  # below the items


def test_a_list_painting_its_own_rows_says_nothing_unless_it_chooses():
    from navml.widgets.dialog.list_viewer import ListViewer
    from navigator.widgets.shell.error_dialog.trace_list import TraceList

    class Painted(ListViewer):
        def render_row(self, surface, y, index, item):
            pass

    long = "  File \"/home/juris/development/navigator/navkit/application.py\", line 1"
    for cls, expected in ((Painted, ""), (TraceList, long)):
        rows = cls(width=20, height=5)
        rows.items = [long]
        assert rows.tooltip_at(3, rows.inset + rows.header) == expected, cls.__name__


# -- drop-down lists -------------------------------------------------------------


def test_a_drop_downs_button_line_and_list_each_say_something(place):
    from navigator.__main__ import Navigator
    from navigator.widgets.shell.commands import InterfaceSetup

    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30))
    seen = {}

    def look(a):
        field = a.modal.interface.language
        seen["button"] = field.history.tooltip_at(1, 0)
        seen["line"] = field.entry.tooltip_at(1, 0)
        dropped = field.history.open()
        seen["list"] = type(dropped).__name__
        a.post_event(KeyEvent("escape"))
        a.post_event(KeyEvent("escape"))

    run_app(app, [lambda a: a.spawn(a.run_command(InterfaceSetup)), lambda a: None, look])
    assert seen["button"] == "Choose from the list (Down)"
    assert seen["line"].startswith("The language captions and messages are in")
    assert seen["list"] == "HistoryList"   # a ListViewer: a cut row shows whole


def test_a_history_button_offers_the_earlier_entries():
    from navml.widgets.dialog.history import History

    button = History()
    assert button.tooltip_at(1, 0) == ""            # nothing to drop
    button.history_id = "mkdir"
    assert button.tooltip_at(1, 0) == "Earlier entries (Down)"
    button.tooltip = "Directories made before"
    assert button.tooltip_at(1, 0) == "Directories made before"


# -- tabs ------------------------------------------------------------------------


@pytest.mark.parametrize("side", ["simple", "top", "left"])
def test_a_settings_tab_says_what_its_page_holds_and_the_page_does_not(place, side):
    from navigator.__main__ import Navigator
    from navigator.widgets.shell.commands import Settings as OpenSettings

    SETTINGS.interface.settings_tabs = side
    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30))
    seen = {}

    def look(a):
        tabs = a.modal.tabs
        at, index, _caption = next(t for t in tabs.tabs() if t[2] == "Confirmations")
        x, y = (2, at) if side == "left" else (at + 1, 0 if side == "simple" else 1)
        seen["tab"] = tabs.tooltip_at(x, y)
        seen["page"] = tabs.tooltip_at(tabs.width - 2, tabs.height - 2)   # inside the page, blank
        a.post_event(KeyEvent("escape"))

    run_app(app, [lambda a: a.spawn(a.run_command(OpenSettings)), lambda a: None, look])
    assert seen["tab"] == "Which actions ask before they act"
    assert seen["page"] == ""


def test_the_tab_arrows_and_a_cut_left_caption():
    from navml.widgets.dialog.tab_page import TabPage
    from navml.widgets.dialog.tab_view import TabView

    view = TabView(width=24, height=12)
    for title in ("One", "A very long caption indeed", "Three", "Four", "Five"):
        view.add(TabPage(title=title))
    view.side = "left"
    at = next(t[0] for t in view.tabs() if t[1] == 1)
    assert view.tooltip_at(2, at) == "A very long caption indeed"   # cut by the column
    first = next(t[0] for t in view.tabs() if t[1] == 0)
    assert view.tooltip_at(2, first) == ""                          # fits: nothing more to say
    view.side = "top"
    view.width = 20                                                 # too narrow: it scrolls
    earlier, later = view.can_scroll()
    assert later and view.tooltip_at(view.width - 1, 1) == "Later tabs"


# -- scroll bars -----------------------------------------------------------------


def test_a_scroll_bar_has_no_tooltip_and_does_not_borrow_its_lists():
    from navml.widgets.dialog.list_viewer import ListViewer

    long = "/home/juris/development/navigator/" * 2
    root = RecordingWidget(" ")
    lines = root.add(ListViewer(x=0, y=0, width=14, height=5))
    lines.items = [long] * 20                       # more than fit: the bar shows
    lines.tooltip = "Pick one"
    app = _app(root)
    settle()
    bar = next(child for child in lines.children if type(child).__name__ == "ScrollBar")
    assert bar.visible
    row = lines.inset + lines.header
    app.pointer, app.hovered = (bar.x, bar.y + 1), bar
    assert app.tooltip_here() == ""
    app.pointer, app.hovered = (3, row), lines
    assert app.tooltip_here() == long                # beside it, the row says itself
    lines.items = [long]                            # all fit: the bar goes, the frame stays
    settle()
    assert lines.tooltip_at(lines.width - 1, row) == "Pick one"


# -- the panel's column titles ---------------------------------------------------


def test_a_column_title_says_what_it_shows_and_what_a_click_sorts_by(place):
    from navigator.__main__ import Navigator

    (place / "one" / "a.txt").write_text("hi\n")
    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(130, 30))
    seen = {}

    def look(a):
        panel = a.manager.left
        panel.view_mode = "detailed"
        panel.sort_by("name", reverse=False)
        settle()
        columns = {key: (left, width) for key, left, width in panel.detail_columns}
        name_x = columns["name"][0] + 1
        seen["name"] = panel.tooltip_at(name_x, panel.inset)
        seen["size"] = panel.tooltip_at(columns["size"][0] + 1, panel.inset)
        seen["row"] = panel.tooltip_at(name_x, panel.inset + 1)
        # What the tooltip promised is what the click does.
        panel.sort_by_column("name")
        seen["after"] = (panel.sort_mode, panel.sort_reverse)

    run_app(app, [look])
    arrow = "↓"
    assert seen["name"] == f"The file's name\nA click sorts by Name {arrow}"
    assert seen["after"] == ("name", True)
    assert seen["size"].startswith("The file's size\nA click sorts by Size ")
    assert seen["row"] == ""


# -- the panel's info lines ------------------------------------------------------


def test_the_info_lines_say_whole_what_they_cut_or_round(place):
    import os

    from navigator.__main__ import Navigator

    long = "a-file-whose-name-is-far-too-long-for-any-panel-to-show-whole.txt"
    (place / "one" / long).write_text("x" * 12345)
    os.symlink(place / "one" / long, place / "one" / "link")
    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30))
    seen = {}

    def look(a):
        panel = a.manager.left
        panel.cursor = next(i for i, item in enumerate(panel.items) if item.name == long)
        settle()
        parts = [part for _text, part in panel.info_lines]
        first = panel.height - panel.inset - panel.info_height
        first += 1 if SETTINGS.file_manager.info_divider else 0

        def at(index):
            return panel.tooltip_at(panel.inset + 1, first + index)

        seen["current"] = at(parts.index("current-file"))
        if "free-space" in parts:
            seen["free"] = at(parts.index("free-space"))
            seen["free_bytes"] = panel.free_space[0]
        seen["divider"] = panel.tooltip_at(panel.inset + 1, first - 1) if SETTINGS.file_manager.info_divider else ""
        panel.cursor = next(i for i, item in enumerate(panel.items) if item.name == "link")
        settle()
        seen["link"] = at(parts.index("current-file") + 1)    # the line under it: -> target

    run_app(app, [look])
    name, size, date = seen["current"].split("\n")[:3]
    assert name == long and size == "12,345 bytes" and date
    assert seen["link"] == f"-> {place / 'one' / long}"
    assert seen["free"].startswith(f"{seen['free_bytes']:,} free bytes on ")
    assert seen["divider"] == ""


# -- the panel's rows ------------------------------------------------------------


@pytest.mark.parametrize("mode", ["simple", "detailed", "list"])
def test_a_panel_row_names_itself_whole_while_cut_and_a_links_target(place, mode):
    import os

    from navigator.__main__ import Navigator

    long = "a-file-whose-name-is-far-too-long-for-any-panel-to-show-whole.txt"
    (place / "one" / long).write_text("x")
    (place / "one" / "short.txt").write_text("x")
    os.symlink("short.txt", place / "one" / "link")
    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30))
    seen = {}

    def look(a):
        panel = a.manager.left
        panel.view_mode = mode
        settle()
        top = panel.inset + panel.header

        def over(name, column="name"):
            index = next(i for i, item in enumerate(panel.items) if item.name == name)
            if mode == "list":
                first, left, _w = next(c for c in panel.list_columns if c[0] <= index < c[0] + panel.rows)
                x, y = left + panel.gutter, top + index - first
            elif mode == "detailed":
                y = top + index - panel.scroll
                x = next(left for key, left, _w in panel.detail_columns if key == column) + 1
            else:
                y, x = top + index - panel.scroll, panel.inset + panel.gutter
            return panel.tooltip_at(x, y)

        seen["long"] = over(long)
        seen["short"] = over("short.txt")
        seen["link"] = over("link")
        seen["up"] = over("..")
        if mode == "detailed":
            seen["size"] = over(long, "size")
            panel.scroll_names(3)                    # Left/Right: every name is cut now
            settle()
            seen["scrolled"] = over("short.txt")

    run_app(app, [look])
    assert seen["long"] == long
    assert seen["short"] == ""
    assert seen["link"] == "-> short.txt"
    assert seen["up"] == ""
    if mode == "detailed":
        assert seen["size"] == ""                    # a size is never cut
        assert seen["scrolled"] == "short.txt"


# -- the panel's title -----------------------------------------------------------


def test_the_panel_title_says_what_it_leaves_out(place):
    from navigator.__main__ import Navigator
    from navigator.lib.system.gitstatus import GitState

    deep = place / "one" / "a-rather-long-directory-name" / "and-another-one-below-it"
    deep.mkdir(parents=True)
    app = Navigator(deep, place / "two", terminal=FakeTerminal(60, 24))
    seen = {}

    def over_title(panel):
        text = panel.title_text()
        return panel.tooltip_at(panel.label_x(text) + 1, 0)

    def look(a):
        panel = a.manager.left
        seen["cut"] = over_title(panel)
        seen["beside"] = panel.tooltip_at(1, 0)            # the frame, past the title
        panel.file_mask = "*.c"
        settle()
        seen["mask"] = plain(over_title(panel))
        panel.file_mask = "*"
        panel.git = GitState("main", ahead=2, behind=1)
        settle()
        seen["git"] = over_title(panel)
        panel.git = GitState("1a2b3c4", detached=True)
        settle()
        seen["detached"] = over_title(panel)

    run_app(app, [look])
    assert seen["cut"] == str(deep)
    assert seen["beside"] == ""
    assert seen["mask"] == f"{deep}\nOnly files matching *.c are shown (Alt-Del)"
    assert seen["git"].endswith("Git work tree, on main\n2 commits ahead of its upstream\n1 commit behind its upstream")
    assert seen["detached"].endswith("Git work tree, HEAD detached at 1a2b3c4")


def test_a_panel_title_that_says_it_all_has_no_tooltip(place):
    from navigator.__main__ import Navigator

    # Wide enough for the test's own temporary path to fit whole.
    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(240, 30))
    seen = []

    def look(a):
        panel = a.manager.left
        text = panel.title_text()
        seen.append(panel.tooltip_at(panel.label_x(text) + 1, 0))

    run_app(app, [look])
    assert seen == [""]


# -- the character tables --------------------------------------------------------


def test_the_unicode_grid_describes_the_character_under_the_pointer():
    from navigator.widgets.shell.unicode_grid.unicode_grid import CELL, UnicodeGrid

    root = RecordingWidget(" ")
    grid = root.add(UnicodeGrid(x=0, y=0, width=20, height=8))
    _app(root)
    grid.show([0x41, 0x2502, 0xE9])
    settle()
    top = grid.inset + grid.header
    first, name = grid.tooltip_at(grid.inset + CELL + 1, top).split("\n")[0].split("  ")[::2]
    assert (first, name) == ("U+2502", "BOX DRAWINGS LIGHT VERTICAL")
    assert "UTF-8 E2 94 82" in grid.tooltip_at(grid.inset + CELL + 1, top)
    assert grid.tooltip_at(grid.inset + 3 * CELL + 1, top) == ""     # past the last character
    # An icon is named by the chart's index, once it has one.
    grid.show([0xE5FA])
    grid.nerd_names = lambda: {0xE5FA: ("seti-folder",)}
    settle()
    assert "nf-seti-folder" in grid.tooltip_at(grid.inset + 1, top)


def test_the_ascii_chart_gives_a_characters_codes_and_its_unicode_name():
    from navigator.widgets.shell.char_table.char_table import CharTable

    table = CharTable(width=32, height=8)
    assert table.tooltip_at(1, 6) == "Char: ┴ Decimal: 193 Hex: c1\nU+2534  ┴  BOX DRAWINGS LIGHT UP AND HORIZONTAL"
    assert table.tooltip_at(0, 0) == "Char:   Decimal:   0 Hex: 00"   # 0 is drawn blank
    assert table.tooltip_at(5, 9) == ""                               # below the chart


def test_a_list_painting_its_own_items_shows_no_raw_row_text():
    from navml.widgets.dialog.list_viewer import ListViewer

    class Cells(ListViewer):
        def render_items(self, surface):
            pass

    rows = Cells(width=8, height=4)
    rows.items = [[0x41, 0x42, 0x43, 0x44, 0x45]]                     # str() would be wide
    assert rows.tooltip_at(2, rows.inset + rows.header) == ""


# -- the root mark ---------------------------------------------------------------


def test_the_root_mark_says_what_it_means_and_how_it_ends():
    from navkit import i18n
    from navigator.widgets.shell.root_mark import RootMark

    SETTINGS.system.root_timeout = 15
    mark = RootMark()
    lines = mark.tooltip_at(1, 0).split("\n")
    assert lines == ["Root access is open",
                     "A step refused permission is done again as root without asking",
                     "It closes after 15 idle minutes",
                     "Utilities > Close root access closes it now"]
    SETTINGS.system.root_timeout = 0                     # closed after each step: no idle time to name
    assert len(mark.tooltip_at(1, 0).split("\n")) == 3
    # The menu path reads as the menu does, in the language shown.
    i18n.register_package("navigator.locales")
    i18n.LOCALE.code = "lv"
    assert mark.tooltip_at(1, 0).split("\n")[-1].startswith("Rīki > Aizvērt root piekļuvi")


# -- the panel divider -----------------------------------------------------------


def test_the_divider_says_how_to_move_it_where_a_press_takes_hold(place):
    from navigator.__main__ import Navigator

    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30))
    seen = {}

    def rest(a, x, y):
        a.pointer = (x, y)
        a._hover(_motion(x, y))
        return a.tooltip_here()

    def look(a):
        manager = a.manager
        first, second = manager._sides()
        ox, oy = manager.offset()
        mx, my = ox + manager.x, oy + manager.y
        row = 5
        seen["right"] = rest(a, mx + second.x, my + row)          # the right side's left frame
        seen["left"] = rest(a, mx + second.x - 1, my + row)       # the left side's right frame
        seen["inside"] = rest(a, mx + second.x + 6, my + row)     # a row of the right panel

    run_app(app, [look])
    expected = "Drag to resize the panels (Alt-Left, Alt-Right)\nDouble-click to split them evenly"
    assert seen["right"] == expected
    assert seen["left"] == expected
    assert "Drag to resize" not in seen["inside"]


# -- the dialogs' check boxes ----------------------------------------------------


def test_every_check_box_groups_tooltips_are_in_step_with_its_items():
    """A markup ``tooltips:`` list one short or long would put each tooltip
    on the wrong box; a conditional ``items:`` is allowed a longer list."""
    import ast
    import re
    from pathlib import Path

    checked = 0
    for path in sorted(Path("navigator").rglob("*.nml")) + sorted(Path("navml").rglob("*.nml")):
        lines = path.read_text(encoding="utf-8").split("\n")
        for index, line in enumerate(lines):
            if not re.match(r"^\s*(CheckBoxes|RadioButtons):\s*$", line):
                continue
            indent = len(line) - len(line.lstrip())
            block = []
            for following in lines[index + 1:]:
                if following.strip() and len(following) - len(following.lstrip()) <= indent:
                    break
                block.append(following.strip())
            items = next((b[len("items:"):].strip() for b in block if b.startswith("items:")), None)
            tips = next((b[len("tooltips:"):].strip() for b in block if b.startswith("tooltips:")), None)
            if items is None or tips is None:
                continue
            tips = ast.literal_eval(tips)
            if " if " in items:
                assert len(tips) >= max(len(ast.literal_eval(part.strip())) for part in
                                        re.split(r"\s+if\s+.*?\s+else\s+", items)), f"{path}:{index + 1}"
            else:
                assert len(tips) == len(ast.literal_eval(items)), f"{path}:{index + 1}"
            checked += 1
    assert checked >= 25


def test_the_copy_dialogs_boxes_say_what_they_do(place):
    from navigator.__main__ import Navigator

    (place / "one" / "a.txt").write_text("x")
    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30))
    seen = {}

    def look(a):
        boxes = a.modal.options
        rows = boxes._rows()
        index = 3                                           # Remove source files
        x = boxes.column_x(index // rows) + 1
        seen["remove"] = boxes.tooltip_at(x, index % rows)
        a.post_event(KeyEvent("escape"))

    run_app(app, [lambda a: setattr(a.manager.left, "cursor", 1), KeyEvent("f5"),
                  Until(lambda a: a.modal is not None and hasattr(a.modal, "options")), look])
    assert seen["remove"] == "Delete the originals once copied: a move"


# -- ways of working: follow-on, keys set apart, reasons, the menu's hint, Shift+F11 ----------


def test_once_one_has_shown_the_next_follows_on_without_the_whole_delay():
    root, left, right = _tree()
    left.tooltip, right.tooltip = "Left", "Right"
    app = _app(root)
    seen = []

    def slow(a):
        a.tooltip_delay = 60_000         # only a follow-on can show in time now

    run_app(app, [
        _motion(3, 2), Until(_shown), slow,
        _motion(25, 2), Until(_shown), lambda a: seen.append(a._tooltip.text),
        KeyEvent("a"), lambda a: seen.append(a._tooltip_warm_until),
        _motion(3, 2), lambda a: seen.append(a._tooltip_timer.seconds),
    ])
    assert seen == ["Right", 0.0, 60.0]   # a key made the next one wait again


def test_markup_sets_a_key_apart_and_a_plain_tilde_is_drawn():
    from navkit.tooltip import Markup, lines, plain, with_keys

    tip = Tooltip(with_keys("Close ~x~", "Ctrl-F4"))
    root = Widget(width=40, height=5)
    root.add(tip)
    assert isinstance(tip.text, Markup)
    assert tip.lines == ("Close ~x~ (Ctrl-F4)",)
    ((_line, marks),) = tip._pieces
    assert [i for i, marked in enumerate(marks) if marked] == list(range(11, 18))
    assert Tooltip("a ~b~ c").lines == ("a ~b~ c",)        # plain: not markup
    assert with_keys("Zoom", "") == "Zoom" and not isinstance(with_keys("Zoom", ""), Markup)
    joined = lines("/a/~b", with_keys("Go", "F5"), "")
    assert isinstance(joined, Markup) and plain(joined) == "/a/~b\nGo (F5)"


def test_a_widget_saying_why_it_refuses_a_command_greys_it_and_gives_the_reason():
    from navkit import commands

    class Nope(commands.Command):
        pass

    class Holder(RecordingWidget):
        async def on_nope(self, event):
            return True

        def refusal(self, command):
            return "Not today" if isinstance(command, Nope) else ""

    root = RecordingWidget(" ")
    holder = root.add(Holder(" ", width=10, height=2))
    holder.can_focus = True
    app = _app(root)
    holder.focus()
    assert not app.command_enabled(Nope)
    assert app.command_disabled_reason(Nope) == "Not today"
    assert app.command_disabled_reason(commands.Command) == ""      # nobody's: no reason


def test_the_key_bar_shows_the_highlighted_menu_rows_tooltip_while_a_menu_is_open(place):
    from navigator.__main__ import Navigator

    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(130, 30))
    seen = {}

    def open_file_menu(a):
        a.shell.menu.open(a.shell.menu.hotkey("f"), drop=True)

    def highlight(a):
        box = a.shell.menu.session.boxes[0]
        captions = [getattr(entry, "text", "").replace("~", "") for entry in box.entries()]
        box.current = captions.index("Delete single file")

    def look(a):
        seen["hint"] = a.shell.keybar.menu_hint()
        seen["row"] = _row(a, a.shell.keybar.y + a.shell.keybar.offset()[1])
        seen["tip"] = a.shell.keybar.tooltip_at(3, 0)

    run_app(app, [open_file_menu, highlight, IDLE, look, KeyEvent("escape"), KeyEvent("escape"),
                  lambda a: seen.update(closed=a.shell.keybar.menu_hint())])
    assert seen["hint"] == "Delete the file at the cursor, not the selection -- The cursor is on no file"
    assert "Delete the file at the cursor" in seen["row"]
    assert seen["tip"] == ""                       # the bar's own tooltips stand aside
    assert seen["closed"] == ""


def test_shift_f11_shows_the_tooltip_of_where_the_keyboard_is_until_the_next_key(place):
    from navigator.__main__ import Navigator

    name = "a" * 70 + ".txt"
    (place / "one" / name).write_text("hi\n")
    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(80, 25))
    seen = {}

    def ok_focused(a):
        a.modal.ok.focus()

    run_app(app, [
        KeyEvent("down"), KeyEvent("shift+f11"), lambda a: seen.update(row=a._tooltip and a._tooltip.text),
        KeyEvent("up"), lambda a: seen.update(after=a._tooltip),
        KeyEvent("f7"), lambda a: None, ok_focused, KeyEvent("shift+f11"),
        lambda a: seen.update(button=a._tooltip and plain(a._tooltip.text)),
        KeyEvent("escape"),
    ])
    assert seen["row"] == name                     # the cut name, at the cursor's row
    assert seen["after"] is None
    assert seen["button"] == "Enter, Alt-K"        # past the modal, which the app's table stands aside for


# -- the sweep: nothing new goes without -------------------------------------------------


def _nml_blocks(kind):
    """``(path, line number, indent, {key: value})`` for every *kind* element of
    every component's markup, its own lines only."""
    import re
    from pathlib import Path

    for path in sorted(Path("navigator").rglob("*.nml")) + sorted(Path("navml").rglob("*.nml")):
        lines = path.read_text(encoding="utf-8").split("\n")
        for index, line in enumerate(lines):
            if not re.match(rf"^\s*{kind}:\s*$", line):
                continue
            indent = len(line) - len(line.lstrip())
            own = {}
            for following in lines[index + 1:]:
                depth = len(following) - len(following.lstrip())
                if following.strip() and depth <= indent:
                    break
                if depth == indent + 4 and ":" in following and not following.strip().startswith("#"):
                    key, _, value = following.strip().partition(":")
                    own[key.strip()] = value.strip()
            yield path, index + 1, indent, own


def test_every_menu_on_the_bar_says_what_it_holds_and_no_tooltip_repeats_its_caption():
    """A window's menu joins the bar, so a top-level one goes without a
    tooltip nowhere; and a tooltip saying the caption again says nothing."""
    import ast

    top = 0
    for kind in ("SubMenu", "MenuItem"):
        for path, line, indent, own in _nml_blocks(kind):
            if kind == "SubMenu" and indent == 4 and "context" not in own:
                assert own.get("tooltip"), f"{path}:{line} {own.get('text')}"
                top += 1
            if "tooltip" in own and "text" in own:
                caption = ast.literal_eval(own["text"]).replace("~", "").rstrip(".…").strip()
                assert ast.literal_eval(own["tooltip"]).strip().lower() != caption.lower(), f"{path}:{line}"
    assert top >= 15


def test_every_tab_views_tooltips_are_in_step_with_its_pages(place):
    from navigator.__main__ import Navigator
    from navigator.widgets.shell.commands import Settings as OpenSettings
    from navml.widgets.dialog.tab_view import TabView

    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30))
    seen = []

    def look(a):
        stack = [a.modal]
        while stack:
            widget = stack.pop()
            if isinstance(widget, TabView) and widget.tooltips:
                seen.append((len(widget.tooltips), len(widget.pages)))
            stack.extend(widget.children)
        a.post_event(KeyEvent("escape"))

    run_app(app, [lambda a: a.spawn(a.run_command(OpenSettings)), lambda a: None, look])
    assert seen and all(tips == pages for tips, pages in seen), seen


def test_shift_f11_has_something_to_say_on_every_settings_control(place):
    """Every control on every page of Options > Settings but a button (whose
    tooltip is its keys) answers Shift+F11 -- which is to say the pointer too."""
    from navigator.__main__ import Navigator
    from navigator.widgets.shell.commands import Settings as OpenSettings
    from navml.widgets.dialog.button import Button

    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30))
    silent, asked = [], []

    def look(a):
        stack = [a.modal]
        while stack:
            widget = stack.pop()
            stack.extend(widget.children)
            if not widget.can_focus or isinstance(widget, Button):
                continue
            ax, ay = widget.tooltip_anchor()
            ox, oy = widget.offset()
            x, y = ox + widget.x + ax, oy + widget.y + ay
            asked.append(widget)
            if not a.tooltip_from(widget.widget_at(widget.x + ax, widget.y + ay) or widget, x, y):
                silent.append((type(widget).__name__, type(widget.parent).__name__))
        a.post_event(KeyEvent("escape"))

    run_app(app, [lambda a: a.spawn(a.run_command(OpenSettings)), lambda a: None, look])
    assert len(asked) >= 50
    assert silent == []
