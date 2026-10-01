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


def test_right_opens_the_branch_and_moves_to_its_first_child():
    app, tree = mounted_tree()
    tree.cursor = 3                      # lib, closed
    settle()
    press(app, tree, KeyEvent("right"))
    assert tree.root.children()[1].children()[0].expanded is True
    assert tree.selected_node.name == "x"
    press(app, tree, KeyEvent("right"))  # x has no children: down a row
    assert tree.selected_node.name == "share"


@pytest.mark.parametrize("key", [KeyEvent("left"), KeyEvent("backspace")])
def test_left_and_backspace_move_to_the_parent(key):
    app, tree = mounted_tree()
    tree.cursor = 4                      # share
    settle()
    press(app, tree, key)
    assert tree.selected_node.name == "usr"
    press(app, tree, key)
    assert tree.selected_node.name == "/"
    press(app, tree, key)                # the root has no parent
    assert tree.selected_node.name == "/"


def test_backspace_closes_the_parent_and_left_does_not():
    app, tree = mounted_tree()
    usr = tree.root.children()[1]
    tree.cursor = 4                      # share
    settle()
    press(app, tree, KeyEvent("left"))
    assert tree.selected_node is usr and usr.expanded is True
    tree.cursor = 4
    settle()
    press(app, tree, KeyEvent("backspace"))
    assert tree.selected_node is usr and usr.expanded is False
    assert "share" not in names(tree)


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
    assert tree.selected_node.name == "usr" and tree.search is None


# -- the quick search: a path, typed through the branches it opens -----------------------------


def counted():
    """``/`` with ``usr/local/bin``, ``usr/lib`` and ``var``, nothing read, and
    the paths whose children have been read, in order."""
    read = []

    def leaf(name):
        return TreeNode(name, loader=load, data=children.get(name, []))

    def load(parent):
        read.append(parent.name)
        return [leaf(name) for name in parent.data]

    children = {"usr": ["lib", "local"], "local": ["bin", "share"], "/": ["usr", "var"]}
    root = TreeNode("/", loader=load, data=children["/"], expanded=True)
    return root, read


def test_ctrl_s_starts_the_search_and_again_finds_the_next():
    app, tree = mounted_tree()
    press(app, tree, KeyEvent("s", ctrl=True))
    assert tree.search == "" and tree.selected_node.name == "/"
    press(app, tree, KeyEvent("*", "*"), KeyEvent("r", "r"))   # a wildcard, then r
    assert tree.selected_node.name == "usr" and tree.search == "*r"
    press(app, tree, KeyEvent("s", ctrl=True))                  # sha-r-e
    assert tree.selected_node.name == "share"
    press(app, tree, KeyEvent("s", ctrl=True))
    assert tree.selected_node.name == "var"
    press(app, tree, KeyEvent("s", ctrl=True))                  # wrapping round
    assert tree.selected_node.name == "usr"


def test_a_slash_opens_the_match_and_confines_the_search_to_its_children():
    root, read = counted()
    app, tree = mounted_tree(root)
    for char in "us/l":
        press(app, tree, KeyEvent(char, char))
    assert tree.selected_node.name == "lib" and tree.search_path == "us/l"
    press(app, tree, KeyEvent("o", "o"), KeyEvent("/", "/"), KeyEvent("b", "b"))
    assert tree.selected_node.names() == ["/", "usr", "local", "bin"]
    assert tree.search_path == "us/lo/b"
    # Only the branches the path went through were read.
    assert read == ["/", "usr", "local"]
    # "v" names var, but var is not inside local: refused.
    press(app, tree, KeyEvent("v", "v"))
    assert tree.selected_node.name == "bin" and tree.search == "b"


def test_backspace_climbs_back_out_through_a_slash():
    root, _ = counted()
    app, tree = mounted_tree(root)
    for char in "us/lo/":
        press(app, tree, KeyEvent(char, char))
    assert tree.selected_node.name == "bin"
    press(app, tree, KeyEvent("backspace"))
    assert tree.selected_node.name == "local" and tree.search_path == "us/lo"
    # "us/l", then "us/", then the slash itself: back out of usr, onto it.
    press(app, tree, KeyEvent("backspace"), KeyEvent("backspace"), KeyEvent("backspace"))
    assert tree.search_path == "us" and tree.search_scope is None
    assert tree.selected_node.name == "usr"
    press(app, tree, KeyEvent("backspace"), KeyEvent("backspace"), KeyEvent("v", "v"))
    assert tree.selected_node.name == "var"         # every row is in scope again


def test_a_slash_first_searches_from_the_root_and_a_leaf_takes_none():
    root, _ = counted()
    app, tree = mounted_tree(root)
    press(app, tree, KeyEvent("s", ctrl=True), KeyEvent("/", "/"))
    assert tree.search_scope is root and tree.selected_node.name == "usr"
    press(app, tree, KeyEvent("v", "v"), KeyEvent("/", "/"))    # var is empty
    assert tree.search_path == "/v" and tree.selected_node.name == "var"


def test_any_other_key_ends_the_search_and_does_its_job():
    app, tree = mounted_tree()
    press(app, tree, KeyEvent("b", "b"), KeyEvent("down"))
    assert tree.search is None and tree.selected_node.name == "usr"


def test_enter_ends_the_search_and_chooses_as_dns_did():
    seen = []

    class Chooser(TreeView):
        async def on_chosen(self, event):
            seen.append(event.node.name)
            return True

    app, tree = mounted_tree(cls=Chooser)
    press(app, tree, KeyEvent("v", "v"), KeyEvent("enter"))
    assert tree.search is None and seen == ["var"]


def test_without_type_to_search_typing_is_declined_and_ctrl_s_searches():
    app, tree = mounted_tree()
    tree.type_to_search = False
    assert asyncio.run(tree.dispatch_key(KeyEvent("v", "v"))) is False
    assert tree.search is None
    press(app, tree, KeyEvent("s", ctrl=True), KeyEvent("v", "v"))
    assert tree.selected_node.name == "var" and tree.edits_text


def test_the_footer_shows_the_path_typed_and_the_caret_follows_it():
    root, _ = counted()
    app, tree = mounted_tree(root)
    for char in "us/l":
        press(app, tree, KeyEvent(char, char))
    footer = rows(tree)[-1]
    assert " Search: us/l " in footer
    x, y = tree.cursor_position()
    assert y == tree.height - 1 and footer[x - len("us/l"):x] == "us/l"


def test_a_new_root_ends_the_search():
    app, tree = mounted_tree()
    press(app, tree, KeyEvent("v", "v"))
    tree.root = sample()
    settle()
    assert tree.search is None


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
    from navigator.widgets.tree.directory_tree.directory_tree import count_files, files_line

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


def test_typing_in_the_ctrl_t_tree_goes_to_the_command_line(places):
    from test_nav import navigator

    app = navigator(places)
    run_app(app, [KeyEvent("t", ctrl=True), KeyEvent("tab"), KeyEvent("g", "g")])
    assert app.shell.command_line.value == "g"
    assert app.manager.tree.search is None


def test_ctrl_s_in_the_ctrl_t_tree_walks_a_path_and_enter_sends_the_panel(places):
    from test_nav import navigator

    app = navigator(places)
    # From the root, every directory down to alpha typed whole, "/" between.
    typed = "/" + "/".join(places.resolve().parts[1:]) + "/alpha"
    seen = []
    run_app(app, [
        KeyEvent("t", ctrl=True), KeyEvent("tab"), KeyEvent("s", ctrl=True),
        *[KeyEvent(char, char) for char in typed],
        lambda a: seen.append((a.manager.tree.search_path, a.manager.tree.edits_text)),
        KeyEvent("enter"),
    ])
    assert seen == [(typed, True)]
    # Enter ended the search and chose, as DN's did; the command line kept out.
    assert app.manager.left.path == (places / "alpha").resolve()
    assert app.shell.command_line.value == ""
    assert app.manager.tree.search is None


def test_a_cursor_at_rest_in_the_tree_takes_the_panel_with_it(places, monkeypatch):
    from test_nav import navigator
    from navigator.widgets.manager.manager import Manager

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
        item = _entry(a.shell.menu, "Panel", "Directory tree")
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
    from navigator.widgets.tree.change_dir_dialog import ChangeDirDialog
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


@pytest.mark.parametrize("size, expected", [
    # The original's 49 by 17 is the floor ...
    ((80, 24), (60, 19, 3)),
    # ... and the dialog grows with the screen, and its controls with it.
    ((120, 40), (90, 32, 6)),
])
def test_the_dialog_takes_its_size_from_the_screen(places, size, expected):
    from test_nav import navigator

    width, height, step = expected
    seen = []
    app = navigator(places, size=size)

    def look(a):
        d = a.modal
        seen.append((
            (d.width, d.height),
            (d.tree.x, d.tree.y, d.tree.width, d.tree.height),
            (d.where.y, d.where.width),
            [(b.x, b.y, b.width) for b in d.buttons_row],
        ))

    run_app(app, [KeyEvent("t", "t", alt=True), lambda a: None, look])
    assert seen == [(
        (width, height),
        (1, 1, width - 15, height - 3),
        (height - 2, width - 16),
        [(width - 13, 2 + i * step, 11) for i in range(5)],
    )]


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


# -- the Directory Tree window (Disk > Directory tree) ---------------------------------------


def tree_window_run(places, *actions):
    from test_nav import navigator

    app = navigator(places)

    def open_it(a):
        from navigator.widgets.shell.commands import OpenTreeWindow

        a.spawn(a.run_command(OpenTreeWindow))

    run_app(app, [open_it, lambda a: None, *actions, lambda a: None])
    return app


def test_the_window_opens_on_the_active_panels_directory_with_the_keys(places):
    from navigator.widgets.tree.tree_window import TreeWindow

    seen = []

    def look(a):
        window = a.shell.desktop.active_window
        tree = window.tree
        seen.append((type(window).__name__, window.title, tree.selected_path,
                     a.focused is tree,
                     (tree.framed, tree.x, tree.y, tree.width, tree.height)
                     == (False, 1, 1, window.width - 1, window.height - 2),
                     tree.x + tree.bar.x == window.width - 1))

    tree_window_run(places, look)
    assert seen == [("TreeWindow", "Directory Tree", places.resolve(), True, True, True)]


def test_enter_sends_the_file_managers_panel_and_keeps_the_keyboard(places):
    app = tree_window_run(places, KeyEvent("+", "+"), KeyEvent("down"), KeyEvent("enter"))
    assert app.manager.left.path == (places / "alpha").resolve()
    window = app.shell.desktop.active_window
    assert type(window).__name__ == "TreeWindow" and app.focused is window.tree


def test_escape_closes_the_window(places):
    app = tree_window_run(places, KeyEvent("escape"))
    assert app.shell.desktop.active_window is app.manager



def test_closing_the_window_gives_the_keyboard_back_to_the_right_panel(places):
    from test_nav import navigator
    from navigator.widgets.shell.commands import OpenTreeWindow

    app = navigator(places)
    run_app(app, [KeyEvent("tab"), lambda a: a.spawn(a.run_command(OpenTreeWindow)),
                  lambda a: None, KeyEvent("escape"), lambda a: None])
    assert app.shell.desktop.active_window is app.manager
    assert app.focused is app.manager.right

def test_ctrl_r_rereads_the_windows_tree(places):
    seen = []
    tree_window_run(
        places, KeyEvent("+", "+"), KeyEvent("down"),
        lambda a: (places / "alpha" / "fresh").mkdir(),
        KeyEvent("r", ctrl=True), KeyEvent("+", "+"),
        lambda a: seen.append(
            [n.name for n in a.shell.desktop.active_window.tree.selected_node.children()]),
    )
    assert seen == [["fresh", "inner"]]


def test_the_disk_menu_entry_is_enabled(places):
    from test_nav import navigator, _entry

    app = navigator(places)
    seen = []
    run_app(app, [lambda a: seen.append(a.command_enabled(
        _entry(a.shell.menu, "Disk", "Directory tree").command, a.manager.left))])
    assert seen == [True]


# -- dot-directories --------------------------------------------------------------


def _children_of(tree, path):
    node = tree.selected_node
    assert node.data == path.resolve()
    return [child.name for child in node.children()]


def test_a_directory_node_hides_dot_directories_when_asked(places):
    from navigator.widgets.tree.directory_tree.directory_tree import directory_node

    (places / ".secret").mkdir()
    assert ".secret" in [n.name for n in directory_node(places).children()]
    assert ".secret" not in [n.name for n in directory_node(places, hidden=False).children()]
    (places / "gamma" / ".only").mkdir()
    assert not directory_node(places / "gamma", hidden=False).has_children()


def test_show_path_grafts_the_dot_directory_it_goes_through(places):
    from navigator.widgets.tree.directory_tree.directory_tree import directory_root, show_path

    (places / ".config" / "app").mkdir(parents=True)
    (places / ".other").mkdir()
    _, tree = mounted_tree(directory_root(hidden=False))
    show_path(tree, places / ".config" / "app")
    assert tree.selected_node.data == (places / ".config" / "app").resolve()
    siblings = [n.name for n in tree.selected_node.parent.parent.children()]
    assert ".config" in siblings and ".other" not in siblings


def test_ctrl_h_hides_dot_directories_in_the_ctrl_t_tree(places):
    from test_nav import navigator

    (places / ".secret").mkdir()
    app = navigator(places)
    seen = []
    run_app(app, [
        KeyEvent("t", ctrl=True), KeyEvent("tab"), KeyEvent("+", "+"),
        lambda a: seen.append(_children_of(a.manager.tree, places)),
        KeyEvent("h", ctrl=True), KeyEvent("+", "+"),
        lambda a: seen.append(_children_of(a.manager.tree, places)),
    ])
    assert ".secret" in seen[0]
    assert ".secret" not in seen[1] and "alpha" in seen[1]


def test_alt_t_and_the_tree_window_take_the_panels_setting(places):
    from test_nav import navigator
    from navigator.widgets.shell.commands import OpenTreeWindow

    (places / ".secret").mkdir()
    app = navigator(places)
    seen = []
    run_app(app, [
        KeyEvent("h", ctrl=True),
        KeyEvent("t", "t", alt=True), lambda a: None, KeyEvent("+", "+"),
        lambda a: seen.append(_children_of(a.modal.tree, places)),
        KeyEvent("escape"),
        lambda a: a.spawn(a.run_command(OpenTreeWindow)), lambda a: None, KeyEvent("+", "+"),
        lambda a: seen.append(_children_of(a.shell.desktop.active_window.tree, places)),
    ])
    assert seen == [["alpha", "beta", "gamma"]] * 2


# -- the quick search in the dialog and the window ------------------------------------------


def _walk_to_alpha(places):
    return [KeyEvent(char, char) for char in "/" + "/".join(places.resolve().parts[1:]) + "/alpha"]


@pytest.mark.parametrize("start", [[], [KeyEvent("s", ctrl=True)]])
def test_the_alt_t_tree_searches_by_typing_or_ctrl_s(places, start):
    seen = []
    chdir_run(places, *start, *_walk_to_alpha(places),
              lambda a: seen.append((a.modal.accept(), a.modal.tree.search is not None)),
              KeyEvent("escape"),
              lambda a: seen.append((a.modal is not None, a.modal.tree.search)))
    # Esc ended the search and left the dialog up.
    assert seen == [((places / "alpha").resolve(), True), (True, None)]


def test_the_tree_window_searches_and_enter_sends_the_panel(places):
    app = tree_window_run(places, *_walk_to_alpha(places), KeyEvent("enter"))
    assert app.manager.left.path == (places / "alpha").resolve()


def test_the_tree_window_shows_the_search_on_its_bottom_frame(places):
    seen = []

    def bottom(a):
        from navigator.widgets.tree.tree_window import TreeWindow

        window = a.focused
        while not isinstance(window, TreeWindow):
            window = window.parent
        # render_tree paints a widget where it stands in its parent.
        buffer = ScreenBuffer(window.x + window.width, window.y + window.height)
        window.render_tree(buffer)
        seen.append(("".join(buffer.get(window.x + x, window.y + window.height - 1)[0] or " "
                             for x in range(window.width)),
                     window.tree.cursor_position(), window.cursor_position(), window.height))

    tree_window_run(places, KeyEvent("s", ctrl=True), KeyEvent("/", "/"), bottom,
                    KeyEvent("escape"), bottom)
    row, tree_caret, window_caret, height = seen[0]
    assert " Search: / " in row
    # The caret is the window's, on the frame right after what was typed.
    assert tree_caret is None
    x, y = window_caret
    assert y == height - 1 and row[x - len(" Search: /"):x] == " Search: /"
    row, _, window_caret, _ = seen[1]
    assert "Search" not in row and window_caret is None   # Esc ended it
