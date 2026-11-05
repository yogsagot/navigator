"""File > Undo (Ctrl+Z): moves, renames, deletes to the Trash and F7's
directories taken back, newest first (:mod:`navigator.lib.file_ops.undo`)."""

from __future__ import annotations

import errno
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.drives import Location
from navigator.lib.file_ops import filecopy
from navigator.lib.file_ops.filecopy import ASK, MOVE, PRESERVE, CopyJob, CopyRequest, OverwriteAnswer, run
from navigator.lib.drives.local import LocalDrive
from navigator.lib.file_ops.undo import UNDO, Copied, History, MadeDirectory, Moved, Renamed, Trashed
from navigator.settings import SETTINGS
from navigator.widgets.manager.commands import Undo


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def move(sources, target, cwd, answers=None):
    job = CopyJob(asker=lambda question: answers.pop(0) if answers else None)
    run(CopyRequest(list(sources), str(target), ASK, PRESERVE | MOVE), job, cwd)
    return job


@pytest.fixture
def tree(tmp_path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    dst.mkdir()
    write(src / "a.txt", "alpha")
    write(src / "sub" / "c.txt", "gamma")
    return src, dst


# -- the history ---------------------------------------------------------------------------


def test_the_history_is_newest_first_and_keeps_its_limit():
    history = History(limit=3)
    for n in range(5):
        history.push(MadeDirectory(Location.of(Path(f"/d{n}"))))
    assert len(history) == 3
    assert history.pop().location.name == "d4"
    assert history.peek().location.name == "d3"
    history.clear()
    assert not history and history.pop() is None


def test_each_entry_asks_in_words():
    here = Location.of(Path("/home/u"))
    assert Renamed(((here, "a", "b"),)).question() == "Rename b back to a?"
    assert Renamed(((here, "a", "b"), (here, "c", "d"))).question() == "Give 2 files their old names back?"
    assert Renamed(((here, "c", "d"), (here, "a", "b"))).undo_pairs() == [(here, "b", "a"), (here, "d", "c")]
    moved = Moved(((here / "a", Location.of(Path("/tmp/a"))), (here / "b", Location.of(Path("/tmp/b")))), 1)
    assert moved.question() == "Move 2 entries back to /home/u?\nThe file it replaced cannot be brought back."
    assert MadeDirectory(here / "new").question() == "Remove the new directory new?"


# -- what a move records ---------------------------------------------------------------------


def test_a_move_on_one_file_system_records_each_source_whole(tree, tmp_path):
    src, dst = tree
    job = move([src / "a.txt", src / "sub"], dst, tmp_path)
    assert job.moved == [(Location.of(src / "a.txt"), Location.of(dst / "a.txt")),
                         (Location.of(src / "sub"), Location.of(dst / "sub"))]
    assert job.replaced == 0


def test_a_move_across_file_systems_records_a_directory_made_anew_as_one(tree, tmp_path, monkeypatch):
    src, dst = tree

    def cross(*args, **kwargs):
        raise OSError(errno.EXDEV, "Invalid cross-device link")

    monkeypatch.setattr(filecopy.os, "rename", cross)
    monkeypatch.setattr(filecopy.os, "replace", cross)
    job = move([src / "sub"], dst, tmp_path)
    assert job.moved == [(Location.of(src / "sub"), Location.of(dst / "sub"))]


def test_a_directory_merged_into_one_there_records_its_children(tree, tmp_path):
    src, dst = tree
    write(dst / "sub" / "old.txt", "kept")
    job = move([src / "sub"], dst, tmp_path)
    assert job.moved == [(Location.of(src / "sub" / "c.txt"), Location.of(dst / "sub" / "c.txt"))]


def test_a_rename_answer_records_where_the_file_went_and_an_overwrite_is_counted(tree, tmp_path):
    src, dst = tree
    write(dst / "a.txt", "there")
    job = move([src / "a.txt"], dst, tmp_path, answers=[OverwriteAnswer("rename", name="a2.txt")])
    assert job.moved == [(Location.of(src / "a.txt"), Location.of(dst / "a2.txt"))]
    write(src / "a.txt", "again")
    job = move([src / "a.txt"], dst, tmp_path, answers=[OverwriteAnswer("overwrite")])
    assert job.replaced == 1


# -- the file manager -------------------------------------------------------------------------


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    work = tmp_path / "work"
    for name in ("a.txt", "b.txt"):
        write(work / name, name)
    (tmp_path / "away").mkdir()
    return work


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def listed(name: str):
    return Until(lambda a: name in [e.name for e in a.manager.left.items])


def on(name: str):
    def act(a):
        panel = a.manager.active_panel
        panel.cursor = [e.name for e in panel.items].index(name)
    return act


def asked(a) -> bool:
    return a.modal is not None and a.modal.title == "Undo"


def ctrl_z() -> list:
    return [KeyEvent("z", ctrl=True), Until(asked), KeyEvent("enter")]


def test_undo_is_disabled_with_nothing_done(place):
    seen = {}
    run_app(navigator(place), [listed("a.txt"), lambda a: seen.update(undo=a.command_enabled(Undo()))])
    assert seen == {"undo": False}


def test_ctrl_z_moves_files_back_even_into_a_directory_gone_since(place, tmp_path):
    away = tmp_path / "away"
    write(place / "sub" / "c.txt", "gamma")

    def go(a):
        panel = a.manager.left
        request = CopyRequest([place / "sub"], str(away) + "/", ASK, PRESERVE | MOVE)
        a.spawn(a.manager._run_copy(panel, request, panel.location, move=True))

    def drop_place(a):
        for name in ("a.txt", "b.txt"):
            (place / name).rename(away / name)
        place.rmdir()

    run_app(navigator(place), [listed("sub"), go, Until(lambda a: (away / "sub" / "c.txt").exists()),
                               Until(lambda a: len(UNDO) == 1), drop_place, *ctrl_z(),
                               Until(lambda a: (place / "sub" / "c.txt").exists()), lambda a: None])
    assert not (away / "sub").exists()
    assert not UNDO


def test_ctrl_z_takes_back_alt_f6s_rename(place):
    def rename(a):
        a.spawn(a.manager._rename_entry(a.manager.left, a.manager.left.selected, "renamed.txt"))

    run_app(navigator(place), [listed("a.txt"), on("a.txt"), rename,
                               Until(lambda a: (place / "renamed.txt").exists()), *ctrl_z(),
                               Until(lambda a: (place / "a.txt").exists()), lambda a: None])
    assert not (place / "renamed.txt").exists()


def test_ctrl_z_restores_what_f8_moved_to_the_trash(place, monkeypatch):
    from navigator.widgets.file_ops.delete_dialog import DeleteDialog

    monkeypatch.setattr(SETTINGS.file_manager, "use_trash", True)
    run_app(navigator(place), [
        listed("a.txt"), on("a.txt"), KeyEvent("f8"), Until(lambda a: isinstance(a.modal, DeleteDialog)),
        KeyEvent("enter"), Until(lambda a: not (place / "a.txt").exists()),
        Until(lambda a: isinstance(UNDO.peek(), Trashed)), *ctrl_z(),
        Until(lambda a: (place / "a.txt").exists()), lambda a: None,
    ])
    assert (place / "a.txt").read_text() == "a.txt"


def test_ctrl_z_removes_f7s_directory_but_never_a_full_one(place):
    def fill(name):
        def act(a):
            a.modal.entry.value = name
        return act

    seen = {}
    run_app(navigator(place), [
        listed("a.txt"), KeyEvent("f7"), Until(lambda a: a.modal is not None), fill("empty"), KeyEvent("enter"),
        Until(lambda a: (place / "empty").is_dir()),
        KeyEvent("f7"), Until(lambda a: a.modal is not None), fill("full"), KeyEvent("enter"),
        Until(lambda a: (place / "full").is_dir()),
        lambda a: write(place / "full" / "inside.txt", "x"),
        *ctrl_z(), Until(lambda a: a.modal is not None and a.modal.title == "Error"),
        lambda a: seen.update(prompt=a.modal.prompt), KeyEvent("enter"),
        Until(lambda a: a.modal is None), *ctrl_z(),
        Until(lambda a: not (place / "empty").exists()), lambda a: None,
        lambda a: seen.update(left=len(UNDO)),
    ])
    assert seen["prompt"] == "full is not empty any more"
    assert (place / "full" / "inside.txt").exists()
    assert seen["left"] == 0


def test_two_operations_are_taken_back_newest_first(place):
    def rename(old, new):
        def act(a):
            on(old)(a)
            a.spawn(a.manager._rename_entry(a.manager.left, a.manager.left.selected, new))
        return act

    run_app(navigator(place), [
        listed("a.txt"), rename("a.txt", "x.txt"), Until(lambda a: len(UNDO) == 1), listed("x.txt"),
        rename("x.txt", "y.txt"), Until(lambda a: len(UNDO) == 2),
        *ctrl_z(), Until(lambda a: (place / "x.txt").exists()),
        *ctrl_z(), Until(lambda a: (place / "a.txt").exists()), lambda a: None,
    ])
    assert not UNDO and not (place / "y.txt").exists()


def test_ctrl_z_is_the_command_lines_while_it_has_text(place):
    seen = {}
    run_app(navigator(place), [
        listed("a.txt"), lambda a: UNDO.push(MadeDirectory(Location.of(place / "d"))),
        KeyEvent("l", "l"), KeyEvent("z", ctrl=True), lambda a: None,
        lambda a: seen.update(modal=a.modal, enabled=a.command_enabled(Undo(by_key=True))),
    ])
    assert seen == {"modal": None, "enabled": False}


# -- copies --------------------------------------------------------------------------------------


def copy(sources, target, cwd, answers=None):
    job = CopyJob(asker=lambda question: answers.pop(0) if answers else None)
    run(CopyRequest(list(sources), str(target), ASK, PRESERVE), job, cwd)
    return job


def test_a_copy_records_what_it_made_a_new_directory_as_one(tree, tmp_path):
    from navigator.lib.file_ops import uncopy

    src, dst = tree
    job = copy([src / "a.txt", src / "sub"], dst, tmp_path)
    assert [dest for dest, _ in job.copied] == [Location.of(dst / "a.txt"), Location.of(dst / "sub")]
    kind, listing = job.copied[1][1]
    assert kind == uncopy.DIR and {entry[0] for entry in listing} == {"c.txt"}
    assert uncopy.check(job.copied, lambda location: LocalDrive()) == ([dest for dest, _ in job.copied], [])


def test_a_copy_into_a_directory_there_records_each_file_and_counts_an_overwrite(tree, tmp_path):
    src, dst = tree
    write(dst / "sub" / "old.txt", "kept")
    write(dst / "a.txt", "there")
    job = copy([src / "a.txt", src / "sub"], dst, tmp_path, answers=[OverwriteAnswer("overwrite")])
    assert [dest for dest, _ in job.copied] == [Location.of(dst / "sub" / "c.txt")]
    assert job.overwritten == 1


def test_what_changed_since_the_copy_is_kept_and_what_is_gone_is_neither(tree, tmp_path):
    import os

    from navigator.lib.file_ops import uncopy

    src, dst = tree
    write(src / "b.txt", "beta")
    job = copy([src / "a.txt", src / "b.txt", src / "sub"], dst, tmp_path)
    write(dst / "a.txt", "edited and longer")
    write(dst / "sub" / "new.txt", "added")
    os.unlink(dst / "b.txt")
    same, changed = uncopy.check(job.copied, lambda location: LocalDrive())
    assert same == [] and changed == [Location.of(dst / "a.txt"), Location.of(dst / "sub")]


def test_the_question_says_where_the_copies_go():
    here = Location.of(Path("/home/u"))
    on_disk = Copied(((here / "a", (0, 1, 0.0)), (here / "b", (0, 1, 0.0))), overwritten=1)
    assert on_disk.question() == ("Remove the 2 entries copied to /home/u?\nThey go to the Trash.\n"
                                  "The file it overwrote cannot be brought back.")
    from navigator.lib.drives.memory import MemoryDrive

    remote = Copied(((MemoryDrive("q").location("/x"), (0, 1, 0.0)),))
    assert remote.question() == f"Remove x, copied to {remote.pairs[0][0].parent}?\nIt is erased for good."


def copy_in_app(sources, target):
    def act(a):
        panel = a.manager.left
        request = CopyRequest(list(sources), str(target), ASK, PRESERVE)
        a.spawn(a.manager._run_copy(panel, request, panel.location, move=False))
    return act


def test_ctrl_z_sends_the_copies_to_the_trash_and_keeps_the_originals(place, tmp_path):
    away = tmp_path / "away"
    write(place / "sub" / "c.txt", "gamma")
    seen = {}
    run_app(navigator(place), [
        listed("sub"), copy_in_app([place / "a.txt", place / "sub"], str(away) + "/"),
        Until(lambda a: isinstance(UNDO.peek(), Copied)), *ctrl_z(),
        Until(lambda a: not (away / "sub").exists() and not (away / "a.txt").exists()), lambda a: None,
        lambda a: seen.update(left=len(UNDO)),
    ])
    trash = tmp_path / "data" / "Trash" / "files"
    assert sorted(p.name for p in trash.iterdir()) == ["a.txt", "sub"]
    assert (place / "a.txt").exists() and (place / "sub" / "c.txt").exists()
    assert seen["left"] == 0


def test_ctrl_z_keeps_a_copy_edited_since_and_says_so(place, tmp_path):
    away = tmp_path / "away"
    seen = {}
    run_app(navigator(place), [
        listed("a.txt"), copy_in_app([place / "a.txt", place / "b.txt"], str(away) + "/"),
        Until(lambda a: isinstance(UNDO.peek(), Copied)),
        lambda a: write(away / "a.txt", "edited since the copy"),
        *ctrl_z(), Until(lambda a: a.modal is not None and a.modal.title == "Undo"),
        lambda a: seen.update(prompt=a.modal.prompt), KeyEvent("enter"),
        Until(lambda a: not (away / "b.txt").exists()), lambda a: None,
    ])
    assert seen["prompt"] == f"1 entry changed since the copy, kept:\n{away / 'a.txt'}"
    assert (away / "a.txt").read_text() == "edited since the copy"


def test_ctrl_z_erases_a_copy_on_another_drive_for_good(place, tmp_path):
    from navigator.lib.drives import mount, unmount
    from navigator.lib.drives.memory import MemoryDrive

    drive = mount(MemoryDrive("undo"))
    drive.make("/in")
    target = drive.location("/in")
    try:
        run_app(navigator(place), [
            listed("a.txt"), copy_in_app([place / "a.txt"], str(target) + "/"),
            Until(lambda a: isinstance(UNDO.peek(), Copied)), *ctrl_z(),
            Until(lambda a: not drive.exists(target / "a.txt")), lambda a: None,
        ])
    finally:
        unmount(drive.site)
    assert not (tmp_path / "data" / "Trash" / "files").exists()
    assert (place / "a.txt").exists()
