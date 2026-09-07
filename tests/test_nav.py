"""The file manager itself: panel model, layout and key handling."""

from __future__ import annotations

import time
from dataclasses import replace
from importlib import metadata
from pathlib import Path

import pytest

from navkit.capabilities import FULL
from navkit.events import KeyEvent, MouseEvent
from navkit.glyphs import GLYPHS_ASCII, GLYPHS_NERD, GLYPHS_UNICODE
from navkit.screen import ScreenBuffer, char_width
from navkit.terminal import encode_key

from conftest import FakeTerminal, run_app, settle
from navigator import icons
from navigator import __version__
from navigator.__main__ import (
    SCHEME,
    THEMES,
    DirEntry,
    Manager,
    Navigator,
    Panel,
    load_scheme,
    main,
    theme_names,
    version_banner,
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


# -- the console and Ctrl+O -------------------------------------------------


@pytest.fixture
def quiet_console(monkeypatch):
    """Stop the console forking a shell.

    Most of what Ctrl+O does has nothing to do with the child: it is which
    widgets paint, and that is worth testing without a process in the way.
    ``test_the_console_runs_a_real_child`` covers the other half.
    """
    monkeypatch.setattr(
        "navigator.__main__.Console.start", lambda self, argv=None: None
    )


def desktop(app, size=(80, 24)) -> ScreenBuffer:
    """Paint the whole desktop and hand back the buffer."""
    buffer = ScreenBuffer(*size)
    app.manager.layout(*size)
    app.manager.render_tree(buffer)
    return buffer


def row_of(buffer: ScreenBuffer, y: int) -> str:
    return "".join(buffer.get(x, y)[0] or " " for x in range(buffer.width))


def test_ctrl_o_shows_the_console_in_place_of_the_panels(tree, quiet_console):
    app = navigator(tree)
    run_app(app, [KeyEvent("o", ctrl=True)])
    manager = app.manager
    assert manager.console_visible is True
    # One flag, three widgets: nothing was made visible by hand.
    assert manager.console.visible is True
    assert manager.left.visible is False
    assert manager.right.visible is False


def test_ctrl_o_toggles_back(tree, quiet_console):
    app = navigator(tree)
    run_app(app, [KeyEvent("o", ctrl=True), KeyEvent("o", ctrl=True)])
    assert app.manager.console_visible is False
    assert app.manager.left.visible is True


def test_the_menu_bar_and_key_bar_stay_over_the_console(tree, quiet_console):
    """The whole point of Ctrl+O, and what Midnight Commander cannot do."""
    app = navigator(tree)
    run_app(app, [KeyEvent("o", ctrl=True),
                  lambda a: a.manager.console._on_output(b"previous output")])
    buffer = desktop(app)
    assert "File" in row_of(buffer, 0)  # the menu bar, still there
    assert "Quit" in row_of(buffer, 23)  # the key bar, still there
    assert "previous output" in row_of(buffer, 1)  # and the output behind them
    # The panels really are gone rather than merely covered.
    assert "╔" not in row_of(buffer, 1)


def test_the_console_is_the_size_of_the_band_the_panels_shared(tree, quiet_console):
    app = navigator(tree)
    run_app(app, [KeyEvent("o", ctrl=True)])
    console = app.manager.console
    assert (console.width, console.height) == (80, 22)
    # And the screen behind it was resized to match, without a layout pass.
    assert (console.screen.columns, console.screen.lines) == (80, 22)


def test_keys_go_to_the_console_while_it_is_showing(tree, quiet_console):
    app = navigator(tree)
    typed: list[bytes] = []
    run_app(app, [
        KeyEvent("o", ctrl=True),
        lambda a: setattr(a.manager.console, "send",
                          lambda event: typed.append(encode_key(event)) or True),
        KeyEvent("down"),
        KeyEvent("x", "x"),
    ])
    assert typed == [b"\x1b[B", b"x"]
    # The panel did not also act on them.
    assert app.manager.left.cursor == 0


def test_quit_still_works_from_the_console(tree, quiet_console):
    app = navigator(tree)
    run_app(app, [KeyEvent("o", ctrl=True), KeyEvent("f10"), KeyEvent("down")])
    assert app.is_running is False


def test_shift_pageup_scrolls_the_console_back(tree, quiet_console):
    app = navigator(tree)
    lines = b"".join(b"line%d\r\n" % n for n in range(60))
    run_app(app, [
        KeyEvent("o", ctrl=True),
        lambda a: a.manager.console._on_output(lines),
        KeyEvent("pageup", shift=True),
    ])
    assert app.manager.console.screen.scrolled_back is True


def test_the_wheel_scrolls_the_console_rather_than_a_panel(tree, quiet_console):
    app = navigator(tree)
    lines = b"".join(b"line%d\r\n" % n for n in range(60))
    run_app(app, [
        KeyEvent("o", ctrl=True),
        lambda a: a.manager.console._on_output(lines),
        MouseEvent(x=10, y=10, button="wheel_up", action="press"),
    ])
    assert app.manager.console.screen.scrolled_back is True
    assert app.manager.left.cursor == 0


def test_the_console_runs_a_real_child(tree):
    """End to end: a program's output really does end up behind the panels."""
    app = navigator(tree)

    def start_child(a):
        # Started before the toggle, so `toggle_console' finds a child already
        # running and does not lay a shell over it.
        a.manager.console.start(["/bin/sh", "-c", "printf 'captured\\r\\n'; sleep 5"])
        a.manager.console_visible = True

    # A generous settle: the driver's awaits are the only chance the loop gets
    # to read from the pty, so the test has to yield rather than sleep.
    run_app(app, [start_child, lambda a: None, lambda a: None], settle=0.3)
    assert "captured" in row_of(desktop(app), 1)


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
    assert plain.manager.left.gutter == 0

    fancy = navigator_with(tree, GLYPHS_NERD)
    run_app(fancy, [])
    assert fancy.manager.left.show_icons
    assert fancy.manager.left.gutter == 2


def test_the_icon_gutter_shifts_the_name_without_touching_the_size_column(tree):
    """Two cells go to the icon; the size column is where it always was."""
    plain = navigator_with(tree, GLYPHS_UNICODE)
    run_app(plain, [])
    without = row_of(desktop(plain), 2)

    fancy = navigator_with(tree, GLYPHS_NERD)
    run_app(fancy, [])
    with_icons = row_of(desktop(fancy), 2)

    # ".." is the first entry either way, and moves right by exactly the gutter.
    assert without.index("..") + 2 == with_icons.index("..")
    # The size column is drawn from the right edge and does not move.
    assert without[-12:] == with_icons[-12:]
    # A name has that much less room, so the two agree on the total width.
    assert fancy.manager.left.name_width == plain.manager.left.name_width


def test_a_sheet_may_refuse_icons_on_a_terminal_that_could_draw_them(tree):
    """``icons: none`` is the escape hatch for strict DOS fidelity."""
    app = navigator_with(tree, GLYPHS_NERD)
    run_app(app, [])
    panel = app.manager.left
    assert panel.show_icons
    panel._stylesheet = load_scheme("default", ("theme.nss", "Panel { icons: none }"))
    settle()
    assert panel.style_property("icons") == "none"
    assert not panel.show_icons
    assert panel.gutter == 0


def test_a_directory_and_a_file_get_different_icons(tree):
    app = navigator_with(tree, GLYPHS_NERD)
    run_app(app, [])
    buffer = desktop(app)
    entries = app.manager.left.entries
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
        (".gitignore", False, icons.FILE),  # a leading dot is not an extension
        ("archive.tar.gz", False, icons.BY_EXTENSION["gz"]),
        ("thing.unheardof", False, icons.FILE),
    ],
)
def test_the_icon_table_reads_a_name(name, is_dir, expected):
    assert icons.icon_for(name, is_dir) == expected


def test_every_icon_is_a_single_cell():
    """The gutter is two columns wide and the second is a space by design.

    A Nerd Font *Mono* build patches its icons to one cell and ``char_width``
    agrees, the Private Use Area measuring as ambiguous.  If one of these ever
    measured two, the name would be shoved along on the Mono build too.
    """
    every = [icons.FOLDER, icons.PARENT, icons.FILE, *icons.BY_EXTENSION.values()]
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
