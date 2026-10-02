"""F8 and Del: the Delete dialog, its questions, its progress box, and the command end to end."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

import pytest

from conftest import FakeTerminal, settle

from navkit.application import Application
from navkit.events import KeyEvent
from navkit.screen import ScreenBuffer

from navigator import fileerase
from navigator.widgets.manager.commands import Delete, DeleteSingle
from navigator.fileerase import EraseRequest, NotEmpty, ReadOnly
from navigator.widgets.file_ops.delete_dialog import DeleteDialog
from navigator.widgets.file_ops.delete_dialog import delete_dialog as delete_dialog_module
from navigator.widgets.file_ops.delete_dialog.delete_dialog import RECURSIVE, cut, prompt_for
from navigator.widgets.file_ops.delete_progress import DeleteProgress
from navigator.widgets.file_ops.erase_query import EraseQuery
from navigator.widgets.manager.panel import DirEntry
from navigator.widgets.shell.shell import Shell


@pytest.fixture(autouse=True)
def fresh_session(monkeypatch):
    monkeypatch.setattr(delete_dialog_module, "_session", {"recursive": False})


def entry(name: str, is_dir: bool = False) -> DirEntry:
    return DirEntry(name, is_dir, 0)


# -- the dialogs ---------------------------------------------------------------------


def test_the_prompt_says_what_is_being_deleted():
    assert prompt_for([entry("f.txt")]) == "file ~f.txt~?"
    assert prompt_for([entry("src", True)]) == "directory ~src~?"
    assert prompt_for([entry("a"), entry("b"), entry("c")]) == "these ~3 files~?"
    assert prompt_for([entry("a~b")]) == "file ~a~~b~?"


def test_a_long_name_loses_its_middle():
    name = "a" * 30 + "b" * 30
    assert len(cut(name)) == 40
    assert cut(name).startswith("a" * 18) and cut(name).endswith("b" * 19)


def test_yes_answers_a_request_and_recursive_is_remembered(tmp_path):
    dialog = DeleteDialog(entries=[entry("f.txt"), entry("d", True)], here=tmp_path)
    assert dialog.title == "Delete"
    assert dialog.ok.text == "~Y~es" and dialog.cancel.text == "~N~o"
    assert dialog.options.value == 0
    assert dialog.accept() == EraseRequest([tmp_path / "f.txt", tmp_path / "d"], recursive=False)
    dialog.options.value = RECURSIVE
    assert dialog.accept().recursive is True
    again = DeleteDialog(entries=[entry("f.txt")], here=tmp_path)
    assert again.options.value == RECURSIVE


def test_the_dialog_opens_with_the_focus_on_yes(tmp_path):
    dialog = DeleteDialog(entries=[entry("f.txt")], here=tmp_path)
    assert dialog.focusable()[0] is dialog.ok


def test_the_query_orders_its_buttons_by_kind(tmp_path):
    directory = EraseQuery(question=NotEmpty(tmp_path / "d"))
    assert directory.buttons_row == (
        directory.refuse, directory.agree, directory.every, directory.abandon
    )
    assert directory.default_button is directory.refuse
    assert "Directory d\nis not empty." in directory.details.text

    readonly = EraseQuery(question=ReadOnly(tmp_path / "f"))
    assert readonly.kind == "read-only"
    assert readonly.buttons_row == (readonly.agree, readonly.refuse, readonly.every)
    assert readonly.default_button is readonly.agree
    assert not readonly.abandon.visible
    assert "is write-protected." in readonly.details.text


def test_the_progress_box_counts_and_cancels():
    box = DeleteProgress()
    assert box.title == "Erase" and box.ok.text == "~C~ancel"
    assert box.count(1234, 5000, 24) == "1,234 of 5,000 (24%)"
    assert box.count(0, 0, 0) == ""
    assert box.accept() is None


# -- end to end ----------------------------------------------------------------------


@pytest.fixture
def two(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "one.txt").write_text("one")
    (a / "two.txt").write_text("two")
    (a / "full").mkdir()
    (a / "full" / "x").write_text("x")
    return a, b


def run_shell(a: Path, b: Path, steps):
    async def main():
        shell = Shell(a, b)
        app = Application(shell, terminal=FakeTerminal(width=80, height=24))
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.1)
        try:
            return await steps(app, shell)
        finally:
            app.exit()
            await task

    return asyncio.run(main())


def screen_text(app) -> str:
    """What is on the screen, one line a row, the dialogs' text as one run each."""
    buffer = ScreenBuffer(80, 24)
    app.root.render_tree(buffer)
    return "\n".join(
        "".join(buffer.get(x, y)[0] or " " for x in range(buffer.width)) for y in range(24)
    )


def put_cursor(panel, name: str) -> None:
    panel.cursor = next(i for i, e in enumerate(panel.items) if e.name == name)


def test_f8_deletes_what_is_tagged_and_untags_it(two):
    a, b = two

    async def steps(app, shell):
        panel = shell.manager.left
        panel.marked = frozenset({"one.txt", "two.txt"})
        app.post_event(KeyEvent("f8"))
        await asyncio.sleep(0.06)
        asked = app.modal
        painted = screen_text(app)
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.2)
        return asked, painted, app.modal, panel.marked

    asked, painted, after, marked = run_shell(a, b, steps)
    assert isinstance(asked, DeleteDialog)
    assert "Do you wish to delete" in painted and "these 2 files?" in painted
    assert "Recursive delete" in painted
    assert after is None
    assert not (a / "one.txt").exists() and not (a / "two.txt").exists()
    assert marked == frozenset()


def test_no_deletes_nothing(two):
    a, b = two

    async def steps(app, shell):
        put_cursor(shell.manager.left, "one.txt")
        app.post_event(KeyEvent("f8"))
        await asyncio.sleep(0.06)
        app.post_event(KeyEvent("n", alt=True))
        await asyncio.sleep(0.1)
        return app.modal

    assert run_shell(a, b, steps) is None
    assert (a / "one.txt").exists()


def test_del_deletes_with_the_line_empty_and_edits_it_otherwise(two):
    a, b = two

    async def steps(app, shell):
        put_cursor(shell.manager.left, "one.txt")
        shell.command_line.set_text("abc")
        settle()
        typed = shell.manager.enables(Delete(by_key=True))
        by_menu = shell.manager.enables(Delete())
        shell.command_line.set_text("")
        settle()
        app.post_event(KeyEvent("delete"))
        await asyncio.sleep(0.06)
        return typed, by_menu, app.modal

    typed, by_menu, modal = run_shell(a, b, steps)
    assert typed is False and by_menu is True
    assert isinstance(modal, DeleteDialog)


def test_shift_f8_ignores_the_tags(two):
    a, b = two

    async def steps(app, shell):
        panel = shell.manager.left
        panel.marked = frozenset({"two.txt"})
        put_cursor(panel, "one.txt")
        app.post_event(KeyEvent("f8", shift=True))
        await asyncio.sleep(0.06)
        painted = screen_text(app)
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.2)
        return painted, panel.marked

    painted, marked = run_shell(a, b, steps)
    assert "file one.txt?" in painted
    assert not (a / "one.txt").exists() and (a / "two.txt").exists()
    assert marked == frozenset({"two.txt"})


def test_delete_is_disabled_on_dot_dot(two):
    a, b = two

    async def steps(app, shell):
        manager = shell.manager
        caption = app.bindings(manager.left).get("f8")
        put_cursor(manager.left, "one.txt")
        settle()
        on_file = manager.enables(Delete()), manager.enables(DeleteSingle())
        manager.left.cursor = 0
        settle()
        return type(caption), on_file, (manager.enables(Delete()), manager.enables(DeleteSingle()))

    kind, on_file, on_dots = run_shell(a, b, steps)
    assert kind is Delete
    assert on_file == (True, True) and on_dots == (False, False)


def test_a_non_empty_directory_asks_and_no_keeps_it(two):
    a, b = two

    async def steps(app, shell):
        put_cursor(shell.manager.left, "full")
        app.post_event(KeyEvent("f8"))
        await asyncio.sleep(0.06)
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.3)
        asked = app.modal
        painted = screen_text(app)
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.2)
        return asked, painted, app.modal

    asked, painted, after = run_shell(a, b, steps)
    assert isinstance(asked, EraseQuery)
    assert "is not empty." in painted
    assert after is None
    assert (a / "full" / "x").exists()


def test_recursive_deletes_a_non_empty_directory_unasked(two):
    a, b = two
    delete_dialog_module._session["recursive"] = True

    async def steps(app, shell):
        put_cursor(shell.manager.left, "full")
        app.post_event(KeyEvent("f8"))
        await asyncio.sleep(0.06)
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.3)
        return app.modal

    assert run_shell(a, b, steps) is None
    assert not (a / "full").exists()


def test_cancel_on_the_progress_box_asks_before_it_stops(two, monkeypatch):
    a, b = two
    seen: dict = {}

    def slow(request, job):
        job.total, job.measuring = 10, False
        job.action, job.path = fileerase.ERASING_FILE, str(request.sources[0])
        while not job.stopped:
            job.wait_while_paused()
            time.sleep(0.01)
        seen["stopped"] = True
        return []

    monkeypatch.setattr(fileerase, "run", slow)

    async def steps(app, shell):
        put_cursor(shell.manager.left, "one.txt")
        app.post_event(KeyEvent("f8"))
        await asyncio.sleep(0.06)
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.4)
        box = app.modal
        painted = screen_text(app)
        app.post_event(KeyEvent("escape"))
        await asyncio.sleep(0.2)
        abort = app.modal
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.3)
        return box, painted, abort, app.modal

    box, painted, abort, after = run_shell(a, b, steps)
    assert isinstance(box, DeleteProgress)
    assert "Erasing the file" in painted and "Cancel" in painted
    assert abort is not None and "Abort operation?" == abort.prompt
    assert [b.text for b in abort.buttons_row if b.visible] == ["~Y~es", "~N~o"]
    assert after is None and seen == {"stopped": True}
    assert (a / "one.txt").exists()


def test_the_file_menu_has_both_entries(two):
    a, b = two

    async def steps(app, shell):
        menu = app.root.menu.file
        return (
            (menu.item_for(Delete).text, menu.item_for(Delete).key),
            (menu.item_for(DeleteSingle).text, menu.item_for(DeleteSingle).key),
        )

    whole, single = run_shell(a, b, steps)
    assert whole == ("~D~elete", "F8")
    assert single == ("Delete single file", "Shift-Del")
