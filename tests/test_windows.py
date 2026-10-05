"""Overlapping windows: the navkit pieces they need, Window, Desktop and Modal."""

from __future__ import annotations

from pathlib import Path

import pytest

from navkit.application import Application
from navkit.events import DoubleClickEvent, KeyEvent, MouseClickEvent
from navkit.screen import ScreenBuffer
from navkit.widget import Widget

from conftest import FakeTerminal, awaited, mounted, run_app, settle
from navml.widgets import Desktop, Dialog, Modal, Window
from navml.widgets.desktop import EmptiedEvent


class Focusable(Widget):
    """A child that can hold the keyboard, and counts the clicks it gets."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.can_focus = True
        self.clicks = 0

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if event.action == "press":
            self.clicks += 1
            self.focus()
            return True
        return False


def press(x, y, button="left"):
    return MouseClickEvent(x, y, button, "press")


def move(x, y, button="left"):
    return MouseClickEvent(x, y, button, "move")


def release(x, y, button="left"):
    return MouseClickEvent(x, y, button, "release")


def handle(app: Application, *events) -> None:
    """Deliver *events* through the application's own routing, in order."""
    for event in events:
        awaited(app._handle(event))
    settle()


def window(x, y, width, height, **kwargs) -> Window:
    """A window of the given rectangle with one focusable child filling it."""
    win = Window(x=x, y=y, width=width, height=height, **kwargs)
    win.inner = Focusable(parent=win, x=1, y=1, width=width - 2, height=height - 2)
    return win


@pytest.fixture
def desk():
    """An application whose root holds one desktop at row 1, 80x22."""
    root = Widget()
    desktop = Desktop(parent=root)
    app = Application(root, terminal=FakeTerminal(width=80, height=24))
    desktop.y, desktop.height = 1, 22
    settle()
    return app, desktop


# -- navkit: raising, capture, painting over children ------------------------


def test_raise_child_is_a_reorder_that_keeps_the_keyboard():
    root = mounted(Widget())
    a, b = Focusable(parent=root), Focusable(parent=root)
    unmounted = []
    a.unmounting = lambda: unmounted.append(a)
    a.focus()
    root.raise_child(a)
    assert root.children == [b, a]
    assert a.is_mounted and a.focused and not unmounted
    root.lower_child(a)
    assert root.children == [a, b]


def test_a_captured_drag_is_delivered_wherever_the_pointer_goes():
    root = Widget()
    seen: list[tuple[int, int, str]] = []

    class Grabber(Widget):
        async def on_mouse_click(self, event):
            seen.append((event.x, event.y, event.action))
            if event.action == "press":
                self.application.capture_mouse(self)
            return True

    grabber = Grabber(parent=root, x=10, y=5, width=4, height=2)
    app = Application(root, terminal=FakeTerminal(width=80, height=24))
    grabber.x, grabber.y, grabber.width, grabber.height = 10, 5, 4, 2
    handle(app, press(11, 5), move(40, 20), release(41, 21))
    assert seen == [(1, 0, "press"), (30, 15, "move"), (31, 16, "release")]
    assert app.mouse_capture is None
    handle(app, press(0, 0))                   # routed by position again
    assert len(seen) == 3


def test_unmounting_the_holder_releases_the_mouse():
    root = mounted(Widget())
    holder = Widget(parent=root)
    app = root.application
    app.capture_mouse(holder)
    root.remove(holder)
    assert app.mouse_capture is None


def test_render_after_paints_over_the_children():
    class Over(Widget):
        def render_after(self, surface):
            surface.draw_text(0, 0, "X", self.style)

    over = Over(width=3, height=1)
    child = Widget(parent=over, width=3, height=1)
    child.render = lambda surface: surface.draw_text(0, 0, "ccc", child.style)
    buffer = ScreenBuffer(3, 1)
    over.render_tree(buffer)
    assert "".join(buffer.get(x, 0)[0] for x in range(3)) == "Xcc"


# -- Window and Desktop ------------------------------------------------------


def test_opening_a_window_activates_it_and_focuses_inside(desk):
    app, desktop = desk
    first = desktop.open(window(2, 2, 30, 10))
    assert desktop.active_window is first and first.active
    assert app.focused is first.inner
    second = desktop.open(window(20, 5, 30, 10))
    assert desktop.children[-1] is second
    assert not first.active and app.focused is second.inner


def test_a_press_on_a_background_window_raises_it_and_still_reaches_the_child(desk):
    app, desktop = desk
    back = desktop.open(window(0, 0, 30, 10))
    front = desktop.open(window(40, 0, 30, 10))
    # Desktop row 5 is screen row 6; x 5 is inside `back' only.
    handle(app, press(5, 6), release(5, 6))
    assert desktop.active_window is back
    assert desktop.children[-1] is back
    assert back.inner.clicks == 1          # the first click was not swallowed
    assert app.focused is back.inner
    assert front.active is False


def test_a_click_nothing_claims_does_not_fall_through_to_the_window_behind(desk):
    app, desktop = desk
    back = desktop.open(Window(x=0, y=0, width=30, height=10))
    front = desktop.open(Window(x=0, y=0, width=30, height=10))
    # Nothing in either window takes a right click; it used to reach `back'
    # and raise it, so each right click swapped the two.
    for _ in range(2):
        handle(app, press(5, 6, "right"), release(5, 6, "right"))
        assert desktop.active_window is front


def test_activation_hands_back_the_focus_a_window_had(desk):
    app, desktop = desk
    back = desktop.open(window(0, 0, 30, 10))
    other = Focusable(parent=back, x=1, y=8, width=5, height=1)
    other.focus()
    desktop.open(window(40, 0, 30, 10))
    desktop.activate(back)
    assert app.focused is other


def test_dragging_the_title_moves_the_window(desk):
    app, desktop = desk
    win = desktop.open(window(10, 5, 30, 10))
    # Title row is desktop row 5, screen row 6; grab it at column 15.
    handle(app, press(15, 6), move(25, 9), move(26, 10), release(26, 10))
    assert (win.x, win.y) == (21, 9)
    assert (win.width, win.height) == (30, 10)


def test_a_drag_leaves_the_title_on_the_desktop(desk):
    app, desktop = desk
    win = desktop.open(window(10, 5, 30, 10))
    handle(app, press(15, 6), move(15, 0), move(-60, 60), release(-60, 60))
    assert win.y == desktop.height - 1
    assert win.x == 8 - win.width


def test_dragging_the_grip_resizes_down_to_the_minimum(desk):
    app, desktop = desk
    win = desktop.open(window(10, 5, 30, 10))
    corner_x, corner_y = 10 + 29, 1 + 5 + 9
    assert win.chrome_hit(29, 9) == "resize"
    handle(app, press(corner_x, corner_y), move(corner_x + 5, corner_y + 2))
    assert (win.width, win.height) == (35, 12)
    handle(app, move(0, 0), release(0, 0))
    assert (win.width, win.height) == (win.min_width, win.min_height)


def test_zoom_fills_the_desktop_and_restore_puts_it_back(desk):
    app, desktop = desk
    win = desktop.open(window(10, 5, 30, 10))
    zoom_x = 10 + win.width - 5
    assert win.chrome_hit(win.width - 5, 0) == "zoom"
    handle(app, press(zoom_x, 6), release(zoom_x, 6))
    assert win.zoomed
    assert (win.x, win.y, win.width, win.height) == (0, 0, 80, 22)
    # A zoomed window follows the desktop when the terminal is resized.
    desktop.width, desktop.height = 100, 30
    settle()
    assert (win.width, win.height) == (100, 30)
    win.toggle_zoom()
    assert (win.x, win.y, win.width, win.height) == (10, 5, 30, 10)


def test_a_double_click_on_the_title_zooms(desk):
    app, desktop = desk
    win = desktop.open(window(10, 5, 30, 10))
    handle(app, press(15, 6), release(15, 6), press(15, 6), release(15, 6))
    assert win.zoomed
    assert app.mouse_capture is None
    handle(app, press(15, 1), release(15, 1), press(15, 1), release(15, 1))
    assert not win.zoomed
    assert (win.x, win.y, win.width, win.height) == (10, 5, 30, 10)


def test_a_single_click_on_a_zoomed_title_does_not_unzoom(desk):
    app, desktop = desk
    win = desktop.open(window(10, 5, 30, 10))
    win.toggle_zoom()
    handle(app, press(15, 1), release(15, 1))
    assert win.zoomed
    assert app.mouse_capture is None


def test_dragging_a_zoomed_title_unzooms_under_the_pointer(desk):
    app, desktop = desk
    win = desktop.open(window(10, 5, 30, 10))
    win.toggle_zoom()
    handle(app, press(15, 1), move(20, 4))
    assert not win.zoomed
    assert (win.x, win.y, win.width, win.height) == (5, 3, 30, 10)
    handle(app, move(22, 4), release(22, 4))
    assert (win.x, win.y) == (7, 3)
    assert app.mouse_capture is None


def test_the_close_icon_closes_and_the_next_window_takes_over(desk):
    app, desktop = desk
    under = desktop.open(window(0, 0, 30, 10))
    top = desktop.open(window(5, 3, 30, 10))
    assert top.chrome_hit(2, 0) == "close"
    handle(app, press(5 + 2, 1 + 3), release(5 + 2, 1 + 3))
    assert top.parent is None
    assert desktop.active_window is under
    assert app.focused is under.inner


def test_an_inactive_window_s_icons_are_not_there_to_click(desk):
    app, desktop = desk
    back = desktop.open(window(0, 0, 30, 10))
    desktop.open(window(40, 0, 30, 10))
    assert back._icons() == {}
    handle(app, press(2, 1), release(2, 1))   # where the close icon would be
    assert back.parent is desktop            # raised, not closed
    assert desktop.active_window is back


def test_closing_the_last_window_says_so():
    root = Widget()
    desktop = Desktop(parent=root)
    heard: list[EmptiedEvent] = []

    async def on_emptied(event):
        heard.append(event)
        return True

    root.on_emptied = on_emptied
    app = Application(root, terminal=FakeTerminal(width=80, height=24))
    win = desktop.open(window(0, 0, 30, 10))
    run_app(app, [lambda a: win.close(), lambda a: None])
    assert desktop.active_window is None
    assert len(heard) == 1


def test_the_window_keys(desk):
    app, desktop = desk
    first = desktop.open(window(0, 0, 30, 10))
    second = desktop.open(window(20, 5, 30, 10))
    # DOS Navigator's cmNext and cmPrev keys, F9 and Shift+F9.
    handle(app, KeyEvent("f9"))
    assert desktop.active_window is first
    handle(app, KeyEvent("f9", shift=True))
    assert desktop.active_window is second
    handle(app, KeyEvent("f9", shift=True))
    assert desktop.active_window is first
    handle(app, KeyEvent("f6", ctrl=True))
    assert desktop.active_window is first  # Ctrl+F6 is no window key any more
    handle(app, KeyEvent("z", "z", alt=True))
    assert first.zoomed
    handle(app, KeyEvent("f4", ctrl=True))
    assert first.parent is None and desktop.active_window is second


def test_keyboard_move_mode_moves_resizes_and_escape_undoes(desk):
    app, desktop = desk
    win = desktop.open(window(10, 5, 30, 10))
    handle(app, KeyEvent("f5", ctrl=True))
    assert win.moving and app.focused is win
    handle(app, KeyEvent("right"), KeyEvent("down"), KeyEvent("right", shift=True))
    assert (win.x, win.y, win.width) == (11, 6, 31)
    handle(app, KeyEvent("escape"))
    assert not win.moving
    assert (win.x, win.y, win.width) == (10, 5, 30)
    assert app.focused is win.inner
    handle(app, KeyEvent("f5", ctrl=True), KeyEvent("left"), KeyEvent("enter"))
    assert win.x == 9 and app.focused is win.inner


def test_a_window_with_nothing_to_focus_holds_the_keyboard_itself(desk):
    # With no focus at all a key reaches no widget, so the desktop's window
    # keys would be dead while such a window is on top.
    app, desktop = desk
    first = desktop.open(window(0, 0, 30, 10))
    bare = desktop.open(Window(x=10, y=5, width=30, height=10))
    assert app.focused is bare
    handle(app, KeyEvent("f9"))                    # Next window still works from it
    assert desktop.active_window is first and app.focused is first.inner
    handle(app, KeyEvent("f9"))
    assert app.focused is bare                     # and it gets the keyboard back
    handle(app, KeyEvent("f4", ctrl=True))         # as does Close
    assert bare.parent is None and app.focused is first.inner


def test_a_bare_window_keeps_the_keyboard_through_move_mode(desk):
    app, desktop = desk
    bare = desktop.open(Window(x=10, y=5, width=30, height=10))
    handle(app, KeyEvent("f5", ctrl=True), KeyEvent("right"), KeyEvent("enter"))
    assert bare.x == 11 and not bare.moving
    assert app.focused is bare and bare.can_focus
    handle(app, KeyEvent("f5", ctrl=True), KeyEvent("escape"))
    assert app.focused is bare


def test_a_window_that_gains_a_control_hands_it_the_keyboard(desk):
    app, desktop = desk
    first = desktop.open(window(0, 0, 30, 10))
    bare = desktop.open(Window(x=10, y=5, width=30, height=10))
    bare.inner = Focusable(parent=bare, x=1, y=1, width=5, height=1)
    desktop.activate(first)
    desktop.activate(bare)
    assert app.focused is bare.inner and not bare.can_focus


# -- Modal -------------------------------------------------------------------


def test_a_modal_is_centred_and_stays_centred(desk):
    app, desktop = desk
    modal = Modal(modal_width=20, modal_height=6)
    app.overlay(modal)
    settle()
    assert (modal.x, modal.y, modal.width, modal.height) == (30, 9, 20, 6)
    app.root.width, app.root.height = 100, 30
    settle()
    assert (modal.x, modal.y) == (40, 12)


def test_a_modal_sits_above_every_window_and_blocks_what_is_outside(desk):
    app, desktop = desk
    back = desktop.open(window(0, 0, 30, 10))
    front = desktop.open(window(40, 0, 30, 10))
    dialog = Dialog(modal_width=20, modal_height=6)
    app.overlay(dialog)
    settle()
    assert app.modal is dialog
    # A click on the background window reaches nothing: it is not raised.
    handle(app, press(5, 6), release(5, 6))
    assert desktop.active_window is front and back.inner.clicks == 0
    # A drag on the modal's title does not move it.
    handle(app, press(dialog.x + 3, dialog.y), move(0, 0), release(0, 0))
    assert (dialog.x, dialog.y) == (30, 9)
    # Raising a window under a modal leaves the modal on top.
    desktop.activate(back)
    assert app.root.children[-1] is dialog
    assert app.focused is not back.inner


# -- Window > Tile, Cascade, Close all ---------------------------------------


def rect(win):
    return win.x, win.y, win.width, win.height


@pytest.mark.parametrize("count, expected", [
    (1, [(0, 0, 80, 22)]),
    # More rows than columns: TileColumnsFirst was never set.
    (2, [(0, 0, 80, 11), (0, 11, 80, 11)]),
    (3, [(0, 0, 80, 7), (0, 7, 80, 7), (0, 14, 80, 8)]),
    (4, [(0, 0, 40, 11), (0, 11, 40, 11), (40, 0, 40, 11), (40, 11, 40, 11)]),
    # The column the grid cannot fill evenly takes a row more.
    (5, [(0, 0, 40, 11), (0, 11, 40, 11),
         (40, 0, 40, 7), (40, 7, 40, 7), (40, 14, 40, 8)]),
])
def test_tile_shares_the_desktop_as_dos_navigator_did(desk, count, expected):
    app, desktop = desk
    windows = [desktop.open(window(3 * i, i, 30, 10)) for i in range(count)]
    top = desktop.active_window
    desktop.tile()
    # The bottom window gets the first tile, and the z-order is left alone.
    assert [rect(w) for w in windows] == expected
    assert desktop.windows() == windows and desktop.active_window is top


def test_every_window_is_tileable_unless_it_says_not():
    assert Window().tileable


def test_tile_leaves_untileable_windows_and_unzooms_the_others(desk):
    app, desktop = desk
    zoomed = desktop.open(window(0, 0, 30, 10))
    zoomed.toggle_zoom()
    other = desktop.open(window(5, 5, 30, 10, tileable=False))
    desktop.tile()
    assert not zoomed.zoomed and rect(zoomed) == (0, 0, 80, 22)
    assert rect(other) == (5, 5, 30, 10)


def test_cascade_steps_equal_windows_so_a_raised_one_hides_none_above_it(desk):
    app, desktop = desk
    windows = [desktop.open(window(10, 5, 30, 10)) for _ in range(3)]
    desktop.cascade()
    # One size for all; only the top window reaches the desktop's corner.
    assert [rect(w) for w in windows] == [(0, 0, 78, 20), (1, 1, 78, 20), (2, 2, 78, 20)]


def test_cascade_is_refused_when_the_minimum_size_does_not_fit(desk):
    app, desktop = desk
    windows = [desktop.open(window(10, 1, 30, 20, min_height=21))
               for _ in range(3)]
    before = [rect(w) for w in windows]
    desktop.cascade()
    assert [rect(w) for w in windows] == before
    for w in windows:
        w.min_height = 20  # exactly the 22 - 2 a three-window cascade leaves
    desktop.cascade()
    assert [rect(w) for w in windows] == [(0, 0, 78, 20), (1, 1, 78, 20), (2, 2, 78, 20)]


def test_close_all_closes_every_closable_window():
    root = Widget()
    desktop = Desktop(parent=root)
    heard: list[EmptiedEvent] = []

    async def on_emptied(event):
        heard.append(event)
        return True

    root.on_emptied = on_emptied
    app = Application(root, terminal=FakeTerminal(width=80, height=24))
    stays = desktop.open(window(0, 0, 30, 10, closable=False))
    desktop.open(window(5, 5, 30, 10))
    desktop.open(window(10, 8, 30, 10))
    seen = []

    def look(a):
        seen.append((desktop.windows(), desktop.active_window, len(heard)))
        stays.closable = True

    run_app(app, [lambda a: desktop.close_all(), look,
                  lambda a: desktop.close_all(), lambda a: None])
    assert seen == [([stays], stays, 0)]
    assert desktop.windows() == [] and len(heard) == 1


def test_tile_cascade_and_close_all_need_a_window_that_consents(desk):
    from navml.commands import CascadeWindows, CloseAllWindows, TileWindows

    app, desktop = desk
    commands = (TileWindows(), CascadeWindows(), CloseAllWindows())
    assert [desktop.enables(c) for c in commands] == [False, False, False]
    desktop.open(window(0, 0, 30, 10, closable=False, tileable=False))
    assert [desktop.enables(c) for c in commands] == [False, False, False]
    desktop.open(window(5, 5, 30, 10))
    assert [desktop.enables(c) for c in commands] == [True, True, True]
