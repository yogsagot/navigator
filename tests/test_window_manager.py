"""Window > List (Alt+0): DOS Navigator's *Windows Manager* dialog."""

from __future__ import annotations

from conftest import run_app
from navkit.events import KeyEvent
from test_nav import _entry, navigator, quiet_console, tree  # noqa: F401 - fixtures

ALT_0 = KeyEvent("0", "0", alt=True)
CTRL_F3 = KeyEvent("f3", ctrl=True)


def managers(app):
    from navigator.widgets.manager import Manager

    return [w for w in app.shell.desktop.windows() if isinstance(w, Manager)]


def run(path, *actions):
    app = navigator(path)
    run_app(app, [*actions, lambda a: None])
    return app


def test_the_dialog_is_laid_out_as_dlgwindowmanager_lays_it_out(tree):
    from navml.widgets.dialog.control.control import parse_shortcut
    from navml.widgets.window_manager import WindowManagerDialog

    dialog = WindowManagerDialog()
    assert (dialog.modal_width, dialog.modal_height, dialog.title) == (70, 14, "Windows Manager")
    assert (dialog.caption.text, dialog.caption.x, dialog.caption.y) == ("~W~indows", 2, 2)
    windows = dialog.windows
    assert (windows.framed, windows.x, windows.y, windows.width, windows.height) == (
        False, 2, 3, 56, 9)
    buttons = dialog.buttons_row
    assert [parse_shortcut(b.text)[0] for b in buttons] == ["OK", "Close", "Cancel", "Help"]
    assert [(b.x, b.y, b.width) for b in buttons] == [(58, y, 10) for y in (3, 5, 7, 11)]
    assert dialog.pick.default and dialog.helper.disabled
    assert dialog.row.visible is False


def test_alt_0_lists_the_windows_top_first_on_the_active_one(tree):
    seen = []

    def look(a):
        dialog = a.modal
        seen.append((type(dialog).__name__, list(dialog.windows.items), dialog.accept(),
                     a.focused is dialog.windows,
                     [dialog.windows.row_text(i, w) for i, w in enumerate(dialog.windows.items)]))

    app = run(tree, KeyEvent("down"), KeyEvent("enter"),   # the first into alpha
              CTRL_F3, lambda a: None, ALT_0, lambda a: None, look)
    first, second = managers(app)
    assert seen == [("WindowManagerDialog", [second, first], second, True,
                     [f" {tree / 'alpha'}", f" {tree / 'alpha'}"])]


def test_a_background_manager_is_named_after_the_panel_it_had(tree):
    # The first manager's right panel had the keyboard, and its left one is
    # somewhere else: the list has to say where the right one is, although
    # the focus is in the dialog and the first manager is behind the second.
    seen = []
    run(tree, KeyEvent("tab"), KeyEvent("down"), KeyEvent("enter"),   # right into alpha
        CTRL_F3, lambda a: None,                                       # both of its panels in alpha
        KeyEvent("enter"), lambda a: None,                             # its left back up, on ..
        ALT_0, lambda a: None,
        lambda a: seen.append([a.modal.windows.row_text(i, w)
                               for i, w in enumerate(a.modal.windows.items)]))
    assert seen == [[f" {tree}", f" {tree / 'alpha'}"]]


def test_enter_switches_to_the_window_under_the_cursor(tree):
    app = run(tree, CTRL_F3, lambda a: None, ALT_0, lambda a: None,
              KeyEvent("down"), KeyEvent("enter"), lambda a: None)
    assert app.modal is None
    assert app.shell.desktop.active_window is app.manager    # brought forward, so now last
    assert managers(app)[-1] is app.manager
    assert app.manager._holds(app.focused)


def test_ok_switches_and_escape_changes_nothing(tree):
    app = run(tree, CTRL_F3, lambda a: None, ALT_0, lambda a: None,
              KeyEvent("down"), KeyEvent("k", "k", alt=True), lambda a: None)
    assert app.shell.desktop.active_window is app.manager
    app = run(tree, CTRL_F3, lambda a: None, ALT_0, lambda a: None,
              KeyEvent("down"), KeyEvent("escape"), lambda a: None)
    first, second = managers(app)
    assert app.modal is None
    assert app.shell.desktop.active_window is second
    assert second._holds(app.focused)


def test_close_takes_the_window_off_and_stays_up(tree):
    seen = []
    app = run(tree, CTRL_F3, lambda a: None, ALT_0, lambda a: None,
              KeyEvent("down"), KeyEvent("l", "l", alt=True), lambda a: None,
              lambda a: seen.append((type(a.modal).__name__, list(a.modal.windows.items),
                                     a.modal.windows.cursor)))
    (only,) = managers(app)
    assert app.manager.parent is None
    assert seen == [("WindowManagerDialog", [only], 0)]


def test_closing_the_last_window_ends_the_dialog(tree, quiet_console):
    app = run(tree, ALT_0, lambda a: None, KeyEvent("l", "l", alt=True), lambda a: None)
    assert app.modal is None
    assert managers(app) == []
    assert app.shell.console_visible is True


def test_a_window_with_no_name_is_not_listed(tree):
    from navml.widgets.window import Window

    seen = []
    app = run(tree, lambda a: a.shell.desktop.open(Window()), lambda a: None,
              ALT_0, lambda a: None,
              lambda a: seen.append(list(a.modal.windows.items)))
    assert seen == [[app.manager]]


def test_the_list_entry_is_alt_0_and_is_enabled(tree):
    from navml.widgets.menu.menu_box.menu_box import key_caption

    app = navigator(tree)
    seen = []

    def look(a):
        item = _entry(a.shell.menu, "Window", "List...")
        seen.append((key_caption(item, a, a.manager.left),
                     a.command_enabled(item.command, a.manager.left)))

    run_app(app, [look])
    assert seen == [("Alt-0", True)]


def test_alt_0_behind_the_console_is_left_for_the_child(tree, quiet_console):
    app = run(tree, KeyEvent("o", ctrl=True), lambda a: None, ALT_0, lambda a: None)
    assert app.modal is None


def test_tile_cascade_and_close_all_are_enabled_with_a_file_manager_open(tree):
    app = navigator(tree)
    seen = []

    def look(a):
        for caption in ("Tile", "Cascade", "Close all"):
            item = _entry(a.shell.menu, "Window", caption)
            seen.append(a.command_enabled(item.command, a.manager.left))

    run_app(app, [look])
    assert seen == [True, True, True]


def test_tile_puts_two_file_managers_one_above_the_other(tree):
    from navml.commands import TileWindows

    app = run(tree, CTRL_F3, lambda a: None,
              lambda a: a.manager.left.spawn(a.manager.left.emit(TileWindows())),
              lambda a: None)
    desktop = app.shell.desktop
    first, second = managers(app)
    assert not first.zoomed and not second.zoomed
    assert (first.y, first.height + second.height) == (0, desktop.height)
    assert second.y == first.height and first.width == second.width == desktop.width


def test_tile_arranges_the_tree_window_with_the_file_manager(tree):
    from navigator.commands import OpenTreeWindow
    from navigator.widgets.tree_window import TreeWindow
    from navml.commands import TileWindows

    app = run(tree, lambda a: a.spawn(a.run_command(OpenTreeWindow)), lambda a: None,
              lambda a: a.shell.desktop.spawn(a.shell.desktop.active_window.emit(TileWindows())),
              lambda a: None)
    desktop = app.shell.desktop
    manager, tree_window = desktop.windows()
    assert isinstance(tree_window, TreeWindow)
    assert (manager.x, manager.y, manager.width) == (0, 0, desktop.width)
    assert (tree_window.x, tree_window.y) == (0, manager.height)
    assert manager.height + tree_window.height == desktop.height
