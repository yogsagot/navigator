"""Alt/Ctrl + Gray ``+``/``-``: DN's ``SelectExt`` and ``SelecType``."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator

NAMES = ("a.txt", "a.c", "b.txt", "b.c", "c.zip", "d.zip", ".hidden.txt")


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    here = tmp_path / "here"
    here.mkdir()
    for name in NAMES:
        (here / name).write_text(name)
    (here / "sub").mkdir()
    (here / "sub2").mkdir()
    return here


def tagged_after(place, on: str, *keys) -> set[str]:
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}

    def put(a):
        panel = a.manager.left
        panel.show_hidden = True
        panel.cursor = [e.name for e in panel.items].index(on)

    def look(a):
        panel = a.manager.left
        seen["tags"] = {e.name for e in panel.items if e.key in panel.marked}

    run_app(app, [lambda a: setattr(a.manager.left, "show_hidden", True), lambda a: None, put, *keys,
                  lambda a: None, look])
    return seen["tags"]


def key(char, **mods):
    return KeyEvent("kp_plus" if char == "+" else "kp_minus", char, **mods)


def test_alt_gray_plus_tags_the_same_name_any_extension(place):
    assert tagged_after(place, "a.txt", key("+", alt=True)) == {"a.txt", "a.c"}


def test_alt_gray_minus_untags_them(place):
    assert tagged_after(place, "a.txt", KeyEvent("insert"), KeyEvent("up"), key("+", alt=True),
                        key("-", alt=True)) == set()


def test_alt_shift_gray_plus_tags_every_other_name_directories_too(place):
    assert tagged_after(place, "a.txt", key("+", alt=True, shift=True)) == {
        "b.txt", "b.c", "c.zip", "d.zip", ".hidden.txt", "sub", "sub2"}


def test_ctrl_gray_plus_tags_the_type_group(place):
    assert tagged_after(place, "c.zip", key("+", ctrl=True)) == {"c.zip", "d.zip"}


def test_ctrl_gray_plus_on_a_directory_tags_the_directories(place):
    assert tagged_after(place, "sub", key("+", ctrl=True)) == {"sub", "sub2"}


def test_ctrl_shift_gray_plus_tags_the_same_extension(place):
    assert tagged_after(place, "a.txt", key("+", ctrl=True, shift=True)) == {"a.txt", "b.txt", ".hidden.txt"}


def test_on_dot_dot_nothing(place):
    assert tagged_after(place, "..", key("+", alt=True), key("+", ctrl=True)) == set()


def test_the_character_forms_do_the_same(place):
    assert tagged_after(place, "a.txt", KeyEvent("plus", "+", alt=True)) == {"a.txt", "a.c"}


def test_refused_while_the_tree_has_the_keyboard(place):
    from navigator.widgets.manager.commands import SelectSimilar

    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}
    run_app(app, [KeyEvent("t", ctrl=True), lambda a: None, KeyEvent("tab"), lambda a: None,
                  lambda a: seen.update(why=a.manager.refusal(SelectSimilar()))])
    assert seen["why"] == "Only in a file panel, not beside it"
