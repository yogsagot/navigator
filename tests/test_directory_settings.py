"""Settings remembered per directory, and the cursor left in one (``directory_settings``)."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, Until, mounted, run_app, settle

from navigator.lib.config import directory_settings, panel_state
from navigator.models.directory_settings import DirectorySettings
from navigator.models.panel_state import PanelState
from navigator.settings import SETTINGS
from navigator.widgets.manager.manager import Manager


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    SETTINGS.startup.autosave_desktop = False
    for name in ("one", "two", "one/inner", "one/inner/deep"):
        (tmp_path / name).mkdir()
    for name in ("a.txt", "b.py", "c.txt"):
        (tmp_path / "one" / name).write_text(name)
    (tmp_path / "two" / "x.py").write_text("x")
    return tmp_path


def manager(place) -> Manager:
    found = mounted(Manager(place / "one", place / "two"), size=(100, 30))
    settle()
    return found


def go(panel, path) -> None:
    panel.path = path
    settle()


def test_a_marked_directory_comes_back_with_its_settings_and_leaving_it_gives_the_panels_back(place):
    left = manager(place).left
    left.remember_here(subdirs=False)
    left.sort_by("size")
    left.set_file_mask("*.py")
    settle()
    assert DirectorySettings.get(path=str(place / "one")).sort_mode == "size"
    go(left, place / "two")
    assert (left.sort_mode, left.file_mask, left.remembered) == ("name", "*", "")
    go(left, place / "one")
    assert (left.sort_mode, left.file_mask) == ("size", "*.py")
    assert [item.name for item in left.items if not item.is_dir] == ["b.py"]
    assert left.remembers_here


def test_arriving_reads_the_directory_once_with_the_records_settings(place, monkeypatch):
    from navigator.widgets.manager.panel import panel as panel_module

    left = manager(place).left
    left.remember_here(subdirs=False)
    left.set_file_mask("*.py")
    go(left, place / "two")
    reads = []
    real = panel_module._read_location

    def counting(location, show_hidden, sort, **kwargs):
        reads.append(kwargs.get("mask"))
        return real(location, show_hidden, sort, **kwargs)

    monkeypatch.setattr(panel_module, "_read_location", counting)
    go(left, place / "one")
    assert reads == ["*.py"]


def test_a_directory_not_marked_for_those_below_is_its_own_alone(place):
    left = manager(place).left
    left.remember_here(subdirs=False)
    left.sort_by("size")
    settle()
    go(left, place / "one" / "inner")
    assert (left.sort_mode, left.remembered) == ("name", "")


def test_one_marked_for_those_below_shows_them_its_way_and_takes_their_changes(place):
    left = manager(place).left
    left.remember_here(subdirs=True)
    left.sort_by("size")
    settle()
    go(left, place / "one" / "inner" / "deep")
    assert left.sort_mode == "size"
    assert left.remembered == str(place / "one") and not left.remembers_here
    assert left.remembered_mark() in ("\u25c7", "+", "\uf02e")
    left.sort_by("time")
    settle()
    assert DirectorySettings.get(path=str(place / "one")).sort_mode == "time"
    assert DirectorySettings.get(path=str(place / "one" / "inner" / "deep")) is None


def test_forgetting_gives_the_panels_own_settings_back(place):
    left = manager(place).left
    left.remember_here(subdirs=False)
    left.sort_by("size")
    settle()
    left.forget_here()
    settle()
    assert (left.sort_mode, left.remembered) == ("name", "")
    assert DirectorySettings.count() == 0


def test_with_the_setting_off_nothing_is_applied(place):
    left = manager(place).left
    left.remember_here(subdirs=False)
    left.sort_by("size")
    settle()
    go(left, place / "two")
    SETTINGS.file_manager.remember_directories = "off"
    go(left, place / "one")
    assert (left.sort_mode, left.remembered) == ("name", "")


def test_every_directory_remembers_what_is_changed_in_it(place):
    SETTINGS.file_manager.remember_directories = "all"
    left = manager(place).left
    left.sort_by("size")
    settle()
    assert left.remembers_here
    go(left, place / "two")
    assert left.sort_mode == "name"
    go(left, place / "one")
    assert left.sort_mode == "size"


def test_the_side_keeps_the_panels_own_settings_not_a_records(place):
    m = manager(place)
    left = m.left
    left.remember_here(subdirs=False)
    left.sort_by("size")
    settle()
    assert panel_state.kept_values(left)["sort_mode"] == "name"
    row = PanelState.get(side="left")
    assert row is None or row.sort_mode != "size"


def test_the_cursor_comes_back_to_where_it_was_left(place):
    left = manager(place).left
    left.cursor = next(i for i, item in enumerate(left.items) if item.name == "c.txt")
    go(left, place / "two")
    go(left, place / "one")
    assert left.selected.name == "c.txt"


def test_going_up_still_lands_on_the_directory_left(place):
    left = manager(place).left
    left.cursor = next(i for i, item in enumerate(left.items) if item.name == "c.txt")
    go(left, place / "one" / "inner")
    left.go_up()
    settle()
    assert left.selected.name == "inner"


def test_without_restore_cursor_a_directory_starts_at_the_top(place):
    SETTINGS.file_manager.restore_cursor = False
    left = manager(place).left
    left.cursor = next(i for i, item in enumerate(left.items) if item.name == "c.txt")
    go(left, place / "two")
    go(left, place / "one")
    assert left.cursor == 0


def test_the_cursors_kept_are_capped(place, monkeypatch):
    from navigator.models.directory_cursor import DirectoryCursor
    from navigator.lib.drives import Location

    monkeypatch.setattr(directory_settings, "CURSORS", 3)
    for index in range(5):
        directory_settings.keep_cursor(Location.of(place / f"d{index}"), "x")
    assert DirectoryCursor.count() == 3
    assert DirectoryCursor.get(path=str(place / "d0")) is None


def test_the_menu_entry_asks_then_marks_and_ticks(place):
    from navkit.events import KeyEvent

    from navigator.__main__ import Navigator
    from navigator.widgets.manager.commands import RememberDirectory

    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30))
    seen = {}

    def look(a):
        seen["ticked"] = a.manager.checks(RememberDirectory())
        seen["title"] = a.manager.left.title_text()

    run_app(app, [
        lambda a: a.spawn(a.run_command(RememberDirectory)),
        Until(lambda a: a.modal is not None),
        KeyEvent("enter"),
        Until(lambda a: a.modal is None),
        look,
    ])
    assert DirectorySettings.get(path=str(place / "one")) is not None
    assert seen["ticked"]
    assert seen["title"].lstrip()[0] in ("\u25c6", "*", "\uf08d")


def test_a_saved_desktop_keeps_the_panels_own_settings_and_the_record_comes_back(place):
    from navigator.lib.config import desktop_state

    left = manager(place).left
    left.remember_here(subdirs=False)
    left.sort_by("size")
    settle()
    kept = desktop_state._panel(left)
    assert (kept["path"], kept["sort_mode"]) == (str(place / "one"), "name")
    fresh = manager(place).left
    desktop_state._seed_panel(fresh, kept)
    settle()
    assert (fresh.sort_mode, fresh.own_settings()["sort_mode"]) == ("size", "name")


def test_a_sort_changed_and_then_remembered_stays_with_the_directory(place):
    left = manager(place).left
    go(left, place / "one" / "inner")
    left.sort_by("size")
    settle()
    left.remember_here(subdirs=False)
    settle()
    left.go_up()
    settle()
    assert (left.sort_mode, left.remembered) == ("name", "")
    go(left, place / "one" / "inner")
    assert left.sort_mode == "size"
