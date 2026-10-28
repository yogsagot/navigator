"""Tooltips of the second round: the lists, views and lines that say more
than they show -- Synchronize, Volumes, Key bindings, the viewer's bytes, the
editor's info line, Compare files, Colors, the calendar, the info panel, the
command line -- each what its row or cell leaves out."""

from __future__ import annotations

import datetime
from pathlib import PurePosixPath

import pytest

from conftest import FakeTerminal, IDLE, Until, run_app, settle
from navkit.events import KeyEvent
from navkit.tooltip import plain
from navkit.widget import Widget


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    for name in ("one", "two"):
        (tmp_path / name).mkdir()
    return tmp_path


# -- lists -------------------------------------------------------------------------


def test_a_list_viewers_own_tooltips_come_before_its_cut_text():
    from navml.widgets.dialog.list_viewer import ListViewer

    root = Widget(width=40, height=10)
    view = root.add(ListViewer(x=0, y=0, width=12, height=5))
    view.items = ["short", "a much longer row than fits"]
    assert view.tooltip_at(2, 2) == "a much longer row than fits"   # cut, as before
    view.tooltips = ["", "Its own"]
    assert view.tooltip_at(2, 1) == ""
    assert view.tooltip_at(2, 2) == "Its own"


def test_a_synchronize_row_says_why_it_differs_and_what_its_action_does():
    from navigator.lib.file_ops import dirsync
    from navigator.lib.file_ops.dircompare import CompareRequest
    from navigator.widgets.manager.sync_list.sync_list import SyncList

    left = dirsync.Side("file", 2048, 2000.0, 0o100644)
    right = dirsync.Side("file", 1000, 1000.0, 0o100600)
    row = dirsync.make_row(PurePosixPath("deep/a.txt"), left, right, dirsync.DIFFERS)
    lonely = dirsync.make_row(PurePosixPath("b"), None, right, dirsync.RIGHT_ONLY)
    clash = dirsync.make_row(PurePosixPath("c"), left, dirsync.Side("dir", 0, 0.0, 0o40755), dirsync.CONFLICT)
    holder = Widget(width=100, height=10)
    holder.request = CompareRequest(attributes=True)
    rows = holder.add(SyncList(x=0, y=0, width=100, height=10))
    rows.items = [row, lonely, clash]
    settle()
    assert rows.cell_tooltip(row, 0, 1).split("\n") == [
        "Different on the two sides", "Sizes 2,048 and 1,000 bytes", "The left one is newer",
        "Permissions 0644 and 0600"]
    assert rows.cell_tooltip(row, 1, 1) == "Copied to the right, over the one there"
    assert rows.cell_tooltip(lonely, 0, 1) == "Only on the right"
    assert rows.cell_tooltip(lonely, 1, 1) == "Copied to the left"
    assert rows.cell_tooltip(clash, 0, 1).startswith("On the left a file, on the right a directory")
    assert rows.cell_tooltip(row, 2, 3) == "deep/a.txt"            # cut: whole
    assert rows.cell_tooltip(row, 2, 30) == ""
    assert rows.cell_tooltip(row, 3, 6) == "2,048 bytes"
    # Asked by the pointer, column by column.
    status_x, _ = rows.columns()[0]
    first_row = rows.inset + rows.header
    assert rows.tooltip_at(status_x + 1, first_row).startswith("Different on the two sides")


def test_a_volume_says_its_whole_mount_point_device_options_and_exact_sizes():
    from navigator.lib.system.volumes import Volume, mount_options
    from navigator.widgets.shell.volume_list.volume_list import VolumeList

    text = "/dev/sda1 /home ext4 rw,relatime 0 0\n/dev/sdb1 /mnt/a\\040b vfat ro 0 0\n"
    assert mount_options(text) == {"/home": "rw,relatime", "/mnt/a b": "ro"}
    volume = Volume("data", "ext4", "/home", "/dev/sda1", total=10_000, free=2_500, options="rw,relatime")
    assert VolumeList().row_tooltip(0, volume).split("\n") == [
        "Mounted on /home", "Device /dev/sda1", "Options rw,relatime", "2,500 bytes free of 10,000"]


#: More keys than a row has room for, however wide the list is laid out.
KEYS = ("ctrl+shift+f12", "alt+shift+f12", "ctrl+alt+f12", "ctrl+shift+f11", "alt+shift+f11", "ctrl+alt+f11",
        "ctrl+shift+f9", "alt+shift+f9")


def test_a_key_binding_row_says_where_its_command_is_and_its_defaults(place):
    from navkit.commands import key_label
    from navigator.__main__ import Navigator
    from navkit.commands import key_table
    from navigator.lib.config.keybindings import entries
    from navigator.widgets.manager.commands import MakeDirectory
    from navigator.widgets.manager.manager import Manager
    from navigator.widgets.setup.key_bindings_dialog.binding_list import BindingList

    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30))
    seen = {}

    def look(a):
        entry = next(e for e in entries(key_table(Manager)) if e.binding is MakeDirectory)
        rows = a.shell.add(BindingList(x=0, y=0, width=40, height=5))
        rows.items = [(entry, KEYS)]
        settle()
        seen["title"] = plain(rows.tooltip_at(rows.inset + 1, rows.inset))
        seen["keys"] = plain(rows.tooltip_at(rows.inset + rows.inner_width - 2, rows.inset))
        a.shell.remove(rows)

    run_app(app, [look])
    assert seen["title"].split("\n") == ["File > Make directory", "Its keys by default: F7"]
    assert seen["keys"].split("\n") == [", ".join(key_label(key) for key in KEYS), "Its keys by default: F7"]


# -- the viewer, the editor, Compare files -----------------------------------------


def test_a_byte_in_hex_mode_says_where_it_is_and_what_it_is_but_only_once_read(tmp_path):
    from navigator.lib.viewer import HEX_PAIRS_AT, ViewSource, hex_chars_at
    from navigator.widgets.viewer.file_viewer.file_viewer import FileViewer

    path = tmp_path / "data.bin"
    path.write_bytes(bytes(range(64)) + b"ABC")
    source = ViewSource(path)
    assert source.peek(65) is None                 # nothing read: never read for a tooltip
    root = Widget(width=80, height=10)
    viewer = root.add(FileViewer(x=0, y=0, width=80, height=8))
    viewer.open(path, source=source)
    viewer.mode = "hex"
    settle()
    source.read(0, source.size)                    # what painting the rows does
    per = viewer.row_bytes()
    index = 65                                     # "B"
    y, column = divmod(index, per)
    tip = viewer.tooltip_at(HEX_PAIRS_AT + column * 3, y).split("\n")
    assert tip == ["Offset 00000041 (65)", "Byte 42, decimal 66, octal 102, binary 01000010", "Character B"]
    assert viewer.tooltip_at(hex_chars_at(per) + column, y) == "\n".join(tip)
    assert viewer.tooltip_at(HEX_PAIRS_AT + column * 3 + 2, y) == ""   # the blank between pairs
    assert viewer.info_tooltip() == f"{path}\n67 bytes"


def test_the_editors_info_line_says_what_a_click_on_each_place_does(place):
    from navigator.__main__ import Navigator
    from navigator.widgets.editor.file_editor.file_editor import InfoLine

    (place / "one" / "a.txt").write_text("hello\n")
    app = Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30))
    seen = {}

    def look(a):
        window = a.shell.desktop.active_window
        line = next(child for child in window.children if isinstance(child, InfoLine))
        editor = window.editor
        seen["place"] = plain(line.tooltip_at(editor.place_indicator()[0], 0))
        seen["code"] = plain(line.tooltip_at(editor.code_indicator()[0], 0))
        seen["else"] = line.tooltip_at(0, 0)

    run_app(app, [KeyEvent("down"), KeyEvent("f4"),
                  Until(lambda a: getattr(a.shell.desktop.active_window, "editor", None)),
                  IDLE, look])
    assert seen["place"].startswith("Line and column: a click goes to a line (Alt-G")
    assert seen["code"].startswith("The character's code: a click opens the character table")
    assert seen["else"] == str(place / "one" / "a.txt")


def test_a_compared_row_says_which_line_it_is_and_what_became_of_it():
    from navigator.lib.file_ops.filediff import align
    from navigator.widgets.viewer.diff_view.diff_view import DiffView

    root = Widget(width=61, height=10)
    view = root.add(DiffView(x=0, y=0, width=61, height=10))
    view.model = align(b"same\nold\ngone\n", b"same\nnew\n")
    view.left_title, view.right_title = "/a/" + "x" * 40, "/b"
    settle()
    left, right = 5, 40
    assert view.tooltip_at(left, 1) == "Line 1, the same as line 1 on the right"
    assert view.tooltip_at(right, 2) == "Line 2, changed: line 2 on the left"
    assert view.tooltip_at(left, 3) == "Line 3, only on the left: removed"
    assert view.tooltip_at(right, 3) == "Line 3 on the left is only there: removed"
    assert view.tooltip_at(left, 0) == "/a/" + "x" * 40              # a heading cut
    assert view.tooltip_at(right, 0) == ""


# -- Colors, the calendar ------------------------------------------------------------


def test_a_colour_entry_says_its_dn_slot_and_variables_and_a_cell_its_colour():
    from navigator.widgets.setup.colors_dialog.colors_dialog import entry_tooltip
    from navml.widgets.dialog.color_selector import ColorSelector

    assert entry_tooltip("bar-key") == "DOS Navigator palette entry 4\nIn a palette file: $bar-key-fg, $bar-key-bg"
    assert entry_tooltip("image").startswith("Not in DOS Navigator: it starts as palette entry 175")
    assert entry_tooltip("shadow").startswith("Not in DOS Navigator, which had no colour for it")
    grid = ColorSelector(width=12, height=4)
    assert grid.tooltip_at(0, 0) == "Black (black)"
    assert grid.tooltip_at(3, 2) == "Light blue (light_blue)"
    assert grid.tooltip_at(13, 0) == ""


def test_a_calendar_day_is_spelled_out_with_its_week():
    from navml.widgets.dialog.date_button.date_button import CalendarView

    view = CalendarView(day=datetime.date(2026, 10, 28), width=22, height=8)
    view.date_format = "%d.%m.%Y"
    for row, week in enumerate(view.weeks()):
        if datetime.date(2026, 10, 28) in week:
            x, y = week.index(datetime.date(2026, 10, 28)) * 3 + 1, row + 2
    first = view.tooltip_at(x, y).split("\n")[0]
    assert first == "Wednesday, 28.10.2026, week 44"
    assert view.tooltip_anchor() == (x, y)
    assert view.tooltip_at(x, 1) == "Wednesday"                       # the weekday row's column
    assert plain(view.tooltip_at(0, 0)) == "The month before"


# -- the info panel, the command line ----------------------------------------------------


def test_the_info_panel_says_a_cut_line_whole_and_the_memory_in_bytes():
    from navigator.lib.system import diskinfo
    from navigator.widgets.manager.info_panel.info_panel import InfoPanel

    panel = InfoPanel(width=20, height=10)
    panel.facts = diskinfo.DiskFacts(memory_total=8 * 1024 * 1024 + 5)
    panel.lines = lambda: [("~/a/very/long/directory/name~", True), ("~8,192~K bytes total memory", True)]
    assert panel.tooltip_at(3, 1) == "/a/very/long/directory/name"
    assert panel.tooltip_at(3, 2) == "8,388,613 bytes of memory in all"


def test_a_cut_prompt_is_said_whole():
    from navigator.widgets.shell.command_line.command_line import CommandLine

    line = CommandLine(width=30, height=1)
    line.prompt = "/home/someone/a/very/deep/directory$"
    assert line.shown_prompt != line.prompt
    assert line.tooltip_at(0, 0) == line.prompt
    line.prompt = "/tmp$"
    assert line.tooltip_at(0, 0) == ""


# -- the low ones: the game, progress, history, the trash can, a title, a label ----------------


def test_the_games_info_says_how_the_score_counts_and_how_far_the_next_level_is():
    from navigator.lib.utilities.tetris import Game
    from navigator.widgets.game.game_window.info import GameInfo

    info = GameInfo(width=23, height=15)
    info.game = game = Game()
    game.preview = True
    assert info.tooltip_at(3, 1).endswith("score 70%")
    game.start_level = game.level = 5
    game.lines = 40
    assert info.tooltip_at(3, 3) == "11 more lines to the next level"      # past 50, at 51
    assert info.tooltip_at(3, 6).startswith("The figure that falls next")
    game.level = 10
    assert info.tooltip_at(3, 3) == "The last level"


def test_a_progress_bar_says_what_it_rounds_and_a_cut_path_is_said_whole():
    from navml.widgets.progress_bar import ProgressBar
    from navigator.widgets.file_ops.copy_progress.copy_progress import whole_path

    bar = ProgressBar(width=20, height=1)
    bar.value, bar.total = 1_234_567, 9_876_543
    assert bar.tooltip_at(3, 0) == "1,234,567 of 9,876,543 done (12.5%), 8,641,976 to go"
    bar.tooltip = "Its own"
    assert bar.tooltip_at(3, 0) == "Its own"
    assert whole_path(" to ", "/a/b", 40) == ""
    assert whole_path(" to ", "/" + "d" * 50, 40) == "/" + "d" * 50


def test_a_history_entry_and_a_file_record_say_when_they_were_last_used(tmp_path):
    from navml.history import HISTORY
    from navigator.lib.config.country import last_used, stamp
    from navigator.models.view_record import ViewRecord
    from navigator.widgets.shell.command_history_dialog.history_list import HistoryList
    from navigator.widgets.shell.file_record_list.file_record_list import FileRecordList

    HISTORY.add("command", "make test")
    when = HISTORY.used("command")["make test"]
    assert when > 0
    assert last_used(when) == f"Last used {stamp(when)}" and last_used(0) == ""
    commands = HistoryList(width=40, height=5)
    commands.items, commands.used = ["make test"], HISTORY.used("command")
    assert commands.row_tooltip(0, "make test") == last_used(when)

    ViewRecord.store(tmp_path / "a.txt", zoomed=True, x=0, y=0, width=80, height=25, desk_width=80,
                     desk_height=25, filter=0, top=0, x_delta=0, cursor=0)
    record = ViewRecord.find(tmp_path / "a.txt")
    files = FileRecordList(width=200, height=5)
    files.items = [record]
    assert record.used > 0 and files.row_tooltip(0, record) == last_used(record.used)


def test_the_trash_can_says_what_a_drop_does_as_file_manager_setup_has_it():
    from navigator.settings import SETTINGS
    from navigator.widgets.shell.trash_can import TrashCan

    can = TrashCan(Widget(width=80, height=25))
    SETTINGS.file_manager.use_trash = False
    assert can.tooltip_at(1, 1).startswith("Files dropped here from a panel are erased")
    SETTINGS.file_manager.use_trash = True
    try:
        assert can.tooltip_at(1, 1).startswith("Files dropped here from a panel are moved to the Trash")
    finally:
        SETTINGS.file_manager.use_trash = False


def test_a_cut_window_title_is_said_whole_with_what_the_frame_does():
    from navml.widgets.window import Window

    window = Window(width=16, height=6)
    window.title = "A title much longer than the frame"
    window.zoomable = True
    assert window.tooltip_at(8, 0) == "A title much longer than the frame\nA double click zooms, a drag moves"
    window.title, window.zoomable = "Short", False
    assert window.tooltip_at(8, 0) == "A drag moves"


def test_a_label_standing_apart_says_its_controls_tooltip():
    from navml.widgets.dialog.input_line import InputLine
    from navml.widgets.dialog.label import Label

    root = Widget(width=40, height=5)
    line = root.add(InputLine(x=10, y=0, width=20, height=1))
    label = root.add(Label(x=0, y=0, width=10, height=1))
    label.text, label.link = "~N~ame", line
    line.tooltip = "What the name is for"
    assert label.tooltip_at(1, 0) == "What the name is for"
    label.tooltip = "Its own"
    assert label.tooltip_at(1, 0) == "Its own"
