"""F4-F8 while the information panel or the Ctrl+T tree has the keyboard.

DN sent a status-line command to the focused view: ``TDiskInfo`` did F4 alone
(*Edit DirInfo*), ``TTreePanel`` F5/F6 (``CopyDir``), F7 (``MkDirectory``) and
F8/Del (``EraseDir``) on the directory under its cursor.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.settings import SETTINGS


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    west, east = tmp_path / "west", tmp_path / "east"
    (west / "sub").mkdir(parents=True)
    (west / "sub" / "f.txt").write_text("f")
    (west / "a.txt").write_text("a")
    east.mkdir()
    return tmp_path


def navigator(place: Path) -> Navigator:
    return Navigator(place / "west", place / "east", terminal=FakeTerminal(100, 30))


# -- the information panel ---------------------------------------------------------------------


INFO = [KeyEvent("l", ctrl=True), lambda a: None, KeyEvent("tab"), lambda a: None]


def test_f4_in_the_info_panel_edits_its_information_file(place):
    from navigator.widgets.editor.edit_window import EditWindow

    (place / "west" / "DIRINFO").write_text("about this\n")
    app = navigator(place)
    seen = {}
    run_app(app, [*INFO, Until(lambda a: a.manager.info.info_path is not None), KeyEvent("f4"),
                  Until(lambda a: isinstance(a.shell.desktop.active_window, EditWindow)),
                  lambda a: seen.update(path=a.shell.desktop.active_window.editor.path)])
    assert seen["path"] == place / "west" / "DIRINFO"


def test_f4_in_the_info_panel_without_one_is_refused(place):
    from navigator.widgets.manager.commands import Edit

    app = navigator(place)
    seen = {}
    run_app(app, [*INFO, lambda a: seen.update(why=a.manager.refusal(Edit()), focused=a.manager.info.focus_within),
                  KeyEvent("f4"), lambda a: None,
                  lambda a: seen.update(window=type(a.shell.desktop.active_window).__name__)])
    assert seen["focused"] and seen["why"] == "No DirInfo or File_ID.DIZ here"
    assert seen["window"] == "Manager"


@pytest.mark.parametrize("key", ["f5", "f8"])
def test_copy_and_erase_do_nothing_from_the_info_panel(place, key):
    from navigator.widgets.manager.commands import Copy, Delete

    app = navigator(place)
    seen = {}
    command = Copy() if key == "f5" else Delete()
    run_app(app, [lambda a: setattr(a.manager.left, "cursor", 1), *INFO,
                  lambda a: seen.update(why=a.manager.refusal(command)), KeyEvent(key), lambda a: None,
                  lambda a: seen.update(modal=a.modal)])
    assert seen["why"] == "Only in a file panel, not beside it" and seen["modal"] is None
    assert (place / "west" / "a.txt").exists() and (place / "west" / "sub").exists()


# -- the Ctrl+T tree -----------------------------------------------------------------------------


def tree_lands_on(target_of):
    """An ``Until`` predicate: the tree's cursor on ``target_of(app)``.

    ``show`` walks on a thread, and a later walk (Ctrl+T's own, to the
    panel's directory) may land after it and take the cursor back: asked
    again then -- but not more than every 0.3 s, as each ``show`` drops the
    walk before it."""
    import time

    asked = [0.0]

    def there(a):
        tree = a.manager.tree
        target = target_of(a)
        if tree.selected_path == target:
            return True
        if time.monotonic() - asked[0] > 0.3:
            asked[0] = time.monotonic()
            tree.show(target)
        return False
    return there


def tree_on(name):
    """Ctrl+T, Tab into the tree, its cursor on *name* (a directory of west)."""
    return [KeyEvent("t", ctrl=True), Until(lambda a: a.manager.tree.selected_path is not None),
            KeyEvent("tab"), lambda a: None,
            Until(tree_lands_on(lambda a: a.manager.left.location.local / name), timeout=5)]


def test_f5_in_the_tree_copies_its_directory(place):
    from navml.widgets.dialog.dialog import Dialog

    app = navigator(place)

    def target(a):
        a.modal.target.value = str(place / "east") + "/"

    run_app(app, [*tree_on("sub"), KeyEvent("f5"), Until(lambda a: isinstance(a.modal, Dialog)), target,
                  KeyEvent("enter"), Until(lambda a: (place / "east" / "sub" / "f.txt").exists())])
    assert (place / "west" / "sub" / "f.txt").exists()


def test_f6_in_the_tree_moves_its_directory(place):
    from navml.widgets.dialog.dialog import Dialog

    app = navigator(place)

    def target(a):
        a.modal.target.value = str(place / "east") + "/"

    run_app(app, [*tree_on("sub"), KeyEvent("f6"), Until(lambda a: isinstance(a.modal, Dialog)), target,
                  KeyEvent("enter"), Until(lambda a: (place / "east" / "sub" / "f.txt").exists()),
                  Until(lambda a: not (place / "west" / "sub").exists())])


def test_f7_in_the_tree_makes_a_directory_under_its_cursor(place):
    from navml.widgets.dialog.dialog import Dialog

    app = navigator(place)
    seen = {}
    run_app(app, [*tree_on("sub"), KeyEvent("f7"), Until(lambda a: isinstance(a.modal, Dialog)),
                  *[KeyEvent(c, c) for c in "new"], KeyEvent("enter"),
                  Until(lambda a: (place / "west" / "sub" / "new").is_dir()),
                  # The tree reads the branch again on a thread, then goes onto it.
                  Until(lambda a: Path(str(a.manager.tree.selected_path)) == place / "west" / "sub" / "new"),
                  lambda a: seen.update(at=a.manager.tree.selected_path)])
    assert not (place / "west" / "new").exists()
    assert Path(str(seen["at"])) == place / "west" / "sub" / "new"


def test_f8_in_the_tree_erases_its_directory(place, monkeypatch):
    from navml.widgets.dialog.dialog import Dialog
    from navigator.widgets.file_ops.delete_dialog import delete_dialog

    # *Recursive delete* ticked, so the non-empty directory goes without a question.
    monkeypatch.setitem(delete_dialog._session, "recursive", True)
    monkeypatch.setattr(SETTINGS.file_manager, "use_trash", False)
    app = navigator(place)
    seen = {}
    run_app(app, [*tree_on("sub"), KeyEvent("f8"), Until(lambda a: isinstance(a.modal, Dialog)),
                  KeyEvent("enter"), Until(lambda a: not (place / "west" / "sub").exists()), lambda a: None,
                  lambda a: seen.update(at=a.manager.tree.selected_path)])
    assert (place / "west" / "a.txt").exists()
    assert seen["at"] is not None and "sub" not in Path(str(seen["at"])).parts
    assert (place / "west" / "a.txt").exists()


def test_the_trees_root_and_its_other_commands_are_refused(place):
    from navigator.widgets.manager.commands import ChangeAttributes, Copy, Delete, DeleteSingle

    app = navigator(place)
    seen = {}

    def look(a):
        m = a.manager
        seen.update(root=m.tree.selected_node is m.tree.root,
                    copy=m.refusal(Copy()), erase=m.refusal(Delete()),
                    single=m.refusal(DeleteSingle()), attrs=m.refusal(ChangeAttributes()))

    run_app(app, [KeyEvent("t", ctrl=True), lambda a: None, KeyEvent("tab"), lambda a: None,
                  KeyEvent("home"), lambda a: None, look])
    assert seen["root"]
    assert seen["copy"] == seen["erase"] == "Not the tree's root"
    assert seen["single"] == seen["attrs"] == "Only in a file panel, not beside it"
