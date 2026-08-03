"""The file manager itself: panel model, layout and key handling."""

from __future__ import annotations

from pathlib import Path

import pytest

from navkit.events import KeyEvent, MouseEvent
from navkit.screen import ScreenBuffer

from conftest import FakeTerminal, run_app, settle
from navigator.__main__ import (
    SCHEME,
    DirEntry,
    Manager,
    Navigator,
    Panel,
    load_scheme,
    theme_names,
)


def navigator(path, size=(80, 24)) -> Navigator:
    """A Navigator on a fake terminal of *size*, both panels showing *path*."""
    return Navigator(path, path, terminal=FakeTerminal(*size))


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
    widget._stylesheet = SCHEME
    return widget


def names(panel: Panel) -> list[str]:
    return [entry.name for entry in panel.entries]


# A panel's model reacts to what it is told rather than doing it on the spot,
# so a test driving it without a running application has to call ``settle()``
# between acting and asserting -- that is what the event loop does per batch.


def test_listing_puts_parent_first_then_directories(panel):
    assert names(panel) == ["..", "alpha", "beta", "one.txt", "two.txt"]


def test_root_has_no_parent_entry():
    # There is nothing above "/", so it must not offer a ".." entry.
    assert ".." not in names(Panel(Path("/"), width=40, height=20))


def test_unreadable_directory_reports_an_error(tmp_path):
    missing = Panel(tmp_path / "nope", width=40, height=20)
    assert missing.error is not None
    # ".." survives, so the user can still climb back out of a dead end.
    assert names(missing) == [".."]


def test_the_error_is_painted_instead_of_a_listing(tmp_path):
    missing = Panel(tmp_path / "nope", width=40, height=20)
    buffer = ScreenBuffer(40, 20)
    missing.render(buffer)
    painted = "".join(buffer.get(x, 2)[0] for x in range(40))
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
    assert panel.cursor == len(panel.entries) - 1


def test_the_cursor_is_clamped_however_it_was_moved(panel):
    # Not through move_cursor: the invariant belongs to the panel, not to the
    # one method that used to enforce it.
    panel.cursor = 99
    settle()
    assert panel.cursor == len(panel.entries) - 1


def test_a_rescan_puts_the_cursor_back_at_the_top(panel, tree):
    panel.move_cursor(4)
    settle()
    (tree / "gamma").mkdir()
    panel.reload()
    settle()
    assert panel.cursor == 0


def test_cursor_scrolls_the_view(tmp_path):
    for index in range(50):
        (tmp_path / f"file{index:02d}").write_text("")
    panel = Panel(tmp_path, width=40, height=10)
    assert panel.scroll == 0
    panel.move_cursor(len(panel.entries))
    settle()
    assert panel.scroll > 0
    assert panel.scroll <= panel.cursor < panel.scroll + panel.rows
    panel.move_cursor(-len(panel.entries))
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


def test_manager_layout_splits_the_screen():
    manager = Manager(Path("."), Path("."))
    manager.layout(80, 24)
    assert (manager.left.x, manager.left.width) == (0, 40)
    assert (manager.right.x, manager.right.width) == (40, 40)
    assert manager.menu.y == 0
    assert manager.keybar.y == 23
    assert manager.left.height == manager.right.height == 22


def test_manager_layout_survives_an_odd_width():
    manager = Manager(Path("."), Path("."))
    manager.layout(81, 24)
    assert manager.left.width + manager.right.width == 81


def test_the_panels_follow_the_desktop_without_a_layout_method():
    # Manager declares its children's geometry once and has no layout of its
    # own; only the root's size is imperative, and everything else derives.
    assert "layout" not in vars(Manager)
    manager = Manager(Path("."), Path("."))
    manager.layout(80, 24)
    manager.layout(120, 40)
    assert (manager.left.width, manager.right.x) == (60, 60)
    assert manager.keybar.y == 39


def test_the_panel_title_and_footer_follow_the_width(panel, tree):
    wide = panel.title_text
    panel.width = 12
    assert panel.title_text != wide
    assert len(panel.title_text) <= panel.width


def test_the_left_panel_starts_active():
    manager = Manager(Path("."), Path("."))
    assert manager.active_panel is manager.left
    manager.switch_panel()
    assert manager.active_panel is manager.right


def test_panel_renders_its_frame_and_contents(panel):
    panel.active = True
    buffer = ScreenBuffer(40, 20)
    panel.render(buffer)
    top = "".join(buffer.get(x, 0)[0] for x in range(40))
    first = "".join(buffer.get(x, 1)[0] for x in range(40))
    assert top.startswith("╔")  # the active panel wears a double frame
    assert str(panel.path)[-10:] in top or "..." in top
    assert ".." in first


def test_inactive_panel_uses_a_single_frame(panel):
    panel.active = False
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


def test_enter_descends_in_the_active_panel(tree):
    app = navigator(tree)
    run_app(app, [KeyEvent("down"), KeyEvent("enter")])
    assert app.manager.left.path == tree / "alpha"


@pytest.mark.parametrize("quit_key", [KeyEvent("f10"), KeyEvent("q", ctrl=True)])
def test_quit_keys_stop_the_application(tree, quit_key):
    app = navigator(tree)
    run_app(app, [quit_key, KeyEvent("down")])
    assert app.is_running is False
    # The key after the quit was never acted on.
    assert app.manager.left.cursor == 0


def test_unhandled_keys_are_ignored(tree):
    app = navigator(tree)
    run_app(app, [KeyEvent("z", "z")])
    assert app.is_running is False  # exited by the driver, not by the key


def test_clicking_a_row_moves_the_cursor(tree):
    app = navigator(tree)
    run_app(app, [MouseEvent(x=5, y=3, button="left", action="press")])
    # Screen row 3 is the second listing line of the left panel: "alpha".
    assert app.manager.left.selected.name == "alpha"


def test_clicking_the_other_panel_activates_it(tree):
    app = navigator(tree)
    run_app(app, [MouseEvent(x=60, y=3, button="left", action="press")])
    assert app.manager.active_panel is app.manager.right


def test_the_wheel_scrolls_the_panel_under_the_pointer(tmp_path):
    for index in range(30):
        (tmp_path / f"file{index:02d}").write_text("")
    app = navigator(tmp_path)
    run_app(app, [MouseEvent(x=5, y=5, button="wheel_down", action="press")])
    assert app.manager.left.cursor == 3

def test_the_scheme_drives_the_panel_rather_than_decorating_it(panel):
    """Swapping the sheet must change what the panel paints.

    The migration is only real if the render methods read the cascade.  A
    theme that redefines one variable should reach the frame colour without
    touching a single rule.
    """
    from navkit.style import LIGHT_GRAY, RED

    # $panel-fg, out of themes/default.nss: entry 85 of DEFAULT.PAL is $87,
    # light gray on dark gray.
    assert panel.style.fg == LIGHT_GRAY
    # A theme is a further sheet loaded after the others, redefining a variable
    # the rules already use -- no rule here is repeated or overridden.
    panel._stylesheet = load_scheme("default", ("theme.nss", "$panel-fg: red;"))
    assert panel.style.fg == RED

    buffer = ScreenBuffer(40, 20)
    panel.render(buffer)
    assert buffer.get(0, 0)[1].fg == RED  # the frame really is painted in it


def test_the_border_comes_from_the_sheet_not_from_active(panel):
    """``active`` picks the frame only because a rule says so."""
    panel.active = True
    assert panel.style_property("border") == "double"
    panel._stylesheet = load_scheme(
        "default", ("theme.nss", "Panel:active { border: single }")
    )
    assert panel.style_property("border") == "single"
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
        manager = Manager(tree, tree, load_scheme(theme))
        buffer = ScreenBuffer(80, 24)
        manager.layout(80, 24)
        manager.render(buffer)  # raises if a variable went undefined
        assert manager.left.style.fg is not None
        assert manager.left.style.bg is not None


def test_no_theme_asks_for_bold(tree):
    """A DOS attribute has no bold bit: intensity is which of the sixteen.

    Saying `bold' as well would double-brighten on terminals that render it as
    bright, so a theme that acquires one is a transcription mistake.
    """
    for theme in theme_names():
        manager = Manager(tree, tree, load_scheme(theme))
        panel = manager.left
        styles = [
            panel.style,
            panel.part_style("title"),
            panel.part_style("row", classes=("directory",)),
            panel.part_style("row", selected=True),
            manager.menu.style,
            manager.menu.part_style("hotkey"),
            manager.keybar.part_style("number"),
        ]
        assert not any(style.bold for style in styles), theme
