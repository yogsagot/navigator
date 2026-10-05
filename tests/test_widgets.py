"""The widget library: that every widget paints, and what each one does.

The first test here is the one that matters most and says least.  Two
components shipped for months unable to paint at all -- ``Dialog`` and
``FramedButton`` both unpacked a six-character charset into ``draw_box``'s
positional arguments and raised ``TypeError`` the moment anything rendered
them -- because nothing in the suite ever rendered a widget.  It is
parametrized over ``navml.widgets.__all__`` rather than over a list, so a
widget added next year is covered by it without anybody remembering.
"""

from __future__ import annotations

import pytest

import navml.widgets
from navkit.glyphs import GLYPHS_ASCII, GLYPHS_UNICODE
from navkit.screen import ScreenBuffer
from navkit.widget import Widget

#: Every component the library publishes, as classes.
WIDGETS = [
    (name, getattr(navml.widgets, name))
    for name in navml.widgets.__all__
]

#: Widget classes only.  ``__all__`` may also carry an event or a helper.
PAINTERS = [(name, cls) for name, cls in WIDGETS if isinstance(cls, type) and issubclass(cls, Widget)]

#: Sizes every widget has to survive.  The degenerate ones are the point:
#: ``draw_box`` returns early below 2x2 and a painter's arithmetic goes
#: negative around there, which is exactly where a widget stops clipping and
#: starts raising.
SIZES = [(24, 6), (40, 1), (1, 1), (0, 0), (3, 2)]


@pytest.mark.parametrize("name, cls", PAINTERS, ids=[n for n, _ in PAINTERS])
@pytest.mark.parametrize("width, height", SIZES, ids=[f"{w}x{h}" for w, h in SIZES])
def test_every_widget_paints(name, cls, width, height):
    """It renders, at every size, without raising."""
    widget = cls(width=width, height=height)
    widget.render(ScreenBuffer(width, height))


@pytest.mark.parametrize("name, cls", PAINTERS, ids=[n for n, _ in PAINTERS])
def test_every_widget_paints_inside_itself(name, cls):
    """A widget may not draw outside its own area.

    ``render_tree`` hands each widget a view of its own rectangle, so this is
    the buffer's guarantee rather than the widget's -- but a widget that
    assumes otherwise is one that looks right alone and wrong in a tree.
    """
    buffer = ScreenBuffer(30, 8)
    widget = cls(width=10, height=3)
    widget.render(buffer.view(2, 2, 10, 3))
    for y in range(8):
        for x in range(30):
            if 2 <= x < 12 and 2 <= y < 5:
                continue
            assert buffer.get(x, y)[0] == " ", f"{name} painted at {x},{y}"


@pytest.mark.parametrize("name, cls", PAINTERS, ids=[n for n, _ in PAINTERS])
def test_every_widget_degrades_to_ascii(name, cls, monkeypatch):
    """Nothing above ASCII reaches the buffer at ``GLYPHS_ASCII``.

    A widget owes both halves of the glyph question: a sheet says which set is
    *wanted* and the tier says which can be *shown*.  A widget that reads the
    first and not the second paints replacement boxes on a terminal that told
    us so.
    """
    widget = cls(width=24, height=6)
    monkeypatch.setattr(type(widget), "glyphs", property(lambda self: GLYPHS_ASCII))
    buffer = ScreenBuffer(24, 6)
    widget.render(buffer)
    for y in range(6):
        for x in range(24):
            char = buffer.get(x, y)[0]
            assert char == "" or ord(char) < 128, (
                f"{name} drew {char!r} at {x},{y} on an ASCII terminal"
            )


@pytest.mark.parametrize("name, cls", PAINTERS, ids=[n for n, _ in PAINTERS])
def test_every_widget_declares_the_parts_it_paints(name, cls):
    """A part name is only checkable where the class is, so check it here.

    Painting at a size big enough to reach every branch, with ``part_style``
    refusing anything undeclared -- so a widget that paints ``::titel`` fails
    here rather than silently taking its owner's colours for ever.
    """
    cls(width=24, height=6).render(ScreenBuffer(24, 6))


# -- the dialog, and the rule it rests on ------------------------------------


import asyncio                                            # noqa: E402

from conftest import FakeTerminal                         # noqa: E402
from navkit.application import Application                # noqa: E402
from navkit.events import KeyEvent                        # noqa: E402
from navml.widgets import Button, Dialog, Label, StaticText, Window  # noqa: E402


class Desktop(Widget):
    def render(self, surface):
        surface.fill(0, 0, self.width, self.height, ".", self.style)


def shown(keys=(), **kwargs):
    """Run a dialog to its answer, posting *keys* once it is up."""
    result: list = []
    frames_while_up: list = []

    async def main():
        root = Desktop()
        terminal = FakeTerminal(width=60, height=16)
        app = Application(root, terminal=terminal)
        loop = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.03)
        dialog = Dialog(**kwargs)
        job = app.spawn(dialog.execute(app))
        await asyncio.sleep(0.05)
        frames_while_up.append(terminal.frames[-1])
        for key in keys:
            app.post_event(key)
            await asyncio.sleep(0.02)
        result.append(await asyncio.wait_for(job, 1))
        app.exit()
        await loop

    asyncio.run(asyncio.wait_for(main(), 5))
    return result[0], frames_while_up[0]


def test_a_dialog_is_painted_before_it_is_answered():
    """The regression for the deadlock, and the reason `spawn` exists.

    A handler that *awaits* a dialog holds the event queue's only consumer, so
    the dialog is mounted and never drawn and the key that would dismiss it is
    never dispatched.  Asserting that the frame carries the dialog *before*
    anything resolves it is what pins the rule.
    """
    _, frame = shown([KeyEvent(key="escape")], title="Confirm", prompt="Really?")
    assert "Confirm" in frame
    assert "Really?" in frame


def test_escape_cancels_and_enter_accepts():
    assert shown([KeyEvent(key="escape")])[0] is None
    assert shown([KeyEvent(key="enter")])[0] is True


def test_a_shortcut_reaches_a_button_that_does_not_hold_the_focus():
    """`dispatch_key` walks the focus path, so the window goes looking."""
    assert shown([KeyEvent(key="c", alt=True)])[0] is None    # Cancel
    assert shown([KeyEvent(key="k", alt=True)])[0] is True    # O~K~


def test_a_focused_button_takes_enter_before_the_default_does():
    """Turbo Vision's rule: the default button is what Enter means *elsewhere*."""
    assert shown([KeyEvent(key="tab"), KeyEvent(key="enter")])[0] is None


def test_a_dialog_binds_its_geometry_so_that_overlay_cannot_resize_it():
    """`Widget.add` lays a child out into its parent, and a literal loses.

    `Component.layout` steps around a side that carries a *binding* and
    overwrites one that does not -- so a dialog sized with a literal becomes
    full-screen the moment it is overlaid.  Routing the size through a
    declared property is what makes it survive, and what lets a derived
    document change it.
    """
    dialog = Dialog(modal_width=34, modal_height=9)
    dialog.layout(200, 60)
    assert (dialog.width, dialog.height) == (34, 9)


def test_a_dialog_refuses_to_be_awaited_from_a_handler():
    """The freeze, turned into a message at the call site."""
    caught: list = []

    class Opener(Widget):
        def render(self, surface):
            pass

        async def on_key(self, event):
            try:
                await Dialog().execute(self.application)
            except RuntimeError as error:
                caught.append(str(error))
            return True

    async def main():
        root = Opener()
        root.can_focus = True
        app = Application(root, terminal=FakeTerminal(40, 10))
        loop = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.03)
        root.focus()
        app.post_event(KeyEvent(key="f1"))
        await asyncio.sleep(0.05)
        app.exit()
        await loop

    asyncio.run(asyncio.wait_for(main(), 5))
    assert caught and "cannot be awaited from an event handler" in caught[0]
    assert "spawn" in caught[0]


def test_a_dialog_puts_its_own_buttons_last_in_the_tab_order():
    """A derived dialog's controls are built *after* its base's buttons.

    ``super().__init__()`` is the generated constructor's first line, so the
    base's tree lands first -- which would open every derived dialog with the
    focus on OK.  ``focusable()`` reorders, and ``_claim_focus`` reads the
    same list.
    """
    dialog = Dialog(buttons="ok-cancel-help")
    order = dialog.focusable()
    assert order[-3:] == [dialog.ok, dialog.cancel, dialog.info]


def test_a_hidden_button_is_out_of_the_tab_order_and_the_shortcut_walk():
    """Which is the whole of what markup's missing conditional costs."""
    dialog = Dialog(buttons="ok")
    assert dialog.cancel not in dialog.focusable()
    assert dialog.cancel not in list(dialog.controls())


# -- arrows between buttons ---------------------------------------------------


def arrows(root, start, *keys):
    """Focus *start* under *root*, press *keys*; who holds the keyboard after each."""
    from conftest import awaited, settle

    app = Application(root, terminal=FakeTerminal(60, 16))
    settle()
    start.focus()
    seen = []
    for key in keys:
        awaited(app._handle(KeyEvent(key=key)))
        settle()
        seen.append(app.focused)
    return seen


def test_the_arrows_walk_a_dialog_s_buttons_and_stop_at_the_ends():
    root = Widget()
    dialog = Dialog(buttons="yes-no-cancel", parent=root)
    ok, no, cancel = dialog.ok, dialog.no, dialog.cancel
    assert arrows(root, ok, "right", "right", "right", "left", "up", "up", "down") == [
        no, cancel, cancel, no, ok, ok, no,
    ]


def test_the_arrows_pass_over_a_hidden_button():
    root = Widget()
    dialog = Dialog(buttons="ok-cancel", parent=root)
    assert not dialog.no.visible
    assert arrows(root, dialog.ok, "right", "left") == [dialog.cancel, dialog.ok]


def test_the_arrows_stay_among_buttons_and_leave_an_input_line_its_own():
    from navml.widgets import InputLine

    root = Widget()
    line = InputLine(parent=root, x=0, y=0, width=20, height=1)
    first = Button("One", parent=root, x=0, y=2, width=11, height=2)
    second = Button("Two", parent=root, x=0, y=4, width=11, height=2)
    third = Button("Three", parent=root, x=0, y=6, width=11, height=2)
    # A column placed by hand, with no layout: Down and Up walk it.
    assert arrows(root, first, "down", "down", "down", "up", "up", "up") == [
        second, third, third, second, first, first,
    ]
    # The input line keeps Left and Right for its cursor.
    assert arrows(root, line, "right", "left") == [line, line]


def test_yes_no_is_yes_and_no_with_no_cancel():
    """``mfYesButton + mfNoButton``: a question with two answers."""
    dialog = Dialog(buttons="yes-no")
    shown = [b for b in dialog.buttons_row if b.visible]
    assert shown == [dialog.ok, dialog.no]
    assert (dialog.ok.text, dialog.no.text) == ("~Y~es", "~N~o")
    assert dialog.focusable()[-2:] == [dialog.ok, dialog.no]


# -- Timer --------------------------------------------------------------------


from conftest import run_app                                # noqa: E402
from navml.widgets import Timer                             # noqa: E402


class _Listener(Widget):
    """Counts the ``TimerEvent``s its children raise."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ticks = 0

    async def on_timer(self, event):
        self.ticks += 1
        return True


def test_a_timer_emits_every_interval_to_whoever_handles_it():
    root = _Listener()
    Timer(parent=root).interval = 10
    run_app(Application(root, terminal=FakeTerminal()), settle=0.1)
    assert root.ticks >= 3


def test_a_removed_timer_stops_and_a_zero_interval_never_starts():
    root = _Listener()
    timer = Timer(parent=root)
    timer.interval = 10
    Timer(parent=root).interval = 0
    seen = []

    def remove(app):
        root.remove(timer)
        seen.append(root.ticks)

    run_app(Application(root, terminal=FakeTerminal()), [remove], settle=0.08)
    assert seen[0] >= 1
    assert root.ticks == seen[0]
    assert timer._repeat is None


def test_changing_the_interval_rearms_the_timer():
    root = _Listener()
    timer = Timer(parent=root)
    timer.interval = 0
    counts = []

    def start(app):
        counts.append(root.ticks)
        timer.interval = 10

    run_app(Application(root, terminal=FakeTerminal()), [start], settle=0.1)
    assert counts == [0]
    assert root.ticks >= 3


def test_a_control_in_a_disabled_container_is_out_of_reach():
    box = Widget()
    button = Button(parent=box, text="~O~K")
    Application(root=box, terminal=FakeTerminal())
    assert button.can_focus is True
    box.disabled = True
    assert button.can_focus is False
    assert button.focus() is False
    assert button.shortcut_match("o") is False
    assert asyncio.run(button.press()) is False
    box.disabled = False
    assert button.can_focus is True


# -- the button: DOS Navigator's face, markers, shadow and press -------------


from navkit.events import KeyReleaseEvent, MouseClickEvent  # noqa: E402
from navkit.screen import ScreenBuffer as _Buffer          # noqa: E402


def _row(buffer, y):
    return "".join(buffer.get(x, y)[0] or " " for x in range(buffer.width))


def test_a_button_is_a_plain_face_with_a_half_block_shadow():
    button = Button(text="OK", width=8, height=2)
    buffer = _Buffer(8, 2)
    button.render(buffer)
    assert _row(buffer, 0) == "       ▄"
    assert _row(buffer, 1) == " ▀▀▀▀▀▀▀"


def test_the_button_enter_would_press_is_marked_and_a_pressed_one_moves_right():
    button = Button(text="OK", width=8, height=2, default=True)
    buffer = _Buffer(8, 2)
    button.render(buffer)
    assert _row(buffer, 0) == "▶     ◀▄"
    button.down = True
    buffer = _Buffer(8, 2)
    button.render(buffer)
    assert _row(buffer, 0) == " ▶     ◀"
    assert _row(buffer, 1) == "        "


def test_a_taller_button_runs_its_shadow_down_in_full_blocks():
    button = Button(width=6, height=3)
    buffer = _Buffer(6, 3)
    button.render(buffer)
    assert [buffer.get(5, y)[0] for y in range(3)] == ["▄", "█", "▀"]


class _Placed(Widget):
    """A root that keeps its children where the test put them."""

    def layout(self, width, height):
        self.width, self.height = width, height


def _two_buttons():
    """A root holding a default OK and a Cancel, and the clicks each gives."""
    clicks: list[str] = []
    root = _Placed(width=40, height=10)
    ok = Button(parent=root, text="O~K~", x=2, y=2, width=10, height=2, default=True)
    cancel = Button(parent=root, text="~C~ancel", x=14, y=2, width=10, height=2)

    for name, button in (("ok", ok), ("cancel", cancel)):
        async def on_click(event, name=name):
            clicks.append(name)
            return True
        button.on_click = on_click
    app = Application(root, terminal=FakeTerminal(width=40, height=10))
    return app, ok, cancel, clicks


def test_the_default_gives_its_look_to_a_focused_button_and_takes_it_back():
    app, ok, cancel, _ = _two_buttons()
    ok.focus()
    assert ok.marked and ok.am_default
    cancel.focus()
    assert cancel.marked and not ok.am_default and not ok.marked
    app.focused = None
    assert ok.am_default and ok.marked and not cancel.marked


def _press(x, y, action="press"):
    return MouseClickEvent(x, y, "left", action)


def test_a_mouse_click_fires_on_the_release_not_the_press():
    app, ok, _, clicks = _two_buttons()
    seen = []
    run_app(app, [
        _press(3, 2),
        lambda app: seen.append((ok.down, list(clicks))),
        _press(3, 2, "release"),
        lambda app: seen.append((ok.down, list(clicks))),
    ])
    assert seen == [(True, []), (False, ["ok"])]


def test_dragging_off_a_held_button_pops_it_up_and_releasing_there_cancels():
    app, ok, _, clicks = _two_buttons()
    seen = []
    run_app(app, [
        _press(3, 2),
        _press(30, 8, "move"),
        lambda app: seen.append(ok.down),
        _press(30, 8, "release"),
    ])
    assert seen == [False]
    assert clicks == []


def test_coming_back_onto_a_held_button_presses_it_again():
    app, ok, _, clicks = _two_buttons()
    run_app(app, [
        _press(3, 2),
        _press(30, 8, "move"),
        _press(11, 2, "move"),     # the shadow's column counts: the face moves there
        _press(11, 2, "release"),
    ])
    assert clicks == ["ok"]


def test_a_press_on_the_shadow_is_not_a_press():
    app, ok, _, clicks = _two_buttons()
    run_app(app, [_press(11, 2), _press(11, 2, "release"), _press(5, 3), _press(5, 3, "release")])
    assert clicks == []
    assert not ok.down


def test_space_holds_the_button_down_until_it_is_released():
    app, ok, _, clicks = _two_buttons()
    seen = []
    run_app(app, [
        lambda app: ok.focus(),
        KeyEvent(" ", " ", releases=True),
        KeyEvent(" ", " ", releases=True),     # the key repeating
        lambda app: seen.append((ok.down, list(clicks))),
        KeyReleaseEvent(" ", " "),
    ])
    assert seen == [(True, [])]
    assert clicks == ["ok"]
    assert not ok.down


def test_space_flashes_where_no_release_will_come():
    app, ok, _, clicks = _two_buttons()
    seen = []
    run_app(app, [
        lambda app: ok.focus(),
        KeyEvent(" ", " "),
        lambda app: seen.append((ok.down, list(clicks))),
        *[lambda app: None] * 6,               # time for the flash to end
    ], settle=0.03)
    assert seen == [(True, [])]
    assert clicks == ["ok"]
    assert not ok.down


def test_enter_presses_at_once():
    app, ok, _, clicks = _two_buttons()
    run_app(app, [lambda app: ok.focus(), KeyEvent("enter", "\n")])
    assert clicks == ["ok"]


def test_a_space_held_while_the_focus_leaves_pops_up_without_a_click():
    app, ok, cancel, clicks = _two_buttons()
    run_app(app, [
        lambda app: ok.focus(),
        KeyEvent(" ", " ", releases=True),
        lambda app: cancel.focus(),
        KeyReleaseEvent(" ", " "),
    ])
    assert clicks == []
    assert not ok.down
