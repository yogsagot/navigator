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
    dialog = Dialog(dialog_width=34, dialog_height=9)
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
