"""File View History and File Edit History: a file opens again as it was left.

``navigator/file_history.py``, the ``ViewRecord``/``EditRecord`` models, the
windows' ``remember_history``/``recall_history`` and the Alt+PgDn / Alt+PgUp
dialog -- DOS Navigator's ``HISTRIES.PAS``.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.file_history import scaled
from navigator.models.edit_record import EditRecord
from navigator.models.view_record import ViewRecord
from navigator.settings import SETTINGS


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
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
        KeyEvent("end"), KeyEvent("f3"), lambda a: None,
        KeyEvent("pagedown"), KeyEvent("pagedown"), KeyEvent("f6"), unzoom,
        lambda a: seen.update(top=active(a).viewer.top),
        KeyEvent("escape"), lambda a: None,
        KeyEvent("f3"), lambda a: None,
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
        KeyEvent("end"), KeyEvent("f3"), lambda a: None, KeyEvent("f4"),
        KeyEvent("escape"), lambda a: None,
        KeyEvent("f3"), lambda a: None, lambda a: modes.append(active(a).viewer.mode),
        KeyEvent("escape"), lambda a: None,
        lambda a: a.manager.spawn(a.manager.view("text")), lambda a: None,
        lambda a: modes.append(active(a).viewer.mode),
    ])
    # File > View > As Text passes its mode, which wins over the record's.
    assert modes == ["hex", "text"]


def test_a_file_that_shrank_is_shown_from_its_start(files):
    ViewRecord.store(files / "text.txt", top=10**6, cursor=10**6)
    app = navigator(files)
    tops = []
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), lambda a: None,
                  lambda a: tops.append(active(a).viewer.top)])
    assert tops == [0]


def test_leaving_navigator_records_the_viewers_still_open(files):
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), lambda a: None, KeyEvent("f2")])
    assert ViewRecord.find(files / "text.txt").wrap is True


def test_with_tracking_off_nothing_is_recorded_or_restored(files):
    SETTINGS.interface.track_viewing = False
    ViewRecord.store(files / "text.txt", mode="hex")
    app = navigator(files)
    modes = []
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), lambda a: None, KeyEvent("f2"),
                  lambda a: modes.append(active(a).viewer.mode)])
    assert modes == ["text"]
    assert ViewRecord.find(files / "text.txt").wrap is False


# -- the editor -------------------------------------------------------------------


def test_an_editor_opens_again_with_its_cursor_and_insert_mode(files):
    app = navigator(files)
    seen = {}
    run_app(app, [
        KeyEvent("end"), KeyEvent("f4"), lambda a: None,
        KeyEvent("pagedown"), KeyEvent("pagedown"), KeyEvent("right"), KeyEvent("insert"),
        lambda a: seen.update(at=(active(a).editor.line, active(a).editor.col,
                                  active(a).editor.top)),
        KeyEvent("escape"), lambda a: None,
        KeyEvent("f4"), lambda a: None,
        lambda a: seen.update(again=active(a)),
    ])
    editor = seen["again"].editor
    assert seen["at"][0] > 0
    assert (editor.line, editor.col, editor.top) == seen["at"]
    assert editor.overwrite is True
    assert EditRecord.find(files / "text.txt").overwrite is True


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
        KeyEvent("down"), KeyEvent("space"), KeyEvent("enter"), lambda a: None,
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
