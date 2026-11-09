"""Shift+F5: the Create link dialog, the links it makes (symbolic and hard), and the command end to end."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

from conftest import FakeTerminal, settle, started, wait_until

from navkit.application import Application
from navkit.events import KeyEvent

from navml.history import HISTORY

from navigator.lib.file_ops import filelink
from navigator.widgets.manager.commands import MakeLink
from navigator.lib.file_ops.filelink import LinkRequest, link_path, make_link
from navigator.widgets.file_ops.link_dialog import LinkDialog
from navigator.widgets.file_ops.link_dialog import link_dialog as link_dialog_module
from navigator.widgets.file_ops.link_dialog.link_dialog import HARD, RELATIVE, SYMBOLIC, prompt_for
from navigator.widgets.manager.panel import DirEntry
from navigator.widgets.shell.shell import Shell


@pytest.fixture(autouse=True)
def fresh_session(monkeypatch):
    monkeypatch.setattr(link_dialog_module, "_session", {"relative": False, "hard": False})


def entry(name: str, is_dir: bool = False) -> DirEntry:
    return DirEntry(name, is_dir, 0)


# -- the dialog ----------------------------------------------------------------------


def test_the_prompt_says_what_is_being_linked():
    assert prompt_for([entry("f.txt")]) == "Create ~s~ymlink to file ~f.txt~ in"
    assert prompt_for([entry("src", True)]) == "Create ~s~ymlink to Directory ~src~ in"
    assert prompt_for([entry("a"), entry("b"), entry("c")]) == "Create ~s~ymlink to ~3 files~ in"
    assert prompt_for([entry("a~b")]) == "Create ~s~ymlink to file ~a~~b~ in"


def test_the_dialog_opens_on_the_other_panel(tmp_path):
    dialog = LinkDialog(entries=[entry("f.txt")], here=tmp_path / "a", other=tmp_path / "b")
    assert dialog.title == "Create link"
    assert dialog.target.value == f"{tmp_path / 'b'}/f.txt"
    assert dialog.target.entry.selected_text == dialog.target.value
    assert dialog.options.value == 0
    assert f"{tmp_path / 'b'}/" in HISTORY.entries("link")


def test_ok_answers_a_request_and_relative_is_remembered(tmp_path):
    dialog = LinkDialog(entries=[entry("f.txt"), entry("g")], here=tmp_path, other=tmp_path / "b")
    dialog.options.value = RELATIVE
    assert dialog.accept() == LinkRequest(
        [tmp_path / "f.txt", tmp_path / "g"], f"{tmp_path / 'b'}/", relative=True
    )
    again = LinkDialog(entries=[entry("f.txt")], here=tmp_path, other=tmp_path / "b")
    assert again.options.value == RELATIVE


def test_the_prompt_says_a_hard_link():
    assert prompt_for([entry("f.txt")], hard=True) == "Create hard ~l~ink to file ~f.txt~ in"
    assert prompt_for([entry("a"), entry("b")], hard=True) == "Create hard ~l~inks to ~2 files~ in"


def test_hard_greys_relative_follows_the_prompt_and_is_remembered(tmp_path):
    dialog = LinkDialog(entries=[entry("f.txt")], here=tmp_path, other=tmp_path / "b")
    dialog.mounted()
    assert dialog.kind.value == SYMBOLIC and dialog.options.enable_mask == -1
    dialog.options.value = RELATIVE
    dialog.kind.value = HARD
    settle()
    assert dialog.options.enable_mask == 0
    assert dialog.prompt_caption.text == "Create hard ~l~ink to file ~f.txt~ in"
    request = dialog.accept()
    assert request.hard and not request.relative  # a hard link holds no path
    again = LinkDialog(entries=[entry("f.txt")], here=tmp_path, other=tmp_path / "b")
    assert again.kind.value == HARD
    assert again.prompt_caption.text == "Create hard ~l~ink to file ~f.txt~ in"


def test_hard_is_greyed_where_the_drive_cannot(tmp_path):
    link_dialog_module._session["hard"] = True
    dialog = LinkDialog(entries=[entry("f.txt")], here=tmp_path, other=tmp_path, can_hard=False)
    assert dialog.kind.value == SYMBOLIC
    assert not dialog.kind.item_enabled(HARD) and dialog.kind.item_enabled(SYMBOLIC)


def test_an_empty_line_answers_nothing(tmp_path):
    dialog = LinkDialog(entries=[entry("f.txt")], here=tmp_path, other=tmp_path)
    assert dialog.accept() is None


# -- the model -----------------------------------------------------------------------


def test_a_link_holds_an_absolute_or_a_relative_path(tmp_path):
    source, dest = tmp_path / "a" / "f.txt", tmp_path / "b" / "c" / "f.txt"
    assert link_path(source, dest, relative=False) == str(source)
    assert link_path(source, dest, relative=True) == "../../a/f.txt"


def test_make_link_links_and_refuses_what_exists(tmp_path):
    (tmp_path / "f.txt").write_text("x")
    make_link(tmp_path / "f.txt", tmp_path / "l", relative=True)
    assert os.readlink(tmp_path / "l") == "f.txt"
    assert (tmp_path / "l").read_text() == "x"
    # A dangling link is still in the way.
    os.symlink("nowhere", tmp_path / "dangling")
    with pytest.raises(FileExistsError):
        make_link(tmp_path / "f.txt", tmp_path / "dangling", relative=False)


def test_make_link_makes_a_hard_link_and_refuses_a_directory(tmp_path):
    import errno

    (tmp_path / "f.txt").write_text("f")
    make_link(tmp_path / "f.txt", tmp_path / "g.txt", relative=False, hard=True)
    assert (tmp_path / "g.txt").stat().st_ino == (tmp_path / "f.txt").stat().st_ino
    assert (tmp_path / "f.txt").stat().st_nlink == 2
    with pytest.raises(FileExistsError):
        make_link(tmp_path / "f.txt", tmp_path / "g.txt", relative=False, hard=True)
    (tmp_path / "d").mkdir()
    with pytest.raises(OSError) as raised:
        make_link(tmp_path / "d", tmp_path / "e", relative=False, hard=True)
    assert raised.value.errno == errno.EISDIR  # not EPERM: no *As root* offered


def test_a_hard_link_to_a_symlink_is_the_symlink_itself(tmp_path):
    (tmp_path / "f.txt").write_text("f")
    (tmp_path / "s").symlink_to("f.txt")
    make_link(tmp_path / "s", tmp_path / "t", relative=False, hard=True)
    assert os.readlink(tmp_path / "t") == "f.txt"  # ``ln -P``
    assert (tmp_path / "t").lstat().st_ino == (tmp_path / "s").lstat().st_ino


def test_a_hard_link_is_refused_on_a_drive_that_cannot(tmp_path):
    import errno

    from navigator.lib.drives import Location, mount, unmount
    from navigator.lib.drives.memory import MemoryDrive

    drive = mount(MemoryDrive("hard"))
    try:
        drive.make("/a.txt", "a")
        with pytest.raises(OSError) as raised:
            filelink.make_hard_link(drive.location("/a.txt"), drive.location("/b.txt"))
        assert raised.value.errno == errno.EOPNOTSUPP
        with pytest.raises(OSError) as raised:
            filelink.make_hard_link(Location.of(tmp_path / "a"), drive.location("/b.txt"))
        assert raised.value.errno == errno.EXDEV
    finally:
        unmount(drive.site)


def test_a_link_to_nothing_is_made(tmp_path):
    make_link(tmp_path / "missing", tmp_path / "l", relative=False)
    assert os.readlink(tmp_path / "l") == str(tmp_path / "missing")


# -- end to end ----------------------------------------------------------------------


@pytest.fixture
def two(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "one.txt").write_text("one")
    (a / "two.txt").write_text("two")
    return a, b


def run_shell(a: Path, b: Path, steps):
    async def main():
        shell = Shell(a, b)
        app = Application(shell, terminal=FakeTerminal(width=80, height=24))
        task = asyncio.create_task(app.run_async())
        await started(app, shell.manager.left, shell.manager.right)
        try:
            return await steps(app, shell.manager)
        finally:
            app.exit()
            await task

    return asyncio.run(main())


async def until(predicate, timeout: float = 2.0) -> None:
    """Wait for *predicate* rather than a fixed time: the link is made on a thread,
    and the panel's re-read on another after it, both slower on a loaded runner."""
    loop = asyncio.get_running_loop()
    end = loop.time() + timeout
    while not predicate():
        assert loop.time() < end, "still waiting"
        await asyncio.sleep(0.01)


def put_cursor(panel, name: str) -> None:
    panel.cursor = next(i for i, e in enumerate(panel.items) if e.name == name)


def test_shift_f5_links_into_the_other_panel(two):
    a, b = two

    async def steps(app, manager):
        put_cursor(manager.left, "one.txt")
        start = len(app.terminal.frames)
        app.post_event(KeyEvent("f5", shift=True))
        await until(lambda: isinstance(app.modal, LinkDialog))
        await wait_until(lambda: " Create link " in "".join(app.terminal.frames[start:]))
        opened = app.modal
        # Every frame since the key, not the last: the clock may have
        # repainted its corner after the dialog's.
        painted = "".join(app.terminal.frames[start:])
        app.post_event(KeyEvent("enter"))
        await until(lambda: not app._tasks and "one.txt" in [e.name for e in manager.right.items])
        return opened, painted, app.modal, [e.name for e in manager.right.items]

    opened, painted, after, right = run_shell(a, b, steps)
    assert isinstance(opened, LinkDialog)
    assert " Create link " in painted
    assert after is None
    assert os.readlink(b / "one.txt") == str(a / "one.txt")
    assert "one.txt" in right


def test_the_other_panel_s_cursor_goes_to_the_link_made(two):
    """As F7's on its directory: the panel showing where the link went looks
    again with its cursor on it, not left on ``..``."""
    a, b = two

    async def steps(app, manager):
        put_cursor(manager.left, "one.txt")
        app.post_event(KeyEvent("f5", shift=True))
        await until(lambda: isinstance(app.modal, LinkDialog))
        app.post_event(KeyEvent("enter"))
        await until(lambda: not app._tasks and manager.right.selected is not None
                    and manager.right.selected.name == "one.txt")
        return manager.left.selected.name, manager.right.selected.name

    assert run_shell(a, b, steps) == ("one.txt", "one.txt")


def test_tagged_entries_are_each_linked_relatively_and_untagged(two):
    a, b = two

    async def steps(app, manager):
        manager.left.marked = frozenset({"one.txt", "two.txt"})
        app.post_event(KeyEvent("f5", shift=True))
        await wait_until(lambda: isinstance(app.modal, LinkDialog))
        app.modal.options.value = RELATIVE
        app.post_event(KeyEvent("enter"))
        await wait_until(lambda: app.modal is None and not manager.left.marked)
        return manager.left.marked

    marked = run_shell(a, b, steps)
    assert os.readlink(b / "one.txt") == "../a/one.txt"
    assert os.readlink(b / "two.txt") == "../a/two.txt"
    assert marked == frozenset()


def test_shift_f5_makes_a_hard_link_when_hard_is_chosen(two):
    a, b = two

    async def steps(app, manager):
        put_cursor(manager.left, "one.txt")
        app.post_event(KeyEvent("f5", shift=True))
        await until(lambda: isinstance(app.modal, LinkDialog))
        app.modal.kind.value = HARD
        app.post_event(KeyEvent("enter"))
        await until(lambda: not app._tasks and "one.txt" in [e.name for e in manager.right.items])
        return [e.nlink for e in manager.right.items if e.name == "one.txt"]

    counts = run_shell(a, b, steps)
    assert not (b / "one.txt").is_symlink()
    assert (b / "one.txt").stat().st_ino == (a / "one.txt").stat().st_ino
    assert counts == [2]


def test_a_link_in_the_way_asks_to_skip(two):
    a, b = two
    (b / "one.txt").write_text("old")

    async def steps(app, manager):
        put_cursor(manager.left, "one.txt")
        app.post_event(KeyEvent("f5", shift=True))
        await wait_until(lambda: isinstance(app.modal, LinkDialog))
        app.post_event(KeyEvent("enter"))
        await wait_until(lambda: app.modal is not None and not isinstance(app.modal, LinkDialog) and "exists" in app.terminal.painted)
        asked = app.modal
        painted = app.terminal.painted
        app.post_event(KeyEvent("enter"))
        await wait_until(lambda: app.modal is None)
        return asked, painted, app.modal

    asked, painted, after = run_shell(a, b, steps)
    assert asked is not None and asked.title == "Error"
    assert "exists" in painted
    assert after is None
    assert (b / "one.txt").read_text() == "old" and not (b / "one.txt").is_symlink()


def test_shift_f5_is_bound_and_disabled_on_dot_dot(two):
    a, b = two

    async def steps(app, manager):
        caption = app.bindings(manager.left).get("shift+f5")
        put_cursor(manager.left, "one.txt")
        settle()
        on_file = manager.enables(MakeLink())
        manager.left.cursor = 0
        settle()
        return type(caption), on_file, manager.enables(MakeLink())

    kind, on_file, on_dots = run_shell(a, b, steps)
    assert kind is MakeLink
    assert on_file is True and on_dots is False


def test_the_file_menu_has_the_entry(two):
    a, b = two

    async def steps(app, manager):
        item = app.root.menu.file.item_for(MakeLink)
        return item.text, item.key

    text, key = run_shell(a, b, steps)
    assert text == "Create ~l~ink..." and key == "Shift-F5"
