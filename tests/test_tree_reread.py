"""DN's ``cmRereadTree``: every tree on the screen re-reads after a copy, an erase or F7 from a panel."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.widgets.file_ops.copy_dialog import CopyDialog
from navigator.widgets.file_ops.delete_dialog import DeleteDialog
from navigator.widgets.file_ops.mkdir_dialog import MkdirDialog
from navigator.widgets.tree.directory_tree import DirectoryTree

from test_side_directory import tree_lands_on


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    for name in ("a/gone", "a/keep", "b"):
        (tmp_path / name).mkdir(parents=True)
    (tmp_path / "a" / "keep" / "x.txt").write_text("x")
    return tmp_path


def listed(tree) -> set:
    return {Path(row.node.data) for row in tree.items if isinstance(row.node.data, (str, Path))}


def with_tree(place):
    """Navigator on ``a``, Ctrl+T's tree beside it, open at ``a``."""
    app = Navigator(place / "a", place / "b", terminal=FakeTerminal(80, 24))
    keep = place / "a" / "keep"
    return app, [KeyEvent("t", ctrl=True), Until(lambda a: a.manager.tree.selected_path is not None),
                 Until(tree_lands_on(lambda a: keep), timeout=3),
                 Until(lambda a: place / "a" / "gone" in listed(a.manager.tree), timeout=3)]


def cursor_to(name):
    def act(a):
        panel = a.manager.active_panel
        panel.cursor = [e.name for e in panel.items].index(name)
    return act


def test_f8_from_the_panel_takes_the_directory_out_of_the_tree(place):
    app, opened = with_tree(place)
    gone = place / "a" / "gone"
    run_app(app, [*opened, cursor_to("gone"), KeyEvent("f8"), Until(lambda a: isinstance(a.modal, DeleteDialog)),
                  KeyEvent("enter"), Until(lambda a: not gone.exists()),
                  Until(lambda a: gone not in listed(a.manager.tree), timeout=3)], timeout=15)
    assert gone not in listed(app.manager.tree)


def test_f7_from_the_panel_puts_the_new_directory_in_the_tree(place):
    app, opened = with_tree(place)
    fresh = place / "a" / "fresh"

    def name(a):
        a.modal.entry.value = "fresh"

    run_app(app, [*opened, KeyEvent("f7"), Until(lambda a: isinstance(a.modal, MkdirDialog)), name,
                  KeyEvent("enter"), Until(lambda a: fresh.is_dir()),
                  Until(lambda a: fresh in listed(a.manager.tree), timeout=3)], timeout=15)
    assert fresh in listed(app.manager.tree)


def test_f5_of_a_directory_puts_the_copy_in_the_tree(place):
    app, opened = with_tree(place)
    copied = place / "a" / "copied"

    def target(a):
        a.modal.target.value = str(copied)

    run_app(app, [*opened, cursor_to("keep"), KeyEvent("f5"), Until(lambda a: isinstance(a.modal, CopyDialog)),
                  target, KeyEvent("enter"), Until(lambda a: (copied / "x.txt").exists()),
                  Until(lambda a: copied in listed(a.manager.tree), timeout=3)], timeout=15)
    assert copied in listed(app.manager.tree)


def test_a_directory_tree_window_follows_an_erase_too(place):
    from navigator.widgets.tree.tree_window import TreeWindow

    app = Navigator(place / "a", place / "b", terminal=FakeTerminal(80, 24))
    gone = place / "a" / "gone"
    keep = place / "a" / "keep"

    def window(a):
        return next(w for w in a.shell.desktop.windows() if isinstance(w, TreeWindow))

    def open_window(a):
        a.shell.desktop.open(TreeWindow())

    def erase(a):
        panel = a.manager.left
        entry = next(e for e in panel.items if e.name == "gone")
        a.manager.spawn(a.manager.erase_entries(panel, [entry], quiet=True))

    run_app(app, [open_window, Until(lambda a: window(a).tree.selected_path is not None, timeout=3),
                  lambda a: window(a).tree.show(keep),
                  Until(lambda a: gone in listed(window(a).tree), timeout=3),
                  erase, Until(lambda a: not gone.exists()),
                  Until(lambda a: gone not in listed(window(a).tree), timeout=3)], timeout=15)
    assert gone not in listed(window(app).tree)
    assert isinstance(window(app).tree, DirectoryTree)
