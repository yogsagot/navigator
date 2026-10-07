"""Alt+K: *Columns Setup* (``CM_SetShowParms``), one panel's detailed columns."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "deep" / "er").mkdir(parents=True)
    (tmp_path / "deep" / "er" / "x.txt").write_text("x")
    (tmp_path / "a.txt").write_text("a")
    return tmp_path


def navigator(path: Path, width: int = 220) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(width, 24))


def keys(panel) -> list[str]:
    return [key for key, _, _ in panel.detail_columns]


def test_ok_shows_the_detailed_mode_with_the_columns_ticked_and_none_is_names_alone(place):
    app = navigator(place)
    seen = {}

    def tick(value):
        def action(a):
            seen.setdefault("title", a.modal.title)
            a.modal.show.value = value
        return action

    run_app(app, [KeyEvent("k", alt=True), lambda a: None, tick(0b1001), KeyEvent("enter"), lambda a: None,
                  lambda a: seen.update(first=(a.manager.left.view_mode, keys(a.manager.left),
                                               a.manager.right.view_mode)),
                  KeyEvent("k", alt=True), lambda a: None, tick(0), KeyEvent("enter"), lambda a: None,
                  lambda a: seen.update(second=a.manager.left.view_mode)])
    assert seen["title"] == "Columns Setup"
    assert seen["first"] == ("detailed", ["name", "size", "date"], "simple")
    assert seen["second"] == "list"


def test_brief_and_full(place):
    app = navigator(place)
    seen = {}

    def narrow(a):
        a.manager.left.columns = frozenset({"size"})

    run_app(app, [narrow, KeyEvent("k", alt=True), lambda a: None, KeyEvent("b", alt=True), lambda a: None,
                  lambda a: seen.update(brief=a.manager.left.view_mode),
                  KeyEvent("k", alt=True), lambda a: None, KeyEvent("f", alt=True), lambda a: None,
                  lambda a: seen.update(full=(a.manager.left.view_mode, keys(a.manager.left)))])
    assert seen["brief"] == "list"
    assert seen["full"] == ("detailed", ["name", "size", "attributes", "owner", "date"])


def test_a_find_listing_has_a_path_column_cut_from_its_start(place):
    from navigator.widgets.manager.commands import DirBranch

    app = navigator(place)
    seen = {}

    def detailed(a):
        a.manager.left.view_mode = "detailed"

    def look(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index("x.txt")
        x = dict((k, (x, w)) for k, x, w in panel.detail_columns)["path"]
        from navkit.screen import ScreenBuffer
        buffer = ScreenBuffer(panel.width, panel.height)
        panel.render(buffer)
        rows = ["".join(buffer.get(c, r)[0] or " " for c in range(x[0], x[0] + x[1]))
                for r in range(panel.height)]
        seen.update(keys=keys(panel), rows=rows, width=x[1])

    run_app(app, [detailed, lambda a: a.spawn(a.run_command(DirBranch)),
                  Until(lambda a: a.manager.left.found is not None and not a.manager.left.found.live),
                  lambda a: None, look])
    assert seen["keys"][-1] == "path"
    deep = str(place / "deep" / "er")
    shown = deep if len(deep) <= seen["width"] else "..." + deep[-(seen["width"] - 3):]
    assert any(row.rstrip() == shown for row in seen["rows"])


def test_column_defaults_seed_a_new_panel_and_each_find_listing(place):
    from navigator.settings import SETTINGS
    from navigator.widgets.manager.commands import DirBranch

    SETTINGS.column_defaults.update({"disk_owner": False, "disk_attributes": False, "find_size": False})
    app = navigator(place)
    seen = {}

    def detailed(a):
        a.manager.left.view_mode = "detailed"
        seen["disk"] = keys(a.manager.left)

    def narrow(a):
        a.manager.left.shown_columns = frozenset({"date"})  # Alt+K on the listing: the listing's alone

    run_app(app, [detailed, lambda a: a.spawn(a.run_command(DirBranch)),
                  Until(lambda a: a.manager.left.found is not None and not a.manager.left.found.live),
                  lambda a: None, lambda a: seen.update(find=keys(a.manager.left)), narrow, lambda a: None,
                  lambda a: a.manager.left.leave_found(), lambda a: None,
                  lambda a: seen.update(back=keys(a.manager.left)),
                  lambda a: a.spawn(a.run_command(DirBranch)),
                  Until(lambda a: a.manager.left.found is not None and not a.manager.left.found.live),
                  lambda a: None, lambda a: seen.update(again=keys(a.manager.left))])
    assert seen["disk"] == ["name", "size", "date"]
    assert seen["find"] == ["name", "attributes", "owner", "date", "path"]
    assert seen["back"] == ["name", "size", "date"]
    assert seen["again"] == seen["find"]


def test_the_column_defaults_dialog_saves_its_section(place):
    from navigator.settings import SETTINGS
    from navigator.widgets.shell.commands import ColumnDefaults

    app = navigator(place)
    seen = {}

    def untick(a):
        seen["title"] = a.modal.title
        seen["before"] = (a.modal.disk.value, a.modal.find.value)
        a.modal.disk.value = 0b1001
        a.modal.find.value = 0b10000

    run_app(app, [lambda a: a.spawn(a.run_command(ColumnDefaults)),
                  Until(lambda a: getattr(a.modal, "title", None) == "Column Defaults", timeout=5),
                  untick, KeyEvent("enter"), lambda a: None])
    assert seen["title"] == "Column Defaults" and seen["before"] == (0b1111, 0b11111)
    assert SETTINGS.column_defaults.columns(False) == {"size", "date"}
    assert SETTINGS.column_defaults.columns(True) == {"path"}
    assert "disk_owner = no" in SETTINGS.path.read_text()
