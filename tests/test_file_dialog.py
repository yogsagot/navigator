"""DOS Navigator's file dialog: ``TFileDialog``, ``TFileList``, ``TFileInfoPane`` (DNSTDDLG.PAS)."""

from __future__ import annotations

import os

import pytest

from conftest import FakeTerminal, run_app
from navkit.application import Application
from navkit.events import KeyEvent
from navkit.widget import Widget

from navml.history import HISTORY
from navml.widgets.dialog.file_dialog import FileDialog
from navml.widgets.dialog.file_list import FileItem, scan


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "beta.txt").write_text("bb")
    (tmp_path / "Alpha.md").write_text("a")
    (tmp_path / "gamma.txt").write_text("g")
    (tmp_path / ".hidden").write_text("h")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "inner.txt").write_text("i")
    (tmp_path / ".dotdir").mkdir()
    return tmp_path


def names(items: list[FileItem]) -> list[str]:
    return [item.name for item in items]


# -- reading a directory ----------------------------------------------------------------


def test_files_match_the_wildcard_and_directories_list_dot_dot_first(tree):
    files, dirs = scan(tree, "*", hidden=False)
    assert names(files) == ["Alpha.md", "beta.txt", "gamma.txt"]
    assert names(dirs) == ["..", "sub"]
    files, _ = scan(tree, "*.txt", hidden=False)
    assert names(files) == ["beta.txt", "gamma.txt"]


def test_dot_files_and_directories_show_only_when_hidden_ones_do(tree):
    files, dirs = scan(tree, "*", hidden=True)
    assert ".hidden" in names(files) and ".dotdir" in names(dirs)


def test_the_root_has_no_parent_to_list():
    _, dirs = scan("/", "*", hidden=False)
    assert ".." not in names(dirs)


# -- the dialog ----------------------------------------------------------------------------


def run(tree, *actions, **kwargs):
    """A FileDialog over *tree*, then *actions*; what it answered, and the dialog.

    An action may be a callable taking the dialog as well, to look at it while
    it is still up -- once the application stops, the dialog is gone.
    """
    root = Widget()
    app = Application(root, terminal=FakeTerminal(80, 25))
    dialog = FileDialog(directory=tree, **kwargs)
    jobs = []

    def bound(action):
        if callable(action) and getattr(action, "wants_dialog", False):
            return lambda a: action(a, dialog)
        return action

    run_app(app, [lambda a: jobs.append(a.spawn(dialog.execute(a))), lambda a: None,
                  *[bound(action) for action in actions], lambda a: None])
    job = jobs[0]
    # Still up when the application stopped: the wait for it was cancelled.
    return ("open" if job.cancelled() or not job.done() else job.result()), dialog


def look(seen, read):
    """An action recording *read(dialog)* while the dialog is up."""
    def action(app, dialog):
        seen.append(read(dialog))
    action.wants_dialog = True
    return action


def keys(*names):
    return [KeyEvent(name) for name in names]


def typed(text):
    return [KeyEvent(c, c) for c in text]


def test_a_name_typed_over_the_wildcard_closes_with_its_full_path(tree):
    answer, dialog = run(tree, *typed("new.txt"), KeyEvent("enter"))
    assert answer == str(tree / "new.txt")


def test_the_files_list_fills_the_name_line_and_the_info_pane(tree):
    answer, dialog = run(tree, KeyEvent("tab"), KeyEvent("down"))
    assert answer == "open"
    assert dialog.target.value == "beta.txt"
    path, line = dialog.info.lines()
    assert path == f" {tree}/*"
    assert line.startswith(" beta.txt     2")


def test_enter_on_a_file_closes_with_it(tree):
    answer, _ = run(tree, KeyEvent("tab"), KeyEvent("down"), KeyEvent("enter"))
    assert answer == str(tree / "beta.txt")


def test_enter_on_a_directory_lists_it_and_stays_up(tree):
    seen = []
    answer, dialog = run(tree, KeyEvent("tab"), KeyEvent("tab"), KeyEvent("down"),
                         KeyEvent("enter"), look(seen, lambda d: d.dirs.focused))
    assert answer == "open"
    assert dialog.directory == tree / "sub"
    assert names(dialog.files.items) == ["inner.txt"]
    assert seen == [True]  # the keyboard stays on the directories


def test_a_typed_wildcard_lists_through_it(tree):
    seen = []
    answer, dialog = run(tree, *typed("*.txt"), KeyEvent("enter"),
                         look(seen, lambda d: d.files.focused))
    assert answer == "open" and dialog.wildcard == "*.txt"
    assert names(dialog.files.items) == ["beta.txt", "gamma.txt"]
    assert seen == [True]


def test_dot_dot_with_the_wildcard_goes_up(tree):
    answer, dialog = run(tree / "sub", KeyEvent("tab"), KeyEvent("tab"), KeyEvent("enter"))
    assert dialog.directory == tree


def test_right_and_left_move_between_controls_but_not_out_of_the_name_line(tree):
    seen = []
    run(tree, KeyEvent("right"), look(seen, lambda d: d.target.entry.focused),
        KeyEvent("tab"), KeyEvent("right"), look(seen, lambda d: d.dirs.focused),
        KeyEvent("left"), look(seen, lambda d: d.files.focused))
    assert seen == [True, True, True]


def test_tab_skips_an_empty_files_list(tree):
    seen = []
    _, dialog = run(tree, *typed("*.none"), KeyEvent("enter"), KeyEvent("tab"),
                    look(seen, lambda d: d.dirs.focused))
    assert dialog.files.items == [] and seen == [True]


def test_typing_in_a_list_searches_it(tree):
    seen = []
    _, dialog = run(tree, KeyEvent("tab"), *typed("g"),
                    look(seen, lambda d: d.files.cursor_position()[0]))
    assert dialog.files.selected.name == "gamma.txt"
    assert seen == [2]  # the caret after the "g" typed
    _, dialog = run(tree, KeyEvent("tab"), *typed("gz"))
    assert dialog.files.selected.name == "gamma.txt"  # nothing begins "gz": ignored
    assert dialog.files.search == "g"


def test_a_name_in_no_directory_is_refused(tree):
    seen = []
    answer, _ = run(tree, *typed("nowhere/x.txt"), KeyEvent("enter"),
                    lambda a: seen.append(a.modal.prompt if a.modal else None))
    assert answer == "open" and seen == ["Invalid file name."]


def test_the_history_keeps_the_full_path(tree):
    run(tree, *typed("kept.txt"), KeyEvent("enter"), history_id="file_dialog_test")
    assert HISTORY.entries("file_dialog_test")[0] == str(tree / "kept.txt")


def test_title_and_label_are_the_callers(tree):
    _, dialog = run(tree, title="Copy block to", label="File ~N~ame")
    assert dialog.title == "Copy block to" and dialog.caption.text == "File ~N~ame"
