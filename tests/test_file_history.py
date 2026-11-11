"""File View History and File Edit History: a file opens again as it was left.

``navigator/lib/config/file_history.py``, the ``ViewRecord``/``EditRecord`` models, the
windows' ``remember_history``/``recall_history`` and the Alt+PgDn / Alt+PgUp
dialog -- DOS Navigator's ``HISTRIES.PAS``.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from conftest import IDLE, FakeTerminal, run_app, key_bar_hints
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.config.file_history import scaled
from navigator.models.edit_record import EditRecord
from navigator.models.view_record import ViewRecord
from navigator.settings import SETTINGS


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "dir").mkdir()
    (tmp_path / "text.txt").write_text("".join(f"line {n:03}\n" for n in range(200)))
    return tmp_path


def navigator(path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def active(app):
    return app.shell.desktop.active_window


# -- the viewer -------------------------------------------------------------------


def test_a_viewer_opens_again_where_and_how_it_was_left(files):
    app = navigator(files)
    seen = {}

    def unzoom(a):
        window = active(a)
        window.toggle_zoom()
        window.locate(3, 2, 50, 15)

    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE,
        KeyEvent("pagedown"), KeyEvent("pagedown"), KeyEvent("f6"), unzoom,
        lambda a: seen.update(top=active(a).viewer.top),
        KeyEvent("escape"), lambda a: None,
        KeyEvent("f3"), IDLE,
        lambda a: seen.update(again=active(a)),
    ])
    window = seen["again"]
    assert seen["top"] > 0 and window.viewer.top == seen["top"]
    assert window.viewer.filter == 1
    assert not window.zoomed and (window.x, window.y, window.width, window.height) == (3, 2, 50, 15)
    assert ViewRecord.find(files / "text.txt").filter == 1


def test_the_mode_comes_back_unless_as_text_asks_for_one(files):
    app = navigator(files)
    modes = []
    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE, KeyEvent("f4"),
        KeyEvent("escape"), lambda a: None,
        KeyEvent("f3"), IDLE, lambda a: modes.append(active(a).viewer.mode),
        KeyEvent("escape"), lambda a: None,
        lambda a: a.manager.spawn(a.manager.view("text")), IDLE,
        lambda a: modes.append(active(a).viewer.mode),
    ])
    # File > View > As Text passes its mode, which wins over the record's.
    assert modes == ["hex", "text"]


def test_a_file_that_shrank_is_shown_from_its_start(files):
    ViewRecord.store(files / "text.txt", top=10**6, cursor=10**6)
    app = navigator(files)
    tops = []
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE,
                  lambda a: tops.append(active(a).viewer.top)])
    assert tops == [0]


def test_leaving_navigator_records_the_viewers_still_open(files):
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE, KeyEvent("f2")])
    assert ViewRecord.find(files / "text.txt").wrap is True


def test_with_tracking_off_nothing_is_recorded_or_restored(files):
    SETTINGS.interface.track_viewing = False
    ViewRecord.store(files / "text.txt", mode="hex")
    app = navigator(files)
    modes = []
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE, KeyEvent("f2"),
                  lambda a: modes.append(active(a).viewer.mode)])
    assert modes == ["text"]
    assert ViewRecord.find(files / "text.txt").wrap is False


def test_without_store_viewer_position_only_the_mode_comes_back(files):
    SETTINGS.interface.store_viewer_position = False
    ViewRecord.store(files / "text.txt", x=3, y=2, width=50, height=15,
                     desk_width=80, desk_height=22, mode="hex", top=512, cursor=600)
    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE,
                  lambda a: seen.update(window=active(a))])
    window = seen["window"]
    assert window.viewer.mode == "hex"
    assert (window.viewer.top, window.viewer.cursor) == (0, 0)
    assert (window.x, window.y, window.width, window.height) != (3, 2, 50, 15)


# -- the editor -------------------------------------------------------------------


def test_an_editor_opens_again_with_its_cursor_and_insert_mode(files):
    app = navigator(files)
    seen = {}
    run_app(app, [
        KeyEvent("end"), KeyEvent("f4"), IDLE,
        KeyEvent("pagedown"), KeyEvent("pagedown"), KeyEvent("right"), KeyEvent("insert"),
        lambda a: seen.update(at=(active(a).editor.line, active(a).editor.col,
                                  active(a).editor.top)),
        KeyEvent("escape"), lambda a: None,
        KeyEvent("f4"), IDLE,
        lambda a: seen.update(again=active(a)),
    ])
    editor = seen["again"].editor
    assert seen["at"][0] > 0
    assert (editor.line, editor.col, editor.top) == seen["at"]
    assert editor.overwrite is True
    assert EditRecord.find(files / "text.txt").overwrite is True


def test_without_store_editor_position_the_record_s_cursor_still_comes_back(files):
    """``EditFile`` put a tracked file's place back under *Track editing* alone
    (``DNUTIL.PAS:1337``); *Store editor position* is where a new editor opens."""
    SETTINGS.interface.store_editor_position = False
    EditRecord.store(files / "text.txt", line=120, col=3, top=110, overwrite=True)
    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), IDLE,
                  lambda a: seen.update(editor=active(a).editor)])
    editor = seen["editor"]
    assert (editor.line, editor.col, editor.top) == (120, 3, 110)
    assert editor.overwrite is True


def test_without_track_editing_the_cursor_starts_at_the_top(files):
    SETTINGS.interface.track_editing = False
    EditRecord.store(files / "text.txt", line=120, col=3, top=110, overwrite=True)
    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), IDLE,
                  lambda a: seen.update(editor=active(a).editor)])
    editor = seen["editor"]
    assert (editor.line, editor.col, editor.top) == (0, 0, 0)
    assert editor.overwrite is False


def test_store_editor_position_opens_a_new_editor_where_the_last_one_was(files):
    """``TempBounds``: the last editor's rectangle, for the next new one; off, the whole desktop."""
    (files / "other.txt").write_text("x\n")
    seen = {}

    def move(a):
        window = active(a)
        window.toggle_zoom()
        window.locate(5, 2, 40, 12)
        window.layout(a.shell.desktop.width, a.shell.desktop.height)

    def to_other(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index("other.txt")

    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), IDLE, move, IDLE, KeyEvent("escape"), IDLE,
                  to_other, KeyEvent("f4"), IDLE,
                  lambda a: seen.update(at=(active(a).x, active(a).y, active(a).width, active(a).height),
                                        zoomed=active(a).zoomed)])
    assert seen["zoomed"] is False and seen["at"] == (5, 2, 40, 12)

    SETTINGS.interface.store_editor_position = False
    EditRecord.delete_where()
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), IDLE, move, IDLE, KeyEvent("escape"), IDLE,
                  to_other, KeyEvent("f4"), IDLE, lambda a: seen.update(zoomed=active(a).zoomed)])
    assert seen["zoomed"] is True


def test_the_last_editor_rectangle_is_kept_between_runs():
    from navigator.lib.config import file_history

    file_history.LAST_EDIT = {"zoomed": False, "x": 3, "y": 1, "width": 50, "height": 15,
                              "desk_width": 80, "desk_height": 23}
    file_history.save_edit_bounds()
    file_history.LAST_EDIT = None
    file_history.load_edit_bounds()
    assert file_history.LAST_EDIT == {"zoomed": False, "x": 3, "y": 1, "width": 50, "height": 15,
                                      "desk_width": 80, "desk_height": 23}


def reopened(files, *changes):
    """The editor F4 opens on ``text.txt`` again, after *changes* to the first one and Esc."""
    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), IDLE, *changes,
                  KeyEvent("escape"), lambda a: None,
                  KeyEvent("f4"), IDLE, lambda a: seen.update(editor=active(a).editor)])
    return seen["editor"]


def test_an_editor_opens_again_with_its_modes_margins_and_block(files):
    def change(a):
        editor = active(a).editor
        editor.auto_indent = False
        editor.auto_brackets = True
        editor.highlight_line = True
        editor.justify_on_wrap = True
        editor.margins = (5, 60, 8)

    editor = reopened(files, change, KeyEvent("down"),
                      *[KeyEvent("right", shift=True)] * 4)
    assert (editor.auto_indent, editor.auto_brackets, editor.highlight_line,
            editor.justify_on_wrap, editor.highlight_column) == (False, True, True, True, False)
    assert editor.margins == (5, 60, 8)
    start, end = editor.block
    assert ((start.line, start.index), (end.line, end.index)) == ((1, 0), (1, 4))
    assert editor.block_hidden is False
    assert EditRecord.find(files / "text.txt").block == "1:0-1:4"


def test_a_column_block_comes_back_as_one_and_hidden_if_it_was(files):
    def mark(a):
        editor = active(a).editor
        editor.vertical_blocks = True
        editor.column_block = ((2, 1), (4, 6))
        editor.block_hidden = True

    editor = reopened(files, mark)
    assert editor.vertical_blocks is True
    assert editor.column_block == ((2, 1), (4, 6))
    assert editor.block_hidden is True
    assert editor.block is None


def test_a_block_the_shortened_file_no_longer_holds_is_dropped(files):
    EditRecord.store(files / "text.txt", line=0, col=0, top=0, block="150:0-150:4",
                     marks="1:2,,,,,,,,")
    (files / "text.txt").write_text("short\n")
    editor = reopened(files)
    assert editor.block is None
    assert editor.markers[0] == (1, 2)  # the markers' own rule, unchanged


def test_a_block_of_the_other_kind_is_dropped(files):
    EditRecord.store(files / "text.txt", line=0, col=0, top=0, block="|1:0-2:3")
    editor = reopened(files)
    assert editor.block is None and editor.column_block is None


def test_a_record_from_before_the_modes_were_kept_leaves_the_setup_s(files):
    SETTINGS.editor.auto_indent = False
    SETTINGS.editor.auto_brackets = True
    SETTINGS.editor.right_margin = 70
    EditRecord.store(files / "text.txt", line=3, col=0, top=0)
    record = EditRecord.find(files / "text.txt")
    assert (record.auto_indent, record.auto_brackets, record.right_margin) == (None, None, None)
    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), IDLE,
                  lambda a: seen.update(editor=active(a).editor)])
    editor = seen["editor"]
    assert (editor.auto_indent, editor.auto_brackets, editor.margins[1]) == (False, True, 70)
    assert editor.line == 3


def test_without_store_editor_position_the_modes_and_block_still_come_back(files):
    SETTINGS.interface.store_editor_position = False
    EditRecord.store(files / "text.txt", line=120, col=3, top=110, auto_indent=False,
                     left_margin=2, right_margin=50, paragraph=4, block="0:0-0:4")
    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), IDLE,
                  lambda a: seen.update(editor=active(a).editor)])
    editor = seen["editor"]
    assert (editor.line, editor.col, editor.top) == (120, 3, 110)
    assert editor.auto_indent is False
    assert editor.margins == (2, 50, 4)
    assert editor.block is not None


def test_tab_characters_switched_from_the_menu_come_back_and_an_old_record_keeps_the_setups(files):
    from navigator.widgets.editor.commands import SwitchTabs

    editor = reopened(files, lambda a: a.spawn(a.run_command(SwitchTabs(), active(a).editor)), IDLE)
    assert editor.insert_tabs is True
    EditRecord.store(files / "text.txt", line=0, col=0, top=0)  # insert_tabs None, as an old row
    SETTINGS.editor.insert_tabs = True
    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), IDLE, lambda a: seen.update(editor=active(a).editor)])
    assert seen["editor"].insert_tabs is True


def test_line_numbers_switched_from_the_menu_come_back_on_reopening(files):
    from navigator.widgets.editor.commands import SwitchLineNumbers

    editor = reopened(files, lambda a: a.spawn(a.run_command(SwitchLineNumbers(), active(a).editor)), IDLE)
    assert editor.line_numbers is True
    assert EditRecord.find(files / "text.txt").line_numbers is True


def test_soft_wrap_comes_back_and_gives_way_to_column_blocks(files):
    from navigator.widgets.editor.commands import SwitchSoftWrap

    editor = reopened(files, lambda a: a.spawn(a.run_command(SwitchSoftWrap(), active(a).editor)), IDLE)
    assert editor.soft_wrap is True
    EditRecord.store(files / "text.txt", line=0, col=0, top=0, vertical_blocks=True, soft_wrap=True)
    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), IDLE, lambda a: seen.update(editor=active(a).editor)])
    assert seen["editor"].vertical_blocks is True and seen["editor"].soft_wrap is False


def test_margins_out_of_order_are_put_right_as_format_margins_does(files):
    EditRecord.store(files / "text.txt", line=0, col=0, top=0,
                     left_margin=90, right_margin=60, paragraph=70)
    assert reopened(files).margins == (0, 60, 0)


def test_an_old_edit_history_table_gains_the_columns_and_keeps_its_rows():
    from navkit.database import DATABASE

    kept = ("path", "pinned", "seq", "used", "zoomed", "x", "y", "width", "height",
            "desk_width", "desk_height", "line", "col", "top", "left",
            "overwrite", "vertical_blocks", "highlight", "file_type", "marks")
    columns = ", ".join(field.column() for field in EditRecord.__fields__ if field.name in kept)
    DATABASE.execute(f'CREATE TABLE "edit_history" (id INTEGER PRIMARY KEY, {columns})')
    DATABASE.execute('INSERT INTO "edit_history" (path, seq, x, y, width, height, desk_width, '
                     'desk_height, line, col, top, "left") '
                     "VALUES ('/old.txt', 1, 0, 0, 80, 24, 80, 24, 7, 0, 0, 0)")
    record = EditRecord.find("/old.txt")
    assert record.line == 7
    assert (record.auto_indent, record.left_margin, record.block, record.block_hidden) == (
        None, None, "", False)


# -- the records -------------------------------------------------------------------


def test_a_record_stored_again_moves_to_the_front_and_keeps_its_pin(tmp_path):
    for name in "abc":
        ViewRecord.store(tmp_path / name)
    ViewRecord.toggle_pin(str(tmp_path / "a"))
    ViewRecord.store(tmp_path / "a", top=5)
    records = ViewRecord.ordered()
    assert [r.path for r in records] == [str(tmp_path / n) for n in "acb"]
    assert records[0].pinned and records[0].top == 5


def test_past_the_history_size_the_oldest_unpinned_records_go(tmp_path):
    assert SETTINGS.interface.history_size == 50
    SETTINGS.interface.history_size = 5
    ViewRecord.store(tmp_path / "keep")
    ViewRecord.toggle_pin(str(tmp_path / "keep"))
    for n in range(8):
        ViewRecord.store(tmp_path / f"f{n}")
    paths = [r.path for r in ViewRecord.ordered()]
    assert str(tmp_path / "keep") in paths and str(tmp_path / "f2") not in paths
    assert len(paths) == 5 + 1


def test_a_pinned_record_cannot_be_deleted(tmp_path):
    ViewRecord.store(tmp_path / "a")
    ViewRecord.toggle_pin(str(tmp_path / "a"))
    assert ViewRecord.forget(str(tmp_path / "a")) is False
    ViewRecord.toggle_pin(str(tmp_path / "a"))
    assert ViewRecord.forget(str(tmp_path / "a")) is True


def test_the_rectangle_is_scaled_to_a_desktop_that_changed_size():
    record = SimpleNamespace(x=10, y=4, width=40, height=10, desk_width=80, desk_height=20)
    assert scaled(record, 80, 20) == (10, 4, 40, 10)
    assert scaled(record, 160, 40) == (20, 8, 80, 20)
    # Shrunk below a window's minimum: DN took the whole desktop.
    assert scaled(record, 20, 6) is None


# -- the dialogs ------------------------------------------------------------------


def test_alt_pgdn_lists_the_files_viewed_and_opens_the_one_chosen(files):
    ViewRecord.store(files / "text.txt", mode="dump")
    ViewRecord.store(files / "other.txt")
    app = navigator(files)
    seen = {}
    run_app(app, [
        KeyEvent("pagedown", alt=True), lambda a: None,
        lambda a: seen.update(rows=[r.path for r in a.modal.records.items]),
        KeyEvent("down"), KeyEvent("space"), KeyEvent("enter"), IDLE,
        lambda a: seen.update(window=active(a)),
    ])
    assert seen["rows"] == [str(files / "other.txt"), str(files / "text.txt")]
    assert seen["window"].viewer.path == files / "text.txt"
    assert seen["window"].viewer.mode == "dump"
    assert ViewRecord.find(files / "text.txt").pinned


def test_delete_refuses_a_pinned_record_and_takes_an_unpinned_one(files):
    ViewRecord.store(files / "a")
    ViewRecord.store(files / "b")
    ViewRecord.toggle_pin(str(files / "b"))
    app = navigator(files)
    seen = {}
    run_app(app, [
        KeyEvent("pagedown", alt=True), lambda a: None,
        KeyEvent("delete"), lambda a: seen.update(after=len(a.modal.records.items)),
        KeyEvent("space"), KeyEvent("delete"), lambda a: None,
        lambda a: seen.update(modal=a.modal),
    ])
    assert seen["after"] == 2 and seen["modal"] is not None
    assert ViewRecord.count() == 1 and ViewRecord.ordered()[0].path == str(files / "a")


def test_with_tracking_off_the_list_says_to_turn_it_on(files):
    SETTINGS.interface.track_editing = False
    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("pageup", alt=True), lambda a: None,
                  lambda a: seen.update(prompt=a.modal.prompt)])
    assert '"Track editing history" ON first' in seen["prompt"]


def test_an_empty_history_shows_nothing(files):
    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("pagedown", alt=True), lambda a: None,
                  lambda a: seen.update(modal=a.modal)])
    assert seen["modal"] is None


def test_the_key_bar_names_the_list_s_own_keys_and_the_frame_does_not(files):
    ViewRecord.store(files / "text.txt")
    app = navigator(files)
    seen = {}

    def bottom(a):
        modal = a.modal
        ox, oy = modal.offset()
        y = oy + modal.y + modal.height - 1
        seen["row"] = "".join(a._front.get(x, y)[0] or " " for x in range(ox + modal.x, ox + modal.x + modal.width))
        seen["hints"] = key_bar_hints(a)

    run_app(app, [KeyEvent("pagedown", alt=True), lambda a: None, lambda a: None, bottom, KeyEvent("escape")])
    assert seen["hints"] == [("Space", "Pin"), ("Shift+↑↓", "Move"), ("←→", "Pinned")]
    assert "Space" not in seen["row"]
