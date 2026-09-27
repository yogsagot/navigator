"""Trees: the library's TreeView, and the directory tree a panel becomes."""

from __future__ import annotations

import asyncio
import pathlib

import pytest

from navkit.application import Application
from navkit.events import KeyEvent, MouseClickEvent
from navkit.screen import ScreenBuffer

from navml.widgets.dialog.tree_view import ChosenEvent, TreeNode, TreeView

from conftest import FakeTerminal, run_app, settle


def node(name, *children, expanded=False):
    made = TreeNode(name, list(children))
    made.expanded = expanded
    return made


def sample():
    """``/`` with bin, usr (lib (x), share) and var; the root and usr open."""
    return node("/", node("bin"),
                node("usr", node("lib", node("x")), node("share"), expanded=True),
                node("var"), expanded=True)


#: Enough of a sheet that the cursor's style differs from a name's.
SHEET = "TreeView::node:selected { bg: red }"


def mounted_tree(root=None, width=30, height=10, cls=TreeView):
    from navkit.stylesheet import parse

    tree = cls()
    tree.root = root or sample()
    app = Application(tree, terminal=FakeTerminal(width, height),
                      stylesheet=parse(SHEET))
    tree.x = tree.y = 0
    tree.width, tree.height = width, height
    tree.focus()
    settle()
    return app, tree


def rows(tree):
    buffer = ScreenBuffer(tree.width, tree.height)
    tree.render_tree(buffer)
    # Without the frame's right edge, so a row reads as what the tree drew.
    return ["".join(buffer.get(x, y)[0] or " " for x in range(tree.width - 1)).rstrip()
            for y in range(tree.height)]


def names(tree):
    return [row.node.name for row in tree.items]


# -- drawing, as TTreeView.Draw does -----------------------------------------------------


def test_branches_rails_and_markers_are_drawn_as_the_original_draws_them():
    _, tree = mounted_tree()
    assert rows(tree)[1:7] == [
        "│  /",
        "│  ├───bin",
        "│  ├─[-] usr",
        "│  │  ├─[+] lib",
        "│  │  └───share",
        "│  └───var",
    ]


def test_the_expanded_view_draws_a_junction_instead_of_a_marker():
    _, tree = mounted_tree()
    tree.collapsible = False
    settle()
    assert "│  ├──┬usr" in rows(tree)
    assert "│  │  │  └───x" in rows(tree)       # everything is shown


def test_the_cursor_marks_the_name_one_column_early_and_nothing_else():
    app, tree = mounted_tree()
    tree.cursor = 1                      # bin
    settle()
    buffer = ScreenBuffer(tree.width, tree.height)
    tree.render_tree(buffer)
    selected = tree.part_style("node", selected=True)
    # " bin " begins on the last cell of "├───"
    assert [buffer.get(x, 2)[1] == selected for x in range(5, 12)] == [
        False, True, True, True, True, True, False]


# -- the node model and what the view does with it ------------------------------------------


def test_a_branch_opens_and_closes_and_the_cursor_follows_a_closed_one():
    _, tree = mounted_tree()
    lib = tree.root.children()[1].children()[0]
    tree.toggle(lib)
    settle()
    assert names(tree) == ["/", "bin", "usr", "lib", "x", "share", "var"]
    tree.cursor = 4                      # x
    settle()
    tree.toggle(tree.root.children()[1])  # close usr, around the cursor
    settle()
    assert names(tree) == ["/", "bin", "usr", "var"]
    assert tree.selected_node.name == "usr"


def test_children_are_read_only_when_a_branch_opens():
    calls = []

    def loader(parent):
        calls.append(parent.name)
        return [TreeNode("child")]

    root = TreeNode("/", loader=loader)
    root.expanded = True
    lazy = TreeNode("lazy", loader=loader, probe=lambda n: True)
    root.set_children([lazy])
    _, tree = mounted_tree(root)
    assert calls == []
    tree.toggle(lazy)
    settle()
    assert calls == ["lazy"] and names(tree) == ["/", "lazy", "child"]


def test_a_probe_answers_for_an_unopened_branch_and_an_empty_one_loses_its_marker():
    empty = TreeNode("empty", loader=lambda n: [])
    root = node("/", expanded=True)
    root.set_children([empty])
    _, tree = mounted_tree(root)
    assert "├───empty" not in "".join(rows(tree))   # unknown: assumed to have some
    tree.toggle(empty)
    settle()
    assert any(r.endswith("└───empty") for r in rows(tree))


def test_locate_opens_every_branch_above_the_node_it_finds():
    _, tree = mounted_tree()
    tree.root.children()[1].expanded = False
    tree.refresh()
    settle()
    found = tree.locate(["/", "usr", "lib", "x", "missing"])
    settle()
    assert found.name == "x" and tree.selected_node is found
    assert names(tree) == ["/", "bin", "usr", "lib", "x", "share", "var"]


# -- keys and the mouse ---------------------------------------------------------------------


def press(app, tree, *keys):
    for key in keys:
        asyncio.run(tree.dispatch_key(key))
        settle()


def test_left_and_right_move_up_and_down_as_in_the_original():
    app, tree = mounted_tree()
    tree.cursor = 2
    settle()
    press(app, tree, KeyEvent("right"))
    assert tree.cursor == 3
    press(app, tree, KeyEvent("left"), KeyEvent("left"))
    assert tree.cursor == 1


@pytest.mark.parametrize("key", [KeyEvent("space", " "), KeyEvent("+", "+"), KeyEvent("-", "-")])
def test_space_plus_and_minus_toggle_the_branch_under_the_cursor(key):
    app, tree = mounted_tree()
    tree.cursor = 3                      # lib, closed
    settle()
    press(app, tree, key)
    assert tree.root.children()[1].children()[0].expanded is True


def test_star_opens_every_branch_already_read():
    app, tree = mounted_tree()
    tree.root.children()[1].children()[0].children()   # lib is read, not open
    press(app, tree, KeyEvent("*", "*"))
    assert "x" in names(tree)


def test_typing_searches_forward_and_backspace_and_escape_end_it():
    app, tree = mounted_tree()
    press(app, tree, KeyEvent("s", "s"))
    assert tree.selected_node.name == "share" and tree.search == "s"
    press(app, tree, KeyEvent("v", "v"))            # no "sv": stays put
    assert tree.selected_node.name == "share" and tree.search == "s"
    press(app, tree, KeyEvent("backspace"))
    assert tree.search == ""
    press(app, tree, KeyEvent("u", "u"), KeyEvent("escape"))
    assert tree.selected_node.name == "usr" and tree.search == ""


def test_enter_emits_chosen_with_the_node():
    seen = []

    class Host(TreeView):
        async def on_chosen(self, event):
            seen.append(event.node.name)
            return True

    app, tree = mounted_tree(cls=Host)
    tree.cursor = 1
    settle()
    press(app, tree, KeyEvent("enter"))
    assert seen == ["bin"]


def test_a_click_on_a_marker_opens_the_branch():
    app, tree = mounted_tree()
    # lib is row 4 of the widget; its "[+]" is DOS Navigator columns 6-8.
    asyncio.run(tree.dispatch_mouse(MouseClickEvent(1 + 6, 4, "left")))
    settle()
    assert tree.root.children()[1].children()[0].expanded is True


# -- the directory tree in the file manager ---------------------------------------------------


@pytest.fixture
def places(tmp_path):
    for sub in ("alpha/inner", "beta", "gamma"):
        (tmp_path / sub).mkdir(parents=True)
    (tmp_path / "alpha" / "file.txt").write_text("hello")
    return tmp_path


def test_the_info_band_counts_the_files_with_their_bytes(places):
    from navigator.widgets.directory_tree.directory_tree import count_files, files_line

    assert count_files(places / "alpha") == (1, 5)
    assert files_line(1, 5) == "1 file with 5 bytes"
    assert files_line(3, 1) == "3 files with 1 byte"
    assert files_line(2, 12345) == "2 files with 12,345 bytes"


def test_ctrl_t_puts_a_tree_where_the_passive_panel_was(places):
    from test_nav import navigator

    app = navigator(places)
    seen = []
    run_app(app, [KeyEvent("t", ctrl=True), lambda a: seen.append((
        a.manager.left.visible, a.manager.right.visible, a.manager.tree.visible,
        a.manager.panels.children.index(a.manager.tree)
        < a.manager.panels.children.index(a.manager.right),
        a.focused is a.manager.left,
        a.manager.tree.selected_path,
    ))])
    assert seen == [(True, False, True, True, True, places.resolve())]


def test_ctrl_t_again_restores_the_panel(places):
    from test_nav import navigator

    app = navigator(places)
    run_app(app, [KeyEvent("t", ctrl=True), KeyEvent("tab"), KeyEvent("t", ctrl=True)])
    manager = app.manager
    assert (manager.right.visible, manager.tree.visible) == (True, False)
    assert manager.tree_replaces is None
    assert app.focused is manager.right      # the tree had it; the panel gets it


def test_the_tree_follows_the_active_panel(places):
    from test_nav import navigator

    app = navigator(places)
    seen = []
    run_app(app, [
        KeyEvent("t", ctrl=True),
        KeyEvent("down"), KeyEvent("enter"),          # the panel goes into alpha
        lambda a: seen.append(a.manager.tree.selected_path),
    ])
    assert seen == [(places / "alpha").resolve()]


def test_enter_in_the_tree_sends_the_panel_there_now(places):
    from test_nav import navigator

    app = navigator(places)
    # The tree opens the branches *above* the panel's directory, not its own:
    # "+" opens it, and Down reaches its first subdirectory.
    run_app(app, [
        KeyEvent("t", ctrl=True), KeyEvent("tab"),
        KeyEvent("+", "+"), KeyEvent("down"), KeyEvent("enter"),
    ])
    assert app.manager.left.path == (places / "alpha").resolve()


def test_a_cursor_at_rest_in_the_tree_takes_the_panel_with_it(places, monkeypatch):
    from test_nav import navigator
    from navigator.widgets.manager import Manager

    monkeypatch.setattr(Manager, "LOCATE_DELAY", 0.01)
    app = navigator(places)
    run_app(app, [
        KeyEvent("t", ctrl=True), KeyEvent("tab"), KeyEvent("+", "+"),
        KeyEvent("down"), lambda a: None,
    ], settle=0.1)
    assert app.manager.left.path == (places / "alpha").resolve()


def test_the_menu_entry_is_ctrl_t_and_is_enabled(places):
    from test_nav import navigator, _entry
    from navml.widgets.menu.menu_box.menu_box import key_caption

    app = navigator(places)
    seen = []

    def look(a):
        item = _entry(a.shell.menu, "Manager", "Directory tree")
        seen.append((key_caption(item, a, a.manager.left),
                     a.command_enabled(item.command, a.manager.left)))

    run_app(app, [look])
    assert seen == [("Ctrl-T", True)]


# -- Choose Directory (Alt+T) --------------------------------------------------------------


def test_a_list_without_its_frame_gives_the_frame_cells_to_its_rows():
    _, tree = mounted_tree()
    tree.framed = False
    settle()
    assert (tree.inset, tree.inner_width, tree.rows) == (0, tree.width - 1, tree.height)
    assert rows(tree)[0] == "  /"          # the root at DOS Navigator's column 2
    assert tree.bar.x == tree.width - 1 and tree.bar.y == 0


def test_the_dialog_is_laid_out_as_ttreedialog_lays_it_out(places):
    from navigator.widgets.change_dir_dialog import ChangeDirDialog
    from navml.widgets.dialog.control.control import parse_shortcut

    dialog = ChangeDirDialog(start=places)
    assert (dialog.modal_width, dialog.modal_height, dialog.title) == (49, 17, "Choose Directory")
    tree = dialog.tree
    assert (tree.framed, tree.x, tree.y, tree.width, tree.height) == (False, 1, 1, 34, 14)
    buttons = dialog.buttons_row
    assert [parse_shortcut(b.text)[0] for b in buttons] == [
        "OK", "Drive...", "Re-read", "MkDir", "Cancel"]
    assert [(b.x, b.y, b.width) for b in buttons] == [(36, y, 11) for y in (2, 5, 8, 11, 14)]
    assert dialog.pick.default and dialog.drive.disabled
    assert dialog.row.visible is False     # Dialog's own bottom row is not this one's
    assert dialog.accept() == places.resolve()


def chdir_run(places, *actions):
    from test_nav import navigator

    app = navigator(places)
    run_app(app, [KeyEvent("t", "t", alt=True), lambda a: None, *actions, lambda a: None])
    return app


def test_alt_t_opens_it_on_the_active_panels_directory(places):
    seen = []
    chdir_run(places, lambda a: seen.append((type(a.modal).__name__, a.modal.accept(),
                                              a.focused is a.modal.tree)))
    assert seen == [("ChangeDirDialog", places.resolve(), True)]


def test_enter_in_the_tree_sends_the_panel_there(places):
    app = chdir_run(places, KeyEvent("+", "+"), KeyEvent("down"), KeyEvent("enter"))
    assert app.modal is None
    assert app.manager.left.path == (places / "alpha").resolve()
    assert app.focused is app.manager.left


def test_ok_sends_the_panel_and_escape_leaves_it(places):
    app = chdir_run(places, KeyEvent("+", "+"), KeyEvent("down"), KeyEvent("down"),
                    KeyEvent("down"), KeyEvent("k", "k", alt=True))
    assert app.manager.left.path == (places / "gamma").resolve()
    app = chdir_run(places, KeyEvent("+", "+"), KeyEvent("down"), KeyEvent("escape"))
    assert app.modal is None and app.manager.left.path == places


def test_mkdir_makes_the_directory_where_the_tree_points(places):
    seen = []
    chdir_run(
        places,
        KeyEvent("+", "+"), KeyEvent("down"),              # alpha
        KeyEvent("m", "m", alt=True), lambda a: None,      # MkDir, over the dialog
        KeyEvent("n", "n"), KeyEvent("e", "e"), KeyEvent("w", "w"),
        KeyEvent("enter"), lambda a: None,
        lambda a: seen.append((type(a.modal).__name__, a.modal.accept())),
    )
    assert (places / "alpha" / "new").is_dir()
    assert seen == [("ChangeDirDialog", (places / "alpha" / "new").resolve())]


def test_reread_keeps_the_cursor_and_finds_what_appeared(places):
    seen = []

    def appear(a):
        (places / "alpha" / "fresh").mkdir()

    chdir_run(
        places, KeyEvent("+", "+"), KeyEvent("down"), appear,
        KeyEvent("r", "r", alt=True),
        lambda a: seen.append(a.modal.accept()),
        KeyEvent("+", "+"),
        lambda a: seen.append([n.name for n in a.modal.tree.selected_node.children()]),
    )
    assert seen == [(places / "alpha").resolve(), ["fresh", "inner"]]


def test_the_menu_entry_is_alt_t_and_is_enabled(places):
    from test_nav import navigator, _entry
    from navml.widgets.menu.menu_box.menu_box import key_caption

    app = navigator(places)
    seen = []

    def look(a):
        item = _entry(a.shell.menu, "Panel", "Change directory")
        seen.append((key_caption(item, a, a.manager.left),
                     a.command_enabled(item.command, a.manager.left)))

    run_app(app, [look])
    assert seen == [("Alt-T", True)]
