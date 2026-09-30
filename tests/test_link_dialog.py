"""Shift+F5: the Create symlink dialog, the links it makes, and the command end to end."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

from conftest import FakeTerminal, settle

from navkit.application import Application
from navkit.events import KeyEvent

from navml.history import HISTORY

from navigator import filelink
from navigator.commands import MakeLink
from navigator.filelink import LinkRequest, link_path, make_link
from navigator.widgets.link_dialog import LinkDialog
from navigator.widgets.link_dialog import link_dialog as link_dialog_module
from navigator.widgets.link_dialog.link_dialog import RELATIVE, prompt_for
from navigator.widgets.panel import DirEntry
from navigator.widgets.shell import Shell


@pytest.fixture(autouse=True)
def fresh_session(monkeypatch):
    monkeypatch.setattr(link_dialog_module, "_session", {"relative": False})


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
    assert dialog.title == "Create symlink"
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
        await asyncio.sleep(0.1)
        try:
            return await steps(app, shell.manager)
        finally:
            app.exit()
            await task

    return asyncio.run(main())


def put_cursor(panel, name: str) -> None:
    panel.cursor = next(i for i, e in enumerate(panel.items) if e.name == name)


def test_shift_f5_links_into_the_other_panel(two):
    a, b = two

    async def steps(app, manager):
        put_cursor(manager.left, "one.txt")
        app.post_event(KeyEvent("f5", shift=True))
        await asyncio.sleep(0.06)
        opened = app.modal
        painted = app.terminal.frames[-1]
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.2)
        return opened, painted, app.modal, [e.name for e in manager.right.items]

    opened, painted, after, right = run_shell(a, b, steps)
    assert isinstance(opened, LinkDialog)
    assert " Create symlink " in painted
    assert after is None
    assert os.readlink(b / "one.txt") == str(a / "one.txt")
    assert "one.txt" in right


def test_tagged_entries_are_each_linked_relatively_and_untagged(two):
    a, b = two

    async def steps(app, manager):
        manager.left.marked = frozenset({"one.txt", "two.txt"})
        app.post_event(KeyEvent("f5", shift=True))
        await asyncio.sleep(0.06)
        app.modal.options.value = RELATIVE
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.2)
        return manager.left.marked

    marked = run_shell(a, b, steps)
    assert os.readlink(b / "one.txt") == "../a/one.txt"
    assert os.readlink(b / "two.txt") == "../a/two.txt"
    assert marked == frozenset()


def test_a_link_in_the_way_asks_to_skip(two):
    a, b = two
    (b / "one.txt").write_text("old")

    async def steps(app, manager):
        put_cursor(manager.left, "one.txt")
        app.post_event(KeyEvent("f5", shift=True))
        await asyncio.sleep(0.06)
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.2)
        asked = app.modal
        painted = app.terminal.painted
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.1)
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
    assert text == "Create ~s~ymlink..." and key == "Shift-F5"
