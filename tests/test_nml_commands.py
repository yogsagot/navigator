"""The ``commands:`` block: a component's command handlers, in markup.

``Command: statement`` becomes the handler navkit delivers the command to; an
``enabled:``/``checked:`` line under it becomes a branch of a generated
``enables``/``checks`` that asks ``super()`` for every other command.
"""

from __future__ import annotations

import asyncio

import pytest

from navkit.commands import Command

from navml.checks import check
from navml.errors import MarkupError
from navml.generator import generate
from navml.parser import parse
from navml.resolve import resolve
from navml.sibling import Sibling


class Flip(Command):
    title = "Flip"


class Other(Command):
    title = "Other"


PRELUDE = (
    "from navml.widgets.layout.horizontal_layout import HorizontalLayout\n"
    f"from {__name__} import Flip, Other\n\n"
)


def resolved_of(text: str, sibling: str | None = None, tmp_path=None):
    path = None
    if sibling is not None:
        path = tmp_path / "widget.py"
        path.write_text(sibling, encoding="utf-8")
    return resolve(
        parse(PRELUDE + text, filename="widget.nml"),
        sibling=Sibling.read(path) if path else None,
    )


def built(text: str, **kwargs):
    resolved = resolved_of(text)
    check(resolved)
    namespace: dict = {"__name__": "generated"}
    exec(compile(generate(resolved), "widget_nml.py", "exec"), namespace)
    return namespace["Widget_"](**kwargs)


def refused(text: str, sibling: str | None = None, tmp_path=None) -> MarkupError:
    with pytest.raises(MarkupError) as caught:
        check(resolved_of(text, sibling, tmp_path))
    return caught.value


FLIP = (
    "Widget_(HorizontalLayout):\n"
    "    property on: False\n"
    "    property allowed: True\n"
    "    commands:\n"
    "        Flip: root.on = not root.on\n"
    "            enabled: root.allowed\n"
    "            checked: root.on\n"
)


def test_a_line_becomes_the_handler_and_consumes():
    widget = built(FLIP)
    assert asyncio.run(widget.on_flip(Flip())) is True
    assert widget.on is True


def test_enabled_and_checked_answer_for_their_command():
    widget = built(FLIP)
    assert widget.enables(Flip()) is True
    widget.allowed = False
    assert widget.enables(Flip()) is False
    assert widget.checks(Flip()) is False
    widget.on = True
    assert widget.checks(Flip()) is True


def test_every_other_command_goes_to_the_base():
    widget = built(FLIP)
    assert widget.enables(Other()) is True
    assert widget.checks(Other()) is None


def test_the_stub_names_the_handlers(tmp_path):
    from navml.stubs import stub

    text = stub(resolved_of(FLIP))
    assert "async def on_flip(self, event: _Any) -> bool: ..." in text
    assert "def enables(self, command: _Any) -> bool: ..." in text
    assert "def checks(self, command: _Any) -> bool | None: ..." in text


@pytest.mark.parametrize(
    ("body", "says"),
    [
        ("    commands:\n        Flip(): root.x()\n", "not a Command class"),
        ("    commands:\n        len: root.x()\n", "not imported"),
        ("    commands:\n        Flip: root.x()\n        Flip: root.y()\n", "already handled"),
        ("    commands:\n        Flip: root.x()\n            visible: True\n", "'enabled: <expression>'"),
        ("    commands:\n        Flip: root.x()\n            checked: 1\n            checked: 2\n", "a second 'checked'"),
        ("    commands:\n        Flip:\n", "is not a handler"),
        ("    on_flip: root.x()\n    commands:\n        Flip: root.y()\n", "already a handler line"),
        ("    Widget_:\n        commands:\n            Flip: root.y()\n", "commands"),
    ],
)
def test_what_a_commands_block_cannot_say(body, says):
    error = refused("Widget_(HorizontalLayout):\n" + body)
    assert says in str(error)


def test_the_hand_written_half_may_not_handle_it_too(tmp_path):
    error = refused(
        "Widget_(HorizontalLayout):\n    commands:\n        Flip: root.x()\n",
        sibling="class Widget_:\n    async def on_flip(self, event): ...\n    def x(self): ...\n",
        tmp_path=tmp_path,
    )
    assert "defines on_flip too" in str(error)


def test_an_enables_that_never_asks_super_is_refused(tmp_path):
    error = refused(
        FLIP,
        sibling="class Widget_:\n    def enables(self, command):\n        return True\n",
        tmp_path=tmp_path,
    )
    assert "never calls super().enables" in str(error)


def test_an_enables_that_asks_super_is_fine(tmp_path):
    check(resolved_of(
        FLIP,
        "class Widget_:\n    def enables(self, command):\n        return super().enables(command)\n",
        tmp_path,
    ))


def test_an_async_method_must_be_awaited_or_spawned(tmp_path):
    error = refused(
        "Widget_(HorizontalLayout):\n    commands:\n        Flip: root.go()\n",
        sibling="class Widget_:\n    async def go(self): ...\n",
        tmp_path=tmp_path,
    )
    assert "builds a coroutine" in str(error)
    check(resolved_of(
        "Widget_(HorizontalLayout):\n    commands:\n        Flip: root.spawn(root.go())\n",
        "class Widget_:\n    async def go(self): ...\n",
        tmp_path,
    ))
