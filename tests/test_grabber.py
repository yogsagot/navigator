"""Shift+Alt+Ins: DOS Navigator's ``ScreenGrabber``."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent
from navkit.screen import ScreenBuffer

from navigator.__main__ import Navigator
from navigator.widgets.shell import grabber


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr(grabber, "_last", [10, 5, 21, 6])
    from navigator.widgets.shell.shell.shell import Shell
    monkeypatch.setattr(Shell, "_grabber_told", False)
    navigator = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    copied: list[str] = []
    navigator.copy_to_clipboard = lambda text, **kw: copied.append(text)
    navigator.copied = copied
    return navigator


def grabbing(a) -> bool:
    return isinstance(a.modal, grabber.ScreenGrabber)


def screen(a) -> ScreenBuffer:
    buffer = ScreenBuffer(80, 24)
    a.root.render_tree(buffer)
    return buffer


def row(buffer: ScreenBuffer, y: int, left: int, right: int) -> str:
    return "".join(buffer.get(x, y)[0] for x in range(left, right))


def test_it_says_how_once_then_enter_copies_the_rectangle(app):
    seen = {}

    def look(a):
        buffer = screen(a)
        seen.update(area=a.modal.area, text=row(buffer, 0, 0, 13) + "\n" + row(buffer, 1, 0, 13),
                    inverted=buffer.get(0, 0)[1].reverse and not buffer.get(13, 0)[1].reverse)

    run_app(app, [
        KeyEvent("insert", alt=True, shift=True), Until(lambda a: a.modal is not None),
        lambda a: seen.update(told=a.modal.title), KeyEvent("enter"), Until(grabbing),
        KeyEvent("pageup"), KeyEvent("home"), KeyEvent("right", shift=True), KeyEvent("right", shift=True),
        KeyEvent("down", shift=True), lambda a: None, look, KeyEvent("enter"), lambda a: None,
        KeyEvent("insert", alt=True, shift=True), Until(grabbing),
        lambda a: seen.update(again=a.modal.area), KeyEvent("escape"), lambda a: None,
    ])
    assert seen["told"] == "Information"
    assert seen["area"] == (0, 0, 13, 2) and seen["inverted"]
    assert app.copied == [seen["text"]]
    assert seen["again"] == (0, 0, 13, 2)  # where it was left; and no welcome the second time


def test_the_rectangle_stays_on_the_screen_and_ctrl_takes_big_steps(app):
    seen = {}
    run_app(app, [
        KeyEvent("insert", alt=True, shift=True), Until(lambda a: a.modal is not None), KeyEvent("enter"),
        Until(grabbing),
        KeyEvent("right", ctrl=True), lambda a: seen.update(ctrl=a.modal.area),
        KeyEvent("end"), KeyEvent("pagedown"), lambda a: seen.update(corner=a.modal.area),
        KeyEvent("right"), KeyEvent("down"), lambda a: seen.update(still=a.modal.area),
        KeyEvent("left", shift=True), *[KeyEvent("left", shift=True)] * 20,
        lambda a: seen.update(narrow=a.modal.area), KeyEvent("escape"), lambda a: None,
    ])
    assert seen["ctrl"] == (18, 5, 29, 6)
    assert seen["corner"] == (69, 23, 80, 24) and seen["still"] == seen["corner"]
    assert seen["narrow"] == (69, 23, 70, 24)
    assert app.copied == []
