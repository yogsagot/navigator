"""F5 and F6: the Copy dialog, the columns its check boxes need, and the copy end to end."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from conftest import FakeTerminal, mounted, settle

from navkit.application import Application
from navkit.events import KeyEvent, MouseClickEvent

from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.control import caption_runs, escape_caption, parse_shortcut
from navml.widgets.dialog.radio_buttons import RadioButtons

from navigator import filecopy
from navigator.filecopy import ASK, CHECK_FREE, MOVE, OVERWRITE, PRESERVE, CopyRequest
from navigator.settings import SETTINGS
from navigator.widgets.file_ops.copy_dialog import CopyDialog
from navigator.widgets.file_ops.copy_dialog import copy_dialog as copy_dialog_module
from navigator.widgets.file_ops.copy_dialog.copy_dialog import prompt_for, target_for
from navigator.widgets.manager.panel import DirEntry
from navigator.widgets.shell.shell import Shell


@pytest.fixture(autouse=True)
def fresh_session(monkeypatch):
    monkeypatch.setattr(copy_dialog_module, "_session", {"mode": ASK, "options": PRESERVE})


def entry(name: str, is_dir: bool = False) -> DirEntry:
    return DirEntry(name, is_dir, 0)


# -- captions ------------------------------------------------------------------------


def test_every_marked_run_is_highlighted_and_the_first_is_the_shortcut():
    text = "~C~opy file ~a~~b.txt~ to"
    assert caption_runs(text) == [
        ("C", True), ("opy file ", False), ("a~b.txt", True), (" to", False),
    ]
    assert parse_shortcut(text)[2] == "c"
    assert escape_caption("a~b") == "a~~b"


# -- the prompt and the target --------------------------------------------------------


def test_the_prompt_says_what_is_being_copied():
    assert prompt_for([entry("a.txt")], move=False) == "~C~opy file ~a.txt~ to"
    assert prompt_for([entry("docs", True)], move=False) == "~C~opy Directory ~docs~ to"
    assert prompt_for([entry("a"), entry("b"), entry("c")], move=False) == "~C~opy ~3 files~ to"
    assert prompt_for([entry("a.txt")], move=True) == "~R~ename or move file ~a.txt~ to"
    assert prompt_for([entry("x~y")], move=False) == "~C~opy file ~x~~y~ to"


def test_the_target_is_the_other_panel(tmp_path):
    here, there = tmp_path / "a", tmp_path / "b"
    assert target_for([entry("f.txt")], here, there, move=False) == f"{there}/f.txt"
    assert target_for([entry("d", True)], here, there, move=False) == f"{there}/"
    assert target_for([entry("f"), entry("g")], here, there, move=False) == f"{there}/"


def test_with_nowhere_else_f5_is_blank_and_f6_renames_in_place(tmp_path):
    assert target_for([entry("f.txt")], tmp_path, tmp_path, move=False) == ""
    assert target_for([entry("f.txt")], tmp_path, tmp_path, move=True) == "f.txt"
    assert target_for([entry("f"), entry("g")], tmp_path, tmp_path, move=True) == ""


# -- the dialog ----------------------------------------------------------------------------


def test_the_dialog_opens_seeded(tmp_path):
    dialog = CopyDialog(entries=[entry("f.txt")], here=tmp_path / "a", other=tmp_path / "b")
    assert dialog.title == "Copy"
    assert dialog.prompt_caption.text == "~C~opy file ~f.txt~ to"
    assert dialog.target.value == f"{tmp_path / 'b'}/f.txt"
    assert dialog.target.entry.selected_text == dialog.target.value
    assert dialog.mode.value == ASK
    assert dialog.options.value == PRESERVE


def test_f6_ticks_remove_source(tmp_path):
    dialog = CopyDialog(entries=[entry("f.txt")], here=tmp_path, other=tmp_path, move=True)
    assert dialog.title == "Rename/move"
    assert dialog.options.value & MOVE


def test_ok_answers_a_request_and_is_remembered(tmp_path):
    dialog = CopyDialog(entries=[entry("f.txt"), entry("g")], here=tmp_path, other=tmp_path / "b")
    dialog.mode.value = OVERWRITE
    dialog.options.value = CHECK_FREE | MOVE
    request = dialog.accept()
    assert request == CopyRequest(
        [tmp_path / "f.txt", tmp_path / "g"], f"{tmp_path / 'b'}/", OVERWRITE, CHECK_FREE | MOVE,
        flush=True,
    )
    # The next F5 opens as this one closed, less F6's *Remove source*.
    again = CopyDialog(entries=[entry("f.txt")], here=tmp_path, other=tmp_path / "b")
    assert again.mode.value == OVERWRITE
    assert again.options.value == CHECK_FREE


def test_the_request_flushes_as_system_setup_says(tmp_path):
    SETTINGS.system.flush_buffers = False
    dialog = CopyDialog(entries=[entry("f.txt")], here=tmp_path, other=tmp_path / "b")
    assert dialog.accept().flush is False


def test_an_empty_line_answers_nothing(tmp_path):
    dialog = CopyDialog(entries=[entry("f.txt")], here=tmp_path, other=tmp_path)
    assert dialog.accept() is None


# -- clusters in columns -------------------------------------------------------------------


def four_boxes(height: int) -> CheckBoxes:
    boxes = CheckBoxes(width=40, height=height)
    boxes.items = ["~A~b", "~C~ccc", "~E~e", "~G~"]
    return mounted(boxes, size=(40, height))


def row(buffer, y: int) -> str:
    return "".join(buffer.get(x, y)[0] for x in range(buffer.width)).rstrip()


def test_a_short_cluster_runs_into_a_second_column():
    boxes = four_boxes(2)
    buffer = boxes_buffer(boxes)
    # The second column two cells past the widest caption, as TCluster's
    # ``Column`` stepped.
    assert row(buffer, 0) == "[ ] Ab    [ ] Ee"
    assert row(buffer, 1) == "[ ] Cccc  [ ] G"
    assert boxes.item_at(12, 1) == 3 and boxes.item_at(2, 0) == 0
    assert boxes.item_at(12, 5) == -1


def test_a_tall_cluster_is_one_column():
    buffer = boxes_buffer(four_boxes(4))
    assert [row(buffer, y) for y in range(4)] == ["[ ] Ab", "[ ] Cccc", "[ ] Ee", "[ ] G"]


def boxes_buffer(boxes):
    from navkit.screen import ScreenBuffer

    buffer = ScreenBuffer(boxes.width, boxes.height)
    boxes.render(buffer)
    return buffer


def test_left_and_right_move_a_column():
    boxes = four_boxes(2)
    asyncio.run(boxes.on_key(KeyEvent("right")))
    assert boxes.sel == 2
    asyncio.run(boxes.on_key(KeyEvent("right")))
    assert boxes.sel == 2
    asyncio.run(boxes.on_key(KeyEvent("left")))
    assert boxes.sel == 0


def test_a_click_in_the_second_column_toggles_its_item():
    boxes = four_boxes(2)
    asyncio.run(boxes.on_mouse_click(MouseClickEvent(13, 1, "left", "press")))
    assert boxes.value == 1 << 3


def test_radio_buttons_choose_as_they_move_across():
    radios = RadioButtons(width=40, height=2)
    radios.items = ["a", "b", "c"]
    mounted(radios, size=(40, 2))
    asyncio.run(radios.on_key(KeyEvent("right")))
    assert radios.value == 2


# -- end to end --------------------------------------------------------------------------------


@pytest.fixture
def two(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "one.txt").write_text("one")
    (a / "two.txt").write_text("two")
    return a, b


def test_f5_copies_what_is_tagged_to_the_other_panel(two):
    a, b = two

    async def main():
        shell = Shell(a, b)
        app = Application(shell, terminal=FakeTerminal(width=80, height=24))
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.1)
        manager = shell.manager
        manager.left.cursor = next(
            i for i, e in enumerate(manager.left.items) if e.name == "one.txt"
        )
        app.post_event(KeyEvent("insert"))
        await asyncio.sleep(0.06)
        assert manager.left.marked == {"one.txt"}
        start = len(app.terminal.frames)
        app.post_event(KeyEvent("f5"))
        await asyncio.sleep(0.06)
        assert isinstance(app.modal, CopyDialog)
        assert " Copy " in "".join(app.terminal.frames[start:])
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.3)
        state = (app.modal, manager.left.marked, [e.name for e in manager.right.items])
        app.exit()
        await task
        return state

    modal, marked, right = asyncio.run(main())
    assert modal is None
    assert (b / "one.txt").read_text() == "one" and not (b / "two.txt").exists()
    assert marked == frozenset()
    assert "one.txt" in right


def test_f5_asks_before_overwriting(two):
    from navigator.widgets.file_ops.overwrite_query import OverwriteQuery

    a, b = two
    (b / "one.txt").write_text("old")

    async def main():
        shell = Shell(a, b)
        app = Application(shell, terminal=FakeTerminal(width=80, height=24))
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.1)
        manager = shell.manager
        manager.left.cursor = next(
            i for i, e in enumerate(manager.left.items) if e.name == "one.txt"
        )
        app.post_event(KeyEvent("f5"))
        await asyncio.sleep(0.06)
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.4)
        asked = app.modal
        painted = app.terminal.painted
        app.post_event(KeyEvent("s", "s", alt=True))
        await asyncio.sleep(0.3)
        after = app.modal
        app.exit()
        await task
        return asked, painted, after

    asked, painted, after = asyncio.run(main())
    assert isinstance(asked, OverwriteQuery)
    assert "already exists" in painted
    assert after is None
    assert (b / "one.txt").read_text() == "old"


def test_f5_to_a_missing_directory_asks_yes_or_no_to_create_it(two):
    """With *Create non-existing dir* ticked in Confirmations -- not DN's default."""
    a, b = two
    SETTINGS.confirmations.create_dir = True

    async def main():
        shell = Shell(a, b)
        app = Application(shell, terminal=FakeTerminal(width=80, height=24))
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.1)
        manager = shell.manager
        manager.left.cursor = next(
            i for i, e in enumerate(manager.left.items) if e.name == "one.txt"
        )
        app.post_event(KeyEvent("f5"))
        await asyncio.sleep(0.06)
        app.modal.target.value = str(b / "new") + "/"
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.4)
        asked = app.modal
        buttons = [w.text for w in asked.buttons_row if w.visible]
        app.post_event(KeyEvent("y", "y", alt=True))
        await asyncio.sleep(0.3)
        after = app.modal
        app.exit()
        await task
        return asked.prompt, buttons, after

    prompt, buttons, after = asyncio.run(main())
    assert prompt.startswith("Would you like to create directory")
    assert buttons == ["~Y~es", "~N~o"]
    assert after is None
    assert (b / "new" / "one.txt").read_text() == "one"


def test_f5_to_a_missing_directory_creates_it_unasked_by_default(two):
    """DN's default ``Confirms`` leaves ``cfCreateSubdir`` out."""
    a, b = two

    async def main():
        shell = Shell(a, b)
        app = Application(shell, terminal=FakeTerminal(width=80, height=24))
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.1)
        manager = shell.manager
        manager.left.cursor = next(
            i for i, e in enumerate(manager.left.items) if e.name == "one.txt"
        )
        app.post_event(KeyEvent("f5"))
        await asyncio.sleep(0.06)
        app.modal.target.value = str(b / "new") + "/"
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.4)
        after = app.modal
        app.exit()
        await task
        return after

    assert asyncio.run(main()) is None
    assert (b / "new" / "one.txt").read_text() == "one"


def test_f5_is_disabled_on_dot_dot(two):
    a, b = two

    async def main():
        shell = Shell(a, b)
        app = Application(shell, terminal=FakeTerminal(width=80, height=24))
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.1)
        manager = shell.manager
        manager.left.cursor = 0
        settle()
        enabled = manager.enables(filecopy_command())
        app.exit()
        await task
        return manager.left.items[0].name, enabled

    first, enabled = asyncio.run(main())
    assert first == ".." and enabled is False


def filecopy_command():
    from navigator.widgets.manager.commands import Copy

    return Copy()


# -- the progress bar ----------------------------------------------------------------------


def bar_row(bar) -> str:
    from navkit.screen import ScreenBuffer

    buffer = ScreenBuffer(bar.width, bar.height)
    bar.render(buffer)
    return "".join(buffer.get(x, 0)[0] for x in range(bar.width))


def test_a_progress_bar_fills_its_width():
    from navml.widgets.progress_bar import ProgressBar

    bar = mounted(ProgressBar(width=10, height=1), size=(10, 1))
    bar.total = 200
    bar.value = 50
    settle()
    assert bar_row(bar) == "██▒▒▒▒▒▒▒▒" and bar.percent == 25
    bar.width = 20
    assert bar_row(bar) == "█████" + "▒" * 15
    bar.total = 0
    assert bar_row(bar) == "█" * 20 and bar.percent == 100


def test_the_copy_gauges_follow_the_box():
    from navigator.widgets.file_ops.copy_progress import CopyProgress

    box = CopyProgress(total=100, done=50)
    box.modal_width = 60
    mounted(box, size=(80, 24))
    settle()
    assert box.total_bar.width == 52
    assert bar_row(box.total_bar).count("█") == 26


def test_the_gauge_is_drawn_in_label_normal():
    """``TWhileView.Draw``'s ``GetColor(7)``: slot [38], black on light grey in ``default``.

    Not the dialog frame's white, which is what the bar inherits with no rule.
    """
    from navml.widgets.dialog.label import Label

    from navigator.scheme import load_scheme
    from navigator.widgets.file_ops.copy_progress import CopyProgress

    box = CopyProgress(total=100, done=50)
    box.stylesheet = load_scheme("default")
    caption = Label(parent=box)
    mounted(box, size=(80, 24))
    settle()
    for bar in (box.file_bar, box.total_bar):
        assert (bar.style.fg, bar.style.bg) == (caption.style.fg, caption.style.bg)
    assert bar.style.fg != box.style.fg
