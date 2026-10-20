"""The *New Manager defaults* still left: *Directory length*, *Current file*,
*Selected files*, *Totals*, *Free space* (DN's ``fmiDirLen``, ``fmiCurrent``,
``fmiSelected``, ``fmiTotals``, ``fmiFree``, drawn by ``TInfoView``) with File
Manager Setup's *Info divider* and *Current file* fields, and *Left panel in a
new Manager*."""

from __future__ import annotations

import os
import stat
import time
from pathlib import Path

import pytest

from conftest import FakeTerminal, awaited, mounted, run_app, settle
from navkit.events import KeyEvent
from navkit.screen import ScreenBuffer

from navigator.__main__ import Navigator
from navigator.lib.appearance.scheme import default_scheme
from navigator.settings import SETTINGS
from navigator.widgets import Panel
from navigator.lib.drives import listing as listing_module
from navigator.widgets.manager.panel import panel as panel_module
from navigator.widgets.manager.panel.panel import ScanJob, scan_directory
from navigator.widgets.shell.commands import NewManager

FREE = (1000, "/")


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr(listing_module, "free_space_of", lambda path: FREE)
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
    assert panel.info_height == 5 and panel.rows == panel.height - 2 - 5
    assert rows[-6][0] in "├╟" and rows[-6][-1] in "┤╢" and rows[-6][1] == "─"
    assert rows[-5].strip("║│ ").startswith("..")
    assert rows[-4].strip("║│ ") == "No files selected"
    assert rows[-3].strip("║│ ") == "Total: 2 files with 5 bytes"
    assert rows[-2].strip("║│ ") == "1,000 free bytes on /"

    SETTINGS.file_manager.info_divider = False
    settle()
    assert panel.info_height == 4 and rows_of(panel)[-3].strip("║│ ") == "Total: 2 files with 5 bytes"

    SETTINGS.panel_defaults.totals = SETTINGS.panel_defaults.free_space = False
    SETTINGS.panel_defaults.current_file = SETTINGS.panel_defaults.selected_files = False
    settle()
    assert panel.info_height == 0 and panel.rows == panel.height - 2


def test_alt_i_hides_the_footer_and_gives_its_rows_to_the_listing(place):
    panel = panel_at(place)
    assert panel.info_height == 4
    panel.toggle_info()
    settle()
    rows = rows_of(panel)
    assert panel.info_height == 0 and panel.rows == panel.height - 2
    assert not any("free" in row for row in rows)
    panel.toggle_info()
    settle()
    assert panel.info_height == 4 and rows_of(panel)[-2].strip("║│ ") == "1,000 free bytes on /"


def test_alt_i_toggles_the_active_panel_s_footer_and_ticks_the_menu(place):
    from navigator.widgets.manager.commands import ToggleInfoLines
    seen = []

    def look(a):
        manager = manager_of(a)
        seen.append((manager.active_panel.show_info, manager.passive_panel.show_info,
                     manager.checks(ToggleInfoLines())))

    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    run_app(app, [lambda a: None, look, lambda a: a.post_event(KeyEvent("alt+i")), look])
    assert seen == [(True, True, True), (False, True, False)]


def test_free_space_over_a_kilobyte_is_shortened_as_df_h_does(place, monkeypatch):
    monkeypatch.setattr(listing_module, "free_space_of", lambda path: (71_123_906_560, "/"))
    assert rows_of(panel_at(place))[-2].strip("║│ ") == "66G free on /"


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


# -- Current file and Selected files ---------------------------------------------

def info_texts(panel: Panel) -> list[tuple[str, str]]:
    return [(text.rstrip(), part) for text, part in panel.info_lines]


def at(panel: Panel, name: str) -> Panel:
    panel.cursor = next(i for i, item in enumerate(panel.items) if item.name == name)
    settle()
    return panel


def stamp(path: Path, fmt: str) -> str:
    return time.strftime(fmt, time.localtime(path.stat().st_mtime))


def test_the_current_file_line_holds_the_detailed_columns_places(place):
    panel = at(panel_at(place, width=80), "a")
    text, part = panel.info_lines[0]
    assert part == "current-file" and [key for key, _, _ in panel.detail_columns] == [
        "name", "size", "attributes", "owner", "date"]
    entry = panel.selected
    for key, x, width in panel.detail_columns:
        cells = text[x - panel.inset: x - panel.inset + width]
        if key == "name":
            assert cells[panel.gutter:].rstrip() == "a" and not cells[:panel.gutter].strip()
        elif key == "size":
            assert cells == "3".rjust(width)
        else:
            assert cells.rstrip() == getattr(entry, Panel.DETAIL_COLUMNS[key][2])
        # A blank where the divider stands.
        assert x - panel.inset - 1 < 0 or text[x - panel.inset - 1] == " "
    assert stamp(place / "a", "%d-%m-%Y %H:%M") in text


def test_a_directory_s_size_is_dn_s_sub_dir_and_dot_dot_up_dir(place):
    panel = at(panel_at(place), "sub")
    assert panel.info_lines[0][0].split()[1] == "SUB-DIR"
    assert at(panel, "..").info_lines[0][0].split()[1] == "UP--DIR"
    SETTINGS.panel_defaults.directory_length = True
    panel = at(panel_at(place), "sub")
    assert panel.info_lines[0][0].split()[1] == "15"


def test_the_line_follows_columns_setup_in_every_mode(place):
    panel = at(panel_at(place, width=80), "a")
    assert panel.view_mode == "simple"
    panel.columns = frozenset({"size"})
    settle()
    assert info_texts(panel)[0][0].split() == ["a", "3"]
    panel.columns = frozenset({"date", "attributes"})
    settle()
    mode = os.stat(place / "a").st_mode
    assert info_texts(panel)[0][0].split() == [
        "a", stat.filemode(mode)[1:], stamp(place / "a", "%d-%m-%Y"), stamp(place / "a", "%H:%M")]
    panel.columns = frozenset()
    settle()
    assert info_texts(panel)[0][0].strip() == "a"


def test_a_narrow_panel_drops_the_columns_the_rows_drop_and_cuts_the_name(place):
    (place / "a_rather_long_file_name.txt").write_text("12345")
    panel = at(panel_at(place, width=30), "a_rather_long_file_name.txt")
    text = panel.info_lines[0][0]
    assert [key for key, _, _ in panel.detail_columns] == ["name", "size"]
    assert len(text) == panel.inner_width == 28
    name, size = text.split()
    assert size == "5" and name.endswith(("…", "...")) and name.startswith("a_rather")


def test_a_size_wider_than_its_column_takes_cells_from_the_name(place):
    (place / "big").write_bytes(b"\0" * 1_234_567)
    panel = at(panel_at(place, width=80), "big")
    _, x, width = panel.detail_columns[1]
    text = panel.info_lines[0][0]
    end = x - panel.inset + width
    assert text[:end].endswith(" 1,234,567") and text[:end].split() == ["big", "1,234,567"]
    assert len("1,234,567") > width


def test_the_selected_line_says_none_then_totals_the_tagged(place):
    panel = at(panel_at(place), "a")
    assert ("No files selected", "selected-files") in info_texts(panel)
    panel.marked = frozenset({"a", "b"})
    settle()
    assert ("~5 bytes in 2~ selected files", "selected-files") in info_texts(panel)


def test_without_selected_files_the_selection_takes_the_current_file_s_line(place):
    SETTINGS.panel_defaults.selected_files = False
    panel = at(panel_at(place), "a")
    assert [part for _, part in panel.info_lines] == ["current-file", "free-space"]
    panel.marked = frozenset({"b"})
    settle()
    assert info_texts(panel)[0] == ("~2 bytes in 1~ selected file", "selected-files")


def test_a_symlink_gets_a_target_line_and_the_listing_keeps_its_height(place):
    (place / "link").symlink_to("a")
    panel = at(panel_at(place), "link")
    assert info_texts(panel)[1] == ("-> a", "current-file")
    rows = panel.rows
    at(panel, "b")
    assert info_texts(panel)[1] == ("", "current-file") and panel.rows == rows
    SETTINGS.file_manager.link_line = False
    settle()
    assert [part for _, part in panel.info_lines] == ["current-file", "selected-files", "free-space"]


def test_without_a_symlink_there_is_no_target_line(place):
    panel = at(panel_at(place), "a")
    assert [part for _, part in panel.info_lines] == ["current-file", "selected-files", "free-space"]


def test_a_name_with_a_tilde_is_drawn_as_it_is(place):
    (place / "~backup~").write_text("")
    panel = at(panel_at(place), "~backup~")
    assert rows_of(panel)[-4].strip("║│ ").startswith("~backup~ ")


def test_the_frame_s_footer_is_left_to_the_quick_search(place):
    panel = at(panel_at(place), "a")
    assert panel.footer_text() == ""
    panel.quick_search = "a"
    assert panel.footer_text().endswith("a ")


def test_the_setup_page_s_display_boxes_carry_the_link_line():
    from navigator.widgets.setup.fm_setup_page import FMSetupPage
    page = FMSetupPage()
    assert page.display.value >> 3 & 1
    page.display.value &= ~(1 << 3)
    assert page.accept()["link_line"] is False
