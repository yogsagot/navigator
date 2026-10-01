"""The file manager itself: panel model, layout and key handling."""

from __future__ import annotations

import asyncio
import pathlib
import subprocess
import sys
import time
from datetime import datetime
from dataclasses import replace
from importlib import metadata
from pathlib import Path

import pytest

from navkit.capabilities import FULL
from navkit.commands import key_table
from navkit.events import DoubleClickEvent, KeyEvent, MouseClickEvent
from navkit.glyphs import GLYPHS_ASCII, GLYPHS_NERD, GLYPHS_UNICODE
from navkit.reactive import is_bound
from navkit.stylesheet import StylesheetError
from navkit.screen import ScreenBuffer, char_width
from navkit.terminal import SHOW_CURSOR, encode_key

from conftest import FakeTerminal, awaited, mounted, run_app, settle
from navigator import filetypes
from navigator import icons
from navigator import __version__
from navkit.application import Application
from navigator.__main__ import Navigator, main, version_banner
from navigator.widgets.manager.manager import Manager
from navigator.widgets.file_ops.mkdir_dialog import MkdirDialog
from navml.widgets import InputLine
from navigator.scheme import THEMES, default_scheme, load_scheme, theme_names
from navigator.widgets import Clock, DirEntry, Manager, Panel, Shell
from navigator.widgets.manager.panel.panel import fit_text, skip_cells, window_text
from navigator.widgets.shell.clock import clock as clock_module
from navml.widgets import Window


def navigator(path, size=(80, 24), **kwargs) -> Navigator:
    """A Navigator on a fake terminal of *size*, both panels showing *path*."""
    return Navigator(path, path, terminal=FakeTerminal(*size), **kwargs)


@pytest.fixture
def tree(tmp_path):
    """A small directory tree to list."""
    (tmp_path / "alpha").mkdir()
    (tmp_path / "beta").mkdir()
    (tmp_path / "one.txt").write_text("x" * 10)
    (tmp_path / "two.txt").write_text("y" * 2048)
    (tmp_path / "alpha" / "nested.txt").write_text("z")
    return tmp_path


@pytest.fixture
def panel(tree):
    # A panel outside the desktop has no scheme to resolve against, so it gets
    # the Navigator one directly -- the same sheet Manager installs on itself.
    widget = Panel(tree, width=40, height=20)
    widget.stylesheet = default_scheme()
    # Mounted, because a panel's effects live in ``mounted()`` now -- see
    # ``conftest.mounted``.  A detached one never rescans, so its listing
    # would be empty and every assertion below would be about nothing.
    return mounted(widget, size=(40, 20))


def names(panel: Panel) -> list[str]:
    return [entry.name for entry in panel.items]


# A panel's model reacts to what it is told rather than doing it on the spot,
# so a test driving it without a running application has to call ``settle()``
# between acting and asserting -- that is what the event loop does per batch.


def test_listing_puts_parent_first_then_directories(panel):
    assert names(panel) == ["..", "alpha", "beta", "one.txt", "two.txt"]


def test_root_has_no_parent_entry():
    # There is nothing above "/", so it must not offer a ".." entry.
    assert ".." not in names(Panel(Path("/"), width=40, height=20))


def test_unreadable_directory_reports_an_error(tmp_path):
    missing = mounted(Panel(tmp_path / "nope", width=40, height=20), size=(40, 20))
    assert missing.error is not None
    # ".." survives, so the user can still climb back out of a dead end.
    assert names(missing) == [".."]


def test_the_error_is_painted_instead_of_a_listing(tmp_path):
    missing = mounted(Panel(tmp_path / "nope", width=40, height=20), size=(40, 20))
    buffer = ScreenBuffer(40, 20)
    missing.render(buffer)
    # Row 1, immediately under the top frame, which is where a list's first
    # row goes.  It was row 2 while the panel painted its own listing and the
    # blank line was nothing in particular; `ListViewer' puts the message
    # where the rows it replaces would have started.
    painted = "".join(buffer.get(x, 1)[0] for x in range(40))
    assert missing.error[:20] in painted


@pytest.mark.parametrize(
    ("name", "is_dir", "size", "expected"),
    [
        ("..", True, 0, " UP--DIR"),
        ("alpha", True, 0, "     DIR"),
        ("small", False, 10, "      10"),
        ("big", False, 2048, "      2K"),
        ("huge", False, 5 * 1024 * 1024, "      5M"),
    ],
)
def test_size_column(name, is_dir, size, expected):
    assert DirEntry(name, is_dir, size).display_size == expected


def test_cursor_movement_is_clamped(panel):
    assert panel.cursor == 0
    panel.move_cursor(-5)
    settle()
    assert panel.cursor == 0
    panel.move_cursor(2)
    settle()
    assert panel.selected.name == "beta"
    panel.move_cursor(999)
    settle()
    assert panel.cursor == len(panel.items) - 1


def test_the_cursor_is_clamped_however_it_was_moved(panel):
    # Not through move_cursor: the invariant belongs to the panel, not to the
    # one method that used to enforce it.
    panel.cursor = 99
    settle()
    assert panel.cursor == len(panel.items) - 1


def test_a_rescan_keeps_the_cursor_on_its_entry(panel, tree):
    # DOS Navigator's RereadDir found the current file again by name, so a
    # re-read after a command left the cursor where the user had it.
    panel.move_cursor(4)
    settle()
    name = panel.selected.name
    (tree / "aaa").mkdir()          # sorts in above it, moving it down a row
    panel.reload()
    settle()
    assert panel.selected.name == name


def test_a_rescan_stays_in_place_when_the_entry_went(panel, tree):
    panel.cursor = next(i for i, e in enumerate(panel.items) if e.name == "one.txt")
    settle()
    where = panel.cursor
    (tree / "one.txt").unlink()
    panel.reload()
    settle()
    assert panel.cursor == min(where, len(panel.items) - 1)


def test_a_rescan_after_a_change_of_directory_starts_at_the_top(panel, tree):
    panel.move_cursor(2)
    settle()
    panel.reload()
    panel.path = tree / "alpha"
    settle()
    assert panel.cursor == 0


def test_cursor_scrolls_the_view(tmp_path):
    for index in range(50):
        (tmp_path / f"file{index:02d}").write_text("")
    panel = mounted(Panel(tmp_path, width=40, height=10), size=(40, 10))
    assert panel.scroll == 0
    panel.move_cursor(len(panel.items))
    settle()
    assert panel.scroll > 0
    assert panel.scroll <= panel.cursor < panel.scroll + panel.rows
    panel.move_cursor(-len(panel.items))
    settle()
    assert panel.scroll == 0


def test_the_scroll_follows_the_cursor_when_the_panel_shrinks(tmp_path):
    for index in range(50):
        (tmp_path / f"file{index:02d}").write_text("")
    panel = Panel(tmp_path, width=40, height=40)
    panel.move_cursor(30)
    settle()
    assert panel.scroll == 0  # everything still fits
    panel.height = 10
    settle()
    # Nothing moved the cursor, but the view has to come and find it.
    assert panel.scroll <= panel.cursor < panel.scroll + panel.rows


def test_entering_a_directory(panel, tree):
    panel.move_cursor(1)  # "alpha"
    settle()
    panel.enter()
    settle()
    assert panel.path == tree / "alpha"
    assert names(panel) == ["..", "nested.txt"]


def test_leaving_a_directory_restores_the_cursor(panel, tree):
    panel.move_cursor(1)
    settle()
    panel.enter()  # into alpha
    settle()
    panel.enter()  # ".." back out
    settle()
    assert panel.path == tree
    assert panel.selected.name == "alpha"


def test_entering_a_file_does_nothing(panel, tree):
    panel.move_cursor(3)  # "one.txt"
    settle()
    panel.enter()
    settle()
    assert panel.path == tree


def test_reload_picks_up_new_files(panel, tree):
    (tree / "gamma").mkdir()
    panel.reload()
    settle()
    assert "gamma" in names(panel)


def screen(left=Path("."), right=Path("."), size=(80, 24)) -> Shell:
    """The whole Navigator screen, mounted on a fake terminal of *size*."""
    return mounted(Shell(left, right), size=size)


def test_manager_layout_splits_the_screen():
    shell = screen()
    manager = shell.manager
    assert (manager.left.x, manager.left.width) == (0, 40)
    assert (manager.right.x, manager.right.width) == (40, 40)
    assert shell.menu.y == 0
    assert shell.keybar.y == 23
    assert shell.command_line.y == 22
    assert manager.left.height == manager.right.height == 21


def test_manager_layout_survives_an_odd_width():
    manager = screen(size=(81, 24)).manager
    assert manager.left.width + manager.right.width == 81


def test_the_panels_follow_the_desktop_without_a_layout_method():
    # The screen declares its children's geometry once; only the root's size
    # is imperative, and everything else derives -- the zoomed file manager
    # included, which the desktop re-fits when its own size moves.
    shell = screen()
    manager = shell.manager
    shell.layout(120, 40)
    settle()
    assert (manager.left.width, manager.right.x) == (60, 60)
    assert manager.left.height == 37
    assert shell.keybar.y == 39
    assert (shell.command_line.y, shell.command_line.width) == (38, 120)


# -- the screen is markup ----------------------------------------------------


def test_the_desktop_is_built_from_its_document():
    """`Manager' and `Shell' are both markup, and say so."""
    from navml.component import Component

    assert Manager.__navml_source__ == "manager.nml"
    assert Shell.__navml_source__ == "shell.nml"
    assert issubclass(Manager, Component)
    assert issubclass(Manager, Window)


def test_the_geometry_in_the_document_is_what_places_the_children():
    shell = screen(size=(100, 30))
    manager = shell.manager
    # The row is bound to the window; the panels in it are arranged by it,
    # so their own geometry is the layout's to write and carries no binding.
    assert is_bound(manager.panels, Panel.width)
    assert not is_bound(manager.left, Panel.width)
    assert is_bound(shell.desktop, Panel.visible)
    assert not is_bound(manager, Panel.width)
    assert (manager.left.width, manager.right.x) == (50, 50)
    assert (shell.console.y, shell.console.height) == (1, 27)
    assert (shell.keybar.y, shell.desktop.height) == (29, 27)
    assert shell.command_line.y == 28


def test_the_file_manager_opens_zoomed_on_the_desktop():
    shell = screen()
    manager = shell.manager
    assert manager.parent is shell.desktop
    assert shell.desktop.active_window is manager
    assert manager.zoomed
    assert (manager.x, manager.y, manager.width, manager.height) == (0, 0, 80, 21)


def test_a_panel_s_path_is_seeded_rather_than_bound(tree):
    """The one rule converting this screen turned up.

    A markup property line compiles to a binding, and navkit refuses a plain
    assignment over a live binding -- so binding ``path`` would have made
    ``enter()`` an error rather than a move.  A property a widget *navigates*
    takes a starting value from its parent and cannot be bound to one, which
    is why the document declares nothing about these three.
    """
    manager = screen(tree, tree).manager
    assert not is_bound(manager.left, Panel.path)
    settle()
    assert manager.left.path == tree
    manager.left.cursor = next(
        i for i, e in enumerate(manager.left.items) if e.name == "alpha"
    )
    manager.left.enter()          # would raise if `path' were bound
    assert manager.left.path == tree / "alpha"


def test_the_panel_title_and_footer_follow_the_width(panel, tree):
    wide = panel.title_text()
    panel.width = 12
    assert panel.title_text() != wide
    assert len(panel.title_text()) <= panel.width


def test_the_left_panel_starts_active():
    """And "active" is now "holds the keyboard", not a flag of its own.

    Opening the window on the desktop is what puts it there, and it has to:
    the panel keys reach a panel along the focus path, and ``Panel:focused``
    is what paints the cursor row.
    """
    manager = screen().manager
    assert manager.left.focused
    assert manager.active_panel is manager.left
    manager.switch_panel()
    assert manager.right.focused
    assert manager.active_panel is manager.right


def test_panel_renders_its_frame_and_contents(panel):
    panel.focus()
    buffer = ScreenBuffer(40, 20)
    panel.render(buffer)
    top = "".join(buffer.get(x, 0)[0] for x in range(40))
    first = "".join(buffer.get(x, 1)[0] for x in range(40))
    assert top.startswith("╔")  # the active panel wears a double frame
    assert str(panel.path)[-10:] in top or "..." in top
    assert ".." in first


def test_inactive_panel_uses_a_single_frame(panel):
    panel.application.focused = None
    buffer = ScreenBuffer(40, 20)
    panel.render(buffer)
    assert "".join(buffer.get(x, 0)[0] for x in range(40)).startswith("┌")


def test_keys_drive_the_active_panel(tree):
    app = navigator(tree)
    run_app(app, [KeyEvent("down"), KeyEvent("down")])
    assert app.manager.left.selected.name == "beta"


def test_tab_switches_panels(tree):
    app = navigator(tree)
    run_app(app, [KeyEvent("tab"), KeyEvent("down")])
    assert app.manager.active_panel is app.manager.right
    assert app.manager.right.cursor == 1
    assert app.manager.left.cursor == 0


def test_tab_repaints_on_its_own(tree):
    # Tab moves the focus and nothing else, and the application did not
    # repaint for its own observables -- so the switch appeared only with the
    # next key.  Counted in frames, because the state was right all along.
    app = navigator(tree)
    painted: list[int] = []
    run_app(app, [
        lambda a: painted.append(len(a.terminal.frames)),
        KeyEvent("tab"),
        lambda a: painted.append(len(a.terminal.frames)),
    ])
    assert painted[1] == painted[0] + 1


def test_enter_descends_in_the_active_panel(tree):
    app = navigator(tree)
    run_app(app, [KeyEvent("down"), KeyEvent("enter")])
    assert app.manager.left.path == tree / "alpha"


def test_f10_is_the_menu_and_holds_the_keys_after_it(tree):
    # DOS Navigator's F10 is cmMenu, not Quit: it highlights the first entry
    # on the bar, and the keys after it are the menu's.
    app = navigator(tree)
    seen = []
    run_app(app, [KeyEvent("f10"), KeyEvent("down"),
                  lambda a: seen.append((a.shell.menu.current, a.is_running))])
    assert seen == [(0, True)]
    assert app.manager.left.cursor == 0


def test_unhandled_keys_are_ignored(tree):
    app = navigator(tree)
    run_app(app, [KeyEvent("z", "z")])
    assert app.is_running is False  # exited by the driver, not by the key


def test_clicking_a_row_moves_the_cursor(tree):
    app = navigator(tree)
    run_app(app, [MouseClickEvent(x=5, y=3, button="left", action="press")])
    # Screen row 3 is the second listing line of the left panel: "alpha".
    assert app.manager.left.selected.name == "alpha"


def test_clicking_the_other_panel_activates_it(tree):
    app = navigator(tree)
    run_app(app, [MouseClickEvent(x=60, y=3, button="left", action="press")])
    assert app.manager.active_panel is app.manager.right


# The original entered a directory on a double-click, and until navkit grew
# one the mouse could not enter a directory at all.  Row 3 of the left panel
# is "alpha", which is a directory.

DOUBLE = MouseClickEvent(x=5, y=3, button="left", action="press")


def test_double_clicking_a_directory_row_enters_it(tree):
    app = navigator(tree)
    run_app(app, [DOUBLE, DOUBLE])
    assert app.manager.left.path.name == "alpha"


def test_double_clicking_dotdot_goes_up_and_puts_the_cursor_back(tree):
    """``..`` is an entry like any other, so ``enter()`` needed nothing added
    for it -- and the cursor lands on the directory just left, which is what
    ``_return_to`` is for."""
    app = navigator(tree / "alpha")
    # Screen row 2 is the first listing line, which is always "..".
    up = MouseClickEvent(x=5, y=2, button="left", action="press")
    run_app(app, [up, up])

    assert app.manager.left.path == tree
    assert app.manager.left.selected.name == "alpha"


def test_the_panel_under_the_pointer_is_the_one_that_opens(tree):
    """The handler is the panel's, so routing by position picks which one
    without anything having to ask."""
    app = navigator(tree)
    click = MouseClickEvent(x=60, y=3, button="left", action="press")
    run_app(app, [click, click])

    assert app.manager.right.path.name == "alpha"
    assert app.manager.left.path == tree


def test_entering_by_mouse_is_the_panel_s_own_handler(tree):
    """Not the application's.  An application hook runs before the widgets and
    would keep the gesture from every panel and dialog there will ever be; this
    one needs nothing but the panel it lands on."""
    assert hasattr(Panel, "on_double_click")
    assert not hasattr(Navigator, "on_double_click")


def test_one_click_only_moves_the_cursor(tree):
    """The press is delivered either way -- the double-click is *additional*
    -- which is what lets on_double_click be three lines that only enter."""
    app = navigator(tree)
    run_app(app, [DOUBLE])
    assert app.manager.left.selected.name == "alpha"
    assert app.manager.left.path == tree


def test_two_clicks_on_different_rows_are_not_a_double_click(tree):
    app = navigator(tree)
    run_app(app, [DOUBLE, MouseClickEvent(x=5, y=4, button="left", action="press")])
    assert app.manager.left.path == tree


def test_a_slow_pair_is_not_a_double_click(tree):
    """The window is shrunk rather than the test sleeping 0.4s: run_app leaves
    0.02s between actions, which is twenty times too slow for this one."""
    app = navigator(tree, double_click=0.001)
    run_app(app, [DOUBLE, DOUBLE])
    assert app.manager.left.path == tree


def test_double_clicking_a_file_row_does_nothing(tree):
    """`enter()' no-ops on anything but a directory, so the guard in the hook
    is about rows that exist rather than about what is on them."""
    app = navigator(tree)
    one_txt = MouseClickEvent(x=5, y=5, button="left", action="press")
    run_app(app, [one_txt, one_txt])
    assert app.manager.left.path == tree
    assert app.manager.left.selected.name == "one.txt"


def test_the_wheel_never_enters_anything(tree):
    """A detent arrives as a press and is not one -- two notches in a cell is
    the normal way to use a wheel."""
    app = navigator(tree)
    wheel = MouseClickEvent(x=5, y=3, button="wheel_down", action="press")
    run_app(app, [wheel, wheel])
    assert app.manager.left.path == tree


def test_the_wheel_ends_a_run_of_clicks(tree):
    app = navigator(tree)
    wheel = MouseClickEvent(x=5, y=3, button="wheel_up", action="press")
    run_app(app, [DOUBLE, wheel, DOUBLE])
    assert app.manager.left.path == tree


def test_the_wheel_scrolls_the_panel_under_the_pointer(tmp_path):
    for index in range(30):
        (tmp_path / f"file{index:02d}").write_text("")
    app = navigator(tmp_path)
    run_app(app, [MouseClickEvent(x=5, y=5, button="wheel_down", action="press")])
    assert app.manager.left.cursor == 3

# -- show modes (Ctrl+Y) -------------------------------------------------------


def text_at(buffer: ScreenBuffer, y: int) -> str:
    return "".join(buffer.get(x, y)[0] for x in range(buffer.width))


def many_files(path: Path, count: int, width: int = 6) -> Path:
    for index in range(count):
        (path / f"f{index:0{width - 1}d}").write_text("")
    return path


def test_ctrl_y_cycles_the_show_modes(panel):
    assert panel.view_mode == "simple" and panel.header == 0
    panel.cycle_view_mode()
    assert panel.view_mode == "detailed" and panel.header == 1
    panel.cycle_view_mode()
    assert panel.view_mode == "list" and panel.header == 1
    panel.cycle_view_mode()
    assert panel.view_mode == "simple" and panel.header == 0


def test_a_dir_entry_carries_permissions_and_a_date(panel, tree):
    (tree / "one.txt").chmod(0o640)
    stamp = datetime(2021, 3, 4, 5, 6).timestamp()
    import os
    os.utime(tree / "one.txt", (stamp, stamp))
    panel.reload()
    settle()
    entry = next(e for e in panel.items if e.name == "one.txt")
    assert entry.display_attributes == "rw-r-----"
    assert entry.display_date == "04-03-21 05:06"


def test_the_detailed_mode_draws_its_columns(tree):
    panel = Panel(tree, width=60, height=10)
    panel.stylesheet = default_scheme()
    panel = mounted(panel, size=(60, 10))
    panel.cycle_view_mode()
    settle()
    assert [key for key, _, _ in panel.detail_columns] == ["name", "size", "attributes", "owner", "date"]
    buffer = ScreenBuffer(60, 10)
    panel.render(buffer)
    heading = text_at(buffer, 1)
    for title in ("Name", "Size", "Attr", "Owner", "Date"):
        assert title in heading
    owner = next(e for e in panel.items if e.name == "two.txt").display_owner
    row = next(text_at(buffer, y) for y in range(2, 9) if "two.txt" in text_at(buffer, y))
    assert "2K" in row and "rw" in row and owner[:5] in row and row[1:-1].count("│") == 4
    # The name column takes what the others leave.
    owner_width = panel.detail_columns[3][2]
    _, x, width = panel.detail_columns[0]
    assert (x, width) == (1, 58 - (8 + 9 + owner_width + 14 + 4))


def test_the_owner_column_is_user_colon_group(panel, tree):
    import grp, os, pwd
    entry = next(e for e in panel.items if e.name == "one.txt")
    user = pwd.getpwuid(os.getuid()).pw_name
    group = grp.getgrgid(os.getgid()).gr_name
    assert entry.display_owner == f"{user}:{group}"
    # An id with no name is shown as its number; an unread entry as nothing.
    assert DirEntry("x", False, 0, uid=2_000_000_001, gid=2_000_000_002).display_owner == "2000000001:2000000002"
    assert DirEntry("x", False, 0).display_owner == ""


def test_the_owner_column_is_as_wide_as_the_longest_owner(tree):
    panel = mounted(Panel(tree, width=80, height=10), size=(80, 10))
    panel.cycle_view_mode()
    settle()
    longest = max(len(e.display_owner) for e in panel.items)
    width = dict((key, w) for key, _, w in panel.detail_columns)["owner"]
    assert width == max(len("Owner"), min(longest, Panel.MAX_OWNER_WIDTH))


def test_a_narrow_detailed_panel_gives_up_owner_and_attributes_first(panel):
    panel.cycle_view_mode()
    settle()
    # 40 wide is half an 80-column screen: name, size and date still fit.
    assert [key for key, _, _ in panel.detail_columns] == ["name", "size", "date"]
    assert panel.detail_columns[0][2] >= Panel.MIN_NAME_WIDTH


def test_the_list_mode_lays_names_out_in_columns(tmp_path):
    many_files(tmp_path, 30)
    panel = Panel(tmp_path, width=40, height=10)
    panel.stylesheet = default_scheme()
    panel = mounted(panel, size=(40, 10))
    panel.cycle_view_mode()
    panel.cycle_view_mode()
    settle()
    rows = panel.rows
    assert rows == 7  # 10, less the frame and the heading
    columns = panel.list_columns
    # ".." and 30 names, seven to a column; each as wide as its longest name.
    assert [first for first, _, _ in columns][:3] == [0, 7, 14]
    assert columns[1][2] == panel.gutter + 6
    buffer = ScreenBuffer(40, 10)
    panel.render(buffer)
    assert "f00006" in text_at(buffer, 2)  # the second column's first row
    assert "Name" in text_at(buffer, 1)


def test_the_list_mode_draws_no_divider_after_the_last_column(tmp_path):
    many_files(tmp_path, 10)
    panel = Panel(tmp_path, width=60, height=10)
    panel.stylesheet = default_scheme()
    panel = mounted(panel, size=(60, 10))
    panel.cycle_view_mode()
    panel.cycle_view_mode()
    settle()
    columns = panel.list_columns
    assert len(columns) == 2
    buffer = ScreenBuffer(60, 10)
    panel.render(buffer)
    glyph = panel.divider_glyph
    between = columns[0][1] + columns[0][2]
    after = columns[-1][1] + columns[-1][2]
    assert after < panel.inset + panel.inner_width
    for y in range(panel.inset, panel.inset + panel.header + panel.rows):
        assert text_at(buffer, y)[between] == glyph
        assert text_at(buffer, y)[after] != glyph


def test_left_and_right_move_a_column_in_the_list_mode(tmp_path):
    many_files(tmp_path, 30)
    panel = mounted(Panel(tmp_path, width=40, height=10), size=(40, 10))
    panel.cycle_view_mode()
    panel.cycle_view_mode()
    settle()
    panel.focus()
    assert awaited(panel.on_key(KeyEvent("right")))
    settle()
    assert panel.cursor == panel.rows
    assert awaited(panel.on_key(KeyEvent("left")))
    settle()
    assert panel.cursor == 0
    # Outside the list mode they are declined, and reach the command line.
    panel.cycle_view_mode()
    assert not awaited(panel.on_key(KeyEvent("right")))


def test_the_list_mode_scrolls_a_whole_column(tmp_path):
    many_files(tmp_path, 100)
    panel = mounted(Panel(tmp_path, width=40, height=10), size=(40, 10))
    panel.cycle_view_mode()
    panel.cycle_view_mode()
    settle()
    panel.cursor = 80
    settle()
    rows = panel.rows
    assert panel.scroll % rows == 0
    right = panel.inset + panel.inner_width
    assert any(
        first <= 80 < first + rows and x + width <= right
        for first, x, width in panel.list_columns
    )
    panel.cursor = 3
    settle()
    assert panel.scroll == 0


def test_a_click_in_the_list_mode_picks_the_column(tmp_path):
    many_files(tmp_path, 30)
    panel = mounted(Panel(tmp_path, width=40, height=10), size=(40, 10))
    panel.cycle_view_mode()
    panel.cycle_view_mode()
    settle()
    first, x, _ = panel.list_columns[1]
    assert panel.index_at(x, panel.inset + panel.header + 2) == first + 2
    assert panel.index_at(x - 1, panel.inset + panel.header) is None  # the divider


def painted_panel(panel) -> ScreenBuffer:
    buffer = ScreenBuffer(panel.width, panel.height)
    panel.render(buffer)
    return buffer


def divider_columns(panel) -> list[int]:
    spans = panel._column_spans()
    return [x + width for _, x, width in spans[:-1]]


def test_a_divider_meets_the_frame_in_a_tee_matching_the_frame(tree):
    app = navigator(tree, size=(200, 24))  # wide enough that the path leaves a divider clear
    run_app(app, [])
    for panel in (app.manager.left, app.manager.right):
        panel.cycle_view_mode()
    settle()
    # The active panel's frame is double, the other's single.
    for panel, tees in ((app.manager.left, "╤╧"), (app.manager.right, "┬┴")):
        buffer = painted_panel(panel)
        columns = divider_columns(panel)
        assert columns
        for x in columns:
            # The top edge carries the path, which may stand on the cell.
            assert buffer.get(x, 0)[0] in (tees[0], *panel.title_text())
            assert buffer.get(x, panel.height - 1)[0] == tees[1]
        assert any(buffer.get(x, 0)[0] == tees[0] for x in columns)


def test_the_list_mode_has_no_tee_after_its_last_column(tmp_path):
    many_files(tmp_path, 10)
    panel = Panel(tmp_path, width=60, height=10)
    panel.stylesheet = default_scheme()
    panel = mounted(panel, size=(60, 10))
    panel.cycle_view_mode()
    panel.cycle_view_mode()
    settle()
    buffer = painted_panel(panel)
    columns = panel.list_columns
    between = columns[0][1] + columns[0][2]
    after = columns[-1][1] + columns[-1][2]
    assert buffer.get(between, panel.height - 1)[0] == "┴"
    assert buffer.get(after, panel.height - 1)[0] == "─"


def test_a_tee_leaves_the_footer_standing_on_its_cell(tmp_path):
    name = "a_long_name_crossing_the_divider"
    (tmp_path / name).write_text("")
    panel = Panel(tmp_path, width=40, height=10)
    panel.stylesheet = default_scheme()
    panel = mounted(panel, size=(40, 10))
    panel.cycle_view_mode()
    settle()
    panel.cursor = 1
    settle()
    buffer = painted_panel(panel)
    footer = row_of(buffer, panel.height - 1)
    assert name in footer
    assert "┴" not in footer and "╧" not in footer


def test_an_ascii_terminal_joins_the_divider_with_a_plus(tree):
    app = navigator_with(tree, GLYPHS_ASCII)
    run_app(app, [])
    panel = app.manager.right
    panel.cycle_view_mode()
    settle()
    buffer = painted_panel(panel)
    x = divider_columns(panel)[0]
    assert buffer.get(x, panel.height - 1)[0] == "+"


def test_fit_text_ends_a_name_cut_short_in_an_ellipsis():
    assert fit_text("short", 10) == "short"
    assert fit_text("exactly10!", 10) == "exactly10!"
    assert fit_text("a_rather_long_name.txt", 10) == "a_rathe..."
    assert fit_text("abcdef", 3) == "abc"  # no room for the marker and a letter
    # Measured in cells: a wide character that would straddle the cut goes.
    assert fit_text("日本語のファイル", 8) == "日本..."


def test_skip_cells_drops_the_start_of_a_name():
    assert skip_cells("abcdef", 0) == "abcdef"
    assert skip_cells("abcdef", 2) == "cdef"
    assert skip_cells("日本語", 2) == "本語"
    assert skip_cells("日本語", 1) == " 本語"  # half a wide character is a blank
    assert skip_cells("ab", 5) == ""


def test_window_text_marks_both_ends_of_a_scrolled_name():
    assert window_text("abcdefghijkl", 0, 8) == "abcde..."
    assert window_text("abcdefghijkl", 2, 8) == "...fg..."
    # Scrolled to its end, only the leading marker: cells 4 to 12.
    assert window_text("abcdefghijkl", 4, 8) == "...hijkl"
    # A short name scrolled out of the window still shows it is there.
    assert window_text("ab", 4, 8) == "..."
    assert window_text("abcdef", 1, 3) == "bcd"  # too narrow for a marker


LONG_NAME = "a_file_whose_name_is_much_too_long_for_its_column.txt"


@pytest.mark.parametrize("modes", [0, 1, 2])
def test_a_name_too_long_for_its_column_ends_in_an_ellipsis(tmp_path, modes):
    (tmp_path / LONG_NAME).write_text("")
    panel = Panel(tmp_path, width=40, height=10)
    panel.stylesheet = default_scheme()
    panel = mounted(panel, size=(40, 10))
    for _ in range(modes):
        panel.cycle_view_mode()
    settle()
    buffer = ScreenBuffer(40, 10)
    panel.render(buffer)
    row = next(text_at(buffer, y) for y in range(10) if "a_file" in text_at(buffer, y))
    assert "..." in row
    assert ".txt" not in row


def test_left_and_right_scroll_the_names_and_stop_at_the_ends(tmp_path, quiet_console):
    (tmp_path / LONG_NAME).write_text("")
    app = navigator(tmp_path, size=(80, 24))
    run_app(app, [KeyEvent("right")] * 200)
    panel = app.manager.left
    assert panel.max_name_scroll > 0
    assert panel.name_offset == panel.max_name_scroll
    buffer = ScreenBuffer(panel.width, panel.height)
    panel.render(buffer)
    # Scrolled to the end, the longest name's tail shows after a marker.
    row = next(text_at(buffer, y) for y in range(panel.height) if "column.txt" in text_at(buffer, y))
    assert row.count("...") == 1
    assert row.index("...") < row.index("column.txt")
    app = navigator(tmp_path)
    run_app(app, [KeyEvent("right")] * 3 + [KeyEvent("left")])
    assert app.manager.left.name_offset == 2


def test_left_and_right_move_the_caret_while_the_line_has_text(tmp_path, quiet_console):
    (tmp_path / LONG_NAME).write_text("")
    app = navigator(tmp_path)
    run_app(app, [*keys("ls"), KeyEvent("left")])
    assert app.manager.left.name_offset == 0
    assert app.shell.command_line.cursor == 1


def test_the_name_scroll_resets_on_a_change_of_mode(tmp_path):
    (tmp_path / LONG_NAME).write_text("")
    panel = mounted(Panel(tmp_path, width=40, height=10), size=(40, 10))
    settle()
    panel.scroll_names(5)
    assert panel.name_offset == 5
    panel.cycle_view_mode()
    assert panel.name_offset == 0


def test_ctrl_y_changes_only_the_active_panel(tree):
    app = navigator(tree)
    run_app(app, [KeyEvent("y", ctrl=True)])
    assert app.manager.left.view_mode == "detailed"
    assert app.manager.right.view_mode == "simple"


def test_ctrl_h_hides_and_shows_the_dot_files(tree):
    (tree / ".hidden").write_text("h")
    (tree / ".config").mkdir()
    panel = mounted(Panel(tree, width=40, height=20), size=(40, 20))
    panel.stylesheet = default_scheme()
    assert {".hidden", ".config"} <= set(names(panel))
    panel.toggle_hidden()
    settle()
    assert not panel.show_hidden
    assert names(panel)[0] == ".."
    assert not any(name.startswith(".") and name != ".." for name in names(panel))
    panel.toggle_hidden()
    settle()
    assert {".hidden", ".config"} <= set(names(panel))


def test_ctrl_h_keeps_the_cursor_and_drops_hidden_tags(tree):
    (tree / ".hidden").write_text("h")
    panel = mounted(Panel(tree, width=40, height=20), size=(40, 20))
    panel.stylesheet = default_scheme()
    panel.cursor = names(panel).index(".hidden")
    panel.toggle_mark()
    panel.cursor = names(panel).index("two.txt")
    settle()
    assert panel.marked == {".hidden"}
    panel.toggle_hidden()
    settle()
    assert panel.selected.name == "two.txt"
    assert panel.marked == frozenset()


def test_ctrl_h_changes_only_the_active_panel(tree):
    (tree / ".hidden").write_text("h")
    app = navigator(tree)
    run_app(app, [KeyEvent("h", ctrl=True)])
    assert ".hidden" not in names(app.manager.left)
    assert ".hidden" in names(app.manager.right)


def keys(text: str) -> list[KeyEvent]:
    return [KeyEvent(c.lower(), c, shift=c.isupper()) for c in text]


def test_ctrl_s_jumps_to_the_first_name_the_typing_begins(tree):
    app = navigator(tree)
    run_app(app, [KeyEvent("s", ctrl=True), *keys("T")])
    panel = app.manager.left
    assert panel.selected.name == "two.txt"
    assert panel.quick_search == "T"
    # Typed into the search, not onto the command line.
    assert app.shell.command_line.value == ""


def test_a_character_that_names_nothing_is_refused(tree):
    app = navigator(tree)
    run_app(app, [KeyEvent("s", ctrl=True), *keys("bx")])
    panel = app.manager.left
    assert panel.quick_search == "b"
    assert panel.selected.name == "beta"


def test_the_search_takes_wildcards_and_backspace(tree):
    app = navigator(tree)
    seen = []
    run_app(app, [
        KeyEvent("s", ctrl=True), *keys("*.t"),
        lambda a: seen.append(a.manager.left.selected.name),
        KeyEvent("backspace"), KeyEvent("backspace"),
        lambda a: seen.append(a.manager.left.quick_search),
        *keys("?w"),
    ])
    assert seen == ["one.txt", "*"]
    assert app.manager.left.selected.name == "two.txt"


def test_ctrl_s_again_finds_the_next_match_and_wraps(tree):
    app = navigator(tree)
    seen = []
    step = lambda a: seen.append(a.manager.left.selected.name)
    run_app(app, [KeyEvent("s", ctrl=True), *keys("*txt"), step,
                  KeyEvent("s", ctrl=True), step, KeyEvent("s", ctrl=True), step])
    assert seen == ["one.txt", "two.txt", "one.txt"]


def test_the_search_never_finds_the_parent_entry(tree):
    app = navigator(tree)
    run_app(app, [KeyEvent("s", ctrl=True), *keys(".")])
    assert app.manager.left.quick_search == ""
    assert app.manager.left.cursor == 0


def test_enter_ends_the_search_and_stays_without_running_the_line(tree, quiet_console):
    app = navigator(tree)
    run_app(app, [*keys("ls"), KeyEvent("s", ctrl=True), *keys("be"), KeyEvent("enter")])
    panel = app.manager.left
    assert panel.quick_search is None
    assert panel.selected.name == "beta"
    assert panel.path == tree
    assert app.shell.command_line.value == "ls"


def test_another_key_ends_the_search_and_does_its_job(tree):
    app = navigator(tree)
    run_app(app, [KeyEvent("s", ctrl=True), *keys("a"), KeyEvent("down")])
    panel = app.manager.left
    assert panel.quick_search is None
    assert panel.selected.name == "beta"


def test_tab_ends_the_search_and_switches_panel(tree):
    app = navigator(tree)
    run_app(app, [KeyEvent("s", ctrl=True), *keys("o"), KeyEvent("tab")])
    assert app.manager.left.quick_search is None
    assert app.manager.active_panel is app.manager.right


def test_the_search_shows_on_the_footer_with_the_caret_after_it(tree):
    app = navigator(tree)
    seen = []

    def look(a):
        panel = a.manager.left
        footer = panel.footer_text()
        seen.append((footer, panel.cursor_position(), panel.label_x(footer)))

    run_app(app, [KeyEvent("s", ctrl=True), *keys("tw"), look])
    footer, caret, x = seen[0]
    assert footer == " Search: tw "
    assert caret == (x + len(" Search: tw"), app.manager.left.height - 1)


def test_the_panel_menu_carries_ctrl_h(tree):
    from navml.widgets.menu.menu_box.menu_box import key_caption

    app = navigator(tree)
    seen = []

    def look(a):
        item = _entry(a.shell.menu, "Panel", "Show/hide hidden files")
        seen.append((key_caption(item, a, a.manager.left),
                     a.command_enabled(item.command, a.manager.left)))

    run_app(app, [look])
    assert seen == [("Ctrl-H", True)]


def test_the_menu_ticks_ctrl_h_while_the_active_panel_shows_dot_files(tree):
    app = navigator(tree)
    seen = []

    def look(a):
        item = _entry(a.shell.menu, "Panel", "Show/hide hidden files")
        seen.append(a.command_checked(item.command, a.manager.left))

    run_app(app, [look, KeyEvent("h", ctrl=True), look, KeyEvent("tab"), look])
    assert seen == [True, False, True]


def test_the_panel_menu_carries_ctrl_y_and_ctrl_s(tree):
    from navml.widgets.menu.menu_box.menu_box import key_caption

    app = navigator(tree)
    seen = []

    def look(a):
        for caption in ("View mode", "Quick search"):
            item = _entry(a.shell.menu, "Panel", caption)
            seen.append((key_caption(item, a, a.manager.left),
                         a.command_enabled(item.command, a.manager.left)))

    run_app(app, [look])
    assert seen == [("Ctrl-Y", True), ("Ctrl-S", True)]


def test_panel_view_mode_from_the_menu_cycles_the_active_panel(tree):
    app = navigator(tree)
    run_app(app, [KeyEvent("f10"), *keys("pw")])
    assert app.manager.left.view_mode == "detailed"
    assert app.manager.right.view_mode == "simple"


def test_panel_quick_search_from_the_menu_keeps_the_keys_after_it(tree):
    """The bar closes before the command runs, so the panel has the keyboard
    back when its search starts, and the search survives to take what follows."""
    app = navigator(tree)
    seen = []
    run_app(app, [KeyEvent("f10"), *keys("pe"), *keys("tw"),
                  lambda a: seen.append(a.manager.left.quick_search)])
    assert seen == ["tw"]


def test_the_scheme_drives_the_panel_rather_than_decorating_it(panel):
    """Swapping the sheet must change what the panel paints.

    The migration is only real if the render methods read the cascade.  A
    theme that redefines one variable should reach the frame colour without
    touching a single rule.
    """
    from navkit.style import RED

    # $panel-fg, out of themes/default.nss: entry 85 of DEFAULT.PAL is $87,
    # light gray on dark gray, lifted to the viewer's #D8D8D8 by palconv's
    # DEPARTURES.
    assert panel.style.fg == (0xD8, 0xD8, 0xD8)
    # A theme is a further sheet loaded after the others, redefining a variable
    # the rules already use -- no rule here is repeated or overridden.
    panel.stylesheet = load_scheme("default", ("theme.nss", "$panel-fg: red;"))
    assert panel.style.fg == RED

    buffer = ScreenBuffer(40, 20)
    panel.render(buffer)
    assert buffer.get(0, 0)[1].fg == RED  # the frame really is painted in it


def test_the_border_comes_from_the_sheet_not_from_focus(panel):
    """Holding the keyboard picks the frame only because a rule says so."""
    panel.focus()
    assert panel.border == "double"
    panel.stylesheet = load_scheme(
        "default", ("theme.nss", "Panel:focused { border: single }")
    )
    assert panel.border == "single"
    buffer = ScreenBuffer(40, 20)
    panel.render(buffer)
    assert "".join(buffer.get(x, 0)[0] for x in range(40)).startswith("┌")


# The themes are generated from DOS Navigator's `.PAL' palettes by
# tools/palconv.py, and the sheet they complete defines no variable of its own.
# So the two halves have to be checked against each other: renaming a variable
# in navigator.nss without regenerating leaves a theme that no longer parses,
# and the failure would otherwise surface only when someone asked for it.


def test_every_theme_completes_the_scheme(tree):
    """Each theme must define every variable the rules read, and paint."""
    assert "default" in theme_names()
    for theme in theme_names():
        shell = Shell(tree, tree, load_scheme(theme))
        manager = shell.manager
        buffer = ScreenBuffer(80, 24)
        shell.layout(80, 24)
        manager.layout(80, 22)
        shell.render_tree(buffer)  # raises if a variable went undefined
        assert manager.left.style.fg is not None
        assert manager.left.style.bg is not None


def test_the_themes_all_carry_the_same_palette():
    """Every theme must define the same variables, being the same 144 entries.

    They are generated together from DOS Navigator's Colors dialog, so a theme
    with a different set is one that was regenerated against a different table
    -- or not regenerated at all.  Compared against each other rather than
    against a count, so adding an entry to the tool needs no edit here.
    """
    from navkit.stylesheet import read

    sets = {theme: set(read(THEMES / f"{theme}.nss").variables)
            for theme in theme_names()}
    # The palettes that reprogram the VGA registers carry sixteen more names.
    core = {theme: {v for v in names if not v.startswith("dn-")}
            for theme, names in sets.items()}
    reference = core["default"]
    assert len(reference) >= 2 * 144
    for theme, names in core.items():
        assert names == reference, f"{theme} defines a different palette"
    for theme, names in sets.items():
        registers = names - core[theme]
        assert len(registers) in (0, 16), f"{theme} has {len(registers)} registers"


def test_a_theme_only_ever_sets_colours():
    """A palette may not smuggle in a property.

    A DOS attribute byte is four bits of foreground and four of background and
    carries nothing else -- no bold, no underline, and no border. So a `.PAL'
    has no way to express one, and a theme that defined anything but an `-fg'
    or a `-bg' would be palconv inventing rather than transcribing.

    Which is why this asks the theme files rather than the resolved styles: a
    rule in navigator.nss may well set `bold' -- one does, on directory rows,
    deliberately -- and that is the sheet's business, not the palette's.
    """
    from navkit.stylesheet import read

    for theme in theme_names():
        for name in read(THEMES / f"{theme}.nss").variables:
            # The sixteen VGA registers a custom-DAC palette pins are whole
            # colours rather than a slot's fore- or background.
            if name.startswith("dn-"):
                continue
            assert name.rsplit("-", 1)[-1] in ("fg", "bg"), f"{theme}: ${name}"


# -- where the widgets live --------------------------------------------------


def _in_a_fresh_process(script: str) -> list[str]:
    return subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    ).stdout.split()


def test_a_scheme_parses_without_the_caller_importing_anything_first():
    """``load_scheme`` imports the widgets whose properties the sheet names.

    A sheet is checked against the properties widgets declare, and a widget
    declares them by its class body running -- so ``navigator.nss``'s
    ``icons: auto`` is an unknown property until ``Panel`` has been imported.
    While every screen lived in one module that was a rule about where to put
    the parse; now it is a rule about what to import before it, and the import
    is inside ``load_scheme`` so that no caller has to know.
    """
    assert _in_a_fresh_process(
        "from navigator.scheme import default_scheme\n"
        "print(len(default_scheme().rules))\n"
    )[0].isdigit()


def test_one_widget_does_not_import_the_others():
    """The lazy re-export, for the same reason ``navml.widgets`` has one.

    Generating a component imports the classes its document names, so a
    package that re-exported eagerly would make importing any one widget
    import every widget -- and a cold build of ``manager.nml`` could then
    generate nothing until everything already had been.
    """
    loaded = _in_a_fresh_process(
        "import importlib, sys\n"
        "importlib.import_module('navigator.widgets.shell.keybar')\n"
        "print(' '.join(sorted(m for m in sys.modules "
        "if m.startswith('navigator.widgets.'))))\n"
    )
    # The group's own package comes in too; it is a docstring and imports
    # none of its members, so `shell.shell' and the console stay out.
    assert loaded == [
        "navigator.widgets.shell",
        "navigator.widgets.shell.keybar",
        "navigator.widgets.shell.keybar.keybar",
    ]


def test_the_desktop_still_pulls_in_the_screens_it_places():
    """And its own generated half, which is what places them."""
    loaded = _in_a_fresh_process(
        "import importlib, sys\n"
        "importlib.import_module('navigator.widgets.shell.shell')\n"
        "print(' '.join(sorted(m for m in sys.modules "
        "if m.startswith('navigator.widgets.'))))\n"
    )
    assert loaded == [
        "navigator.widgets.file_ops",
        "navigator.widgets.file_ops.mkdir_dialog",          # F7, imported by the desktop",
        "navigator.widgets.file_ops.mkdir_dialog.mkdir_dialog",
        "navigator.widgets.file_ops.mkdir_dialog.mkdir_dialog_nml",
        "navigator.widgets.manager",
        "navigator.widgets.manager.commands",               # names only, no widget
        "navigator.widgets.manager.manager",
        "navigator.widgets.manager.manager.manager",
        "navigator.widgets.manager.manager.manager_nml",
        "navigator.widgets.manager.panel",
        "navigator.widgets.manager.panel.panel",
        "navigator.widgets.shell",
        "navigator.widgets.shell.clock",
        "navigator.widgets.shell.clock.clock",
        "navigator.widgets.shell.clock.clock_nml",
        "navigator.widgets.shell.command_line",
        "navigator.widgets.shell.command_line.command_line",
        "navigator.widgets.shell.commands",
        "navigator.widgets.shell.console",
        "navigator.widgets.shell.console.console",
        "navigator.widgets.shell.keybar",
        "navigator.widgets.shell.keybar.keybar",
        "navigator.widgets.shell.main_menu",
        "navigator.widgets.shell.main_menu.main_menu",
        "navigator.widgets.shell.main_menu.main_menu_nml",
        "navigator.widgets.shell.shell",
        "navigator.widgets.shell.shell.shell",
        "navigator.widgets.shell.shell.shell_nml",
        "navigator.widgets.tree",
        "navigator.widgets.tree.directory_tree",   # Ctrl+T, placed by the manager",
        "navigator.widgets.tree.directory_tree.directory_tree",
        "navigator.widgets.viewer",
        "navigator.widgets.viewer.file_viewer",
        "navigator.widgets.viewer.file_viewer.file_viewer",
        "navigator.widgets.viewer.quick_viewer",
        "navigator.widgets.viewer.quick_viewer.quick_viewer",
        "navigator.widgets.viewer.quick_viewer.quick_viewer_nml",
    ]


# -- the console and Ctrl+O -------------------------------------------------


@pytest.fixture
def quiet_console(monkeypatch):
    """Stop the console forking a shell.

    Most of what Ctrl+O does has nothing to do with the child: it is which
    widgets paint, and that is worth testing without a process in the way.
    ``test_the_console_runs_a_real_child`` covers the other half.  A command
    run with no shell finishes at once, with 127, as a failed start does.
    """
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)


def running(app) -> None:
    """Pretend a command the command line sent is running on the console."""
    app.shell.console.subshell.busy = True


def desktop(app, size=(80, 24)) -> ScreenBuffer:
    """Paint the whole screen and hand back the buffer."""
    buffer = ScreenBuffer(*size)
    app.shell.layout(*size)
    settle()
    app.shell.render_tree(buffer)
    return buffer


def row_of(buffer: ScreenBuffer, y: int) -> str:
    return "".join(buffer.get(x, y)[0] or " " for x in range(buffer.width))


def test_ctrl_o_shows_the_console_in_place_of_the_panels(tree, quiet_console):
    app = navigator(tree)
    run_app(app, [KeyEvent("o", ctrl=True)])
    shell = app.shell
    assert shell.console_visible is True
    # One flag, one widget: the desktop goes, and every window with it.  The
    # console was showing all along, behind the windows.
    assert shell.console.visible is True
    assert shell.desktop.visible is False
    assert app.focused is shell.console


def test_ctrl_o_toggles_back(tree, quiet_console):
    app = navigator(tree)
    run_app(app, [KeyEvent("o", ctrl=True), KeyEvent("o", ctrl=True)])
    assert app.shell.console_visible is False
    assert app.shell.desktop.visible is True


def test_the_menu_bar_and_key_bar_stay_over_the_console(tree, quiet_console):
    """The whole point of Ctrl+O, and what Midnight Commander cannot do."""
    app = navigator(tree)
    run_app(app, [KeyEvent("o", ctrl=True),
                  lambda a: a.shell.console._on_output(b"previous output")])
    buffer = desktop(app)
    assert "File" in row_of(buffer, 0)  # the menu bar, still there
    assert "Menu" in row_of(buffer, 23)  # the key bar, still there
    assert "previous output" in row_of(buffer, 1)  # and the output behind them
    # The panels really are gone rather than merely covered.
    assert "╔" not in row_of(buffer, 1)


def test_the_console_is_the_size_of_the_band_the_panels_shared(tree, quiet_console):
    app = navigator(tree)
    run_app(app, [KeyEvent("o", ctrl=True)])
    console = app.shell.console
    assert (console.width, console.height) == (80, 21)
    # And the screen behind it was resized to match, without a layout pass.
    assert (console.screen.columns, console.screen.lines) == (80, 21)


def test_keys_go_to_the_program_while_a_command_runs(tree, quiet_console):
    app = navigator(tree)
    typed: list[bytes] = []
    run_app(app, [
        KeyEvent("o", ctrl=True),
        running,
        lambda a: setattr(a.shell.console, "send",
                          lambda event: typed.append(encode_key(event)) or True),
        KeyEvent("down"),
        KeyEvent("x", "x"),
        KeyEvent("enter"),
    ])
    assert typed == [b"\x1b[B", b"x", b"\r"]
    # The panel did not also act on them, and nothing reached the line.
    assert app.manager.left.cursor == 0
    assert app.shell.command_line.value == ""


def test_typing_at_the_idle_console_reaches_the_command_line(tree, quiet_console):
    # Ctrl+O shows output; the prompt the user types at is still the line.
    app = navigator(tree)
    run_app(app, [KeyEvent("o", ctrl=True), KeyEvent("l", "l"), KeyEvent("s", "s")])
    assert app.shell.console_visible is True
    assert app.shell.command_line.value == "ls"


def test_quit_still_works_from_the_console(tree, quiet_console):
    # Alt+X is the child's while the console is over the windows, so the way
    # out is the one DOS Navigator gave: F10, File, Exit.
    app = navigator(tree)
    run_app(app, [KeyEvent("o", ctrl=True), KeyEvent("f10"),
                  KeyEvent("f", "f"), KeyEvent("x", "x")])
    assert app.is_running is False


def test_shift_pageup_scrolls_the_console_back(tree, quiet_console):
    app = navigator(tree)
    lines = b"".join(b"line%d\r\n" % n for n in range(60))
    run_app(app, [
        KeyEvent("o", ctrl=True),
        lambda a: a.shell.console._on_output(lines),
        KeyEvent("pageup", shift=True),
    ])
    assert app.shell.console.screen.scrolled_back is True


def test_the_wheel_scrolls_the_console_rather_than_a_panel(tree, quiet_console):
    app = navigator(tree)
    lines = b"".join(b"line%d\r\n" % n for n in range(60))
    run_app(app, [
        KeyEvent("o", ctrl=True),
        lambda a: a.shell.console._on_output(lines),
        MouseClickEvent(x=10, y=10, button="wheel_up", action="press"),
    ])
    assert app.shell.console.screen.scrolled_back is True
    assert app.manager.left.cursor == 0


def test_the_console_runs_a_real_child(tree, monkeypatch):
    """End to end: a command line's output really does end up behind the panels.

    Typed on the line, run by a real shell in the panel's directory, echoed
    after the prompt the shell printed, and the panels back once it is done.
    """
    monkeypatch.setenv("SHELL", "/bin/sh")
    app = navigator(tree)
    keys = [KeyEvent(c, c) for c in "echo captured"]
    # A generous settle: the driver's awaits are the only chance the loop gets
    # to read from the pty, so the test has to yield rather than sleep.
    run_app(app, [*keys, KeyEvent("enter")] + [lambda a: None] * 6,
            settle=0.3, timeout=20)
    screen = "\n".join(app.shell.console.screen.screen.display)
    assert f"{tree}>echo captured" in screen
    assert "\ncaptured" in screen
    assert app.shell.console_visible is False
    assert app.shell.command_line.value == ""


# -- glyphs: what the terminal's font can actually draw ------------------------
#
# The sheet says which character set is *wanted* and the terminal says which
# can be *shown*; a panel owes both a look.  These go through a live
# application rather than the detached ``panel`` fixture, because the tier is
# read off the terminal and a detached widget has none to read.


def navigator_with(path, glyphs, size=(80, 24)) -> Navigator:
    """A Navigator whose terminal admits to exactly *glyphs*."""
    info = replace(FULL, glyphs=glyphs)
    return Navigator(path, path, terminal=FakeTerminal(*size, info=info))


def test_an_ascii_terminal_gets_a_plus_and_minus_frame(tree):
    """The frame degrades wholesale rather than arriving as replacement boxes."""
    app = navigator_with(tree, GLYPHS_ASCII)
    run_app(app, [])
    buffer = desktop(app)
    assert row_of(buffer, 1).startswith("+")   # a corner
    assert row_of(buffer, 2).startswith("|")   # and a side
    # Nothing above US-ASCII survives anywhere on the desktop, which is the
    # whole point: one replacement box per line is worse than a plain frame.
    painted = "".join(row_of(buffer, y) for y in range(24))
    assert not any(char in painted for char in "┌┐└┘─│╔╗╚╝═║")


def test_a_unicode_terminal_still_gets_the_dos_frame(tree):
    """The default look is unchanged by any of this."""
    app = navigator_with(tree, GLYPHS_UNICODE)
    run_app(app, [])
    top = row_of(desktop(app), 1)
    assert "╔" in top  # the active panel's double frame


def test_icons_appear_only_when_the_font_can_draw_them(tree):
    """A Nerd Font glyph is a replacement box without the font, so it waits."""
    plain = navigator_with(tree, GLYPHS_UNICODE)
    run_app(plain, [])
    assert not plain.manager.left.show_icons
    assert plain.manager.left.gutter == 1

    fancy = navigator_with(tree, GLYPHS_NERD)
    run_app(fancy, [])
    assert fancy.manager.left.show_icons
    assert fancy.manager.left.gutter == 2


def test_the_icon_gutter_shifts_the_name_without_touching_the_size_column(tree):
    """Two cells go to the icon and one to the type mark without it; the size
    column is where it always was."""
    plain = navigator_with(tree, GLYPHS_UNICODE)
    run_app(plain, [])
    without = row_of(desktop(plain), 2)

    fancy = navigator_with(tree, GLYPHS_NERD)
    run_app(fancy, [])
    with_icons = row_of(desktop(fancy), 2)

    # ".." is the first entry either way, and moves right by the difference.
    assert without.index("..") + 1 == with_icons.index("..")
    # The size column is drawn from the right edge and does not move.
    assert without[-12:] == with_icons[-12:]
    # A name has that much less room, so the two agree on the total width.
    assert fancy.manager.left.name_width == plain.manager.left.name_width


def test_every_kind_of_entry_gets_midnight_commanders_type_mark(tmp_path):
    """Read through the panel's own rescan, so the link wiring is covered too."""
    import os
    import socket

    (tmp_path / "plain").write_text("x")
    (tmp_path / "run").write_text("x")
    (tmp_path / "run").chmod(0o755)
    (tmp_path / "dir").mkdir()
    (tmp_path / "to_file").symlink_to("plain")
    (tmp_path / "to_dir").symlink_to("dir")
    (tmp_path / "stale").symlink_to("nowhere")
    (tmp_path / "chr").symlink_to("/dev/null")
    os.mkfifo(tmp_path / "fifo")
    sock = socket.socket(socket.AF_UNIX)
    try:
        sock.bind(str(tmp_path / "sock"))
        panel = Panel(tmp_path, width=40, height=20)
        panel.stylesheet = default_scheme()
        panel = mounted(panel, size=(40, 20))
        marks = {entry.name: entry.type_mark for entry in panel.items}
    finally:
        sock.close()
    assert marks == {
        "..": "/", "dir": "/", "plain": " ", "run": "*", "to_file": "@", "to_dir": "~",
        "stale": "!", "chr": "@", "fifo": "|", "sock": "=",
    }


@pytest.mark.parametrize(
    "mode, expected",
    [(0o020666, "-"), (0o060660, "+"), (0o010644, "|"), (0o140755, "="), (0o100644, " "),
     (0o100744, "*"), (0o100601, "*"), (0, " ")],
)
def test_the_type_mark_reads_the_mode(mode, expected):
    assert DirEntry("x", False, 0, mode).type_mark == expected


def test_without_icons_the_gutter_holds_the_type_mark(tree):
    (tree / "run.sh").write_text("#!/bin/sh")
    (tree / "run.sh").chmod(0o755)
    app = navigator_with(tree, GLYPHS_UNICODE)
    run_app(app, [])
    buffer = desktop(app)
    entries = app.manager.left.items
    marks = [buffer.get(1, 2 + row)[0] for row in range(len(entries))]
    assert marks == [entry.type_mark for entry in entries]
    assert marks[0] == "/"  # ".."
    assert marks[[e.name for e in entries].index("run.sh")] == "*"
    assert row_of(buffer, 2).index("..") == 2


def test_insert_tags_the_entry_and_steps_down(tree):
    """DN's ``kbIns``: ``..`` is never tagged, the cursor moves down either way."""
    app = navigator_with(tree, GLYPHS_UNICODE)
    run_app(app, [lambda a: [a.post_event(KeyEvent(key="insert")) for _ in range(3)]])
    panel = app.manager.left
    names = [entry.name for entry in panel.items]
    assert names[:3] == ["..", "alpha", "beta"]
    assert panel.marked == {"alpha", "beta"}
    assert panel.cursor == 3


def test_insert_again_untags(panel):
    panel.cursor = 1
    panel.toggle_mark()
    panel.cursor = 1
    panel.toggle_mark()
    assert panel.marked == frozenset()
    assert panel.cursor == 2


def test_a_tagged_row_shows_the_tag_char_and_its_own_colours(tree):
    app = navigator_with(tree, GLYPHS_UNICODE)
    run_app(app, [lambda a: a.post_event(KeyEvent(key="insert")),
                  lambda a: a.post_event(KeyEvent(key="insert"))])
    buffer = desktop(app)
    panel = app.manager.left
    assert panel.marked == {"alpha"}
    char, style = buffer.get(1, 3)  # "alpha", the second row
    assert char == "√"
    assert style == panel.part_style("row", classes=("directory", "marked"))
    assert style.fg != panel.part_style("row", classes=("directory",)).fg
    assert buffer.get(1, 4)[0] == "/"  # "beta", untagged, keeps its type mark
    # Under the cursor a tagged row is [89], not the plain cursor.
    panel.cursor = 1
    settle()
    assert panel.row_style(1, panel.items[1]) != panel.part_style("row", selected=True)


def test_the_ascii_tier_tags_with_a_plus(tree):
    app = navigator_with(tree, GLYPHS_ASCII)
    run_app(app, [lambda a: [a.post_event(KeyEvent(key="insert")) for _ in range(2)]])
    assert desktop(app).get(1, 3)[0] == "+"


def test_the_icon_gives_way_to_the_tag(tree):
    app = navigator_with(tree, GLYPHS_NERD)
    run_app(app, [lambda a: [a.post_event(KeyEvent(key="insert")) for _ in range(2)]])
    assert desktop(app).get(1, 3)[0] == "√"


def test_tags_survive_a_reread_but_not_a_move(panel, tree):
    panel.marked = frozenset({"one.txt", "two.txt"})
    (tree / "two.txt").unlink()
    panel.reload()
    settle()
    assert panel.marked == {"one.txt"}
    panel.cursor = [e.name for e in panel.items].index("alpha")
    panel.enter()
    settle()
    assert panel.marked == frozenset()


def test_the_footer_sums_the_tagged_files(panel):
    panel.marked = frozenset({"one.txt", "two.txt"})
    assert panel.footer_text() == " 2,058 bytes in 2 selected files "


def test_the_footer_names_a_symlinks_target(panel, tree):
    (tree / "link").symlink_to("one.txt")
    (tree / "stale").symlink_to("/nowhere/at/all")
    panel.reload()
    settle()
    panel.cursor = names(panel).index("link")
    assert panel.footer_text() == " link -> one.txt "
    panel.cursor = names(panel).index("stale")
    assert panel.footer_text() == " stale -> /nowhere/at/all "
    panel.cursor = names(panel).index("one.txt")
    assert panel.footer_text() == " one.txt "


def test_space_tags_while_the_command_line_is_empty(tree):
    """DN's ``fmoSpaceToggle``: Space is Insert until something is typed."""
    app = navigator_with(tree, GLYPHS_UNICODE)
    run_app(app, [lambda a: [a.post_event(KeyEvent(" ", " ")) for _ in range(2)]])
    panel = app.manager.left
    assert panel.marked == {"alpha"}
    assert panel.cursor == 2
    assert app.shell.command_line.value == ""


def test_space_types_once_the_command_line_has_text(tree):
    app = navigator_with(tree, GLYPHS_UNICODE)
    run_app(app, [lambda a: [a.post_event(KeyEvent(c, c)) for c in "ls -l"]])
    assert app.shell.command_line.value == "ls -l"
    assert app.manager.left.marked == frozenset()


def test_go_up_lands_on_the_directory_it_left(panel, tree):
    panel.path = tree / "alpha"
    settle()
    panel.go_up()
    settle()
    assert panel.path == tree
    assert panel.selected.name == "alpha"


def test_go_up_at_the_root_stays(panel):
    panel.path = pathlib.Path("/")
    settle()
    panel.go_up()
    settle()
    assert panel.path == pathlib.Path("/")


def test_backspace_goes_up_while_the_command_line_is_empty(tree):
    """DN's ``fmoBackGoesBack``."""
    app = navigator_with(tree, GLYPHS_UNICODE)
    run_app(app, [
        lambda a: setattr(a.manager.left, "path", tree / "alpha"),
        lambda a: a.post_event(KeyEvent("backspace")),
    ])
    assert app.manager.left.path == tree
    assert app.manager.left.selected.name == "alpha"


def test_backspace_edits_the_command_line_once_it_has_text(tree):
    app = navigator_with(tree, GLYPHS_UNICODE)
    run_app(app, [
        lambda a: [a.post_event(KeyEvent(c, c)) for c in "ls"],
        lambda a: a.post_event(KeyEvent("backspace")),
    ])
    assert app.shell.command_line.value == "l"
    assert app.manager.left.path == tree


def test_shift_backspace_goes_up_whatever_the_command_line_holds(tree):
    app = navigator_with(tree, GLYPHS_UNICODE)
    run_app(app, [
        lambda a: [a.post_event(KeyEvent(c, c)) for c in "ls"],
        lambda a: a.post_event(KeyEvent("backspace", shift=True)),
    ])
    assert app.shell.command_line.value == "ls"
    assert app.manager.left.path == tree.parent


@pytest.mark.parametrize("line", ["", "ls"])
def test_ctrl_pageup_goes_up_whatever_the_command_line_holds(tree, line):
    app = navigator_with(tree, GLYPHS_UNICODE)
    run_app(app, [
        lambda a: setattr(a.manager.left, "path", tree / "alpha"),
        lambda a: [a.post_event(KeyEvent(c, c)) for c in line],
        lambda a: a.post_event(KeyEvent("pageup", ctrl=True)),
    ])
    assert app.shell.command_line.value == line
    assert app.manager.left.path == tree
    assert app.manager.left.selected.name == "alpha"


@pytest.fixture
def mixed(tmp_path):
    for name in ("a.txt", "B.TXT", "c.py", "Makefile", "notes.md"):
        (tmp_path / name).write_text("x")
    (tmp_path / "docs.txt").mkdir()
    panel = Panel(tmp_path, width=40, height=20)
    panel.stylesheet = default_scheme()
    return mounted(panel, size=(40, 20))


def test_select_group_tags_the_files_a_mask_matches(mixed):
    mixed.select_group("*.txt")
    # Case folded as DN's InMask folded it; a directory is passed over.
    assert mixed.marked == {"a.txt", "B.TXT"}


def test_star_dot_star_matches_a_name_without_a_dot_too(mixed):
    mixed.select_group("*.*")
    assert mixed.marked == {"a.txt", "B.TXT", "c.py", "Makefile", "notes.md"}
    mixed.marked = frozenset()
    mixed.select_group("makefile.*")
    assert mixed.marked == {"Makefile"}


def test_select_group_takes_several_masks_and_an_except(mixed):
    mixed.select_group("*.py; *.md")
    assert mixed.marked == {"c.py", "notes.md"}
    mixed.marked = frozenset()
    mixed.select_group("*.txt", invert=True)
    assert mixed.marked == {"c.py", "Makefile", "notes.md"}


def test_unselect_group_reaches_directories_and_never_tags(mixed):
    mixed.marked = frozenset({"a.txt", "c.py", "docs.txt"})
    mixed.select_group("*.txt", select=False)
    assert mixed.marked == {"c.py"}
    mixed.select_group("*", select=False, invert=True)
    assert mixed.marked == {"c.py"}


def test_gray_star_inverts_the_files_and_leaves_directories_alone(mixed):
    mixed.marked = frozenset({"a.txt", "docs.txt"})
    mixed.invert_marks()
    # docs.txt is a directory: it keeps its tag.
    assert mixed.marked == {"B.TXT", "c.py", "Makefile", "notes.md", "docs.txt"}


def test_ctrl_hray_star_inverts_the_directories_too(mixed):
    mixed.marked = frozenset({"a.txt", "docs.txt"})
    mixed.invert_marks(directories=True)
    assert mixed.marked == {"B.TXT", "c.py", "Makefile", "notes.md"}
    assert ".." not in mixed.marked


def test_gray_star_and_ctrl_hray_star_reach_the_panel(tree):
    app = navigator_with(tree, GLYPHS_UNICODE)
    run_app(app, [lambda a: a.post_event(KeyEvent("kp_multiply", "*"))])
    assert app.manager.left.marked == {"one.txt", "two.txt"}

    app = navigator_with(tree, GLYPHS_UNICODE)
    run_app(app, [lambda a: a.post_event(KeyEvent("kp_multiply", "*", ctrl=True))])
    assert app.manager.left.marked == {"alpha", "beta", "one.txt", "two.txt"}


@pytest.mark.parametrize("key, char", [("kp_plus", "+"), ("kp_minus", "-"), ("kp_multiply", "*")])
def test_a_gray_key_types_once_the_command_line_has_text(tree, key, char):
    app = navigator_with(tree, GLYPHS_UNICODE)
    run_app(app, [
        lambda a: [a.post_event(KeyEvent(c, c)) for c in "ls"],
        lambda a: a.post_event(KeyEvent(key, char)),
        lambda a: a.post_event(KeyEvent(key, char, shift=True)),
    ])
    assert app.shell.command_line.value == "ls" + char + char
    assert app.modal is None
    assert app.manager.left.marked == frozenset()


@pytest.mark.parametrize("char", ["+", "-", "*"])
def test_the_plain_characters_act_as_the_gray_keys_on_an_empty_line(tree, char):
    """Midnight Commander's rule, for terminals that send Gray + as a plain +."""
    from navigator.widgets.manager.select_dialog import SelectDialog

    app = navigator_with(tree, GLYPHS_UNICODE)
    seen = []
    run_app(app, [lambda a: a.post_event(KeyEvent(char, char)),
                  lambda a: seen.append((a.modal, a.shell.command_line.value))])
    modal, line = seen[0]
    assert line == ""
    if char == "*":
        assert modal is None and app.manager.left.marked == {"one.txt", "two.txt"}
    else:
        assert isinstance(modal, SelectDialog) and modal.select == (char == "+")


def test_the_plain_characters_type_after_anything_else(tree):
    app = navigator_with(tree, GLYPHS_UNICODE)
    run_app(app, [lambda a: [a.post_event(KeyEvent(c, c)) for c in "a+b-c*d"]])
    assert app.shell.command_line.value == "a+b-c*d"
    assert app.modal is None


def test_the_menu_entries_work_whatever_the_command_line_holds(tree):
    """Only the keys step aside: they are characters, a menu entry is not."""
    from navigator.widgets.manager.commands import InvertSelection

    app = navigator_with(tree, GLYPHS_UNICODE)
    run_app(app, [lambda a: [a.post_event(KeyEvent(c, c)) for c in "ls"]])
    manager = app.manager
    assert manager.enables(InvertSelection())
    assert not manager.enables(InvertSelection(by_key=True))


def test_gray_plus_asks_for_a_mask_and_tags_what_it_matches(mixed):
    """End to end: Gray +, the dialog painted, a mask typed, Enter."""
    from navigator.widgets.manager.select_dialog import SelectDialog

    root = mixed.path

    async def main():
        shell = Shell(root, root)
        app = Application(shell, terminal=FakeTerminal(width=80, height=24))
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.1)
        app.post_event(KeyEvent("kp_plus", "+"))
        await asyncio.sleep(0.06)
        assert isinstance(app.modal, SelectDialog)
        assert " Select " in app.terminal.frames[-1]
        assert app.modal.mask.value == "*.*"
        assert app.modal.options.value == 0
        # The default is selected, so the first key replaces it.
        assert app.modal.mask.entry.selected_text == "*.*"
        for char in "*.md":
            app.post_event(KeyEvent(char, char))
        await asyncio.sleep(0.06)
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.12)
        marked = shell.manager.left.marked
        modal = app.modal
        app.exit()
        await task
        return marked, modal

    marked, modal = asyncio.run(main())
    assert modal is None
    assert marked == {"notes.md"}


def test_the_select_dialog_opens_on_the_last_mask():
    """DN's ``HistoryStr(hsSelectBox, 0)``: the newest mask, shared by both."""
    from navml.history import HISTORY
    from navigator.widgets.manager.select_dialog import SelectDialog

    HISTORY.add("select", "*.py")
    dialog = SelectDialog(select=False)
    assert dialog.mask.value == "*.py"
    assert dialog.title == "Unselect"


def test_shift_gray_minus_opens_unselect_with_except_ticked(mixed):
    from navigator.widgets.manager.select_dialog import SelectDialog

    root = mixed.path

    async def main():
        shell = Shell(root, root)
        app = Application(shell, terminal=FakeTerminal(width=80, height=24))
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.1)
        app.post_event(KeyEvent("kp_minus", "-", shift=True))
        await asyncio.sleep(0.06)
        modal = app.modal
        title, invert = modal.title, modal.options.value
        app.post_event(KeyEvent("escape"))
        await asyncio.sleep(0.06)
        app.exit()
        await task
        return modal, title, invert

    modal, title, invert = asyncio.run(main())
    assert isinstance(modal, SelectDialog)
    assert (title, invert) == ("Unselect", 1)


def test_a_sheet_may_refuse_icons_on_a_terminal_that_could_draw_them(tree):
    """``icons: none`` is the escape hatch for strict DOS fidelity."""
    app = navigator_with(tree, GLYPHS_NERD)
    run_app(app, [])
    panel = app.manager.left
    assert panel.show_icons
    panel.stylesheet = load_scheme("default", ("theme.nss", "Panel { icons: none }"))
    settle()
    assert panel.icons == "none"
    assert not panel.show_icons
    assert panel.gutter == 1


def test_a_misspelled_icons_value_fails_at_the_sheet_and_not_silently():
    """``icons: mone`` used to mean icons-on, since the read site only tested
    for ``none``.  The declaration on ``Panel`` is what closes that."""
    with pytest.raises(StylesheetError) as raised:
        load_scheme("default", ("bad.nss", "Panel { icons: mone }"))
    assert "not a valid icons" in str(raised.value)
    assert "bad.nss:1" in str(raised.value)
    # The spelling it was reaching for still loads.
    load_scheme("default", ("bad.nss", "Panel { icons: none }"))


def test_a_directory_and_a_file_get_different_icons(tree):
    app = navigator_with(tree, GLYPHS_NERD)
    run_app(app, [])
    buffer = desktop(app)
    entries = app.manager.left.items
    # Row 2 is the first listing line; ".." leads, then the directories.
    drawn = [buffer.get(1, 2 + row)[0] for row in range(len(entries))]
    assert drawn[0] == icons.PARENT
    assert drawn[entries.index(next(e for e in entries if e.is_dir and e.name != ".."))] == icons.FOLDER
    assert drawn[entries.index(next(e for e in entries if not e.is_dir))] == icons.BY_EXTENSION["txt"]


@pytest.mark.parametrize(
    "name, is_dir, expected",
    [
        ("..", True, icons.PARENT),
        ("src", True, icons.FOLDER),
        ("main.py", False, icons.BY_EXTENSION["py"]),
        ("MAIN.PY", False, icons.BY_EXTENSION["py"]),  # extensions fold case
        ("README", False, icons.FILE),
        (".gitignore", False, icons.HIDDEN_FILE),  # a leading dot is not an extension
        (".config", True, icons.HIDDEN_FOLDER),
        (".config.json", False, icons.BY_EXTENSION["json"]),  # a known extension wins
        ("archive.tar.gz", False, icons.BY_EXTENSION["gz"]),
        ("thing.unheardof", False, icons.FILE),
    ],
)
def test_the_icon_table_reads_a_name(name, is_dir, expected):
    assert icons.icon_for(name, is_dir) == expected


@pytest.mark.parametrize(
    "name, is_dir, mark, expected",
    [
        *[("thing", False, mark, glyph) for mark, glyph in icons.BY_TYPE.items()],
        ("build.sh", False, "*", icons.BY_TYPE["*"]),  # the type beats the extension
        ("lib", True, "~", icons.BY_TYPE["~"]),  # a link to a directory is a link
        ("src", True, "/", icons.FOLDER),
        ("..", True, "/", icons.PARENT),
        ("main.py", False, " ", icons.BY_EXTENSION["py"]),
        (".local", True, "~", icons.BY_TYPE["~"]),  # a hidden link is a link
        (".run", False, "*", icons.BY_TYPE["*"]),  # a hidden executable runs
        (".cache", True, "/", icons.HIDDEN_FOLDER),
    ],
)
def test_the_type_mark_picks_the_icon(name, is_dir, mark, expected):
    assert icons.icon_for(name, is_dir, mark) == expected


def test_the_nerd_gutter_shows_each_type_as_a_glyph(tmp_path):
    import os

    (tmp_path / "plain.txt").write_text("x")
    (tmp_path / "run.sh").write_text("x")
    (tmp_path / "run.sh").chmod(0o755)
    (tmp_path / "dir").mkdir()
    (tmp_path / "to_file").symlink_to("plain.txt")
    (tmp_path / "to_dir").symlink_to("dir")
    (tmp_path / "stale").symlink_to("nowhere")
    os.mkfifo(tmp_path / "fifo")
    app = navigator_with(tmp_path, GLYPHS_NERD)
    run_app(app, [])
    buffer = desktop(app)
    entries = app.manager.left.items
    drawn = {e.name: buffer.get(1, 2 + row)[0] for row, e in enumerate(entries)}
    for name, mark in [("run.sh", "*"), ("to_file", "@"), ("to_dir", "~"), ("stale", "!"), ("fifo", "|")]:
        assert drawn[name] == icons.BY_TYPE[mark], name
    assert drawn["dir"] == icons.FOLDER
    assert drawn["plain.txt"] == icons.BY_EXTENSION["txt"]

    # A tag still takes the gutter over the type's glyph.
    panel = app.manager.left
    panel.marked = frozenset({"to_file"})
    settle()
    buffer = ScreenBuffer(panel.width, panel.height)
    panel.render(buffer)
    assert buffer.get(1, 1 + [e.name for e in entries].index("to_file"))[0] == "√"


@pytest.mark.parametrize(
    "name, is_dir, mark, expected",
    [
        *[("thing", False, mark, cls) for mark, cls in filetypes.BY_TYPE.items()],
        ("src", True, "/", None),  # a plain directory is `.directory' alone
        ("backup.zip", True, "/", None),  # and never an archive
        ("..", True, "/", None),
        ("README", False, " ", None),
        (".bashrc", False, " ", None),  # a leading dot is not an extension
        ("archive.tar.gz", False, " ", "archive"),
        ("PHOTO.JPG", False, " ", "image"),  # masks fold case, as DN's did
        ("song.flac", False, " ", "media"),
        ("report.pdf", False, " ", "document"),
        ("main.py", False, " ", "source"),
        ("notes~", False, " ", "temp"),
        ("#draft#", False, " ", "temp"),
        (".main.py.swp", False, " ", "temp"),
        ("build.sh", False, "*", "executable"),  # the type beats the extension
        ("photos.zip", False, "@", "symlink"),
        ("lib", True, "~", "symlink"),
        ("thing.unheardof", False, " ", None),
    ],
)
def test_the_file_type_picks_the_row_class(name, is_dir, mark, expected):
    assert filetypes.category_of(name, is_dir, mark) == expected


def test_a_row_is_coloured_by_its_file_type(tmp_path):
    for name in ("plain", "pack.zip", "shot.png", "old.bak"):
        (tmp_path / name).write_text("x")
    (tmp_path / "run").write_text("x")
    (tmp_path / "run").chmod(0o755)
    (tmp_path / "link").symlink_to("plain")
    (tmp_path / "stale").symlink_to("nowhere")
    panel = Panel(tmp_path, width=40, height=20)
    panel.stylesheet = default_scheme()
    mounted(panel, size=(40, 20))
    rows = {item.name: (index, item) for index, item in enumerate(panel.items)}
    plain = panel.part_style("row")
    styles = {name: panel.row_style(*rows[name]) for name in rows if name != ".."}
    for name, cls in [("pack.zip", "archive"), ("shot.png", "image"), ("old.bak", "temp"),
                      ("run", "executable"), ("link", "symlink"), ("stale", "stale-link")]:
        assert styles[name] == panel.part_style("row", classes=(cls,)), name
        assert styles[name].fg != plain.fg, name
    assert styles["plain"] == plain

    # The cursor and a tag both win over the file type.
    index, item = rows["pack.zip"]
    panel.focus()
    panel.cursor = index
    settle()
    assert panel.row_style(index, item) == panel.part_style("row", selected=True)
    panel.marked = frozenset({"pack.zip"})
    settle()
    assert panel.row_style(index, item) == panel.part_style("row", classes=("marked",), selected=True)


def test_no_icon_comes_from_the_range_nerd_fonts_3_removed():
    """``nf-mdi`` (U+F500 to U+FD46) was dropped in Nerd Fonts 3 and moved
    to the supplementary planes, so a glyph from it is a box on a current font."""
    every = [icons.FOLDER, icons.PARENT, icons.FILE, *icons.BY_EXTENSION.values(),
             *icons.BY_TYPE.values()]
    assert not [hex(ord(glyph)) for glyph in every if 0xF500 <= ord(glyph) <= 0xFD46]


def test_every_icon_is_a_single_cell():
    """The gutter is two columns wide and the second is a space by design.

    A Nerd Font *Mono* build patches its icons to one cell and ``char_width``
    agrees, the Private Use Area measuring as ambiguous.  If one of these ever
    measured two, the name would be shoved along on the Mono build too.
    """
    every = [icons.FOLDER, icons.PARENT, icons.FILE, *icons.BY_EXTENSION.values(),
             *icons.BY_TYPE.values()]
    assert {char_width(glyph) for glyph in every} == {1}


def test_the_version_banner_names_the_command_and_the_running_copy():
    """Not the version alone: *which* copy printed it.

    Navigator can be installed as a system package, as a pipx copy and as a
    checkout at the same time, and PATH decides which one runs -- so the path
    is the half of this that answers a bug report.
    """
    banner = version_banner()
    assert banner.startswith("nav ")
    # The directory holding navigator/__main__.py, whichever copy that is.
    assert str(Path(main.__code__.co_filename).resolve().parent) in banner


def test_the_version_falls_back_to_the_source_tree(monkeypatch):
    """A checkout has no distribution metadata, and must still report.

    This is the ordinary case while developing, so it is the one that would
    go unnoticed if it broke: the installed-metadata path is what runs on a
    machine that has Navigator installed, and never here.
    """
    def missing(name):
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr(metadata, "version", missing)
    assert version_banner().startswith(f"nav {__version__} from ")


def test_the_version_prefers_installed_metadata_over_the_source(monkeypatch):
    """The two differ once a checkout is edited after being installed."""
    monkeypatch.setattr(metadata, "version", lambda name: "9.9.9")
    assert version_banner().startswith("nav 9.9.9 from ")


def test_version_exits_zero_without_starting_the_application(capsys):
    """``action="version"`` leaves through SystemExit -- deliberately."""
    with pytest.raises(SystemExit) as exit:
        main(["--version"])
    assert exit.value.code == 0
    assert capsys.readouterr().out.startswith("nav ")


def test_usage_names_the_installed_command(capsys):
    """The console script is ``nav``; ``prog`` used to say ``navigator``."""
    with pytest.raises(SystemExit):
        main(["--help"])
    assert capsys.readouterr().out.startswith("usage: nav ")


# -- the console's cursor is the terminal's own ------------------------------


def test_the_console_takes_the_keyboard_while_it_is_showing(tree, quiet_console):
    app = navigator(tree)
    console = app.shell.console
    run_app(app, [KeyEvent("o", ctrl=True), lambda a: None])
    assert app.focused is console


def test_hiding_the_console_gives_the_keyboard_back(tree, quiet_console):
    """To exactly the widget that had it -- activating a window restores it."""
    app = navigator(tree)
    run_app(app, [
        lambda a: a.manager.right.focus(),
        KeyEvent("o", ctrl=True),
        KeyEvent("o", ctrl=True),
        lambda a: None,
    ])
    assert app.focused is app.manager.right


def test_the_console_reports_the_childs_cursor(tree, quiet_console):
    app = navigator(tree)
    console = app.shell.console

    def show(a):
        a.shell.toggle_console()
        running(a)
        console._on_output(b"hello: ")

    seen = []
    run_app(app, [show, lambda a: seen.append((console.cursor_position(), a._cursor()))])
    # Seven characters in, on the first line of the console's own area; and
    # the console starts one row down, under the menu bar.
    assert seen == [((7, 0), (7, 1, "default"))]


def test_the_terminals_cursor_is_placed_where_the_child_put_it(tree, quiet_console):
    app = navigator(tree)
    terminal = app.terminal

    def show(a):
        a.shell.toggle_console()
        running(a)
        a.shell.console._on_output(b"hello: ")

    run_app(app, [show, lambda a: None])
    assert "\x1b[2;8H" + SHOW_CURSOR in terminal.painted


def test_the_caret_is_on_the_command_line_while_the_panels_are_up(tree, quiet_console):
    # The panel holds the keyboard and has no caret; what it declines is
    # typed on the line, so that is where the terminal's cursor goes.
    app = navigator(tree)
    run_app(app, [KeyEvent("l", "l"), lambda a: None])
    prompt = len(app.shell.command_line.shown_prompt)
    # "default": the user's own cursor shape, as at any other shell prompt.
    assert app._cursor() == (prompt + 1, 22, "default")
    assert f"\x1b[23;{prompt + 2}H" + SHOW_CURSOR in app.terminal.painted


def test_the_idle_console_leaves_the_caret_to_the_command_line(tree, quiet_console):
    app = navigator(tree)
    console = app.shell.console

    def show(a):
        a.shell.toggle_console()
        console._on_output(b"hello: ")

    run_app(app, [show, lambda a: None])
    assert console.cursor_position() is None
    assert app._cursor()[1] == 22


def test_the_console_reports_no_cursor_while_it_is_scrolled_back(tree, quiet_console):
    app = navigator(tree)
    console = app.shell.console

    def show(a):
        a.shell.toggle_console()
        running(a)
        console._on_output(b"\r\n".join(b"line %d" % n for n in range(60)))

    seen = []
    run_app(app, [show, lambda a: console.scroll_back(),
                  lambda a: seen.append((console.cursor_position(), a._cursor()))])
    assert console.screen.scrolled_back is True
    # The rows on screen are history; the live cursor means nothing among
    # them -- and the program still has the keys, so the line gets no caret.
    assert seen == [(None, None)]


def test_a_hidden_child_cursor_is_not_drawn(tree, quiet_console):
    app = navigator(tree)
    console = app.shell.console

    def show(a):
        a.shell.toggle_console()
        running(a)
        console._on_output(b"\x1b[?25l")  # the child hides its own cursor

    run_app(app, [show, lambda a: None])
    assert console.cursor_position() is None


# -- who owns which key ------------------------------------------------------


def test_ctrl_o_and_the_key_behind_it_arrive_in_one_batch(tree, quiet_console):
    # A paste, or fast typing: both events are dispatched before any effect
    # runs, so a focus handover queued as an effect would still be pointing at
    # the panels when the second key is routed.
    app = navigator(tree)
    typed: list[bytes] = []

    def stub(a):
        running(a)
        a.shell.console.send = lambda e: typed.append(encode_key(e)) or True

    def both(a):
        a.post_event(KeyEvent("o", ctrl=True))
        a.post_event(KeyEvent("x", "x"))

    run_app(app, [stub, both])
    assert typed == [b"x"]
    assert app.manager.left.cursor == 0


def test_the_console_swallows_keys_it_has_no_child_for(tree, quiet_console):
    # Nothing to type at, and the panels are behind it showing nothing -- a
    # key that fell through would move a cursor the user cannot see.
    app = navigator(tree)
    run_app(app, [KeyEvent("o", ctrl=True), running, KeyEvent("down"), KeyEvent("down")])
    assert app.shell.console.process is None
    assert app.manager.left.cursor == 0


def test_alt_x_quits_from_the_panels(tree):
    app = navigator(tree)
    run_app(app, [KeyEvent("x", "x", alt=True)])
    assert app.is_running is False


def test_alt_x_quits_once_the_file_manager_is_closed(tree, quiet_console):
    # It used to be Manager's, so closing the window took the key with it.
    app = navigator(tree)
    run_app(app, [
        KeyEvent("f4", ctrl=True),
        lambda a: None,
        KeyEvent("x", "x", alt=True),
    ])
    assert app.manager.parent is None
    assert app.is_running is False


def test_alt_x_goes_to_the_child_from_the_console(tree, quiet_console):
    # It is a desktop key rather than a global one: with the console up over
    # the windows it is a keystroke like any other.
    app = navigator(tree)
    typed: list[bytes] = []
    alive: list[bool] = []
    run_app(app, [
        KeyEvent("o", ctrl=True),
        running,
        lambda a: setattr(a.shell.console, "send",
                          lambda e: typed.append(encode_key(e)) or True),
        KeyEvent("x", "x", alt=True),
        # run_app exits the application itself once the actions are done, so
        # "still running" has to be read while it still is.
        lambda a: alive.append(a.is_running),
    ])
    assert alive == [True]
    assert typed == [b"\x1bx"]


def test_the_desktop_owns_the_panel_keys(tree):
    # Reached through the tree now, not from the application hook: nothing is
    # focused while the panels are up, so the root widget is offered the key.
    app = navigator(tree)
    run_app(app, [KeyEvent("down")])
    assert app.manager.left.cursor == 1


def test_the_application_keeps_only_what_is_global():
    # The application's table is consulted before any widget's, so what it
    # binds is kept from the whole tree -- the ways in and out of the console
    # and of Navigator, and the two commands that are nobody's panel's.
    from navigator.commands import Help, Quit, ToggleConsole
    from navml.widgets.menu.commands import OpenMenu

    table = key_table(Navigator)
    assert set(table) == {
        "ctrl+o", "ctrl+f3", "f1", "f10", "alt+x",
        # The command line's, while it has text; the panel's otherwise.
        "enter", "home", "end", "tab",
    }
    assert table["ctrl+o"] is ToggleConsole
    assert table["f1"] is Help
    assert table["f10"] is OpenMenu
    assert table["alt+x"] == Quit(desktop=True)


def test_a_panel_can_be_built_the_way_markup_builds_one(tree):
    """A child block compiles to ``Panel(parent=self)``, so that has to work.

    It did not: ``path`` was a required positional argument, which would have
    kept the panel out of any document and the desktop out of markup for a
    reason nothing had written down.  The default is the reactive's own, so a
    panel built this way lists the working directory until a ``path:`` binding
    arrives.
    """
    panel = Panel(parent=None, width=40, height=20)
    settle()
    assert panel.path == Path(".")
    assert panel.width == 40
    # And the ordinary spelling is untouched.
    assert Panel(tree, width=40, height=20).path == tree


def test_every_part_the_sheet_names_is_one_a_widget_paints():
    """The half of the part check a stylesheet parse cannot do for itself.

    A ``::part`` selector matches by class *name* over the MRO, so the parser
    has no class to ask and `Panel::rwo' would be accepted and silently match
    nothing.  Here the widgets are imported, so the question can be asked --
    and asking it of the shipped sheet is what turns a typo into a failure.
    """
    import navigator.widgets
    from navkit.stylesheet import parts_of
    from navigator.scheme import default_scheme

    widgets = {name: getattr(navigator.widgets, name) for name in navigator.widgets.__all__}
    checked = 0
    for rule in default_scheme().rules:
        # Only the subject may carry a part; the grammar allows it nowhere else.
        compound = rule.selector.subject
        if compound.part is None:
            continue
        widget = widgets.get(compound.type_name or "")
        if widget is None:
            continue              # a type this package does not define
        assert compound.part in parts_of(widget), (
            f"{compound.type_name}::{compound.part} names a part "
            f"{compound.type_name} does not paint"
        )
        checked += 1
    assert checked, "the sheet names no parts at all -- has the selector moved?"


# -- the desktop, frozen -----------------------------------------------------


GOLDEN = pathlib.Path(__file__).resolve().parent / "fixtures" / "desktop-80x24.txt"


def desktop_dump(manager, width=80, height=24) -> str:
    """Every cell of the desktop, as its character and its style runs.

    Characters alone would miss a colour regression and a whole ``Style``
    per cell would be unreadable, so each row is its text followed by the
    style runs underneath it.  That is enough to catch a frame that moved by
    one column *or* one palette entry.
    """
    buffer = ScreenBuffer(width, height)
    manager.render_tree(buffer)
    lines = []
    for y in range(height):
        chars, styles = [], []
        for x in range(width):
            char, style = buffer.get(x, y)
            chars.append(char or " ")
            styles.append(f"{style.fg},{style.bg},{int(style.bold)}")
        runs, last, count = [], None, 0
        for spec in styles:
            if spec == last:
                count += 1
            else:
                if last is not None:
                    runs.append(f"{last}x{count}")
                last, count = spec, 1
        runs.append(f"{last}x{count}")
        lines.append("".join(chars).rstrip() + "\n  | " + " ".join(runs))
    return "\n".join(lines) + "\n"


def test_the_desktop_paints_what_it_has_always_painted(tmp_path, monkeypatch):
    """The frame this refactor may not change, captured before it started.

    ``manager.nml``'s conversion was proved by running the trees before and
    after on a pty and comparing the escape streams byte for byte -- 3725
    bytes, ``cmp``-identical.  That check was a one-off between two commits
    and lived only as prose.  This is the same guarantee in a form the suite
    can run on every change: a fixture captured from the tree as it was, and
    compared against what the tree paints now.

    It has changed once, deliberately: when the file manager became a window
    on a desktop, the fixture gained exactly its two icons -- ``[■]`` on the
    left panel's top edge and ``[↕]`` on the right's -- and not one other
    cell, which is what the conversion was checked against.  And once more
    when the clock arrived: the last five cells of the menu bar, pinned to
    ``12:34`` here so the fixture does not depend on when it runs.  And once
    more when the key bar began reading its captions off the key tables: the
    same ten captions, with every one whose command has no handler yet in the
    status line's *Disabled* colour -- the bottom row's styles, and nothing
    else.  That is also why this runs under ``Navigator`` rather than a bare
    ``Application``: F1, F9 and F10 are the application's keys.  And once
    more when the command line arrived: the panels gave up their last empty
    row, and the row above the key bar is ``.>`` in DOS Navigator's
    hard-coded white on black -- the only two rows that changed.  And once
    more when F3 got its viewer: *View* left the *Disabled* colour, and the
    key bar's styles are the only thing that moved.  And once more, the same
    way, when F4 got its editor.  And once more when rows took their file
    type's colour: ``one.txt`` and ``two.txt`` are documents, and their two
    rows' styles are all that moved.  And once more when F5 and F6 got the
    copy: *Copy* and *Ren* left the *Disabled* colour, the key bar's styles
    again the only thing that moved.  And once more, the same way, when F8
    got the delete.
    """
    monkeypatch.setattr(clock_module, "now", lambda: datetime(2026, 1, 1, 12, 34))
    (tmp_path / "alpha").mkdir()
    (tmp_path / "beta").mkdir()
    (tmp_path / "one.txt").touch()
    (tmp_path / "two.txt").touch()
    # A relative path, from inside the tree: the panel titles are then "." in
    # both panels rather than a `tmp_path' whose length changes what the
    # title clips to, so the fixture is about the desktop and not about where
    # pytest happened to put a directory.
    monkeypatch.chdir(tmp_path)

    async def main():
        app = Navigator(
            pathlib.Path("."),
            pathlib.Path("."),
            terminal=FakeTerminal(width=80, height=24),
        )
        shell = app.shell
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.15)
        dump = desktop_dump(shell)
        app.exit()
        await task
        return dump

    dump = asyncio.run(asyncio.wait_for(main(), 10))
    assert dump == GOLDEN.read_text(encoding="utf-8")


# -- the first dialog wired into the application -----------------------------


def test_f7_makes_a_directory(tmp_path):
    """The library, end to end, in the real desktop.

    Everything the widget library is for happens in this one path: a handler
    *starts* a dialog rather than waiting for one, the dialog paints while
    the loop keeps running, the keyboard goes into its input line, Enter
    accepts, the answer comes back out of ``execute`` into the task, and the
    focus lands back on the panel because the mount walks put it there.
    """

    async def main():
        shell = Shell(tmp_path, tmp_path)
        manager = shell.manager
        app = Application(shell, terminal=FakeTerminal(width=80, height=24))
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.1)

        app.post_event(KeyEvent(key="f7"))
        await asyncio.sleep(0.06)
        # Painted *before* anything answers it, which is the whole rule.
        assert "Make directory" in app.terminal.frames[-1]
        assert isinstance(app.modal, MkdirDialog)
        assert isinstance(app.focused, InputLine)

        for char in "reports":
            app.post_event(KeyEvent(key=char, char=char))
        await asyncio.sleep(0.06)
        app.post_event(KeyEvent(key="enter"))
        await asyncio.sleep(0.12)

        made = (tmp_path / "reports").is_dir()
        listed = [entry.name for entry in manager.left.items]
        back = app.focused
        app.exit()
        await task
        return made, listed, back

    made, listed, back = asyncio.run(asyncio.wait_for(main(), 10))
    assert made, "the directory was not created"
    assert "reports" in listed, "the panel did not rescan"
    assert isinstance(back, Panel), "the keyboard did not come back"


def test_escaping_f7_makes_nothing(tmp_path):
    async def main():
        shell = Shell(tmp_path, tmp_path)
        manager = shell.manager
        app = Application(shell, terminal=FakeTerminal(width=80, height=24))
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.1)
        app.post_event(KeyEvent(key="f7"))
        await asyncio.sleep(0.06)
        for char in "nope":
            app.post_event(KeyEvent(key=char, char=char))
        await asyncio.sleep(0.06)
        app.post_event(KeyEvent(key="escape"))
        await asyncio.sleep(0.12)
        modal = app.modal
        app.exit()
        await task
        return modal

    assert asyncio.run(asyncio.wait_for(main(), 10)) is None
    assert not (tmp_path / "nope").exists()


# -- the file manager is a window --------------------------------------------


def test_ctrl_o_and_f10_wait_while_a_dialog_is_open(tmp_path, quiet_console):
    """An application hook runs before the modal routing, so it has to ask."""
    app = navigator(tmp_path)
    seen = []
    run_app(app, [
        KeyEvent("f7"),
        lambda a: None,
        KeyEvent("o", ctrl=True),
        KeyEvent("f10"),
        lambda a: None,
        lambda a: seen.append((a.modal, a.is_running, a.shell.console_visible)),
    ])
    modal, running, console_visible = seen[0]
    assert isinstance(modal, MkdirDialog)
    assert running and not console_visible


def test_closing_the_file_manager_leaves_the_console(tree, quiet_console):
    app = navigator(tree)
    run_app(app, [KeyEvent("f4", ctrl=True), lambda a: None, lambda a: None])
    assert app.manager.parent is None
    assert app.shell.console_visible is True
    assert app.focused is app.shell.console
    # And Ctrl+O has no windows to bring back.
    app.shell.toggle_console()
    assert app.shell.console_visible is True


def test_dragging_the_restored_file_manager_moves_both_panels(tree, quiet_console):
    app = navigator(tree)
    manager = app.manager
    zoom = MouseClickEvent(80 - 5, 1, "left", "press")
    start: list[tuple[int, int]] = []

    def drag(a):
        # Restored now: take hold of the left panel's title and pull.
        x, y = manager.x, manager.y
        start.append((x, y))
        grab = MouseClickEvent(x + 10, 1 + y, "left", "press")
        for event in (grab, replace(grab, x=x + 13, y=1 + y + 2, action="move"),
                      replace(grab, x=x + 13, y=1 + y + 2, action="release")):
            a.post_event(event)

    run_app(app, [zoom, replace(zoom, action="release"), lambda a: None,
                  drag, lambda a: None])
    x, y = start[0]
    assert not manager.zoomed
    assert (manager.x, manager.y) == (x + 3, y + 2)
    assert manager.right.x == manager.width // 2
    buffer = desktop(app)
    # The console shows around the window now, and the panels moved with it.
    assert row_of(buffer, 1 + y + 2)[x + 3] in "╔┌"


# -- the clock ---------------------------------------------------------------


def test_the_clock_sits_in_the_top_right_corner(tree):
    app = navigator(tree, size=(80, 24))
    clock = app.shell.clock
    assert isinstance(clock, Clock)
    assert (clock.x, clock.y, clock.width, clock.height) == (75, 0, 5, 1)


def test_the_clock_shows_24_hour_time_and_blinks_its_colon(monkeypatch):
    monkeypatch.setattr(clock_module, "now", lambda: datetime(2026, 1, 1, 17, 5))
    clock = Clock()
    assert clock.text() == "17:05"
    clock.blink = False
    assert clock.text() == "17 05"


def test_the_clock_blinks_every_half_second(tree):
    app = navigator(tree, size=(80, 24))
    clock = app.shell.clock
    assert clock.tick.interval == 500
    seen = []
    run_app(app, [lambda a: seen.append(clock.blink)], settle=0.02)
    assert seen == [True]

    # One tick of its timer flips it, and the next flips it back.
    async def two_ticks():
        await clock.tick._tick()
        seen.append(clock.blink)
        await clock.tick._tick()
        seen.append(clock.blink)

    asyncio.run(two_ticks())
    assert seen == [True, False, True]


# -- the panel's scrollbar ---------------------------------------------------


def test_a_panel_that_fits_shows_no_scrollbar(panel):
    settle()
    assert len(panel.items) <= panel.rows
    assert not panel.bar.visible


def test_a_long_listing_shows_the_scrollbar_on_the_right_frame(tmp_path):
    for n in range(60):
        (tmp_path / f"file{n:02}").touch()
    panel = Panel(tmp_path, width=40, height=20)
    panel.stylesheet = default_scheme()
    mounted(panel, size=(40, 20))
    settle()
    bar = panel.bar
    assert bar.visible
    assert (bar.x, bar.y, bar.width, bar.height) == (39, 1, 1, 18)
    # Turbo Vision's rule: the bar's value is the cursor, not the scroll.
    assert (bar.value, bar.maximum) == (0, len(panel.items) - 1)
    panel.cursor = 45
    settle()
    assert bar.value == 45

    buffer = ScreenBuffer(40, 20)
    panel.render_tree(buffer)
    column = "".join(buffer.get(39, y)[0] for y in range(1, 19))
    assert column[0] == "▲" and column[-1] == "▼"


def test_working_the_scrollbar_moves_the_cursor_and_the_scroll_follows(tmp_path):
    for n in range(60):
        (tmp_path / f"file{n:02}").touch()
    panel = mounted(Panel(tmp_path, width=40, height=20), size=(40, 20))
    settle()
    # A click on the bottom arrow asks for one more; on the track below the
    # thumb, a page more.
    awaited(panel.bar.on_mouse_click(MouseClickEvent(0, 17, "left", "press")))
    settle()
    assert panel.cursor == 1
    awaited(panel.bar.on_mouse_click(MouseClickEvent(0, 10, "left", "press")))
    settle()
    assert panel.cursor == 1 + panel.page()
    assert panel.scroll <= panel.cursor < panel.scroll + panel.rows


# -- the key bar reads the key tables ---------------------------------------------


#: DOS Navigator's own file-panel status line, ``StatusDef hcFilePanel``.
STATUS = " F1 Help  F2 User  F3 View  F4 Edit  F5 Copy  F6 Ren  F7 MkDir  F8 Del  F10 Menu"


def test_the_key_bar_is_dos_navigators_status_line(tree):
    app = navigator(tree)
    run_app(app, [])
    assert row_of(desktop(app), 23).rstrip() == STATUS


def test_the_key_bar_greys_what_nobody_can_run_yet(tree):
    app = navigator(tree)
    enabled = []
    run_app(app, [lambda a: enabled.extend(
        (c.title, a.command_enabled(c)) for _, c, _, _ in a.shell.keybar.items()
    )])
    # View, Edit, MkDir and the menu work; the rest are file operations still to come.
    assert [title for title, on in enabled if on] == ["View", "Edit", "MkDir", "Menu"]


def test_the_key_bar_follows_the_keyboard_into_the_console(tree, quiet_console):
    app = navigator(tree)
    seen = []
    run_app(app, [
        KeyEvent("o", ctrl=True),
        lambda a: seen.append([c.title for _, c, _, _ in a.shell.keybar.items()]),
    ])
    # The panel keys are the file manager's, and the console has the keyboard.
    assert seen == [["Help", "Menu"]]


def test_a_click_on_an_item_asks_for_its_command(tree):
    app = navigator(tree)
    column = STATUS.index("F10")
    run_app(app, [MouseClickEvent(column, 23, "left"),
                  lambda a: None])
    assert app.shell.menu.current == 0


def test_a_click_on_a_greyed_caption_does_nothing_and_goes_nowhere(tree):
    app = navigator(tree)
    cursor = []
    run_app(app, [
        MouseClickEvent(STATUS.index("F3"), 23, "left"),
        lambda a: cursor.append((a.is_running, a.modal)),
    ])
    assert cursor == [(True, None)]


#: The same line while each modifier is held: the ``-``, ``+`` and ``:`` items
#: of ``StatusDef hcFilePanel``, the function keys first, then the letters
#: nearest table first -- the file manager's, the desktop's Zoom and Close,
#: the application's.  At 80 columns the Ctrl row closes before *Show*: the
#: desktop's F4 Close takes the room, which DOS Navigator's file panel row
#: did not caption.  The Alt row closes before *Exit* the same way: E Attr,
#: which DN's row did not carry either, takes its room.
ALT_STATUS = (" F6 Ren  F7 Find  B Sort  C Drive  S Setup  L List  R Re-read"
              "  E Attr  Z Zoom")
CTRL_STATUS = (" F3 New Manager  F4 Close  F6 Calc  F9 Print  K Desc  L Info"
               "  T Tree  Q Preview")
SHIFT_STATUS = (" F1 Arc  F2 Ext  F3 Phones  F4 Edit...  F5 SymLnk"
                "  F6 Reanimate  F8 Del")


@pytest.mark.parametrize(
    ("held", "expected"),
    [({"alt"}, ALT_STATUS), ({"ctrl"}, CTRL_STATUS), ({"shift"}, SHIFT_STATUS)],
)
def test_a_held_modifier_swaps_the_key_bar_for_its_row(tree, held, expected):
    from navkit.events import ModifiersEvent

    app = navigator(tree)
    rows = []
    run_app(app, [
        ModifiersEvent(frozenset(held)),
        lambda a: rows.append(row_of(desktop(a), 23).rstrip()),
        ModifiersEvent(frozenset()),
        lambda a: rows.append(row_of(desktop(a), 23).rstrip()),
    ])
    assert rows[0] == expected
    assert rows[1] == STATUS


def test_the_ctrl_row_greys_what_is_not_written_and_not_what_is(tree):
    from navkit.events import ModifiersEvent

    app = navigator(tree)
    enabled = []
    run_app(app, [
        ModifiersEvent(frozenset({"ctrl"})),
        lambda a: enabled.extend(
            c.title for _, c, _, _ in a.shell.keybar.items() if a.command_enabled(c)
        ),
    ])
    assert "Print" not in enabled
    assert enabled == ["New Manager", "Close", "Tree", "Preview"]


def test_a_click_on_a_held_row_runs_that_rows_command(tree):
    from navkit.events import ModifiersEvent

    app = navigator(tree)
    before = []
    run_app(app, [
        lambda a: before.append(len(a.shell.desktop.windows())),
        ModifiersEvent(frozenset({"ctrl"})),
        MouseClickEvent(CTRL_STATUS.index("F3"), 23, "left"),
        lambda a: before.append(len(a.shell.desktop.windows())),
    ])
    assert before[1] == before[0] + 1


def test_a_window_s_own_function_key_takes_the_bar(tree):
    from navkit.commands import Command
    from navml.widgets.window import Window

    class Hex(Command):
        title = "Hex"

    class Editor(Window):
        keys = {"f4": Hex}

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.can_focus = True

        async def on_hex(self, event):
            return True

    app = navigator(tree)
    rows = []

    def open_editor(a):
        editor = Editor(width=20, height=5)
        a.shell.desktop.open(editor)
        editor.focus()

    run_app(app, [open_editor, lambda a: rows.append(row_of(desktop(a), 23).rstrip())])
    assert " F4 Hex " in rows[0] and "Edit" not in rows[0]


def test_alt_x_is_vetoed_while_a_program_is_over_the_windows(tree, quiet_console):
    from navigator.commands import Quit

    app = navigator(tree)
    answers = []
    run_app(app, [
        lambda a: answers.append(a.command_enabled(Quit(desktop=True))),
        KeyEvent("o", ctrl=True),
        # Idle, the console is only showing output: Alt+X still quits.
        lambda a: answers.append(a.command_enabled(Quit(desktop=True))),
        running,
        lambda a: answers.append(a.command_enabled(Quit(desktop=True))),
        # Every command is the program's while it runs, the menu's Exit too.
        lambda a: answers.append(a.command_enabled(Quit)),
    ])
    assert answers == [True, True, False, False]


# -- DOS Navigator's main menu ------------------------------------------------------


def _entry(menu, *captions):
    """The entry reached by following *captions* down the menu tree."""
    from navml.widgets.dialog.control.control import parse_shortcut

    node = menu
    for caption in captions:
        node = next(e for e in node.entries()
                    if parse_shortcut(getattr(e, "text", ""))[0] == caption)
    return node


def test_the_menu_is_dos_navigators_own(tree):
    from navml.widgets.dialog.control.control import parse_shortcut

    app = navigator(tree)
    bar = [parse_shortcut(e.text)[0] for e in app.shell.menu.entries()]
    assert bar == ["≡", "File", "Disk", "Utilities", "Panel", "Manager",
                   "Options", "Window"]


def test_the_menu_makes_a_directory_like_f7_does(tree):
    app = navigator(tree)
    seen = []
    run_app(app, [KeyEvent("f10"), KeyEvent("f", "f"), KeyEvent("m", "m"),
                  lambda a: None, lambda a: seen.append(type(a.modal).__name__)])
    assert seen == ["MkdirDialog"]


def test_alt_letter_drops_its_menu_from_the_panels(tree):
    app = navigator(tree)
    seen = []
    run_app(app, [KeyEvent("d", "d", alt=True),
                  lambda a: seen.append((a.shell.menu.current, len(a.modal.boxes)))])
    assert seen == [(2, 1)]  # Disk, dropped


def test_a_bound_entry_shows_its_live_key_and_an_unbound_one_dos_navigators(tree):
    from navml.widgets.menu.menu_box.menu_box import key_caption

    app = navigator(tree)
    menu, behind = app.shell.menu, app.manager.left
    captions = []
    run_app(app, [lambda a: captions.extend(
        key_caption(_entry(menu, *path), a, behind) for path in (
            ("File", "Make directory"),     # bound: F7
            ("File", "Exit"),               # unbound Quit(): the original's
            ("Panel", "Re-read"),           # bound twice: the first binding
            ("Window", "Zoom"),             # the desktop's table
            ("Utilities", "Calculator"),    # bound, but nobody handles it
        )
    )])
    assert captions == ["F7", "Alt-X", "Alt-R", "Alt-Z", "Ctrl-F6"]


def test_only_entries_with_a_handler_behind_them_are_enabled(tree):
    from navml.widgets.menu.menu_box import MenuBox

    app = navigator(tree)
    seen = []

    def probe(a):
        box = MenuBox(_entry(a.shell.menu, "File"))
        box.behind = a.manager.left
        a.shell.add(box)
        seen.extend(parse(e.text) for e in box.entries()
                     if not isinstance(e, MenuLine) and box.enabled(e))
        a.shell.remove(box)

    from navml.widgets.dialog.control.control import parse_shortcut
    from navml.widgets.menu.menu_line import MenuLine

    def parse(text):
        return parse_shortcut(text)[0]

    run_app(app, [probe])
    assert seen == ["View", "Edit", "Make directory", "Exit"]


def test_a_nested_menu_shades_the_box_it_opened_from(tree):
    # Options > Configuration opens inside the Options box, and its shadow
    # falls on it -- which it only does if each box is painted over its own
    # shadow in turn, as Turbo Vision drew them.
    from navml.widgets.menu.menu_bar.menu_session import SHADOW

    app = navigator(tree)
    seen = []

    def look(a):
        buffer = desktop(a)
        parent, nested = a.modal.boxes
        x, y = nested.x + nested.width, nested.y + 1
        seen.append((parent.contains(x, y), buffer.get(x, y)[1] == SHADOW))

    run_app(app, [KeyEvent("o", "o", alt=True), KeyEvent("right"), look])
    assert seen == [(True, True)]


def test_a_dialog_and_a_window_cast_turbo_visions_shadow(tree, quiet_console):
    # Two columns down the right, one row along the bottom starting two in --
    # and the file manager, zoomed, casts one that the desktop clips away.
    from navkit.style import SHADOW

    app = navigator(tree)
    seen = []

    def look(a):
        buffer = desktop(a)
        d = a.modal
        right = [buffer.get(d.x + d.width + dx, d.y + 1)[1] for dx in (0, 1)]
        bottom = [buffer.get(d.x + x, d.y + d.height)[1] for x in (1, 2)]
        seen.append((right == [SHADOW, SHADOW], bottom[0] != SHADOW, bottom[1] == SHADOW))

    run_app(app, [KeyEvent("f7"), lambda a: None, look])
    assert seen == [(True, True, True)]
    assert app.manager.shadow and app.manager.zoomed


def test_every_menu_has_an_id_a_plugin_can_reach_it_by(tree):
    from navml.widgets.menu.sub_menu import SubMenu

    menu = navigator(tree).shell.menu
    ids = ["system", "file", "file_view", "file_edit", "disk", "utilities",
           "manager", "options", "options_configuration",
           "options_file_manager", "options_archives", "window"]
    assert all(isinstance(getattr(menu, name), SubMenu) for name in ids)
    # Panel is the file manager's own, reached through the window.
    assert not hasattr(menu, "panel")
    assert isinstance(menu.parent.manager.panel_menu, SubMenu)
    assert menu.file_view.parent is menu.file
    # And the one-line way in for a plugin.
    menu.file.add_item("~Z~ip...", key="Alt-Z", after="Make directory")
    assert menu.file.entries()[menu.file.entries().index(
        menu.file.entry("Make directory")) + 1].text == "~Z~ip..."


# -- Manager > New (Ctrl+F3) ----------------------------------------------------------------


def managers(app):
    return [w for w in app.shell.desktop.windows() if isinstance(w, Manager)]


def test_ctrl_f3_opens_another_file_manager_where_the_active_panel_is(tree):
    app = navigator(tree)
    seen = []
    run_app(app, [
        KeyEvent("down"), KeyEvent("enter"),              # left panel into alpha
        KeyEvent("f3", ctrl=True),
        lambda a: seen.append(a.shell.desktop.active_window),
    ])
    first, second = managers(app)
    assert seen == [second] and first is app.manager
    assert second.zoomed
    assert second.left.path == second.right.path == tree / "alpha"
    assert second._holds(app.focused)


def test_ctrl_f3_from_the_console_with_no_file_manager_left(tree, quiet_console):
    app = navigator(tree)
    run_app(app, [
        KeyEvent("f4", ctrl=True), lambda a: None,        # close the only one
        KeyEvent("f3", ctrl=True), lambda a: None,
    ])
    assert app.manager.parent is None
    (only,) = managers(app)
    assert app.shell.console_visible is False
    assert only._holds(app.focused)


def test_a_tree_window_opened_behind_the_console_brings_the_desktop_back(tree, quiet_console):
    # Opening a window is what shows it: the desktop announces the opening and
    # the shell hides the console, so no command has to remember to.
    from navigator.widgets.shell.commands import OpenTreeWindow
    from navigator.widgets.tree.tree_window import TreeWindow

    for hide in (KeyEvent("o", ctrl=True), KeyEvent("f4", ctrl=True)):  # Ctrl+O, or close the last window
        app = navigator(tree)
        run_app(app, [
            hide, lambda a: None,
            lambda a: a.spawn(a.run_command(OpenTreeWindow)), lambda a: None,
        ])
        window = app.shell.desktop.active_window
        assert isinstance(window, TreeWindow)
        assert app.shell.console_visible is False
        assert window._holds(app.focused)


def test_the_tree_window_steers_the_file_manager_in_front(tree):
    from navigator.widgets.shell.commands import OpenTreeWindow

    app = navigator(tree)
    run_app(app, [
        KeyEvent("f3", ctrl=True), lambda a: None,
        lambda a: a.spawn(a.run_command(OpenTreeWindow)), lambda a: None,
        KeyEvent("+", "+"), KeyEvent("down"), KeyEvent("enter"),
    ])
    first, second = managers(app)
    assert second.left.path == (tree / "alpha").resolve()
    assert first.left.path == tree


def test_the_new_entry_is_ctrl_f3_and_is_enabled(tree):
    from navml.widgets.menu.menu_box.menu_box import key_caption

    app = navigator(tree)
    seen = []

    def look(a):
        item = _entry(a.shell.menu, "Manager", "New")
        seen.append((key_caption(item, a, a.manager.left),
                     a.command_enabled(item.command, a.manager.left)))

    run_app(app, [look])
    assert seen == [("Ctrl-F3", True)]


# -- the command line ----------------------------------------------------------


def typed(text: str) -> list[KeyEvent]:
    return [KeyEvent(c, c) for c in text]


def test_the_command_line_sits_above_the_key_bar_with_the_panel_s_prompt(tree, quiet_console):
    app = navigator(tree)
    run_app(app, [*typed("ls"), lambda a: None])
    buffer = desktop(app)
    assert row_of(buffer, 22).rstrip() == f"{app.shell.command_line.shown_prompt}ls"
    assert "F1" in row_of(buffer, 23)


def test_the_prompt_follows_the_active_panel(tree, quiet_console):
    app = navigator(tree)
    seen = []
    run_app(app, [
        lambda a: seen.append(a.shell.command_prompt),
        lambda a: setattr(a.manager.right, "path", tree / "alpha"),
        KeyEvent("tab"),
        lambda a: seen.append(a.shell.command_prompt),
    ])
    assert seen == [f"{tree}>", f"{tree / 'alpha'}>"]


def shell_prompt(app, cwd, data=b"\x1b[32mme\x1b[0m$ "):
    """Pretend the shell printed *data* as its prompt, in *cwd*."""
    app.shell.console._prompted(data, cwd)
    settle()


def test_the_shell_s_own_prompt_is_painted_with_its_colours(tree, quiet_console):
    app = navigator(tree)
    run_app(app, [*typed("ls"), lambda a: shell_prompt(a, tree)])
    buffer = desktop(app)
    assert row_of(buffer, 22).rstrip() == "me$ ls"
    assert buffer.get(0, 22)[1].fg == 2
    # What the shell left uncoloured is the line's own colour, not the terminal's.
    assert buffer.get(2, 22)[1].fg == app.shell.command_line.style.fg
    assert app.shell.command_line.cursor_position() == (len("me$ ls"), 0)


def test_a_prompt_printed_in_another_directory_is_not_shown(tree, quiet_console):
    app = navigator(tree)
    run_app(app, [
        lambda a: shell_prompt(a, tree),
        lambda a: setattr(a.manager.right, "path", tree / "alpha"),
        KeyEvent("tab"),
    ])
    # The shell has not caught up with the panel yet: DOS Navigator's prompt
    # stands in until it does.
    assert app.shell.command_line.prompt_cells == ()
    assert app.shell.command_line.prompt == f"{tree / 'alpha'}>"
    assert row_of(desktop(app), 22).startswith(app.shell.command_line.shown_prompt)
    shell_prompt(app, tree / "alpha")
    assert row_of(desktop(app), 22).startswith("me$ ")


def test_the_last_prompt_stays_while_the_shell_follows_the_panel(tree, quiet_console, monkeypatch):
    from navigator.subshell import Subshell
    catching_up = [True]
    monkeypatch.setattr(Subshell, "catching_up", property(lambda self: catching_up[0]))
    app = navigator(tree)
    seen = []
    run_app(app, [
        lambda a: shell_prompt(a, tree, b"old$ "),
        lambda a: setattr(a.manager.right, "path", tree / "alpha"),
        KeyEvent("tab"),
        # The silent cd is on its way: no <dir>> flashes up before its prompt.
        lambda a: seen.append(row_of(desktop(a), 22).rstrip()),
        lambda a: (catching_up.__setitem__(0, False), shell_prompt(a, tree / "alpha", b"new$ ")),
        lambda a: seen.append(row_of(desktop(a), 22).rstrip()),
        # A cd that failed prints its prompt where the shell already was.
        lambda a: setattr(a.manager.right, "path", tree),
        lambda a: shell_prompt(a, tree / "alpha", b"new$ "),
        lambda a: seen.append(a.shell.command_line.prompt_cells),
    ])
    assert seen == ["old$", "new$", ()]


def test_the_idle_shell_follows_the_active_panel(tree, quiet_console, monkeypatch):
    asked = []
    monkeypatch.setattr("navigator.subshell.Subshell.sync",
                        lambda self, cwd: asked.append(cwd))
    app = navigator(tree)
    run_app(app, [
        lambda a: setattr(a.manager.right, "path", tree / "alpha"),
        KeyEvent("tab"),
    ])
    assert asked[0] == tree
    assert asked[-1] == tree / "alpha"


def test_printable_keys_on_a_panel_are_typed_on_the_command_line(tree, quiet_console):
    app = navigator(tree)
    run_app(app, [*typed("lsx"), KeyEvent("backspace"), KeyEvent("left"),
                  KeyEvent("space", " ")])
    assert app.shell.command_line.value == "l s"
    assert app.manager.left.cursor == 0


def test_enter_on_an_empty_line_is_still_the_panel_s(tree, quiet_console):
    app = navigator(tree)
    run_app(app, [KeyEvent("down"), KeyEvent("enter"), lambda a: None])
    assert app.manager.left.path == tree / "alpha"
    assert app.shell.console_visible is False


def test_home_and_end_are_the_line_s_only_while_it_has_text(tree, quiet_console):
    app = navigator(tree)
    line = app.shell.command_line
    seen = []
    run_app(app, [
        KeyEvent("end"),
        lambda a: seen.append(a.manager.left.cursor > 0),
        KeyEvent("home"),
        *typed("abc"),
        KeyEvent("home"),
        lambda a: seen.append((line.cursor, a.manager.left.cursor)),
        KeyEvent("end"),
        lambda a: seen.append((line.cursor, a.manager.left.cursor)),
    ])
    assert seen == [True, (0, 0), (3, 0)]


def test_escape_clears_the_line(tree, quiet_console):
    app = navigator(tree)
    run_app(app, [*typed("rm -rf"), KeyEvent("escape")])
    assert app.shell.command_line.value == ""


def test_enter_runs_the_line_and_the_panels_come_back(tree, quiet_console):
    app = navigator(tree)
    ran = []
    app.shell.console.run = lambda command, cwd: ran.append((command, cwd))
    seen = []
    run_app(app, [
        lambda a: a.manager.right.focus(),
        *typed("make"),
        KeyEvent("enter"),
        lambda a: seen.append((a.shell.console_visible, a.focused is a.shell.console,
                               a.shell.command_line.value)),
        lambda a: a.shell.command_finished(0, tree),
        lambda a: None,
    ])
    assert ran == [("make", tree)]
    assert seen == [(True, True, "")]
    assert app.shell.console_visible is False
    assert app.focused is app.manager.right


def test_a_cd_in_the_shell_moves_the_active_panel(tree, quiet_console):
    app = navigator(tree)
    app.shell.console.run = lambda command, cwd: None
    run_app(app, [*typed("cd alpha"), KeyEvent("enter"),
                  lambda a: a.shell.command_finished(0, tree / "alpha"),
                  lambda a: None])
    assert app.manager.left.path == tree / "alpha"


def test_a_command_run_from_ctrl_o_leaves_the_console_up(tree, quiet_console):
    app = navigator(tree)
    app.shell.console.run = lambda command, cwd: None
    run_app(app, [KeyEvent("o", ctrl=True), *typed("ls"), KeyEvent("enter"),
                  lambda a: a.shell.command_finished(0, tree), lambda a: None])
    assert app.shell.console_visible is True
    assert app.focused is app.shell.console


def test_ctrl_e_and_ctrl_x_walk_the_command_history(tree, quiet_console):
    from navml.history import HISTORY

    HISTORY.clear("command")
    app = navigator(tree)
    app.shell.console.run = lambda command, cwd: None
    line = app.shell.command_line
    seen = []
    record = lambda a: seen.append(line.value)
    run_app(app, [
        *typed("one"), KeyEvent("enter"), lambda a: a.shell.command_finished(0, tree),
        *typed("two"), KeyEvent("enter"), lambda a: a.shell.command_finished(0, tree),
        KeyEvent("e", ctrl=True), record,
        KeyEvent("e", ctrl=True), record,
        KeyEvent("e", ctrl=True), record,     # no older one: stays
        KeyEvent("x", ctrl=True), record,
        KeyEvent("x", ctrl=True), record,     # past the newest: the empty line
    ])
    HISTORY.clear("command")
    assert seen == ["two", "one", "one", "two", ""]


def test_a_paste_lands_on_the_command_line(tree, quiet_console):
    from navkit.events import PasteEvent

    app = navigator(tree)
    run_app(app, [PasteEvent("echo a\nb")])
    assert app.shell.command_line.value == "echo a b"


def test_a_real_cd_moves_the_panel(tree, monkeypatch):
    monkeypatch.setenv("SHELL", "/bin/sh")
    app = navigator(tree)
    run_app(app, [*typed("cd alpha"), KeyEvent("enter")] + [lambda a: None] * 6,
            settle=0.3, timeout=20)
    assert app.manager.left.path == tree / "alpha"
    assert app.shell.console_visible is False


# -- a full-screen program on the console ------------------------------------------


@pytest.fixture
def program(monkeypatch, quiet_console):
    """A command running on the console, whose input is collected rather than sent."""
    from navigator.subshell import Subshell

    typed: list[bytes] = []
    monkeypatch.setattr(Subshell, "is_running", property(lambda self: True))
    monkeypatch.setattr(Subshell, "write", lambda self, data: typed.append(data))

    def start(app, output: bytes = b""):
        running(app)
        app.shell.toggle_console()
        app.shell.console.screen.feed(output)

    return typed, start


def test_f10_and_the_command_line_keys_are_the_program_s_while_it_runs(tree, program):
    # F10 is how htop and mc are left; Navigator's menu must not take it.
    typed, start = program
    app = navigator(tree)

    def begin(a):
        a.shell.command_line.set_text("half-typed")
        start(a)

    run_app(app, [begin, KeyEvent("f10"), KeyEvent("enter"), KeyEvent("home"),
                  KeyEvent("f3", ctrl=True), lambda a: None])
    assert typed == [b"\x1b[21~", b"\r", b"\x1b[H", b"\x1b[1;5R"]
    assert app.modal is None                           # no menu dropped
    assert len(app.shell.desktop.windows()) == 1       # no second manager
    assert app.shell.command_line.value == "half-typed"


def test_arrows_follow_the_program_s_cursor_mode(tree, program):
    typed, start = program
    app = navigator(tree)
    run_app(app, [lambda a: start(a, b"\x1b[?1h"), KeyEvent("up")])
    assert typed == [b"\x1bOA"]


def test_the_mouse_goes_to_a_program_that_asked_for_it(tree, program):
    typed, start = program
    app = navigator(tree)
    run_app(app, [
        lambda a: start(a, b"\x1b[?1000h\x1b[?1006h"),
        MouseClickEvent(x=9, y=9, button="left", action="press"),
        MouseClickEvent(x=9, y=9, button="wheel_up", action="press"),
    ])
    # One row down: the console starts under the menu bar.
    assert typed == [b"\x1b[<0;10;9M", b"\x1b[<64;10;9M"]
    assert not app.shell.console.screen.scrolled_back


def test_ctrl_o_is_the_program_s_too(tree, program):
    # mc's own panel toggle, nano's Write Out: nothing is kept back.
    typed, start = program
    app = navigator(tree)
    run_app(app, [start, KeyEvent("o", ctrl=True), KeyEvent("x", "x", alt=True),
                  lambda a: None])
    assert typed == [b"\x0f", b"\x1bx"]
    assert app.shell.console_visible is True
    assert app.focused is app.shell.console


# -- the console's selection ---------------------------------------------------


def console_with(app, text: bytes):
    console = app.shell.console
    app.shell.layout(80, 24)
    settle()  # the console's size first: pyte drops rows when it shrinks
    console.screen.feed(text)
    console._changed()
    settle()
    return console


def drag(console, start, end):
    (sx, sy), (ex, ey) = start, end
    awaited(console.on_mouse_click(MouseClickEvent(sx, sy, "left", "press")))
    awaited(console.on_mouse_click(MouseClickEvent(ex, ey, "left", "move")))
    awaited(console.on_mouse_click(MouseClickEvent(ex, ey, "left", "release")))


def test_a_drag_over_the_console_selects_and_copies_its_text(tree, quiet_console):
    app = navigator(tree)
    console = console_with(app, b"first line\r\nsecond line")
    drag(console, (6, 0), (5, 1))
    assert console.selected_text == "line\nsecond"
    assert app.terminal.clipboard == [("line\nsecond", True)]
    # Shown reversed, as a terminal shows its own.
    buffer = ScreenBuffer(80, 24)
    console.render(buffer)
    assert buffer.get(6, 0)[1].reverse and not buffer.get(5, 0)[1].reverse


def test_ctrl_insert_copies_the_console_s_selection_before_the_command_line(tree, quiet_console):
    app = navigator(tree)
    console = console_with(app, b"some output")
    drag(console, (0, 0), (3, 0))
    app.terminal.clipboard.clear()
    awaited(app.shell.on_key(KeyEvent("insert", ctrl=True)))
    assert app.terminal.clipboard == [("some", False)]


def test_a_double_click_selects_a_word_of_output(tree, quiet_console):
    app = navigator(tree)
    console = console_with(app, b"ls -la /etc/hosts done")
    awaited(console.on_double_click(DoubleClickEvent.of(MouseClickEvent(9, 0, "left", "press"))))
    assert console.selected_text == "/etc/hosts"


def test_new_output_clears_the_selection(tree, quiet_console):
    app = navigator(tree)
    console = console_with(app, b"old")
    drag(console, (0, 0), (2, 0))
    console._on_output(b" new")
    assert console.selection is None


def test_a_program_that_tracks_the_mouse_keeps_it(tree, quiet_console, monkeypatch):
    app = navigator(tree)
    console = console_with(app, b"text")
    monkeypatch.setattr(type(console), "tracks_mouse", property(lambda self: True))
    monkeypatch.setattr("navigator.subshell.Subshell.is_running", property(lambda self: True))
    monkeypatch.setattr("navigator.subshell.Subshell.write", lambda self, data: None)
    drag(console, (0, 0), (3, 0))
    assert console.selection is None


# -- Tab completion ------------------------------------------------------------


@pytest.fixture
def completing(monkeypatch):
    """A shell that is running, can complete, and answers with *answer*."""
    asked = []

    class Answer:
        start = 0
        candidates: list[str] = []

    def complete(self, line, point, cwd, callback):
        asked.append((line, point, cwd))
        word = line[Answer.start : point]
        callback(Answer.start, [c for c in Answer.candidates if c.startswith(word)])
        return True

    monkeypatch.setattr("navigator.subshell.Subshell.is_running", property(lambda self: True))
    monkeypatch.setattr("navigator.subshell.Subshell.complete", complete)
    real_init = Subshell.__init__

    def init(self, *args, **kwargs):
        real_init(self, *args, **kwargs)
        self.can_complete = True

    monkeypatch.setattr(Subshell, "__init__", init)
    monkeypatch.setattr("navigator.subshell.Subshell.sync", lambda self, cwd: None)
    Answer.asked = asked
    return Answer


from navigator.subshell import Subshell  # noqa: E402


def test_tab_on_an_empty_line_still_switches_panels(tree, quiet_console, completing):
    app = navigator(tree)
    run_app(app, [KeyEvent("tab")])
    assert app.manager.active_panel is app.manager.right
    assert completing.asked == []


def test_tab_completes_the_only_candidate_and_ends_the_word(tree, quiet_console, completing):
    completing.start, completing.candidates = 0, ["echo"]
    app = navigator(tree)
    run_app(app, [*typed("ech"), KeyEvent("tab")])
    assert completing.asked == [("ech", 3, tree)]
    assert app.shell.command_line.value == "echo "
    assert app.manager.active_panel is app.manager.left


def test_a_directory_ends_in_a_slash(tree, quiet_console, completing):
    completing.start, completing.candidates = 3, ["alpha"]
    app = navigator(tree)
    run_app(app, [*typed("ls al"), KeyEvent("tab")])
    assert app.shell.command_line.value == "ls alpha/"


def test_a_name_the_shell_would_split_is_escaped(tree, quiet_console, completing):
    (tree / "my file").write_text("")
    completing.start, completing.candidates = 3, ["my file"]
    app = navigator(tree)
    run_app(app, [*typed("ls my"), KeyEvent("tab")])
    assert app.shell.command_line.value == "ls my\\ file "


def test_candidates_that_agree_extend_the_word(tree, quiet_console, completing):
    completing.start, completing.candidates = 4, ["checkout ", "cherry ", "cherry-pick "]
    app = navigator(tree)
    run_app(app, [*typed("git ch"), KeyEvent("tab")])
    assert app.shell.command_line.value == "git che"


def test_candidates_that_do_not_agree_are_listed(tree, quiet_console, completing):
    from navigator.widgets.shell.completion_list import CompletionList

    completing.start, completing.candidates = 3, ["alpha", "beta"]
    app = navigator(tree)
    lists = []
    run_app(app, [
        *typed("ls "), KeyEvent("tab"),
        lambda a: lists.append(a.modal),
        KeyEvent("down"), KeyEvent("enter"),
    ])
    assert isinstance(lists[0], CompletionList)
    assert app.shell.command_line.value == "ls beta/"
    assert app.modal is None


def test_an_answer_to_a_line_that_moved_on_is_dropped(tree, quiet_console):
    from navigator.subshell import CompletionsReady

    app = navigator(tree)
    run_app(app, [*typed("ls x")])
    app.shell.completions_ready(CompletionsReady("ls ", 3, 3, ("alpha",)))
    assert app.shell.command_line.value == "ls x"


def test_typing_with_the_list_open_narrows_it_and_edits_the_line(tree, quiet_console, completing):
    completing.start, completing.candidates = 3, ["alpha", "apple", "beta"]
    app = navigator(tree)
    seen = []
    run_app(app, [
        *typed("ls "), KeyEvent("tab"),
        *typed("a"), lambda a: seen.append((a.shell.command_line.value, list(a.modal.items))),
        *typed("l"), lambda a: seen.append((a.shell.command_line.value, list(a.modal.items))),
        KeyEvent("backspace"), lambda a: seen.append(list(a.modal.items)),
        KeyEvent("enter"),
    ])
    assert seen == [
        ("ls a", ["alpha", "apple"]),
        ("ls al", ["alpha"]),        # one left, and still a list: typing is not choosing
        ["alpha", "apple"],
    ]
    assert app.shell.command_line.value == "ls alpha/"
    assert app.modal is None


def test_a_blank_or_backspacing_past_the_word_closes_the_list(tree, quiet_console, completing):
    completing.start, completing.candidates = 3, ["alpha", "beta"]
    app = navigator(tree)
    modals = []
    run_app(app, [
        *typed("ls "), KeyEvent("tab"), *typed(" "),
        lambda a: modals.append(a.modal),
    ])
    assert modals == [None]
    assert app.shell.command_line.value == "ls  "


def test_typing_what_nothing_starts_with_closes_the_list(tree, quiet_console, completing):
    completing.start, completing.candidates = 3, ["alpha", "beta"]
    app = navigator(tree)
    modals = []
    run_app(app, [*typed("ls "), KeyEvent("tab"), *typed("z"), lambda a: modals.append(a.modal)])
    assert modals == [None]
    assert app.shell.command_line.value == "ls z"


def test_the_completion_list_does_not_dim_the_line_being_typed(tree, quiet_console, completing):
    from navigator.widgets.shell.completion_list import CompletionList

    assert CompletionList.dims_behind is False


# -- Up, Down and Ctrl+R on the console ------------------------------------------


@pytest.fixture
def shell_history(monkeypatch):
    """A running shell whose history is *entries* and whose searches are recorded."""

    class State:
        entries = ["echo second", "echo first"]
        searches: list[tuple[str, list[str]]] = []
        up_binding = None
        search_binding = None

    def history(self, callback):
        callback(list(State.entries))
        return True

    def search_history(self, line, args, callback):
        State.searches.append((line, args))
        return True

    real_init = Subshell.__init__

    def init(self, *args, **kwargs):
        real_init(self, *args, **kwargs)
        self.can_complete = True
        self.up_binding, self.search_binding = State.up_binding, State.search_binding

    monkeypatch.setattr(Subshell, "__init__", init)
    monkeypatch.setattr("navigator.subshell.Subshell.is_running", property(lambda self: True))
    monkeypatch.setattr("navigator.subshell.Subshell.history", history)
    monkeypatch.setattr("navigator.subshell.Subshell.search_history", search_history)
    monkeypatch.setattr("navigator.subshell.Subshell.sync", lambda self, cwd: None)
    State.searches = []
    return State


def test_up_and_down_on_the_console_walk_the_shell_s_history(tree, quiet_console, shell_history):
    app = navigator(tree)
    seen = []
    note = lambda a: seen.append(a.shell.command_line.value)
    run_app(app, [
        KeyEvent("o", ctrl=True), *typed("ec"),
        KeyEvent("up"), note, KeyEvent("up"), note, KeyEvent("up"), note,
        KeyEvent("down"), note, KeyEvent("down"), note,
    ])
    assert seen == ["echo second", "echo first", "echo first", "echo second", "ec"]


def test_up_with_the_panels_up_is_still_the_panel_s(tree, quiet_console, shell_history):
    app = navigator(tree)
    run_app(app, [KeyEvent("down"), KeyEvent("up")])
    assert app.manager.left.cursor == 0
    assert app.shell.command_line.value == ""


def test_up_runs_atuin_where_the_user_s_up_does(tree, quiet_console, shell_history):
    shell_history.up_binding = shell_history.search_binding = "atuin"
    app = navigator(tree)
    run_app(app, [
        KeyEvent("o", ctrl=True), *typed("gi"), KeyEvent("up"), KeyEvent("r", ctrl=True),
    ])
    assert shell_history.searches == [
        ("gi", ["--shell-up-key-binding", "--keymap-mode=emacs"]),
        ("gi", ["--keymap-mode=emacs"]),
    ]


def test_ctrl_r_on_the_console_is_nothing_without_atuin(tree, quiet_console, shell_history):
    app = navigator(tree)
    run_app(app, [KeyEvent("o", ctrl=True), KeyEvent("r", ctrl=True)])
    assert shell_history.searches == []


def test_what_atuin_chose_goes_on_the_line_or_runs(tree, quiet_console, monkeypatch):
    app = navigator(tree)
    ran = []
    monkeypatch.setattr(app.shell, "run_command", ran.append)
    app.shell.history_chosen("git status")
    assert app.shell.command_line.value == "git status"
    app.shell.history_chosen("__atuin_accept__:make test")
    assert ran == ["make test"]
    app.shell.command_line.clear()
    app.shell.history_chosen("")  # cancelled
    assert app.shell.command_line.value == ""


def test_the_console_keeps_the_panel_that_was_active(tree, quiet_console, monkeypatch):
    # Right panel active, then Ctrl+O: the console has the keyboard now, and
    # a command still runs where the right panel is -- not back in the left.
    synced = []
    monkeypatch.setattr("navigator.subshell.Subshell.sync", lambda self, cwd: synced.append(cwd))
    app = Navigator(tree, tree / "alpha", terminal=FakeTerminal(80, 24))
    seen = []
    run_app(app, [
        KeyEvent("tab"),
        KeyEvent("o", ctrl=True),
        lambda a: seen.append((a.shell._command_directory(), a.shell.command_prompt,
                               a.manager.active_panel is a.manager.right)),
        KeyEvent("o", ctrl=True),
        lambda a: seen.append(a.manager.right.focused),
    ])
    assert seen[0] == (tree / "alpha", f"{tree / 'alpha'}>", True)
    assert synced[-1] == tree / "alpha"
    # And Ctrl+O again hands the keyboard back to the right panel.
    assert seen[1] is True


def test_a_dialog_does_not_move_the_active_panel(tree, quiet_console):
    app = Navigator(tree, tree / "alpha", terminal=FakeTerminal(80, 24))
    seen = []
    run_app(app, [
        KeyEvent("tab"),
        lambda a: a.manager.right.focused and a.shell.console.focus(),  # focus elsewhere
        lambda a: seen.append(a.manager.active_panel is a.manager.right),
    ])
    assert seen == [True]


# -- running a file, and putting its name on the command line --------------------


def on_entry(app, name):
    panel = app.manager.left
    panel.cursor = next(i for i, e in enumerate(panel.items) if e.name == name)


@pytest.fixture
def runnable(tree):
    script = tree / "run me.sh"
    script.write_text("#!/bin/sh\necho ran\n")
    script.chmod(0o755)
    return tree


def test_enter_on_an_executable_runs_it(runnable, quiet_console, monkeypatch):
    app = navigator(runnable)
    ran = []
    monkeypatch.setattr(app.shell, "run_command", ran.append)
    run_app(app, [lambda a: on_entry(a, "run me.sh"), KeyEvent("enter")])
    assert ran == ["./run\\ me.sh"]


def test_enter_on_a_plain_file_runs_nothing(tree, quiet_console, monkeypatch):
    app = navigator(tree)
    ran = []
    monkeypatch.setattr(app.shell, "run_command", ran.append)
    run_app(app, [lambda a: on_entry(a, "one.txt"), KeyEvent("enter")])
    assert ran == [] and app.manager.left.path == tree


@pytest.mark.parametrize("key", [KeyEvent("enter", ctrl=True), KeyEvent("enter", alt=True)])
def test_ctrl_enter_puts_the_name_on_the_command_line(runnable, quiet_console, key):
    app = navigator(runnable)
    run_app(app, [
        *typed("cat"), lambda a: on_entry(a, "one.txt"), key,
        lambda a: on_entry(a, "run me.sh"), key,
    ])
    # A space before the first, because the caret was after a word; one after
    # each, so the next can follow; and the blank in a name escaped.
    assert app.shell.command_line.value == "cat one.txt run\\ me.sh "


def test_ctrl_enter_on_dot_dot_is_the_directory_itself(tree, quiet_console):
    app = navigator(tree / "alpha")
    run_app(app, [lambda a: on_entry(a, ".."), KeyEvent("enter", ctrl=True)])
    assert app.shell.command_line.value == f"{tree / 'alpha'}/"


def test_ctrl_shift_enter_puts_the_whole_path(tree, quiet_console):
    app = navigator(tree)
    run_app(app, [lambda a: on_entry(a, "one.txt"), KeyEvent("enter", ctrl=True, shift=True)])
    assert app.shell.command_line.value == f"{tree / 'one.txt'} "


def test_a_ctrl_double_click_is_ctrl_enter(tree, quiet_console):
    app = navigator(tree)
    app.shell.layout(80, 24)
    settle()
    panel = app.manager.left
    row = next(i for i, e in enumerate(panel.items) if e.name == "one.txt")
    run_app(app, [
        lambda a: setattr(panel, "cursor", row),
        lambda a: awaited_inline(a, panel, row),
    ])
    assert app.shell.command_line.value == "one.txt "


def awaited_inline(app, panel, row):
    y = row - panel.scroll + panel.inset
    app.post_event(DoubleClickEvent.of(MouseClickEvent(
        panel.offset()[0] + panel.x + 2, panel.offset()[1] + panel.y + y, "left", "press", ctrl=True)))


def test_running_as_root_marks_every_title_dark_red(tree, monkeypatch):
    monkeypatch.setattr("os.geteuid", lambda: 0)
    app = navigator(tree)
    shell = app.shell
    assert "root" in shell.classes
    title = shell.manager.part_style("title")
    assert (title.fg, title.bg) == (15, 1)
    manager = shell.manager
    active = manager.active_panel
    passive = manager.right if active is manager.left else manager.left
    assert active.focused
    title = active.part_style("title")
    assert (title.fg, title.bg) == (15, 1)
    assert passive.part_style("title").bg != 1
    dialog = MkdirDialog()
    app.overlay(dialog)
    title = dialog.part_style("title")
    assert (title.fg, title.bg) == (15, 1)


def test_an_ordinary_user_s_titles_are_the_theme_s(tree, monkeypatch):
    monkeypatch.setattr("os.geteuid", lambda: 1000)
    app = navigator(tree)
    assert "root" not in app.shell.classes
    assert app.shell.manager.part_style("title").bg != 1


# -- Panel is the file manager's own menu ---------------------------------------------------


def test_panel_is_on_the_bar_only_while_a_file_manager_is_active(tree):
    from navml.widgets.dialog.control.control import parse_shortcut
    from navigator.widgets.shell.commands import NewManager

    (tree / "note.txt").write_text("hello\n")
    app = navigator(tree)
    seen = []

    def bar(a):
        seen.append([parse_shortcut(e.text)[0] for e in a.shell.menu.entries()])

    def new_enabled(a):
        seen.append(a.command_enabled(NewManager, a.focused))

    run_app(app, [
        bar,
        KeyEvent("end"), KeyEvent("f3"), lambda a: None, bar,     # a viewer
        KeyEvent("escape"), lambda a: None,
        lambda a: a.shell.desktop.close_window(a.manager), lambda a: None,
        bar, new_enabled,                                          # an empty desktop
    ])
    assert seen[0] == ["≡", "File", "Disk", "Utilities", "Panel", "Manager",
                       "Options", "Window"]
    assert seen[1] == ["≡", "File", "View", "Disk", "Utilities", "Manager",
                       "Options", "Window"]
    assert seen[2] == ["≡", "File", "Disk", "Utilities", "Manager", "Options", "Window"]
    assert seen[3] is True


def test_the_panel_menu_holds_the_tree_info_and_quick_view_and_manager_does_not(tree):
    app = navigator(tree)
    seen = {}

    def look(a):
        from navml.widgets.dialog.control.control import parse_shortcut

        names = lambda m: [parse_shortcut(getattr(e, "text", ""))[0]    # noqa: E731
                           for e in _entry(a.shell.menu, m).entries()]
        seen["panel"], seen["manager"] = names("Panel"), names("Manager")

    run_app(app, [look,
                  KeyEvent("p", "p", alt=True), KeyEvent("y", "y"), lambda a: None,
                  lambda a: seen.update(tree=a.manager.tree.visible)])
    for caption in ("Directory tree", "Info", "Quick view"):
        assert caption in seen["panel"] and caption not in seen["manager"]
    assert seen["manager"][0] == "New"
    # Alt+P, then the entry's letter: the menu runs Ctrl+T's command.
    assert seen["tree"] is True
