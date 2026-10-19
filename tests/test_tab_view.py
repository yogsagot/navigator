"""navml's ``TabView``: pages behind a row of tabs, one shown at a time."""

from __future__ import annotations

from conftest import FakeTerminal, run_app
from navkit.application import Application
from navkit.events import KeyEvent, MouseClickEvent
from navkit.screen import ScreenBuffer
from navkit.widget import Widget

from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.dialog.tab_view import TabView


def rows(buffer: ScreenBuffer) -> list[str]:
    return ["".join(buffer.get(x, y)[0] or " " for x in range(buffer.width)) for y in range(buffer.height)]


def page(tabs: TabView, title: str, *captions: str) -> Widget:
    """A page of *tabs* with one box a caption, a row each from its second."""
    widget = Widget(parent=tabs)
    widget.title = title
    for row, caption in enumerate(captions, start=1):
        box = CheckBoxes(parent=widget, items=[caption])
        box.x, box.y, box.width, box.height = 1, row, 16, 1
    return widget


def dialog(width: int = 40) -> tuple[Dialog, TabView]:
    box = Dialog(modal_width=width, modal_height=14, title="Tabs")
    tabs = TabView(parent=box)
    tabs.x, tabs.y, tabs.width, tabs.height = 1, 1, width - 2, 9
    return box, tabs


def look(read):
    """An action recording *read(dialog)* while the dialog is up."""
    read.look = True
    return read


def run(box: Dialog, *actions) -> list:
    """*box* up over an empty desktop, then *actions*; what each :func:`look`
    among them read, in order.  Any other callable is given the dialog."""
    app = Application(Widget(), terminal=FakeTerminal(80, 25))
    seen = []

    def bound(action):
        if getattr(action, "look", False):
            return lambda a: seen.append(action(box))
        if callable(action):
            return lambda a: action(box)
        return action

    run_app(app, [lambda a: a.spawn(box.execute(a)), lambda a: None,
                  *[bound(action) for action in actions], lambda a: None])
    return seen


def test_the_tabs_stand_on_a_baseline_the_current_one_double_and_open_into_its_page():
    box, tabs = dialog()
    first = page(tabs, "One", "~A~lpha")
    second = page(tabs, "Two")
    third = page(tabs, "Three")
    tabs.x, tabs.y, tabs.width, tabs.height = 0, 0, 30, 6
    assert not tabs.scrolls and tabs.can_scroll() == (False, False)
    assert first.visible and not second.visible and not third.visible
    tabs.arrange()
    # A page's first row is the baseline, as a dialog's is its frame.
    assert (first.x, first.y, first.width, first.height) == (0, 2, 30, 4)
    buffer = ScreenBuffer(30, 6)
    tabs.render_tree(buffer)
    assert rows(buffer)[:4] == [
        "╔═════╗┌─────┐┌───────┐       ",
        "║ One ║│ Two ││ Three │       ",
        "╜     ╙┴─────┴┴───────┴───────",
        " [ ] Alpha                    ",
    ]


def test_tabs_that_do_not_fit_scroll_one_row_between_arrows():
    box, tabs = dialog()
    for title in ("One", "Two", "Three"):
        page(tabs, title)
    tabs.x, tabs.y, tabs.width, tabs.height = 0, 0, 20, 6
    assert tabs.scrolls
    assert [(x, title) for x, _, title in tabs.tabs()] == [(1, "One"), (8, "Two")]
    assert tabs.can_scroll() == (False, True)
    buffer = ScreenBuffer(20, 6)
    tabs.render_tree(buffer)
    assert rows(buffer)[1] == " ║ One ║│ Two │    ►"
    tabs.scroll(1)
    assert [title for _, _, title in tabs.tabs()] == ["Two", "Three"]
    assert tabs.can_scroll() == (True, False)
    # Never so far on that the row ends short with tabs hidden before it.
    tabs.scroll(1)
    assert [title for _, _, title in tabs.tabs()] == ["Two", "Three"]
    buffer = ScreenBuffer(20, 6)
    tabs.render_tree(buffer)
    assert rows(buffer)[1] == "◄│ Two ││ Three │   "


def test_the_arrows_scroll_and_a_tab_chosen_out_of_sight_comes_into_view():
    box, tabs = dialog(22)
    for title in ("One", "Two", "Three"):
        page(tabs, title, f"~{title[0]}~{title[1:]}")
    seen = run(
        box,
        look(lambda b: tabs.width),
        lambda b: b.spawn(tabs.on_mouse_click(MouseClickEvent(19, 1, "left"))), lambda a: None,
        look(lambda b: ([t for _, _, t in tabs.tabs()], tabs.current)),
        lambda b: b.spawn(tabs.on_mouse_click(MouseClickEvent(0, 1, "left"))), lambda a: None,
        look(lambda b: [t for _, _, t in tabs.tabs()]),
        KeyEvent("pageup", ctrl=True), lambda a: None,
        look(lambda b: (tabs.current, [t for _, _, t in tabs.tabs()])),
    )
    assert seen == [20, (["Two", "Three"], 0), ["One", "Two"], (2, ["Two", "Three"])]


def test_ctrl_pgdn_and_pgup_turn_the_pages_round_and_the_keyboard_follows():
    box, tabs = dialog()
    first = page(tabs, "First", "~A~lpha")
    second = page(tabs, "Second", "~B~eta")
    seen = run(
        box,
        look(lambda b: b.application.focused.items),
        KeyEvent("pagedown", ctrl=True), lambda a: None,
        look(lambda b: (tabs.current, b.application.focused.items, first.visible, second.visible)),
        KeyEvent("pagedown", ctrl=True), lambda a: None,
        look(lambda b: (tabs.current, b.application.focused.items)),
        KeyEvent("pageup", ctrl=True), lambda a: None,
        look(lambda b: tabs.current),
    )
    assert seen == [["~A~lpha"], (1, ["~B~eta"], False, True), (0, ["~A~lpha"]), 1]


def test_a_click_on_a_tab_shows_its_page():
    box, tabs = dialog()
    page(tabs, "First", "~A~lpha")
    page(tabs, "Second", "~B~eta")
    seen = run(
        box,
        lambda b: b.spawn(tabs.on_mouse_click(MouseClickEvent(9, 0, "left"))),
        lambda a: None,
        look(lambda b: (tabs.current, b.application.focused.items)),
        lambda b: b.spawn(tabs.on_mouse_click(MouseClickEvent(30, 0, "left"))),
        lambda a: None,
        look(lambda b: tabs.current),
    )
    assert seen == [(1, ["~B~eta"]), 1]


def test_a_click_on_a_tabs_foot_on_the_baseline_shows_its_page_too():
    box, tabs = dialog()
    page(tabs, "First", "~A~lpha")
    page(tabs, "Second", "~B~eta")

    def click_foot(b):
        # Through the whole tree: the baseline is the shown page's first row,
        # which the page leaves to the tabs.
        x, y = box.x + tabs.x + 12, box.y + tabs.y + tabs.strip_rows
        b.application.post_event(MouseClickEvent(x, y, "left"))

    seen = run(box, click_foot, lambda a: None, look(lambda b: tabs.current))
    assert seen == [1]


def test_the_wheel_over_the_tabs_scrolls_them_and_leaves_the_current_one():
    box, tabs = dialog(22)
    for title in ("One", "Two", "Three"):
        page(tabs, title, f"~{title[0]}~{title[1:]}")

    def wheel(button, y=1):
        def action(b):
            b.application.post_event(MouseClickEvent(box.x + tabs.x + 5, box.y + tabs.y + y, button))
        return action

    def titles(b):
        return [t for _, _, t in tabs.tabs()], tabs.current

    seen = run(
        box,
        wheel("wheel_down"), lambda a: None, look(titles),
        wheel("wheel_up", y=2), lambda a: None, look(titles),
        wheel("wheel_right", y=0), lambda a: None, look(titles),
        wheel("wheel_down", y=4), lambda a: None, look(titles),
    )
    assert seen == [
        (["Two", "Three"], 0),
        (["One", "Two"], 0),
        (["Two", "Three"], 0),
        (["Two", "Three"], 0),   # below the strip, on the page: not the tabs'
    ]


def test_alt_letters_and_tab_stay_on_the_page_shown():
    box, tabs = dialog()
    first = page(tabs, "First", "~A~lpha")
    second = page(tabs, "Second", "~A~nother", "~B~eta")
    seen = run(
        box,
        KeyEvent("a", alt=True), KeyEvent("b", alt=True), lambda a: None,
        look(lambda b: (first.children[0].value, second.children[0].value, second.children[1].value)),
        look(lambda b: [type(w).__name__ for w in b.focusable()]),
    )
    assert seen[0] == (1, 0, 0)
    assert seen[1] == ["CheckBoxes", "Button", "Button", "TabView"]


def test_a_list_leaves_ctrl_pgdn_to_the_tabs():
    box, tabs = dialog()
    first = page(tabs, "First")
    items = ListViewer(parent=first, framed=False)
    items.x, items.y, items.width, items.height = 1, 1, 10, 3
    items.items = [str(n) for n in range(20)]
    page(tabs, "Second", "~B~eta")
    seen = run(
        box,
        look(lambda b: b.application.focused is items),
        KeyEvent("pagedown", ctrl=True), lambda a: None,
        look(lambda b: (tabs.current, items.cursor)),
    )
    assert seen == [True, (1, 0)]


# -- down the left --------------------------------------------------------------


def test_down_the_left_a_tab_a_row_the_current_one_marked_beside_an_unbroken_rule():
    box, tabs = dialog()
    first = page(tabs, "One", "~A~lpha")
    page(tabs, "Two")
    page(tabs, "Three")
    tabs.side = "left"
    tabs.x, tabs.y, tabs.width, tabs.height = 0, 0, 24, 4
    assert tabs.column == 8 and not tabs.scrolls
    assert [(y, title) for y, _, title in tabs.tabs()] == [(0, "One"), (1, "Two"), (2, "Three")]
    tabs.arrange()
    assert (first.x, first.y, first.width, first.height) == (9, 0, 15, 4)
    buffer = ScreenBuffer(24, 4)
    tabs.render_tree(buffer)
    assert rows(buffer) == [
        "► One   │               ",
        "  Two   │ [ ] Alpha     ",
        "  Three │               ",
        "        │               ",
    ]
    assert tabs.tab_at(3, 2) == 2 and tabs.tab_at(12, 2) is None


def test_down_the_left_more_tabs_than_rows_scroll_between_up_and_down_arrows():
    box, tabs = dialog()
    for title in ("One", "Two", "Three", "Four", "Five"):
        page(tabs, title)
    tabs.side = "left"
    tabs.x, tabs.y, tabs.width, tabs.height = 0, 0, 20, 4
    assert tabs.scrolls
    assert [(y, title) for y, _, title in tabs.tabs()] == [(1, "One"), (2, "Two")]
    buffer = ScreenBuffer(20, 4)
    tabs.render_tree(buffer)
    assert [row[:9] for row in rows(buffer)] == [
        "        │",
        "► One   │",
        "  Two   │",
        "    ▼   │",
    ]
    assert tabs._on_arrow(4, 3) == 1 and tabs._on_arrow(4, 0) == 0
    tabs.scroll(5)
    assert [title for _, _, title in tabs.tabs()] == ["Four", "Five"]
    assert tabs.can_scroll() == (True, False)


def test_down_the_left_a_long_caption_is_cut_to_the_column():
    box, tabs = dialog()
    page(tabs, "A caption much too long for the column")
    tabs.side = "left"
    tabs.x, tabs.y, tabs.width, tabs.height = 0, 0, 40, 2
    assert tabs.column == 20
    buffer = ScreenBuffer(40, 2)
    tabs.render_tree(buffer)
    # A mark, a blank, as much of it as leaves a blank before the rule.
    assert rows(buffer)[0][:21] == "► A caption much t… │"


def test_down_the_left_over_the_frame_the_rule_meets_it_and_the_buttons_keep_their_clicks():
    box = Dialog(modal_width=30, modal_height=10, title="Tabs")
    tabs = TabView(parent=box, side="left", joins_frame=True)
    tabs.x, tabs.y, tabs.width, tabs.height = 1, 0, 28, 10
    first = page(tabs, "One", "~A~lpha")
    page(tabs, "Two")

    def painted(b):
        buffer = ScreenBuffer(80, 25)
        b.application.root.render_tree(buffer)
        return [row[b.x:b.x + 30] for row in rows(buffer)[b.y:b.y + 10]]

    def click_ok(b):
        # A button answers on the release, as Turbo Vision's did.
        x, y = b.x + b.row.x + b.ok.x + 3, b.y + b.row.y
        b.application.post_event(MouseClickEvent(x, y, "left"))
        b.application.post_event(MouseClickEvent(x, y, "left", action="release"))

    seen = run(box, look(lambda b: [(y, t) for y, _, t in tabs.tabs()]),
               look(lambda b: (first.y, first.height)), look(painted), click_ok, lambda a: None,
               look(lambda b: b.parent is None))
    assert seen[0] == [(1, "One"), (2, "Two")]
    assert seen[1] == (1, 8)
    assert [row[:8] for row in seen[2]][:3] == ["╔══════╤", "║► One │", "║  Two │"]
    assert seen[2][-1][:8] == "╚══════╧"
    assert seen[3] is True


def test_on_top_across_the_frame_the_baseline_meets_it_and_the_frame_stays_whole():
    box = Dialog(modal_width=30, modal_height=10, title="Tabs")
    tabs = TabView(parent=box, joins_frame=True)
    tabs.x, tabs.y, tabs.width, tabs.height = 0, 1, 30, 5
    first = page(tabs, "One", "~A~lpha")
    page(tabs, "Two")

    def painted(b):
        buffer = ScreenBuffer(80, 25)
        b.application.root.render_tree(buffer)
        return [row[b.x:b.x + 30] for row in rows(buffer)[b.y:b.y + 5]]

    seen = run(box, look(lambda b: [(x, t) for x, _, t in tabs.tabs()]),
               look(lambda b: (first.x, first.width)), look(painted))
    assert seen[0] == [(1, "One"), (8, "Two")]
    assert seen[1] == (1, 28)
    assert seen[2][1:4] == [
        "║╔═════╗┌─────┐              ║",
        "║║ One ║│ Two │              ║",
        "╟╜     ╙┴─────┴──────────────╢",
    ]


def test_tab_past_cancel_reaches_the_strip_whose_arrows_change_the_tab_and_tab_goes_on_to_the_page():
    box, tabs = dialog()
    page(tabs, "One", "~A~lpha")
    page(tabs, "Two", "~B~eta", "~G~amma")
    page(tabs, "Three", "~D~elta")

    def holder(b):
        focused = b.application.focused
        return "strip" if focused is tabs else getattr(focused, "items", None) or focused.text

    seen = run(
        box,
        look(lambda b: [type(w).__name__ for w in b.focusable()]),
        look(holder),
        KeyEvent("tab"), KeyEvent("tab"), lambda a: None, look(holder),
        KeyEvent("tab"), lambda a: None, look(holder),
        KeyEvent("right"), lambda a: None, look(lambda b: (tabs.current, holder(b))),
        KeyEvent("down"), KeyEvent("down"), lambda a: None, look(lambda b: (tabs.current, holder(b))),
        KeyEvent("home"), KeyEvent("right"), lambda a: None, look(lambda b: tabs.current),
        KeyEvent("tab"), lambda a: None, look(holder),
        KeyEvent("tab", shift=True), lambda a: None, look(holder),
        KeyEvent("pageup", ctrl=True), lambda a: None, look(lambda b: (tabs.current, holder(b))),
    )
    assert seen == [
        ["CheckBoxes", "Button", "Button", "TabView"],   # the strip after Cancel
        ["~A~lpha"],
        "~C~ancel",
        "strip",
        (1, "strip"),                                    # the tab changes, the strip keeps the keyboard
        (2, "strip"),                                    # and stops at the last
        1,
        ["~B~eta"],                                      # Tab goes on to the page's first control
        "strip",                                         # Shift+Tab back
        (0, "strip"),
    ]


def test_coming_back_to_a_page_puts_the_keyboard_where_it_was_on_it():
    box, tabs = dialog()
    page(tabs, "One", "~A~lpha", "~B~eta", "~G~amma")
    page(tabs, "Two", "~D~elta", "~E~psilon")

    def holder(b):
        focused = b.application.focused
        return focused.items[0] if hasattr(focused, "items") else focused.text

    seen = run(
        box,
        KeyEvent("tab"), KeyEvent("tab"), lambda a: None, look(holder),        # Gamma, on One
        KeyEvent("pagedown", ctrl=True), lambda a: None, look(holder),         # Two, not visited: its first
        KeyEvent("tab"), lambda a: None, look(holder),                         # Epsilon
        KeyEvent("pageup", ctrl=True), lambda a: None, look(holder),           # back on One: Gamma again
        KeyEvent("tab"), lambda a: None, look(holder),                         # off the page, to OK
        lambda b: b.spawn(tabs.on_mouse_click(MouseClickEvent(9, 1, "left"))), lambda a: None,
        look(holder),                                                          # a click on Two: Epsilon
        KeyEvent("tab"), KeyEvent("tab"), KeyEvent("tab"), lambda a: None,     # OK, Cancel, the strip
        look(lambda b: b.application.focused is tabs),
        KeyEvent("left"), KeyEvent("tab"), lambda a: None, look(holder),       # One, and Tab: Gamma
        KeyEvent("tab"), KeyEvent("tab"), KeyEvent("tab"),                    # OK, Cancel, the strip
        KeyEvent("right"), KeyEvent("tab"), lambda a: None, look(holder),      # Two, and Tab: Epsilon
    )
    assert seen == ["~G~amma", "~D~elta", "~E~psilon", "~G~amma", "O~K~", "~E~psilon", True,
                    "~G~amma", "~E~psilon"]


def test_pgdn_and_pgup_turn_the_pages_unless_the_control_takes_them():
    box, tabs = dialog()
    first = page(tabs, "One", "~A~lpha")
    items = ListViewer(parent=first, framed=False)
    items.x, items.y, items.width, items.height = 1, 2, 10, 3
    items.items = [str(n) for n in range(20)]
    page(tabs, "Two", "~B~eta")
    seen = run(
        box,
        KeyEvent("pagedown"), lambda a: None, look(lambda b: tabs.current),    # from a check box: the tabs'
        KeyEvent("pageup"), lambda a: None, look(lambda b: tabs.current),
        KeyEvent("tab"), lambda a: None,                                       # onto the list
        KeyEvent("pagedown"), lambda a: None, look(lambda b: (tabs.current, items.cursor > 0)),
    )
    assert seen == [1, 0, (0, True)]


def test_home_and_end_on_the_strip_go_to_the_first_and_last_tab():
    box, tabs = dialog()
    for title in ("One", "Two", "Three"):
        page(tabs, title, f"~{title[0]}~{title[1:]}")
    seen = run(
        box,
        KeyEvent("tab"), KeyEvent("tab"), KeyEvent("tab"), lambda a: None,     # OK, Cancel, the strip
        KeyEvent("end"), lambda a: None, look(lambda b: (tabs.current, b.application.focused is tabs)),
        KeyEvent("home"), lambda a: None, look(lambda b: (tabs.current, b.application.focused is tabs)),
    )
    assert seen == [(2, True), (0, True)]


def test_down_the_left_the_wheel_over_the_tabs_chooses_the_one_above_or_below():
    box = Dialog(modal_width=40, modal_height=12, title="Tabs")
    tabs = TabView(parent=box, side="left")
    tabs.x, tabs.y, tabs.width, tabs.height = 1, 1, 38, 7
    for title in ("One", "Two", "Three"):
        page(tabs, title, f"~{title[0]}~{title[1:]}")

    def wheel(button, x=2):
        def action(b):
            b.application.post_event(MouseClickEvent(box.x + tabs.x + x, box.y + tabs.y + 1, button))
        return action

    def where(b):
        focused = b.application.focused
        return tabs.current, focused.items[0] if hasattr(focused, "items") else focused

    seen = run(
        box,
        wheel("wheel_down"), lambda a: None, look(where),
        wheel("wheel_down"), wheel("wheel_down"), lambda a: None, look(where),   # stops at the last
        wheel("wheel_up"), lambda a: None, look(where),
        wheel("wheel_down", x=20), lambda a: None, look(where),                  # over the page: not the tabs'
    )
    assert seen == [(1, "~T~wo"), (2, "~T~hree"), (1, "~T~wo"), (1, "~T~wo")]
