"""What the screen used to wait on, read on a thread: the viewer, the quick view,
the tree's counts and probes, Alt+E's survey, the bookmarks box, the file dialog."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.widgets.editor import loading


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "alpha").mkdir()
    (tmp_path / "alpha" / "inner.txt").write_text("12345")
    (tmp_path / "one.txt").write_text("one\n")
    (tmp_path / "two.txt").write_text("two\n")
    return tmp_path


def navigator(path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def held(monkeypatch, owner, name, *, when=lambda *a: True):
    """Make ``owner.name`` wait until the returned event is set, for calls *when* says."""
    release = threading.Event()
    real = getattr(owner, name)

    def slow(*args, **kwargs):
        if when(*args):
            release.wait(5)
        return real(*args, **kwargs)

    monkeypatch.setattr(owner, name, slow)
    return release


def go_to(name):
    def action(app):
        panel = app.manager.active_panel
        panel.cursor = [entry.name for entry in panel.items].index(name)
    return action


def writewin(app):
    from navigator.widgets.file_ops.write_win import WriteWin

    return isinstance(app.modal, WriteWin)


# -- F3 ---------------------------------------------------------------------------------


def test_a_slow_viewer_open_shows_the_box_and_cancel_opens_nothing(files, monkeypatch):
    import navigator.viewer as viewer_model

    release = held(monkeypatch, viewer_model.ViewSource, "__init__")
    monkeypatch.setattr(loading, "SLOW_PROGRESS_DELAY", 0.05)
    monkeypatch.setattr("navigator.progress.SLOW_PROGRESS_DELAY", 0.05)
    app = navigator(files)
    seen = []

    def windows(a):
        from navigator.widgets.viewer.file_window import FileWindow
        return [w for w in a.shell.desktop.windows() if isinstance(w, FileWindow)]

    run_app(app, [go_to("one.txt"), KeyEvent("f3"), Until(writewin),
                  lambda a: seen.append(a.modal.notice), KeyEvent("escape"),
                  Until(lambda a: a.modal is None), lambda a: release.set(),
                  lambda a: None, lambda a: seen.append(len(windows(a)))])
    assert seen == ["Reading file", 0]


# -- the quick view ---------------------------------------------------------------------


def test_the_quick_view_shows_only_the_file_the_cursor_ended_on(files, monkeypatch):
    import navigator.widgets.viewer.quick_viewer.quick_viewer as quick_module

    release = held(monkeypatch, quick_module, "ViewSource",
                   when=lambda path: Path(path).name == "one.txt")
    app = navigator(files)
    seen = []
    run_app(app, [go_to("two.txt"), KeyEvent("q", ctrl=True), lambda a: None,
                  go_to("one.txt"), lambda a: None,        # one.txt hangs...
                  go_to("two.txt"),                        # ...and the cursor moves on
                  Until(lambda a: a.manager.quick.viewer.path == files / "two.txt"),
                  lambda a: release.set(), lambda a: None, lambda a: None,
                  lambda a: seen.append(a.manager.quick.viewer.path)])
    assert seen == [files / "two.txt"]


# -- the tree ---------------------------------------------------------------------------


def test_a_slow_count_leaves_the_line_blank_and_the_tree_moving(files, monkeypatch):
    import navigator.widgets.tree.directory_tree.directory_tree as tree_module

    release = held(monkeypatch, tree_module, "count_files")
    app = navigator(files)
    seen = {}

    def look(a):
        tree = a.manager.tree
        seen.update(counted=dict(tree._counts), cursor=tree.cursor)

    run_app(app, [KeyEvent("t", ctrl=True), lambda a: None, lambda a: None, look,
                  lambda a: release.set(),
                  Until(lambda a: a.manager.tree.selected_path in a.manager.tree._counts),
                  lambda a: seen.update(after=a.manager.tree._counts[a.manager.tree.selected_path])])
    assert seen["counted"] == {}  # nothing counted while the count waited
    assert seen["after"] == (2, 8)


def test_a_slow_probe_shows_a_branch_until_it_answers(files, monkeypatch):
    import navigator.widgets.tree.directory_tree.directory_tree as tree_module

    release = held(monkeypatch, tree_module, "_has_subdirectory",
                   when=lambda node: Path(node.data).name == "alpha")
    app = navigator(files)
    seen = []

    def alpha(a):
        tree = a.manager.tree
        return next(row for row in tree.items if row.node.name == "alpha")

    def open_here(a):
        tree = a.manager.tree
        tree.expand(tree.selected_node)

    run_app(app, [KeyEvent("t", ctrl=True), lambda a: None, open_here, lambda a: None,
                  lambda a: seen.append(a.manager.tree.branch(alpha(a))[-4:]),
                  lambda a: release.set(),
                  Until(lambda a: alpha(a).node._has_children is not None), lambda a: None,
                  lambda a: seen.append(a.manager.tree.branch(alpha(a))[-4:])])
    # ``[+]`` while the probe waits -- alpha holds no directory, so then none.
    assert seen[0] == "[+] "
    assert "[" not in seen[1]


# -- Alt+E ------------------------------------------------------------------------------


def test_a_slow_attributes_survey_shows_the_box(files, monkeypatch):
    from navigator import fileattr

    release = held(monkeypatch, fileattr, "survey")
    monkeypatch.setattr("navigator.progress.SLOW_PROGRESS_DELAY", 0.05)
    app = navigator(files)
    seen = []
    run_app(app, [go_to("one.txt"), KeyEvent("e", alt=True), Until(writewin),
                  lambda a: seen.append(a.modal.notice), lambda a: release.set(),
                  Until(lambda a: a.modal is not None and not writewin(a)),
                  lambda a: seen.append(type(a.modal).__name__), KeyEvent("escape"),
                  lambda a: None])
    assert seen == ["Reading file attributes", "AttrDialog"]


# -- the file dialog --------------------------------------------------------------------


def test_the_file_dialog_shows_the_directory_it_was_taken_to_last(files, monkeypatch):
    import navml.widgets.dialog.file_dialog.file_dialog as dialog_module

    (files / "slow").mkdir()
    (files / "slow" / "never.txt").write_text("")
    release = held(monkeypatch, dialog_module, "scan",
                   when=lambda directory, *rest: Path(directory).name == "slow")
    app = navigator(files)
    seen = []

    def go(name):
        return lambda a: a.modal._change_to(files / name if name else files, "*")

    def look(a):
        seen.append(([i.name for i in a.modal.files.items], a.modal.directory))

    # The editor's F3, *Open a File*, stands in for any file dialog.
    run_app(app, [go_to("one.txt"), KeyEvent("f4"), Until(lambda a: a.shell.desktop.active_window
                                                            .__class__.__name__ == "EditWindow"),
                  KeyEvent("f3"), Until(lambda a: a.modal is not None),
                  go("slow"), lambda a: None, go("alpha"),
                  Until(lambda a: [i.name for i in a.modal.files.items] == ["inner.txt"]),
                  lambda a: release.set(), lambda a: None, lambda a: None, look,
                  KeyEvent("escape"), lambda a: None])
    assert seen == [(["inner.txt"], files / "alpha")]
