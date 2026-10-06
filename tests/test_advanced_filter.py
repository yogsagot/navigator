"""Alt+Del: the advanced *Filter* (``CM_AdvancedFilter``)."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.advfilter import combine, extensions
from navigator.widgets.manager.panel.panel import DirEntry


def test_the_box_lists_star_and_each_extension_once():
    entries = [DirEntry("..", True, 0), DirEntry("dir.d", True, 0), DirEntry("a.c", False, 1),
               DirEntry("b.c", False, 1), DirEntry("C.TXT", False, 1), DirEntry("README", False, 1),
               DirEntry(".rc", False, 1)]
    assert extensions(entries) == ["*", "*.c", "*.TXT"]


@pytest.mark.parametrize("mask, chosen, show, result", [
    ("*", ["*.txt"], True, "*.txt"),
    ("*", ["*.bak", "*.o"], False, "*;-*.bak;-*.o"),
    ("*.txt", ["*.c"], True, "*.txt;*.c"),
    ("*;-*.bak", ["*.bak"], True, "*;*.bak"),
    ("*.txt;*.c", ["*.txt"], False, "*.c;-*.txt"),
    ("*.txt", ["*"], True, "*"),
    ("*.txt", ["*"], False, "-*"),
    ("*.txt", [], True, "*.txt"),
])
def test_show_and_hide_fold_into_the_mask(mask, chosen, show, result):
    assert combine(mask, chosen, show) == result


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    for name in ("a.c", "b.c", "x.bak", "y.txt"):
        (tmp_path / name).write_text(name)
    (tmp_path / "sub").mkdir()
    return tmp_path


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def listed(app) -> list[str]:
    return [e.name for e in app.manager.left.items if e.name != ".."]


def filtering(app) -> bool:
    return app.modal is not None and app.modal.title == "Filter"


def test_hide_then_show_then_close(place):
    app = navigator(place)
    seen = {}

    def on(mask):
        def action(a):
            a.modal.masks.cursor = a.modal.masks.items.index(mask)
        return action

    run_app(app, [
        KeyEvent("delete", alt=True), Until(filtering),
        lambda a: seen.update(masks=list(a.modal.masks.items)),
        on("*.bak"), KeyEvent("h", alt=True), Until(lambda a: "x.bak" not in listed(a)),
        Until(filtering),
        lambda a: seen.update(hidden=listed(a), mask=a.manager.left.file_mask, again=a.modal.masks.cursor),
        on("*.c"), KeyEvent("space"), on("*.txt"), KeyEvent("space"), KeyEvent("s", alt=True),
        Until(lambda a: "a.c" in listed(a) and "x.bak" not in listed(a) and len(listed(a)) == 4),
        Until(filtering), KeyEvent("escape"), lambda a: None,
        lambda a: seen.update(shown=listed(a), last=a.manager.left.file_mask, modal=a.modal),
    ])
    assert seen["masks"] == ["*", "*.bak", "*.c", "*.txt"]
    assert seen["hidden"] == ["sub", "a.c", "b.c", "y.txt"] and seen["mask"] == "*;-*.bak"
    assert seen["again"] == 1
    assert seen["last"] == "*;-*.bak;*.c;*.txt" and seen["modal"] is None
    assert seen["shown"] == ["sub", "a.c", "b.c", "y.txt"]


def test_a_mask_shows_in_the_panels_title_and_the_path_gives_way(place):
    app = navigator(place)
    seen = {}

    def masked(a):
        a.manager.left.set_file_mask("*;-*.bak")

    run_app(app, [lambda a: seen.update(plain=a.manager.left.title_text()), masked, lambda a: None,
                  lambda a: seen.update(masked=a.manager.left.title_text(),
                                        right=a.manager.right.title_text(),
                                        width=a.manager.left.width)])
    assert "[" not in seen["plain"] and seen["right"] == seen["plain"]
    assert seen["masked"].endswith(" [*;-*.bak] ")
    assert len(seen["masked"]) <= seen["width"] - 4 + 2


def test_a_long_mask_is_cut_and_still_bracketed(place):
    from navigator.widgets.manager.panel.panel import Panel

    panel = Panel(place)
    panel.width = 30
    panel.file_mask = ";".join(f"*.e{n}" for n in range(20))
    title = panel.title_text()
    assert title.endswith("...] ") and "[" in title and len(title) <= 30 - 4 + 2
