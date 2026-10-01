"""Alt+E: the File Attributes dialog, its tri-state grid, its drop-downs, and the command end to end."""

from __future__ import annotations

import asyncio
import os
import stat
from pathlib import Path

import pytest

from conftest import FakeTerminal, settle

from navkit.application import Application
from navkit.events import KeyEvent, MouseClickEvent
from navkit.screen import ScreenBuffer

from navml.history import HISTORY
from navml.widgets.dialog.check_boxes import CheckBoxes

from navigator import fileattr
from navigator.commands import ChangeAttributes
from navigator.widgets.file_ops.attr_dialog import AttrDialog
from navigator.widgets.file_ops.attr_dialog.attr_dialog import info_for, name_for
from navigator.widgets.manager.panel import DirEntry
from navigator.widgets.shell.shell import Shell


def entry(name: str, is_dir: bool = False) -> DirEntry:
    return DirEntry(name, is_dir, 0)


def make(path: Path, mode: int) -> Path:
    path.write_text("x")
    os.chmod(path, mode)
    return path


def mode_of(path: Path) -> int:
    return stat.S_IMODE(os.stat(path).st_mode)


# -- the tri-state check box ---------------------------------------------------------


def test_a_tristate_bit_cycles_mixed_on_off_and_back():
    boxes = CheckBoxes(items=["a", "b"])
    boxes.mixed = boxes.tristate = 0b01
    seen = []
    for _ in range(4):
        seen.append((boxes.is_mixed(0), boxes.chosen(0)))
        boxes.toggle(0)
    assert seen == [(True, False), (False, True), (False, False), (True, False)]


def test_a_bit_that_is_not_tristate_stays_two_state():
    boxes = CheckBoxes(items=["a", "b"])
    boxes.toggle(1)
    boxes.toggle(1)
    boxes.toggle(1)
    assert (boxes.value, boxes.mixed) == (0b10, 0)


def test_a_mixed_bit_is_painted_with_a_question_mark():
    boxes = CheckBoxes(items=["a", "b"], width=10, height=2)
    boxes.value, boxes.mixed = 0b10, 0b01
    buffer = ScreenBuffer(10, 2)
    boxes.render(buffer)
    rows = ["".join(buffer.get(x, y)[0] or " " for x in range(10)) for y in range(2)]
    assert rows[0].startswith("[?] a") and rows[1].startswith("[X] b")


# -- the dialog alone ----------------------------------------------------------------


def test_the_name_row_says_what_was_selected():
    assert name_for([entry("f.txt")]) == "File ~f.txt~"
    assert name_for([entry("src", True)]) == "Directory ~src~"
    assert name_for([entry("a"), entry("b"), entry("d", True)]) == "~2 files, 1 directory~"
    assert name_for([entry("a~b")]) == "File ~a~~b~"


def test_one_file_opens_on_its_own_mode_owner_and_time(tmp_path):
    f = make(tmp_path / "f", 0o640)
    os.utime(f, (0, 1_700_000_000))
    dialog = AttrDialog(entries=[entry("f")], here=tmp_path)
    assert dialog.title == "File Attributes"
    assert dialog.bits.value == fileattr.to_items(0o640) and dialog.bits.mixed == 0
    assert (dialog.octal.value, dialog.symbolic.text) == ("0640", "rw-r-----")
    assert dialog.user.value == fileattr.user_name(os.getuid())
    assert dialog.date.value == fileattr.date_text(1_700_000_000)
    assert dialog.info_row.text == "1 bytes"
    assert dialog.recurse.disabled
    assert dialog.user.choices == fileattr.users()
    assert dialog.group.choices == fileattr.assignable_groups()


def test_untouched_ok_changes_nothing(tmp_path):
    make(tmp_path / "f", 0o640)
    dialog = AttrDialog(entries=[entry("f")], here=tmp_path)
    assert dialog.accept() is None


def test_files_that_disagree_open_mixed_and_blank(tmp_path):
    a = make(tmp_path / "a", 0o644)
    make(tmp_path / "b", 0o755)
    os.utime(a, (0, 1))
    dialog = AttrDialog(entries=[entry("a"), entry("b")], here=tmp_path)
    mixed = fileattr.to_items(0o111)
    assert dialog.bits.mixed == mixed and dialog.bits.tristate == mixed
    assert dialog.octal.value == "0???" and dialog.symbolic.text == "rw?r-?r-?"
    assert (dialog.date.value, dialog.clock.value) == ("", "")


def test_only_the_bits_pressed_go_in_the_request(tmp_path):
    (tmp_path / "d").mkdir()
    os.chmod(tmp_path / "d", 0o755)
    dialog = AttrDialog(entries=[entry("d", True)], here=tmp_path)
    dialog.mounted()
    group_write = 4
    dialog.bits.toggle(group_write)
    settle()
    assert dialog.octal.value == "0775"
    dialog.recurse.value = fileattr.RECURSE.index(fileattr.FILES)
    request = dialog.accept()
    # The directory's own execute bits are shown ticked and were not pressed,
    # so the files under it are not given them.
    assert (request.set_bits, request.clear_bits) == (0o020, 0)
    assert request.recurse == fileattr.FILES
    assert request.sources == [tmp_path / "d"]


def test_a_mixed_bit_moved_is_applied_and_one_left_mixed_is_not(tmp_path):
    make(tmp_path / "a", 0o644)
    make(tmp_path / "b", 0o755)
    dialog = AttrDialog(entries=[entry("a"), entry("b")], here=tmp_path)
    dialog.mounted()
    owner_exec, group_exec = 2, 5
    dialog.bits.toggle(owner_exec)   # ? -> X
    dialog.bits.toggle(group_exec)   # ? -> X
    dialog.bits.toggle(group_exec)   # X -> blank
    settle()
    request = dialog.accept()
    assert (request.set_bits, request.clear_bits) == (0o100, 0o010)


def test_r_w_and_x_press_a_box_in_the_cursors_column(tmp_path):
    make(tmp_path / "f", 0o644)
    dialog = AttrDialog(entries=[entry("f")], here=tmp_path)
    dialog.mounted()
    bits = dialog.bits

    def key(*events):
        for event in events:
            assert asyncio.run(bits.on_key(event)) is True

    key(KeyEvent("right"), KeyEvent("x", "x"))          # group, exec
    assert bits.sel == 5 and bits.chosen(5)
    key(KeyEvent("w", "w"))                               # group, write
    assert bits.sel == 4 and bits.chosen(4)
    key(KeyEvent("r", "r"))                               # group, read: off
    assert bits.sel == 3 and not bits.chosen(3)
    key(KeyEvent("right"), KeyEvent("x", "x"))          # others, exec
    assert bits.sel == 8 and bits.chosen(8)
    settle()
    assert dialog.octal.value == "0635"
    # The special column has no read, write or execute: nothing moves.
    key(KeyEvent("right"), KeyEvent("r", "r"))
    assert bits.sel == 11 and bits.value == fileattr.to_items(0o635)
    # Shifted letters count; Alt+R is still the dialog's shortcut.
    key(KeyEvent("left"), KeyEvent("r", "R", shift=True))
    assert bits.chosen(6) is False
    assert asyncio.run(bits.on_key(KeyEvent("r", alt=True))) is False


def test_typing_an_octal_mode_sets_the_whole_grid(tmp_path):
    make(tmp_path / "a", 0o644)
    make(tmp_path / "b", 0o755)
    dialog = AttrDialog(entries=[entry("a"), entry("b")], here=tmp_path)
    dialog.mounted()
    line = dialog.octal.entry
    assert dialog.octal.value == "0???"
    for char in "0600":
        asyncio.run(line.on_key(KeyEvent(char, char)))
        settle()
    assert dialog.bits.mixed == 0 and dialog.bits.value == fileattr.to_items(0o600)
    assert dialog.symbolic.text == "rw-------"
    request = dialog.accept()
    # Each digit that changed something claims its three bits; the special
    # digit typed as it was claims none, and stays the files' own.
    assert (request.set_bits, request.clear_bits) == (0o600, 0o177)


def test_the_octal_line_takes_only_octal_digits_and_a_digit_at_a_time_reaches_the_grid(tmp_path):
    make(tmp_path / "a", 0o644)
    make(tmp_path / "b", 0o755)
    dialog = AttrDialog(entries=[entry("a"), entry("b")], here=tmp_path)
    dialog.mounted()
    line = dialog.octal.entry
    line.select_all()

    def key(event):
        assert asyncio.run(line.on_key(event)) is True
        settle()

    key(KeyEvent("8", "8"))
    key(KeyEvent("9", "9"))
    assert dialog.octal.value == "0???"
    key(KeyEvent("right"))
    key(KeyEvent("7", "7"))
    # Only the owner's three boxes left ``[?]``: the others are still unknown.
    assert dialog.octal.value == "07??"
    assert dialog.bits.mixed == fileattr.to_items(0o011)
    assert dialog.bits.value & fileattr.to_items(0o700) == fileattr.to_items(0o700)
    # Up steps the mode as an octal number, carrying in eights: the owner's 7
    # and one is 0, carried into the special digit -- the sticky bit.  An
    # unknown place counts as 0 in the arithmetic, and is known afterwards.
    key(KeyEvent("left"))
    key(KeyEvent("up"))
    assert dialog.octal.value == "1000"
    assert dialog.bits.mixed == 0
    assert dialog.bits.value == fileattr.to_items(0o1000)


def test_an_unreadable_value_keeps_the_dialog_up(tmp_path):
    make(tmp_path / "f", 0o644)
    dialog = AttrDialog(entries=[entry("f")], here=tmp_path)
    dialog.group.value = "no-such-group-here"
    assert dialog.valid() is False
    dialog.group.value = ""
    dialog.date.value = "31-02-2024"
    assert dialog.valid() is False


# -- the command ---------------------------------------------------------------------


@pytest.fixture
def two(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    make(a / "one.txt", 0o644)
    make(a / "two.txt", 0o755)
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


def put_cursor(panel, name: str) -> None:
    panel.cursor = next(i for i, e in enumerate(panel.items) if e.name == name)


def test_alt_e_changes_the_tagged_files_and_untags_them(two):
    a, b = two

    async def steps(app, shell):
        panel = shell.manager.left
        panel.marked = frozenset({"one.txt", "two.txt"})
        app.post_event(KeyEvent("e", alt=True))
        await asyncio.sleep(0.06)
        asked = type(app.modal).__name__
        # The grid has the keyboard: across to Group, down to Write, press.
        for key in (KeyEvent("right"), KeyEvent("down"), KeyEvent(" ", " ")):
            app.post_event(key)
        await asyncio.sleep(0.06)
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.3)
        return asked, app.modal, panel.marked

    asked, modal, marked = run_shell(a, b, steps)
    assert asked == "AttrDialog" and modal is None
    assert (mode_of(a / "one.txt"), mode_of(a / "two.txt")) == (0o664, 0o775)
    assert marked == frozenset()


def test_dismissing_unchanged_closes_at_once_and_changed_asks_first(two):
    a, b = two

    async def steps(app, shell):
        put_cursor(shell.manager.left, "one.txt")
        seen = {}

        # Unchanged -- and a box pressed back is no change: Esc closes it.
        app.post_event(KeyEvent("e", alt=True))
        await asyncio.sleep(0.06)
        for key in (KeyEvent(" ", " "), KeyEvent(" ", " "), KeyEvent("escape")):
            app.post_event(key)
        await asyncio.sleep(0.06)
        seen["unchanged"] = app.modal

        # Changed: Esc asks, and No keeps the dialog up as it was.
        app.post_event(KeyEvent("e", alt=True))
        await asyncio.sleep(0.06)
        dialog = app.modal
        app.post_event(KeyEvent(" ", " "))
        app.post_event(KeyEvent("escape"))
        await asyncio.sleep(0.06)
        question = app.modal
        seen["asked"] = (
            type(question).__name__,
            question.prompt,
            [b.text for b in question.buttons_row if b.visible],
        )
        app.post_event(KeyEvent("n", alt=True))
        await asyncio.sleep(0.06)
        seen["no"] = app.modal is dialog

        # Esc on the question is no answer either: the dialog stays.
        app.post_event(KeyEvent("escape"))
        await asyncio.sleep(0.06)
        app.post_event(KeyEvent("escape"))
        await asyncio.sleep(0.06)
        seen["esc"] = app.modal is dialog

        # The close icon asks as Esc does, and Yes lets it go.
        app.post_event(MouseClickEvent(dialog.x + dialog.width - 4, dialog.y, "left", "press"))
        await asyncio.sleep(0.06)
        seen["icon"] = type(app.modal).__name__
        app.post_event(KeyEvent("y", alt=True))
        await asyncio.sleep(0.06)
        seen["yes"] = app.modal

        # The Cancel button is the answer: changed, it closes without asking.
        app.post_event(KeyEvent("e", alt=True))
        await asyncio.sleep(0.06)
        dialog = app.modal
        app.post_event(KeyEvent(" ", " "))
        await asyncio.sleep(0.06)
        seen["changed"] = dialog.must_ask()
        await dialog.cancel.press()
        await asyncio.sleep(0.06)
        seen["cancel"] = app.modal
        return seen

    seen = run_shell(a, b, steps)
    assert seen["unchanged"] is None
    assert seen["asked"] == ("Dialog", "Changes will be lost. Are you sure?", ["~Y~es", "~N~o"])
    assert seen["no"] is True
    assert seen["esc"] is True
    assert seen["icon"] == "Dialog"
    assert seen["yes"] is None
    assert seen["changed"] is True and seen["cancel"] is None
    assert mode_of(a / "one.txt") == 0o644


def test_the_group_drop_down_offers_the_groups_on_the_current_one(two):
    a, b = two

    async def steps(app, shell):
        put_cursor(shell.manager.left, "one.txt")
        app.post_event(KeyEvent("e", alt=True))
        await asyncio.sleep(0.06)
        dialog = app.modal
        dialog.group.entry.focus()
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.06)
        dropped = app.modal
        seen = (type(dropped).__name__, dropped.items, dropped.selected, dialog.group.value)
        app.post_event(KeyEvent("escape"))
        app.post_event(KeyEvent("escape"))
        await asyncio.sleep(0.06)
        return seen

    kind, items, selected, current = run_shell(a, b, steps)
    assert kind == "HistoryList"
    assert items == fileattr.assignable_groups()
    assert selected == current
    # A list of choices is not a history: nothing was recorded.
    assert HISTORY.entries("") == []


def test_the_command_is_bound_on_the_menu_and_off_on_dotdot(two):
    a, b = two

    async def steps(app, shell):
        manager = shell.manager
        put_cursor(manager.left, "one.txt")
        settle()
        on_file = manager.enables(ChangeAttributes())
        put_cursor(manager.left, "..")
        settle()
        on_parent = manager.enables(ChangeAttributes())
        item = app.root.menu.file.item_for(ChangeAttributes)
        bound = app.bindings(manager.left).get("alt+e")
        return on_file, on_parent, item.text, item.key, bound

    on_file, on_parent, text, key, bound = run_shell(a, b, steps)
    assert on_file is True and on_parent is False
    assert (text, key) == ("File ~A~ttributes...", "Alt-E")
    assert isinstance(bound, ChangeAttributes)


# -- the user and group lines: chosen, never typed ----------------------------------------


def test_any_key_on_the_group_line_drops_its_list_and_typing_searches_it(two):
    a, b = two
    groups = fileattr.assignable_groups()
    target = groups[-1]

    async def steps(app, shell):
        put_cursor(shell.manager.left, "one.txt")
        app.post_event(KeyEvent("e", alt=True))
        await asyncio.sleep(0.06)
        dialog = app.modal
        line = dialog.group.entry
        seen = {}

        line.focus()
        # Tab is the dialog's: it moves on and drops nothing.
        app.post_event(KeyEvent("tab"))
        await asyncio.sleep(0.06)
        seen["tab"] = (app.modal is dialog, line.focused)

        line.focus()
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.06)
        seen["enter"] = type(app.modal).__name__
        app.post_event(KeyEvent("escape"))
        await asyncio.sleep(0.06)

        # A letter drops the list and searches it for itself.
        for char in target:
            app.post_event(KeyEvent(char, char))
        await asyncio.sleep(0.06)
        dropped = app.modal
        seen["search"] = (dropped.search, dropped.selected, dropped.footer_text())
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.06)
        seen["chosen"] = (app.modal is dialog, dialog.group.value, line.focused)
        app.post_event(KeyEvent("escape"))
        await asyncio.sleep(0.06)
        return seen

    seen = run_shell(a, b, steps)
    assert seen["tab"] == (True, False)
    assert seen["enter"] == "HistoryList"
    assert seen["search"] == (target, target, f" Search: {target} ")
    assert seen["chosen"] == (True, target, True)


def test_the_search_refuses_what_names_nothing_and_backspace_takes_one_back():
    from navml.widgets.dialog.history import History, HistoryList

    button = History()
    button.choices = ["adm", "audio", "sudo", "users"]
    window = HistoryList(button)
    window.items = list(button.choices)
    window.type_to_search = True

    def key(event):
        asyncio.run(window.on_key(event))

    key(KeyEvent("u", "u"))
    assert (window.search, window.selected) == ("u", "users")
    key(KeyEvent("q", "q"))
    assert (window.search, window.selected) == ("u", "users")
    key(KeyEvent("backspace"))
    assert window.search is None
    key(KeyEvent("a", "a"))
    key(KeyEvent("u", "u"))
    assert (window.search, window.selected) == ("au", "audio")
    key(KeyEvent("*", "*"))
    key(KeyEvent("o", "o"))
    assert window.selected == "audio"
    key(KeyEvent("down"))
    assert window.search is None and window.selected == "sudo"


def test_a_choice_line_refuses_a_paste_and_shows_no_caret():
    from navkit.events import PasteEvent
    from navml.widgets.dialog.choice_line import ChoiceLine

    line = ChoiceLine()
    line.value = "root"
    assert asyncio.run(line.on_paste(PasteEvent("evil"))) is False
    assert line.value == "root" and line.cursor_position() is None


def test_a_group_that_is_not_the_users_own_is_still_offered(tmp_path, monkeypatch):
    make(tmp_path / "f", 0o644)
    current = fileattr.group_name(os.stat(tmp_path / "f").st_gid)
    monkeypatch.setattr(fileattr, "assignable_groups", lambda: ["aaa", "zzz"])
    dialog = AttrDialog(entries=[entry("f")], here=tmp_path)
    assert dialog.group.value == current
    assert dialog.group.choices == sorted(["aaa", "zzz", current])


def test_up_and_down_move_between_the_lines_and_step_on_octal_date_and_time(two):
    a, b = two

    async def steps(app, shell):
        put_cursor(shell.manager.left, "one.txt")
        app.post_event(KeyEvent("e", alt=True))
        await asyncio.sleep(0.06)
        dialog = app.modal
        dialog.user.disabled = True
        names = {id(line): name for line, name in zip(
            dialog.lines, ("octal", "user", "group", "date", "time"))}
        seen = []

        async def press(key):
            app.post_event(KeyEvent(key))
            await asyncio.sleep(0.03)
            seen.append(names.get(id(app.focused), type(app.modal).__name__))

        dialog.group.entry.focus()
        await press("up")       # past the disabled user line, onto octal
        await press("up")       # octal keeps it: a step
        dialog.group.entry.focus()
        await press("down")     # onto date
        dialog.date.value = "01-10-2026"
        dialog.date.entry.select_all()
        await press("up")       # date keeps it: a step
        return seen, dialog.octal.value, dialog.date.value

    seen, octal, date = run_shell(a, b, steps)
    assert seen == ["octal", "octal", "date", "date"]
    assert octal == "1644"
    assert date == "11-10-2026"


def test_home_and_end_in_the_group_list_go_to_its_ends(two):
    a, b = two

    async def steps(app, shell):
        put_cursor(shell.manager.left, "one.txt")
        app.post_event(KeyEvent("e", alt=True))
        await asyncio.sleep(0.06)
        dialog = app.modal
        dialog.group.entry.focus()
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.06)
        groups = app.modal
        app.post_event(KeyEvent("end"))
        await asyncio.sleep(0.03)
        last = groups.selected
        app.post_event(KeyEvent("home"))
        await asyncio.sleep(0.03)
        first = groups.selected
        app.post_event(KeyEvent("escape"))
        app.post_event(KeyEvent("escape"))
        await asyncio.sleep(0.03)
        return first, last, list(groups.items)

    first, last, items = run_shell(a, b, steps)
    assert (first, last) == (items[0], items[-1])


def test_home_and_end_choose_the_first_and_last_recurse_and_move_in_the_grid(tmp_path):
    (tmp_path / "d").mkdir()
    dialog = AttrDialog(entries=[entry("d", True)], here=tmp_path)

    def key(widget, name):
        assert asyncio.run(widget.on_key(KeyEvent(name))) is True

    key(dialog.recurse, "end")
    assert (dialog.recurse.sel, dialog.recurse.value) == (3, 3)
    key(dialog.recurse, "home")
    assert (dialog.recurse.sel, dialog.recurse.value) == (0, 0)
    # In the grid they only move: a check box column does not choose as it moves.
    before = dialog.bits.value
    key(dialog.bits, "end")
    assert dialog.bits.sel == 11 and dialog.bits.value == before
    key(dialog.bits, "home")
    assert dialog.bits.sel == 0


def test_a_click_on_a_letter_of_the_symbolic_mode_presses_its_box(tmp_path):
    from navkit.events import MouseClickEvent

    make(tmp_path / "a", 0o644)
    make(tmp_path / "b", 0o755)
    dialog = AttrDialog(entries=[entry("a"), entry("b")], here=tmp_path)
    dialog.mounted()

    def click(x, y=0, action="press"):
        return asyncio.run(dialog.symbolic.on_mouse_click(MouseClickEvent(x, y, "left", action=action)))

    assert click(4) is True                 # group write: off to on
    settle()
    assert dialog.symbolic.text == "rw?rw?r-?" and dialog.octal.value == "0???"
    assert dialog.bits.sel == 4
    assert click(2) is True                 # owner exec: ? to x
    settle()
    assert dialog.symbolic.text == "rwxrw?r-?"
    # A release, a click past the nine letters or on another row does nothing.
    assert click(2, action="release") is False
    assert click(9) is False and click(2, 1) is False
    request = dialog.accept()
    assert (request.set_bits, request.clear_bits) == (0o120, 0)
