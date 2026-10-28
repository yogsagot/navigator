"""Alt+F12: Miller columns in the two panels' place (a departure)."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.drives import Location
from navigator.settings import SETTINGS
from navigator.widgets.manager.commands import QuickView, SwapPanels, ToggleMiller, ToggleTree
from navigator.widgets.manager.miller import MillerColumn

ALT_F12 = KeyEvent("f12", alt=True)


@pytest.fixture
def tree(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr(SETTINGS.file_manager, "miller_width", 20)
    (tmp_path / "east").mkdir()
    deep = tmp_path / "west" / "src" / "pkg"
    deep.mkdir(parents=True)
    (tmp_path / "west" / "notes.txt").write_text("hello columns\n")
    (tmp_path / "west" / "src" / "main.py").write_text("print(1)\n")
    (deep / "mod.py").write_text("x = 1\n")
    return tmp_path


def navigator(tree: Path, width: int = 120) -> Navigator:
    return Navigator(tree / "west", tree / "east", terminal=FakeTerminal(width, 30))


def cursor_on(name: str):
    def act(app):
        column = app.manager.active_panel
        column.cursor = next(i for i, item in enumerate(column.items) if item.name == name)
    return act


def test_alt_f12_opens_the_chain_from_the_root_down_to_the_active_panel(tree):
    app = navigator(tree)
    run_app(app, [cursor_on("src"), ALT_F12, lambda a: None])
    m = app.manager
    chain = m.miller.chain
    assert m.miller_mode and not m.left.visible and not m.right.visible
    assert [c.location for c in chain] == [Location.of(p) for p in reversed((tree / "west").parents)] + [
        Location.of(tree / "west")]
    current = chain[-1]
    assert m.active_panel is current and app.focused is current
    assert current.selected.name == "src"
    # Each column above has its cursor on the way down, and no ``..``.
    assert chain[-2].selected.name == "west"
    assert all(item.name != ".." for item in current.items)
    # The preview lists the directory at the cursor.
    assert m.miller.preview == "directory" and m.miller.preview_dir.location == Location.of(tree / "west" / "src")


def test_right_steps_in_and_left_steps_back(tree):
    app = navigator(tree)
    seen = {}

    def stepped_in(a):
        m = a.manager
        seen["current"] = current = m.active_panel
        assert current.location == Location.of(tree / "west" / "src") and a.focused is current
        assert m.miller.chain[-2].trail and m.miller.chain[-2].selected.name == "src"

    run_app(app, [cursor_on("src"), ALT_F12, KeyEvent("right"), stepped_in, KeyEvent("left"), lambda a: None])
    m = app.manager
    assert m.active_panel.location == Location.of(tree / "west")
    assert m.miller.preview_dir is seen["current"]  # the column left becomes the preview, cursor kept


def test_enter_on_a_directory_steps_in_and_backspace_steps_back(tree):
    app = navigator(tree)
    seen = []
    record = lambda a: seen.append(a.manager.active_panel.location)  # noqa: E731
    run_app(app, [cursor_on("src"), ALT_F12, KeyEvent("enter"), record, KeyEvent("backspace"), record])
    assert seen == [Location.of(tree / "west" / "src"), Location.of(tree / "west")]


def test_a_file_at_the_cursor_is_previewed_in_the_quick_view(tree):
    app = navigator(tree)
    run_app(app, [cursor_on("notes.txt"), ALT_F12,
                  Until(lambda a: a.manager.miller.preview_file.viewer.source is not None)])
    miller = app.manager.miller
    assert miller.preview == "file" and miller.preview_file.visible
    assert miller.preview_file.viewer.path == tree / "west" / "notes.txt"
    assert not miller.preview_dir.visible


def test_the_leftmost_columns_give_way_and_the_preview_takes_the_rest(tree):
    app = navigator(tree, width=70)
    run_app(app, [cursor_on("src"), ALT_F12, lambda a: None])
    miller = app.manager.miller
    shown = [c for c in miller.chain if c.visible]
    assert len(shown) == (70 - 20) // 20 and shown[-1] is miller.chain[-1]
    assert [c.x for c in shown] == [0, 20]
    assert miller.preview_dir.x == 40 and miller.preview_dir.width == 30


def test_a_column_moved_by_itself_brings_the_chain_with_it(tree):
    app = navigator(tree)

    def go(a):
        a.manager.active_panel.path = tree / "west" / "src" / "pkg"

    run_app(app, [ALT_F12, go, lambda a: None])
    chain = app.manager.miller.chain
    assert chain[-1].location == Location.of(tree / "west" / "src" / "pkg")
    assert chain[-2].location == Location.of(tree / "west" / "src") and chain[-2].selected.name == "pkg"
    assert chain[-3].selected.name == "src"


def test_alt_f12_again_gives_the_panels_back_at_the_directory_browsed(tree):
    app = navigator(tree)
    run_app(app, [cursor_on("src"), ALT_F12, KeyEvent("right"), cursor_on("pkg"), lambda a: None,
                  ALT_F12, lambda a: None])
    m = app.manager
    assert not m.miller_mode and m.left.visible and m.right.visible
    assert not m.miller.chain and not [c for c in m.miller.children if isinstance(c, MillerColumn)]
    assert m.left.path == tree / "west" / "src" and m.left.selected.name == "pkg"
    assert m.right.path == tree / "east" and app.focused is m.left


def test_copy_offers_the_directory_browsed(tree):
    app = navigator(tree)
    run_app(app, [ALT_F12, lambda a: None])
    m = app.manager
    assert m.passive_panel is m.active_panel


def test_tab_goes_into_the_file_previewed_and_back(tree):
    app = navigator(tree)
    seen = []
    record = lambda a: seen.append((a.focused, a.manager.active_panel))  # noqa: E731
    run_app(app, [cursor_on("notes.txt"), ALT_F12, lambda a: None, KeyEvent("tab"), record, KeyEvent("tab"),
                  record])
    miller = app.manager.miller
    assert seen == [(miller.preview_file.viewer, miller.chain[-1]), (miller.chain[-1], miller.chain[-1])]


def test_what_needs_two_panels_is_greyed(tree):
    app = navigator(tree)
    run_app(app, [ALT_F12, lambda a: None])
    m = app.manager
    for command in (SwapPanels(), ToggleTree(), QuickView()):
        assert not m.enables(command)
    assert m.enables(ToggleMiller()) and m.checks(ToggleMiller())


def test_only_the_steps_go_into_the_directory_history(tree):
    from navml.history import HISTORY

    app = navigator(tree)
    run_app(app, [cursor_on("src"), ALT_F12, lambda a: None, KeyEvent("down"), KeyEvent("up"),
                  KeyEvent("right"), lambda a: None])
    remembered = HISTORY.entries("directories")
    assert str(tree / "west" / "src") in remembered
    assert str(tree) not in remembered


def test_the_desktop_keeps_miller_columns(tree):
    from navigator.lib.config import desktop_state

    app = navigator(tree)
    run_app(app, [cursor_on("src"), ALT_F12, lambda a: None])
    kept = desktop_state._window(app.manager)
    assert kept["miller"] == {"path": str(tree / "west"), "cursor": "src", "side": "left"}


# -- tooltips -------------------------------------------------------------------


def test_a_miller_columns_cut_names_and_its_title_say_themselves_whole(tree):
    long = "a-file-with-a-name-far-too-long-for-a-column.txt"
    (tree / "west" / long).write_text("x")
    app = navigator(tree)
    seen = {}

    def look(a):
        column = a.manager.miller.chain[-1]
        top = column.inset + column.header
        row = {item.name: top + i - column.scroll for i, item in enumerate(column.items)}
        x = column.inset + column.gutter
        seen["long"] = column.tooltip_at(x, row[long])
        seen["short"] = column.tooltip_at(x, row["src"])
        text = column.title_text()
        seen["title"] = column.tooltip_at(column.label_x(text) + 1, 0)

    run_app(app, [ALT_F12, lambda a: None, look])
    assert seen["long"] == long
    assert seen["short"] == ""
    # The title names the directory alone; its tooltip gives the whole path.
    assert seen["title"] == str(tree / "west")
