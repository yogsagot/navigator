"""The *New Manager defaults* still left: *Directory length*, *Totals*, *Free
space* (DN's ``fmiDirLen``, ``fmiTotals``, ``fmiFree``, drawn by ``TInfoView``)
with File Manager Setup's *Info divider*, and *Left panel in a new Manager*."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, awaited, mounted, run_app, settle
from navkit.events import KeyEvent
from navkit.screen import ScreenBuffer

from navigator.__main__ import Navigator
from navigator.scheme import default_scheme
from navigator.settings import SETTINGS
from navigator.widgets import Panel
from navigator.widgets.manager.panel import panel as panel_module
from navigator.widgets.manager.panel.panel import ScanJob, scan_directory
from navigator.widgets.shell.commands import NewManager

FREE = "~1,000~ free bytes on ~/"


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr(panel_module, "free_space_text", lambda path: FREE)
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "x").write_text("x" * 10)
    (tmp_path / "sub" / "deeper").mkdir()
    (tmp_path / "sub" / "deeper" / "y").write_text("y" * 5)
    (tmp_path / "a").write_text("abc")
    (tmp_path / "b").write_text("de")
    return tmp_path


def panel_at(path: Path, width: int = 60, height: int = 12) -> Panel:
    panel = Panel(path, width=width, height=height)
    panel.stylesheet = default_scheme()
    return mounted(panel, size=(width, height))


def rows_of(panel: Panel) -> list[str]:
    buffer = ScreenBuffer(panel.width, panel.height)
    panel.render(buffer)
    return ["".join(buffer.get(x, y)[0] or " " for x in range(panel.width)) for y in range(panel.height)]


def test_free_space_takes_a_line_under_a_divider_and_totals_another(place):
    SETTINGS.panel_defaults.totals = True
    panel = panel_at(place)
    rows = rows_of(panel)
    assert panel.info_height == 3 and panel.rows == panel.height - 2 - 3
    assert rows[-4].strip("║│ ").startswith("─")
    assert rows[-3].strip("║│ ") == "Total: 2 files with 5 bytes"
    assert rows[-2].strip("║│ ") == "1,000 free bytes on /"

    SETTINGS.file_manager.info_divider = False
    settle()
    assert panel.info_height == 2 and rows_of(panel)[-3].strip("║│ ") == "Total: 2 files with 5 bytes"

    SETTINGS.panel_defaults.totals = SETTINGS.panel_defaults.free_space = False
    settle()
    assert panel.info_height == 0 and panel.rows == panel.height - 2


def test_a_column_divider_meets_the_info_divider_in_a_tee_and_not_the_frame(place):
    panel = panel_at(place, width=120)
    panel.cycle_view_mode()
    settle()
    buffer = ScreenBuffer(panel.width, panel.height)
    panel.render(buffer)
    spans = panel._column_spans()
    columns = [x + width for _, x, width in spans[:-1] if x + width < panel.width - 1]
    assert columns
    divider_y = panel.height - 1 - panel.info_height
    for x in columns:
        assert buffer.get(x, divider_y)[0] == "┴"
        assert buffer.get(x, panel.height - 1)[0] in ("─", "═", *panel.footer_text())


def test_directory_length_counts_each_directory_and_dot_dot_the_one_listed(place):
    entries, _ = scan_directory(place, True, dir_length=True)
    sizes = {entry.name: (entry.size, entry.counted) for entry in entries}
    assert sizes["sub"] == (15, True)
    assert sizes[".."] == (20, True)

    job = ScanJob()
    job.stop()
    entries, _ = scan_directory(place, True, dir_length=True, job=job)
    assert not any(entry.counted for entry in entries)


def test_esc_while_counting_turns_the_box_off_for_that_panel(place):
    SETTINGS.panel_defaults.directory_length = True
    panel = panel_at(place)
    assert panel.selected is not None and panel.items[0].counted
    job = panel._scan_job = ScanJob()
    panel.scanning = True
    assert awaited(panel.on_key(KeyEvent("escape")))
    assert job.stopped and not panel.shows("directory_length") and panel.shows("free_space")


def manager_of(app):
    return app.shell.desktop.active_window


@pytest.mark.parametrize("choice", ["info", "tree", "absent"])
def test_left_panel_shapes_the_first_manager_and_a_new_one(place, choice):
    SETTINGS.panel_defaults.left_panel = choice
    seen = {}

    def look(key):
        def action(a):
            manager = manager_of(a)
            seen[key] = (manager.replacement, manager.info, manager.tree, manager.hidden_side,
                         manager.right.focused)
        return action

    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    run_app(app, [lambda a: None, look("first"), lambda a: a.spawn(a.run_command(NewManager)),
                  lambda a: None, look("new")])
    for replacement, info, tree, hidden, right_focused in seen.values():
        assert right_focused
        if choice == "info":
            assert replacement is info
        elif choice == "tree":
            assert replacement is tree
        else:
            assert hidden == "left" and replacement is None


def test_files_leaves_both_panels(place):
    seen = {}
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    run_app(app, [lambda a: None, lambda a: seen.update(
        state=(a.manager.replacement, a.manager.hidden_side, a.manager.left.focused))])
    assert seen["state"] == (None, None, True)
