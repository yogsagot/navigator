"""F5 and F6: the Copy dialog, the columns its check boxes need, and the copy end to end."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from conftest import FakeTerminal, handled, mounted, settle, started, wait_until

from navkit.application import Application
from navkit.screen import ScreenBuffer
from navkit.events import KeyEvent, MouseClickEvent

from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.control import caption_runs, escape_caption, parse_shortcut
from navml.widgets.dialog.radio_buttons import RadioButtons

from navigator.lib.file_ops import filecopy
from navigator.lib.file_ops.filecopy import ASK, CHECK_FREE, MOVE, OVERWRITE, PRESERVE, CopyRequest
from navigator.lib.file_ops.undo import UNDO
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
        await started(app, shell.manager.left, shell.manager.right)
        manager = shell.manager
        manager.left.cursor = next(
            i for i, e in enumerate(manager.left.items) if e.name == "one.txt"
        )
        app.post_event(KeyEvent("insert"))
        await wait_until(lambda: manager.left.marked == {"one.txt"})
        assert manager.left.marked == {"one.txt"}
        start = len(app.terminal.frames)
        app.post_event(KeyEvent("f5"))
        await wait_until(lambda: isinstance(app.modal, CopyDialog) and " Copy " in "".join(app.terminal.frames[start:]))
        assert isinstance(app.modal, CopyDialog)
        assert " Copy " in "".join(app.terminal.frames[start:])
        app.post_event(KeyEvent("enter"))
        await wait_until(lambda: app.modal is None and not manager.left.marked and "one.txt" in [e.name for e in manager.right.items])
        state = (app.modal, manager.left.marked, [e.name for e in manager.right.items])
        app.exit()
        await task
        return state

    modal, marked, right = asyncio.run(main())
    assert modal is None
    assert (b / "one.txt").read_text() == "one" and not (b / "two.txt").exists()
    assert marked == frozenset()
    assert "one.txt" in right


def run_two(a, b, steps):
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

    return asyncio.run(asyncio.wait_for(main(), 10))


def on(panel, name: str) -> bool:
    return panel.selected is not None and panel.selected.name == name


@pytest.mark.parametrize("key", ["f5", "f6"])
def test_f5_and_f6_put_the_other_panel_s_cursor_on_what_went_there(two, key):
    """As F7's on its directory: the panel showing where it went lands on it,
    not left on ``..``."""
    a, b = two

    async def steps(app, manager):
        manager.left.cursor = next(i for i, e in enumerate(manager.left.items) if e.name == "two.txt")
        app.post_event(KeyEvent(key))
        await wait_until(lambda: isinstance(app.modal, CopyDialog))
        app.post_event(KeyEvent("enter"))
        await wait_until(lambda: app.modal is None and on(manager.right, "two.txt"))
        return manager.right.selected.name

    assert run_two(a, b, steps) == "two.txt"
    assert (b / "two.txt").exists() and (a / "two.txt").exists() == (key == "f5")


def test_f6_renaming_in_place_puts_the_cursor_on_the_new_name(two):
    a, b = two

    async def steps(app, manager):
        manager.left.cursor = next(i for i, e in enumerate(manager.left.items) if e.name == "two.txt")
        app.post_event(KeyEvent("f6"))
        await wait_until(lambda: isinstance(app.modal, CopyDialog))
        app.modal.target.value = "aaa.txt"
        app.post_event(KeyEvent("enter"))
        await wait_until(lambda: app.modal is None and on(manager.left, "aaa.txt"))
        return manager.left.selected.name, manager.right.selected.name

    assert run_two(a, b, steps) == ("aaa.txt", "..")
    assert (a / "aaa.txt").exists() and not (a / "two.txt").exists()


def test_f5_asks_before_overwriting(two):
    from navigator.widgets.file_ops.overwrite_query import OverwriteQuery

    a, b = two
    (b / "one.txt").write_text("old")

    async def main():
        shell = Shell(a, b)
        app = Application(shell, terminal=FakeTerminal(width=80, height=24))
        task = asyncio.create_task(app.run_async())
        await started(app, shell.manager.left, shell.manager.right)
        manager = shell.manager
        manager.left.cursor = next(
            i for i, e in enumerate(manager.left.items) if e.name == "one.txt"
        )
        app.post_event(KeyEvent("f5"))
        await wait_until(lambda: isinstance(app.modal, CopyDialog))
        app.post_event(KeyEvent("enter"))
        await wait_until(lambda: isinstance(app.modal, OverwriteQuery) and "already exists" in app.terminal.painted)
        asked = app.modal
        painted = app.terminal.painted
        app.post_event(KeyEvent("s", "s", alt=True))
        await wait_until(lambda: app.modal is None)
        after = app.modal
        app.exit()
        await task
        return asked, painted, after

    asked, painted, after = asyncio.run(main())
    assert isinstance(asked, OverwriteQuery)
    assert "already exists" in painted
    assert after is None
    assert (b / "one.txt").read_text() == "old"


def test_not_enough_room_is_dn_s_error_box_naming_the_drive(two):
    # ``erNotDiskSpace1``, ``mfError``: the mount point for DN's drive letter.
    from navigator.lib.file_ops.filecopy import NoRoom

    a, b = two

    async def main():
        shell = Shell(a, b)
        app = Application(shell, terminal=FakeTerminal(width=80, height=24))
        task = asyncio.create_task(app.run_async())
        await started(app, shell.manager.left, shell.manager.right)
        asked = asyncio.ensure_future(shell.manager._answer_copy_question(NoRoom(b / "one.txt", 9, 1, "/mnt/x")))
        await wait_until(lambda: app.modal is not None)
        seen = app.modal.title, app.modal.prompt
        app.post_event(KeyEvent("escape"))
        answer = await asked
        app.exit()
        await task
        return seen, answer

    (title, prompt), answer = asyncio.run(main())
    assert title == "Error"
    assert prompt == "There is not enough room\non /mnt/x to copy\nfile one.txt. Copy other files?"
    assert answer is False


def test_the_query_names_the_whole_destination_its_middle_cut():
    from navigator.lib.file_ops.filecopy import Overwrite
    from navigator.widgets.file_ops.overwrite_query.overwrite_query import describe

    dest = Path("/home/somebody/a/rather/long/directory/path/to/the/file.txt")
    line = describe(Overwrite(Path("/src/file.txt"), dest, 1, 0.0, 2, 0.0)).splitlines()[0]
    name = line[len("File "):]
    assert len(name) == 40 and name.startswith("/home/some") and name.endswith("/to/the/file.txt")
    assert "..." in name


def _rename_box(two, keys):
    """F5 onto ``one.txt`` there already, Rename in the query, then *keys* in
    the rename box: what the box opened with, and what the file holds after."""
    from navigator.widgets.file_ops.mkdir_dialog import MkdirDialog
    from navigator.widgets.file_ops.overwrite_query import OverwriteQuery

    a, b = two
    (b / "one.txt").write_text("old")

    async def main():
        shell = Shell(a, b)
        app = Application(shell, terminal=FakeTerminal(width=80, height=24))
        task = asyncio.create_task(app.run_async())
        await started(app, shell.manager.left, shell.manager.right)
        manager = shell.manager
        manager.left.cursor = next(i for i, e in enumerate(manager.left.items) if e.name == "one.txt")
        app.post_event(KeyEvent("f5"))
        await wait_until(lambda: isinstance(app.modal, CopyDialog))
        app.post_event(KeyEvent("enter"))
        await wait_until(lambda: isinstance(app.modal, OverwriteQuery))
        app.post_event(KeyEvent("r", "r", alt=True))
        await wait_until(lambda: isinstance(app.modal, MkdirDialog))
        opened = app.modal.entry.value
        for key in keys:
            app.post_event(key)
            await handled(app)
        await wait_until(lambda: app.modal is None)
        await handled(app)
        app.exit()
        await task
        return opened

    opened = asyncio.run(main())
    return opened, (b / "one.txt").read_text()


def test_rename_opens_on_the_whole_destination(two):
    a, b = two
    opened, _ = _rename_box(two, [KeyEvent("escape")])
    assert opened == str(b / "one.txt")


def test_escape_in_the_rename_box_skips_the_file(two):
    _, held = _rename_box(two, [KeyEvent("escape")])
    assert held == "old"


def test_an_empty_rename_skips_the_file(two):
    _, held = _rename_box(two, [KeyEvent("delete"), KeyEvent("enter")])
    assert held == "old"


def test_f5_to_a_missing_directory_asks_yes_or_no_to_create_it(two):
    """With *Create non-existing dir* ticked in Confirmations -- not DN's default."""
    a, b = two
    SETTINGS.confirmations.create_dir = True

    async def main():
        shell = Shell(a, b)
        app = Application(shell, terminal=FakeTerminal(width=80, height=24))
        task = asyncio.create_task(app.run_async())
        await started(app, shell.manager.left, shell.manager.right)
        manager = shell.manager
        manager.left.cursor = next(
            i for i, e in enumerate(manager.left.items) if e.name == "one.txt"
        )
        app.post_event(KeyEvent("f5"))
        await wait_until(lambda: isinstance(app.modal, CopyDialog))
        app.modal.target.value = str(b / "new") + "/"
        app.post_event(KeyEvent("enter"))
        await wait_until(lambda: app.modal is not None and not isinstance(app.modal, CopyDialog))
        asked = app.modal
        buttons = [w.text for w in asked.buttons_row if w.visible]
        app.post_event(KeyEvent("y", "y", alt=True))
        # Done, not just begun: a file there may be half written, and quitting
        # then stops the copy and takes it away.  Undo records it once done.
        await wait_until(lambda: app.modal is None and len(UNDO) == 1)
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
        await started(app, shell.manager.left, shell.manager.right)
        manager = shell.manager
        manager.left.cursor = next(
            i for i, e in enumerate(manager.left.items) if e.name == "one.txt"
        )
        app.post_event(KeyEvent("f5"))
        await wait_until(lambda: isinstance(app.modal, CopyDialog))
        app.modal.target.value = str(b / "new") + "/"
        app.post_event(KeyEvent("enter"))
        # Done, not just begun: a file there may be half written, and quitting
        # then stops the copy and takes it away.  Undo records it once done.
        await wait_until(lambda: app.modal is None and len(UNDO) == 1)
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
        await started(app, shell.manager.left, shell.manager.right)
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


def _painted_box(**values):
    """A :class:`CopyProgress` with *values*, shown over a shell: its rows, top to bottom frame."""
    import tempfile

    from navigator.widgets.file_ops.copy_progress import CopyProgress

    with tempfile.TemporaryDirectory() as where:
        a, b = Path(where) / "a", Path(where) / "b"
        a.mkdir()
        b.mkdir()

        async def main():
            shell = Shell(a, b)
            app = Application(shell, terminal=FakeTerminal(width=80, height=24))
            task = asyncio.create_task(app.run_async())
            await started(app, shell.manager.left, shell.manager.right)
            box = CopyProgress(**values)
            asyncio.ensure_future(box.execute(app))
            await wait_until(lambda: app.modal is box)
            await handled(app)
            buffer = ScreenBuffer(80, 24)
            app.root.render_tree(buffer)
            rows = ["".join(buffer.get(x, y)[0] or " " for x in range(box.x, box.x + box.width))
                    for y in range(box.y, box.y + box.height)]
            box.close(None)
            app.exit()
            await task
            return rows

        return asyncio.run(main())


def test_the_copy_box_says_dn_s_total_on_its_bottom_frame():
    rows = _painted_box(total=1234567, done=50, source="/a/b.txt", dest="/c")
    assert " Total 1,234,567 bytes " in rows[-1]
    assert rows[7].strip(" ║").startswith("50 bytes")  # the bytes done, under the total gauge


def test_while_measuring_the_copy_box_is_checking_directories():
    rows = _painted_box(measuring=True)
    assert "Checking directories..." in rows[1]
    assert not any("bytes" in row for row in rows)


@pytest.mark.parametrize("note, said", [("exists", "File exists - skipped"), ("older", "Older file - skipped"),
                                        ("deleting", "Deleting source file...")])
def test_dn_s_lines_take_the_speed_row(note, said):
    rows = _painted_box(total=10, done=5, note=note, speed=1000.0)
    assert said in rows[8] and "Speed" not in rows[8]


def test_rate_follows_the_last_seconds():
    from navigator.lib.system.progress import Rate, duration_text

    rate = Rate(window=5.0)
    assert rate.speed() is None and rate.left(100) is None
    rate.add(0.0, 0)
    rate.add(1.0, 1000)
    assert rate.speed() == 1000 and rate.left(5000) == 4
    # A long stall behind a question, then copying again: the stall leaves the window.
    rate.add(20.0, 1000)
    rate.add(21.0, 3000)
    assert rate.speed() == 2000
    rate.add(22.0, 3000)
    assert rate.left(3000) == 0
    assert [duration_text(s) for s in (0, 41.2, 725, 3723)] == ["0:00", "0:42", "12:05", "1:02:03"]


def test_the_copy_box_says_speed_and_time_left():
    from navigator.widgets.file_ops.copy_progress import CopyProgress

    box = CopyProgress(total=100, done=50)
    box.modal_width = 60
    mounted(box, size=(80, 24))
    settle()
    assert box.pace_row.text == ""
    assert box.count(512, 50) == "512 bytes (50%)"
    assert box.count(372_244_480, 8) == "372,244,480 bytes (355MB, 8%)"
    assert box.total_count.text == "50 bytes (50%)"  # DN's Total is on the frame
    box.speed, box.left = 9.5 * 1024 * 1024, 42.0
    settle()
    assert box.pace_row.text == "Speed 9.5MB/s, 0:42 left"
    box.left = -1.0
    settle()
    assert box.pace_row.text == "Speed 9.5MB/s"
    # Its own row, between the total's count and the Stop button.
    assert box.total_count.y < box.pace_row.y < box.ok.parent.y - 1


def test_the_gauge_is_drawn_in_label_normal():
    """``TWhileView.Draw``'s ``GetColor(7)``: slot [38], black on light grey in ``default``.

    Not the dialog frame's white, which is what the bar inherits with no rule.
    """
    from navml.widgets.dialog.label import Label

    from navigator.lib.appearance.scheme import load_scheme
    from navigator.widgets.file_ops.copy_progress import CopyProgress

    box = CopyProgress(total=100, done=50)
    box.stylesheet = load_scheme("default")
    caption = Label(parent=box)
    mounted(box, size=(80, 24))
    settle()
    for bar in (box.file_bar, box.total_bar):
        assert (bar.style.fg, bar.style.bg) == (caption.style.fg, caption.style.bg)
    assert bar.style.fg != box.style.fg
