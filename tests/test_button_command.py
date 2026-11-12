"""``Button.command``: a button that asks for a command, as Turbo Vision's did.

A button with a command asks for it from itself when pressed, through
``Application.run_command`` -- so its window's handler runs it, and its
``enables()`` can refuse it -- and emits no click.  Without one it clicks.
"""

from __future__ import annotations

from navkit.application import Application
from navkit.commands import Command
from navkit.widget import Widget

from conftest import run_app

from navml.widgets.dialog.button import Button


class Launch(Command):
    title = "Launch"


class Host(Widget):
    """Runs Launch while it allows it, and counts the clicks that reach it."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ran: list[Command] = []
        self.clicks = 0
        self.allow = True

    def enables(self, command):
        return self.allow

    async def on_launch(self, event):
        self.ran.append(event)
        return True

    async def on_click(self, event):
        self.clicks += 1
        return True


def setup(command=None):
    host = Host(width=40, height=5)
    button = Button(parent=host, width=10, height=2, text="~G~o", command=command)
    app = Application(host)
    return app, host, button


def test_a_button_with_a_command_asks_for_it_and_does_not_click():
    app, host, button = setup(Launch)
    pressed = []
    run_app(app, [lambda a: a.spawn(_press(button, pressed)), lambda a: None])
    assert pressed == [True]
    assert len(host.ran) == 1 and isinstance(host.ran[0], Launch)
    assert host.clicks == 0


def test_a_refused_command_runs_nothing_and_press_says_so():
    app, host, button = setup(Launch)
    host.allow = False
    pressed = []
    run_app(app, [lambda a: a.spawn(_press(button, pressed)), lambda a: None])
    assert pressed == [False]
    assert host.ran == []
    assert host.clicks == 0


def test_without_a_command_a_button_still_clicks():
    app, host, button = setup()
    pressed = []
    run_app(app, [lambda a: a.spawn(_press(button, pressed)), lambda a: None])
    assert pressed == [True]
    assert host.ran == []
    assert host.clicks == 1


async def _press(button, into):
    into.append(await button.press())
