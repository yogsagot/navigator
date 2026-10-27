"""The freedesktop Trash: F8 moving files there, the ``trash:///`` drive,
Restore, Empty Trash and the ways in (navigator.lib.file_ops.trash,
navigator.lib.drives.trash).

``conftest`` points ``XDG_DATA_HOME`` into each test's own directory, so the
home trash here is ``tmp_path / "data" / "Trash"`` and never the user's.
"""

from __future__ import annotations

import errno
import os
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import DoubleClickEvent, KeyEvent

from navml.widgets.dialog.dialog import Dialog

from navigator.__main__ import Navigator
from navigator.lib.drives import drive_of
from navigator.lib.drives import trash as trash_drive
from navigator.lib.drives.location import Location
from navigator.lib.file_ops import fileerase, trash
from navigator.settings import SETTINGS
from navigator.widgets.file_ops.delete_dialog import DeleteDialog
from navigator.widgets.file_ops.delete_dialog import delete_dialog as delete_dialog_module
from navigator.widgets.file_ops.delete_dialog.delete_dialog import RECURSIVE, TRASH
from navigator.widgets.file_ops.erase_query import EraseQuery
from navigator.widgets.manager.commands import RestoreTrash
from navigator.widgets.manager.panel import DirEntry
from navigator.widgets.shell.commands import EmptyTrash, OpenTrash, ToggleTrashCan


@pytest.fixture(autouse=True)
def fresh_session(monkeypatch):
    monkeypatch.setattr(delete_dialog_module, "_session", {"recursive": False})


@pytest.fixture
def home(tmp_path) -> Path:
    return tmp_path / "data" / "Trash"


@pytest.fixture
def place(tmp_path, monkeypatch) -> Path:
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    work = tmp_path / "work"
    work.mkdir()
    for name in ("a.txt", "b.txt"):
        (work / name).write_text(name)
    (work / "full").mkdir()
    (work / "full" / "inside.txt").write_text("x")
    return work


def navigator(place: Path) -> Navigator:
    return Navigator(place, place, terminal=FakeTerminal(100, 30))


# -- the model -----------------------------------------------------------------------


def test_move_writes_the_info_file_and_renames_into_files(place, home):
    item = trash.move(place / "a.txt")
    assert not (place / "a.txt").exists()
    assert (home / "files" / "a.txt").read_text() == "a.txt"
    lines = (home / "info" / "a.txt.trashinfo").read_text().splitlines()
    assert lines[0] == "[Trash Info]"
    assert lines[1] == f"Path={place / 'a.txt'}"
    assert lines[2].startswith("DeletionDate=") and "T" in lines[2]
    assert item.original == place / "a.txt" and item.name == "a.txt"


def test_a_name_taken_gets_a_number_before_its_extension(place, home):
    trash.move(place / "a.txt")
    (place / "a.txt").write_text("again")
    second = trash.move(place / "a.txt")
    assert second.name == "a.2.txt"
    assert (home / "files" / "a.2.txt").read_text() == "again"


def test_the_path_is_percent_encoded_and_read_back(place):
    odd = place / "with space%.txt"
    odd.write_text("x")
    item = trash.move(odd)
    assert "Path=" + str(place).replace(" ", "%20") + "/with%20space%25.txt" in item.info.read_text()
    (listed,) = trash.items()
    assert listed.original == odd and listed.deleted is not None


def test_a_file_without_an_info_file_is_listed_and_an_info_without_a_file_is_not(home):
    (home / "files").mkdir(parents=True)
    (home / "info").mkdir()
    (home / "files" / "orphan").write_text("x")
    (home / "info" / "ghost.trashinfo").write_text("[Trash Info]\nPath=/ghost\n")
    assert [(item.name, item.original) for item in trash.items()] == [("orphan", None)]


def test_restore_puts_it_back_and_never_over_anything(place, home):
    item = trash.move(place / "full")
    (place / "full").mkdir()
    with pytest.raises(FileExistsError):
        trash.restore(item)
    (place / "full").rmdir()
    assert trash.restore(item) == place / "full"
    assert (place / "full" / "inside.txt").exists()
    assert not item.info.exists() and not item.path.exists()


def test_another_file_system_uses_its_own_trash(tmp_path, monkeypatch):
    top = tmp_path / "mnt"
    top.mkdir()
    victim = top / "f.txt"
    victim.write_text("x")
    real_stat = os.stat

    class Other:
        def __init__(self, st):
            self.st = st

        def __getattr__(self, name):
            return 1 if name == "st_dev" else getattr(self.st, name)

    def lstat(path, *a, **k):
        st = real_stat(path, *a, follow_symlinks=False, **k)
        return Other(st) if str(path).startswith(str(top)) else st

    monkeypatch.setattr(trash.os, "lstat", lstat)
    found = trash.trash_for(victim, mounts=["/", str(top)])
    assert found == (top / f".Trash-{os.getuid()}", top)
    item = trash.move(victim, mounts=["/", str(top)])
    assert f"Path=f.txt" in item.info.read_text()


def test_no_trash_is_exdev(place, monkeypatch):
    monkeypatch.setattr(trash, "trash_for", lambda path, mounts=None: None)
    with pytest.raises(OSError) as raised:
        trash.move(place / "a.txt")
    assert raised.value.errno == errno.EXDEV
    assert (place / "a.txt").exists()


# -- the eraser -------------------------------------------------------------------


def test_the_eraser_trashes_and_asks_before_erasing_what_cannot_go(place, monkeypatch):
    job = fileerase.EraseJob(asker=lambda question: pytest.fail(f"asked {question}"))
    done = fileerase.run(fileerase.EraseRequest([place / "full"], trash=True), job)
    assert done == [place / "full"] and trash.items()[0].name == "full"

    monkeypatch.setattr(trash, "trash_for", lambda path, mounts=None: None)
    asked = []
    job = fileerase.EraseJob(asker=lambda question: asked.append(question) or fileerase.NO)
    assert fileerase.run(fileerase.EraseRequest([place / "a.txt"], trash=True), job) == []
    assert isinstance(asked[0], fileerase.NoTrash) and (place / "a.txt").exists()
    job = fileerase.EraseJob(asker=lambda question: fileerase.YES)
    assert fileerase.run(fileerase.EraseRequest([place / "a.txt"], trash=True), job) == [place / "a.txt"]
    assert not (place / "a.txt").exists() and len(trash.items()) == 1


def test_the_no_trash_question_puts_no_first(place):
    query = EraseQuery(question=fileerase.NoTrash(place / "a.txt", "Invalid cross-device link"))
    assert query.default_button is query.refuse
    assert "Cannot move a.txt to the Trash" in query.details.text


# -- the dialog ----------------------------------------------------------------------


def test_the_box_is_offered_ticked_only_when_asked_for(tmp_path):
    entry = DirEntry("f.txt", False, 0)
    plain = DeleteDialog(entries=[entry], here=tmp_path)
    assert len(plain.options.items) == 1 and plain.accept().trash is False
    offered = DeleteDialog(entries=[entry], here=tmp_path, trash=True)
    assert len(offered.options.items) == 2 and offered.options.value == TRASH
    assert offered.prompt_head.text == "Do you wish to move to the Trash"
    assert offered.accept().trash is True
    offered.options.value = RECURSIVE
    assert offered.prompt_head.text == "Do you wish to delete"
    assert offered.accept().trash is False


# -- the file manager ----------------------------------------------------------------


def on(name: str):
    def act(a):
        panel = a.manager.active_panel
        panel.cursor = [e.name for e in panel.items].index(name)
    return act


def test_f8_moves_to_the_trash_when_set(place, home):
    SETTINGS.file_manager.use_trash = True
    seen = {}
    run_app(navigator(place), [
        on("a.txt"), KeyEvent("f8"), Until(lambda a: isinstance(a.modal, DeleteDialog)),
        lambda a: seen.update(head=a.modal.prompt_head.text), KeyEvent("enter"),
        Until(lambda a: not (place / "a.txt").exists()),
    ])
    assert seen["head"] == "Do you wish to move to the Trash"
    assert (home / "files" / "a.txt").exists()


def test_restore_is_not_in_the_file_menu_outside_the_trash(place):
    seen = {}

    def look(a):
        item = a.shell.menu.file_restore_trash
        seen.update(enabled=a.command_enabled(RestoreTrash), hidden=item.hidden,
                    listed=item in a.shell.menu.file.entries())

    run_app(navigator(place), [look])
    assert seen == {"enabled": False, "hidden": True, "listed": False}


def test_f8_erases_as_before_when_not_set(place, home):
    run_app(navigator(place), [
        on("a.txt"), KeyEvent("f8"), Until(lambda a: isinstance(a.modal, DeleteDialog)),
        lambda a: len(a.modal.options.items) == 1 or pytest.fail("offered"), KeyEvent("enter"),
        Until(lambda a: not (place / "a.txt").exists()),
    ])
    assert not (home / "files").exists()


def test_the_trash_drive_lists_restores_and_erases(place, home):
    SETTINGS.file_manager.use_trash = True
    trash.move(place / "a.txt")
    trash.move(place / "full")
    seen = {}

    def look(a):
        panel = a.manager.active_panel
        seen["names"] = sorted(e.name for e in panel.items)
        seen["title"] = drive_of(panel.location).get_dir(panel.location)
        on("full")(a)
        seen["line"] = panel._second_line(panel.selected)
        seen["restore"] = a.command_enabled(RestoreTrash)
        seen["in_file_menu"] = a.shell.menu.file_restore_trash in a.shell.menu.file.entries()

    run_app(navigator(place), [
        lambda a: a.spawn(a.run_command(OpenTrash)),
        Until(lambda a: trash_drive.is_trash(a.manager.active_panel.location)
              and len(a.manager.active_panel.items) == 3),
        look,
        lambda a: a.spawn(a.run_command(RestoreTrash)),
        Until(lambda a: (place / "full" / "inside.txt").exists()),
        Until(lambda a: [e.name for e in a.manager.active_panel.items] == ["..", "a.txt"]),
        on("a.txt"), KeyEvent("f8"), Until(lambda a: isinstance(a.modal, DeleteDialog)),
        lambda a: seen.update(offered=len(a.modal.options.items)), KeyEvent("enter"),
        Until(lambda a: not (home / "files" / "a.txt").exists()),
    ])
    assert seen["names"] == ["..", "a.txt", "full"]
    assert seen["title"] == "TRASH:/"
    assert seen["line"].startswith("From ") and "/full, deleted " in seen["line"]
    assert seen["restore"] is True and seen["in_file_menu"]
    assert seen["offered"] == 1
    assert not (home / "info" / "a.txt.trashinfo").exists()


@pytest.mark.parametrize("leave", ["dotdot", "backspace"])
def test_dotdot_and_backspace_leave_the_trash_for_where_the_panel_was(place, leave):
    trash.move(place / "a.txt")
    (place / "sub").mkdir()
    seen = {}

    def out(a):
        if leave == "dotdot":
            on("..")(a)
            a.post_event(KeyEvent("enter"))
        else:
            a.post_event(KeyEvent("backspace"))

    run_app(navigator(place), [
        lambda a: setattr(a.manager.active_panel, "path", place / "sub"),
        Until(lambda a: a.manager.active_panel.items and a.manager.active_panel.path == place / "sub"),
        lambda a: a.spawn(a.run_command(OpenTrash)),
        Until(lambda a: trash_drive.is_trash(a.manager.active_panel.location)
              and [e.name for e in a.manager.active_panel.items] == ["..", "a.txt"]),
        out,
        Until(lambda a: a.manager.active_panel.location.is_local),
        lambda a: seen.update(where=a.manager.active_panel.path),
    ])
    assert seen["where"] == place / "sub"


def test_empty_trash_asks_and_erases_everything(place, home):
    trash.move(place / "a.txt")
    trash.move(place / "full")
    run_app(navigator(place), [
        lambda a: a.spawn(a.run_command(EmptyTrash)), Until(lambda a: type(a.modal) is Dialog),
        KeyEvent("y", "y", alt=True), Until(lambda a: not trash.items()),
    ])
    assert list((home / "info").iterdir()) == [] and list((home / "files").iterdir()) == []


def test_the_trash_can_drop_trashes_and_its_double_click_opens_the_trash(place, home):
    from test_trash_can import drop_on_trash

    SETTINGS.file_manager.use_trash = True
    seen = {}

    def double(a):
        can = a.shell.trash
        a.post_event(DoubleClickEvent(can.x + 2, can.y + 1, button="left", action="press"))

    run_app(navigator(place), [
        lambda a: a.spawn(a.run_command(ToggleTrashCan)), lambda a: None,
        drop_on_trash("a.txt"), Until(lambda a: type(a.modal) is Dialog),
        lambda a: seen.update(prompt=a.modal.prompt), KeyEvent("y", "y", alt=True),
        Until(lambda a: not (place / "a.txt").exists()),
        double, Until(lambda a: trash_drive.is_trash(a.manager.active_panel.location)),
    ])
    assert seen["prompt"] == "Do you wish to move a.txt to the Trash?"
    assert (home / "files" / "a.txt").exists()


def test_a_trash_url_round_trips():
    where = Location.parse("trash:///a.txt")
    assert trash_drive.is_trash(where) and str(where) == "trash:///a.txt"
    assert str(trash_drive.location()) == "trash:///"


