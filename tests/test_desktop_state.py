"""Options > Save/Load desktop and Startup's *Autosave desktop* (``SaveDesktop``, ``RetrieveDesktop``)."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.lib.config import desktop_state
from navigator.__main__ import Navigator
from navigator.settings import SETTINGS
from navigator.widgets.manager.manager import Manager


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    SETTINGS.interface.store_editor_position = False
    for name in ("one", "two"):
        (tmp_path / name).mkdir()
    (tmp_path / "one" / "a.txt").write_text("hello\n")
    (tmp_path / "one" / "b.txt").write_text("b\n")
    return tmp_path


def navigator(place: Path, **kwargs) -> Navigator:
    return Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30), **kwargs)


def kinds(app) -> list[str]:
    return [type(w).__name__ for w in app.shell.desktop.windows()]


def arrange(a):
    """A desktop worth keeping: a manager in a state, a tree window and the calculator."""
    from navigator.widgets.shell.calculator_window import CalculatorWindow
    from navigator.widgets.tree.tree_window import TreeWindow

    left = a.manager.left
    left.view_mode = "detailed"
    left.sort_by("size")
    left.set_file_mask("*.txt")
    a.manager.right.focus()
    a.manager.switch_view(a.manager.info)
    a.shell.desktop.open(TreeWindow(start=a.manager.right.path))
    calc = a.shell.desktop.open(CalculatorWindow())
    calc.line.value = "6*7"


def cursor_on_b(a):
    """After the re-reads the sort and the mask asked for have landed."""
    left = a.manager.left
    left.cursor = [e.name for e in left.items].index("b.txt")


def test_save_then_load_brings_the_windows_and_their_state_back(place):
    from navigator.widgets.shell.commands import LoadDesktop, SaveDesktop

    app = navigator(place)
    seen = {}

    def close_all(a):
        for window in list(a.shell.desktop.windows()):
            window.close()

    def look(a):
        manager = next(w for w in a.shell.desktop.windows() if isinstance(w, Manager))
        left = manager.left
        seen.update(kinds=kinds(a), left=(left.path, left.view_mode, left.sort_mode, left.file_mask,
                                         left.selected.name if left.selected else None),
                    replaced=manager.replacement is manager.info and manager.replaced is manager.left,
                    calc=a.shell.desktop.windows()[-1].line.value)

    run_app(app, [arrange, lambda a: None, lambda a: None, cursor_on_b, lambda a: None,
                  lambda a: a.spawn(a.run_command(SaveDesktop)),
                  lambda a: None, close_all, lambda a: None,
                  lambda a: a.spawn(a.run_command(LoadDesktop)),
                  Until(lambda a: len(a.shell.desktop.windows()) == 3), lambda a: None, lambda a: None, look])
    assert seen["kinds"] == ["Manager", "TreeWindow", "CalculatorWindow"]
    assert seen["left"] == (place / "one", "detailed", "size", "*.txt", "b.txt")
    assert seen["replaced"] and seen["calc"] == "6*7"


def test_an_editor_comes_back_on_its_file(place):
    from navigator.widgets.editor.edit_window import EditWindow

    async def open_one(a):
        from navigator.lib.config.file_history import open_editor

        await open_editor(a.shell.desktop, place / "one" / "a.txt")

    app = navigator(place)
    seen = {}

    async def round_trip(a):
        data = desktop_state.snapshot(a.shell.desktop)
        for window in list(a.shell.desktop.windows()):
            window.close()
        await desktop_state.restore(a.shell.desktop, data)
        editor = next(w for w in a.shell.desktop.windows() if isinstance(w, EditWindow))
        seen.update(path=editor.editor.path, front=a.shell.desktop.active_window is editor)

    run_app(app, [lambda a: a.spawn(open_one(a)), Until(lambda a: "EditWindow" in kinds(a)),
                  lambda a: a.spawn(round_trip(a)), Until(lambda a: "path" in seen)])
    assert seen == {"path": place / "one" / "a.txt", "front": True}


def _editor_round_trip(place, path, change, *, smartpad=False):
    """An editor on *path* (SmartPad if *smartpad*), *change* made to it, the
    desktop kept and every window closed, then the desktop restored: the
    editor that came back, looked at by the caller through ``seen``."""
    from navigator.widgets.editor.edit_window import EditWindow

    async def open_one(a):
        if smartpad:
            from navigator.lib.utilities.smartpad import open_smartpad

            await open_smartpad(a.shell.desktop)
        else:
            from navigator.lib.config.file_history import open_editor

            await open_editor(a.shell.desktop, path)

    app = navigator(place)
    seen = {}

    async def round_trip(a):
        editor = next(w for w in a.shell.desktop.windows() if isinstance(w, EditWindow))
        change(editor)
        if smartpad:
            await editor.save()  # as closing it would, unasked
        seen["before"] = editor.editor.document.encode()
        data = desktop_state.snapshot(a.shell.desktop)
        for window in list(a.shell.desktop.windows()):
            window.close()
        from navigator.models.edit_record import EditRecord

        EditRecord.delete_where()
        await desktop_state.restore(a.shell.desktop, data)
        seen["window"] = next(w for w in a.shell.desktop.windows() if isinstance(w, EditWindow))

    run_app(app, [lambda a: a.spawn(open_one(a)), Until(lambda a: "EditWindow" in kinds(a)),
                  lambda a: a.spawn(round_trip(a)), Until(lambda a: "window" in seen)])
    return seen


def test_an_editor_comes_back_with_its_place_markers_margins_and_modes_untracked(place):
    """``TFileEditor.Store``/``Awaken``: kept whatever *Track editing* says."""
    path = place / "one" / "long.txt"
    path.write_text("".join(f"line {n} of the text\n" for n in range(40)))
    SETTINGS.interface.track_editing = False

    def change(window):
        editor = window.editor
        editor._move_to(2, 3)
        editor.markers = [(5, 1)] + [None] * 8
        editor.margins = (2, 60, 4)
        editor.autowrap, editor.optimal_fill, editor.back_indent = True, True, False

    seen = _editor_round_trip(place, path, change)
    editor = seen["window"].editor
    assert (editor.line, editor.col) == (2, 3)
    assert editor.markers[0] == (5, 1)
    assert editor.margins == (2, 60, 4)
    assert (editor.autowrap, editor.optimal_fill, editor.back_indent) == (True, True, False)


def test_an_editor_kept_before_its_state_was_still_opens(place):
    from navigator.widgets.editor.edit_window import EditWindow

    seen = {}
    data = {"version": desktop_state.VERSION, "front": 0,
            "windows": [{"kind": "editor", "path": str(place / "one" / "a.txt"), "smartpad": False}]}
    app = navigator(place)

    async def restore(a):
        await desktop_state.restore(a.shell.desktop, data)
        seen["path"] = next(w for w in a.shell.desktop.windows() if isinstance(w, EditWindow)).editor.path

    run_app(app, [lambda a: a.spawn(restore(a)), Until(lambda a: "path" in seen)])
    assert seen["path"] == place / "one" / "a.txt"


def test_a_restored_smartpad_is_not_stamped_again(place, monkeypatch):
    monkeypatch.setenv("SMARTPAD", str(place / "notes"))
    seen = _editor_round_trip(place, None, lambda window: None, smartpad=True)
    window = seen["window"]
    assert window.smartpad and window.editor.document.encode() == seen["before"]


def test_load_with_nothing_saved_says_so(place):
    from navigator.widgets.shell.commands import LoadDesktop

    app = navigator(place)
    seen = {}
    run_app(app, [lambda a: a.spawn(a.run_command(LoadDesktop)), Until(lambda a: a.modal is not None),
                  lambda a: seen.update(prompt=a.modal.prompt), KeyEvent("enter")])
    assert seen["prompt"] == "No desktop has been saved"


def test_autosave_saves_on_exit_and_restores_at_the_next_start(place):
    SETTINGS.startup.autosave_desktop = True
    run_app(navigator(place), [arrange, lambda a: None, lambda a: None])
    second = navigator(place)
    seen = {}
    run_app(second, [Until(lambda a: len(a.shell.desktop.windows()) == 3), lambda a: None,
                     lambda a: seen.update(kinds=kinds(a), mode=next(
                         w for w in a.shell.desktop.windows() if isinstance(w, Manager)).left.view_mode)])
    assert seen["kinds"] == ["Manager", "TreeWindow", "CalculatorWindow"] and seen["mode"] == "detailed"


def test_without_autosave_nothing_is_saved_or_restored(place):
    run_app(navigator(place), [arrange, lambda a: None])
    assert desktop_state.load() is None
    desktop_state.save(navigator(place).shell.desktop)
    second = navigator(place)
    seen = {}
    run_app(second, [lambda a: None, lambda a: seen.update(kinds=kinds(a))])
    assert seen["kinds"] == ["Manager"]


def test_directories_on_the_command_line_win_over_the_first_managers(place):
    SETTINGS.startup.autosave_desktop = True
    run_app(navigator(place), [arrange, lambda a: None, lambda a: None])
    third = Navigator(place / "two", place / "two", terminal=FakeTerminal(100, 30), given=True)
    seen = {}

    def look(a):
        manager = next(w for w in a.shell.desktop.windows() if isinstance(w, Manager))
        seen.update(paths=(manager.left.path, manager.right.path), mode=manager.left.view_mode)

    run_app(third, [Until(lambda a: len(a.shell.desktop.windows()) == 3), lambda a: None, look])
    assert seen["paths"] == (place / "two", place / "two") and seen["mode"] == "detailed"


def test_a_volumes_window_comes_back_showing_what_it_showed(place, monkeypatch):
    from navigator.lib.system import volumes
    from navigator.widgets.shell.volumes_window import VolumesWindow

    monkeypatch.setattr(volumes, "gather", lambda: [])
    app = navigator(place)
    seen = {}

    async def round_trip(a):
        a.shell.desktop.open(VolumesWindow(show_all=True, show_free=True))
        data = desktop_state.snapshot(a.shell.desktop)
        for window in list(a.shell.desktop.windows()):
            window.close()
        await desktop_state.restore(a.shell.desktop, data)
        window = a.shell.desktop.windows()[-1]
        seen.update(kinds=kinds(a), all=window.show_all, free=window.show_free)

    run_app(app, [lambda a: a.spawn(round_trip(a)), Until(lambda a: "kinds" in seen)])
    assert seen == {"kinds": ["Manager", "VolumesWindow"], "all": True, "free": True}


def test_a_calendar_saved_shorter_comes_back_its_own_size(place):
    from navigator.widgets.shell.calendar_window import CalendarWindow
    app = navigator(place)
    seen = {}

    async def round_trip(a):
        window = a.shell.desktop.open(CalendarWindow())
        width, height = window.size()
        window.locate(5, 3, width, height)
        data = desktop_state.snapshot(a.shell.desktop)
        # As a Navigator before the spelled row saved it: a row shorter.
        data["windows"][-1]["rect"]["height"] = height - 1
        for window in list(a.shell.desktop.windows()):
            window.close()
        await desktop_state.restore(a.shell.desktop, data)
        window = a.shell.desktop.windows()[-1]
        seen.update(rect=(window.x, window.y, window.width, window.height), size=(width, height))

    run_app(app, [lambda a: a.spawn(round_trip(a)), Until(lambda a: "rect" in seen)])
    # Its own size, which follows the month's weeks.
    assert seen["rect"] == (5, 3, *seen["size"])


# -- the database window (``TDBWindow.Store``) ----------------------------------------------------


def db_windows(a) -> list:
    from navigator.widgets.viewer.db_window import DBWindow

    return [w for w in a.shell.desktop.windows() if isinstance(w, DBWindow)]


def round_trip(seen, *, then=None):
    """Snapshot (through JSON, as the database keeps it), every window
    closed, and the desktop restored; *then* given the windows made."""
    import json

    async def act(a):
        data = json.loads(json.dumps(desktop_state.snapshot(a.shell.desktop)))
        seen["data"] = data
        for window in list(a.shell.desktop.windows()):
            window.close()
        seen["made"] = await desktop_state.restore(a.shell.desktop, data)
        if then is not None:
            then(a)
        seen["done"] = True

    return [lambda a: a.spawn(act(a)), Until(lambda a: "done" in seen, timeout=5)]


def opened(opener):
    async def act(a):
        await opener(a.shell.desktop)

    return [lambda a: a.spawn(act(a)), Until(lambda a: bool(db_windows(a)))]


def entry(seen) -> dict:
    return next(w for w in seen["data"]["windows"] if w.get("kind") == "database")


def test_a_dbase_window_comes_back_on_its_cell_widths_search_and_code_page(place):
    from test_dbf import write_dbf, write_russian
    from navigator.widgets.viewer.db_window.db_window import open_database

    write_dbf(place / "one" / "people.dbf")
    write_russian(place / "one" / "ru.dbf", "cp866", 0)
    app = navigator(place)
    seen = {}

    def arrange_it(a):
        window = db_windows(a)[0]
        window.db.set_codec("cp866")
        window.viewer.go(record=1, field=1)
        window.viewer.widths = {0: 4}
        window._search = {"text": "Анна", "case": False, "all_fields": True, "direction": 1}

    def look(a):
        window = db_windows(a)[0]
        seen.update(cell=(window.viewer.record, window.viewer.field), widths=window.viewer.widths,
                    codec=window.db.codec, search=window._search, name=window.db.fields[0].name)

    run_app(app, [*opened(lambda d: open_database(d, place / "one" / "ru.dbf")), arrange_it,
                  *round_trip(seen, then=look)])
    kept = entry(seen)
    assert kept["source"] == "dbf" and kept["codec"] == "cp866" and kept["path"] == str(place / "one" / "ru.dbf")
    assert seen["cell"] == (1, 1) and seen["widths"] == {0: 4}
    assert seen["codec"] == "cp866" and seen["name"] == "ИМЯ"
    assert seen["search"] == {"text": "Анна", "case": False, "all_fields": True, "direction": 1}


def test_a_page_the_file_names_itself_is_not_kept(place):
    from test_dbf import write_russian
    from navigator.widgets.viewer.db_window.db_window import open_database

    write_russian(place / "one" / "ru.dbf")  # byte 0x65: CP866 by itself
    app = navigator(place)
    seen = {}
    run_app(app, [*opened(lambda d: open_database(d, place / "one" / "ru.dbf")), *round_trip(seen)])
    assert "codec" not in entry(seen)


def test_a_sorted_table_comes_back_unsorted_on_the_same_record(place):
    from test_dbf import write_dbf
    from navigator.lib.viewer.table import SortedView
    from navigator.widgets.viewer.db_window.db_window import open_database

    write_dbf(place / "one" / "people.dbf")
    app = navigator(place)
    seen = {}

    def look(a):
        window = db_windows(a)[0]
        seen.update(sorted=isinstance(window.db, SortedView), record=window.viewer.record)

    # AGE (field 1) descending puts Cid (record 2) first: F8 twice.
    run_app(app, [*opened(lambda d: open_database(d, place / "one" / "people.dbf")),
                  lambda a: db_windows(a)[0].viewer.go(field=1), KeyEvent("f8"),
                  Until(lambda a: isinstance(db_windows(a)[0].db, SortedView)), KeyEvent("f8"),
                  Until(lambda a: db_windows(a)[0].db.sort == (1, True)),
                  lambda a: db_windows(a)[0].viewer.go(record=0),
                  *round_trip(seen, then=look)])
    assert entry(seen)["record"] == 2 and "top" not in entry(seen)
    assert seen["sorted"] is False and seen["record"] == 2


def make_sqlite(path):
    import sqlite3

    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE first(a)")
    connection.execute("CREATE TABLE second(name, n)")
    connection.executemany("INSERT INTO second VALUES (?, ?)", [(f"row{n}", n) for n in range(20)])
    connection.commit()
    connection.close()


@pytest.mark.parametrize("how", ["table", "query"])
def test_a_sqlite_table_or_query_comes_back_without_the_tables_box(place, how):
    from navigator.widgets.viewer.db_window.db_window import _reopen_sqlite, open_sqlite

    path = place / "one" / "two.sqlite"
    make_sqlite(path)
    app = navigator(place)
    seen = {}

    async def open_it(desktop):
        if how == "table":
            await open_sqlite(desktop, path, table="second")
        else:
            await open_sqlite(desktop, path, query="SELECT name FROM second WHERE n >= 10")

    def look(a):
        window = db_windows(a)[0]
        seen.update(name=window.db.name, count=window.db.count, record=window.viewer.record, modal=a.modal)

    run_app(app, [*opened(open_it), lambda a: db_windows(a)[0].viewer.go(record=5), *round_trip(seen, then=look)])
    kept = entry(seen)
    assert kept["source"] == "sqlite"
    if how == "table":
        assert kept["table"] == "second" and seen["name"] == "second" and seen["count"] == 20
    else:
        assert kept["query"] == "SELECT name FROM second WHERE n >= 10" and seen["count"] == 10
    assert seen["record"] == 5 and seen["modal"] is None


def test_a_table_gone_is_left_out_and_the_rest_come_back(place):
    import sqlite3

    from navigator.widgets.viewer.db_window.db_window import open_sqlite

    path = place / "one" / "two.sqlite"
    make_sqlite(path)
    app = navigator(place)
    seen = {}

    def drop(a):
        connection = sqlite3.connect(path)
        connection.execute("DROP TABLE second")
        connection.commit()
        connection.close()

    async def act(a):
        data = desktop_state.snapshot(a.shell.desktop)
        for window in list(a.shell.desktop.windows()):
            window.close()
        drop(a)
        await desktop_state.restore(a.shell.desktop, data)
        seen.update(kinds=kinds(a), modal=a.modal)

    run_app(app, [*opened(lambda d: open_sqlite(d, path, table="second")),
                  lambda a: a.spawn(act(a)), Until(lambda a: "kinds" in seen, timeout=5)])
    assert seen["kinds"] == ["Manager"] and seen["modal"] is None


def test_a_csv_comes_back_read_as_format_said_on_its_row(place):
    from navigator.lib.viewer.table import Dialect
    from navigator.widgets.viewer.db_window.db_window import open_csv

    path = place / "one" / "t.csv"
    path.write_text("".join(f"{n};x{n}\n" for n in range(30)))
    app = navigator(place)
    seen = {}

    def look(a):
        window = db_windows(a)[0]
        seen.update(dialect=window.csv.dialect, record=window.viewer.record, count=window.db.count)

    run_app(app, [*opened(lambda d: open_csv(d, path, dialect=Dialect(delimiter=";", header=False))),
                  lambda a: db_windows(a)[0].viewer.go(record=5), *round_trip(seen, then=look)])
    assert entry(seen)["dialect"] == {"delimiter": ";", "quotechar": '"', "header": False, "encoding": "utf-8"}
    assert seen["dialect"].delimiter == ";" and seen["dialect"].header is False
    assert seen["record"] == 5 and seen["count"] == 30


def test_a_window_on_a_fetched_copy_is_not_kept(place):
    from test_dbf import write_dbf
    from navigator.widgets.viewer.db_window.db_window import open_database

    write_dbf(place / "one" / "people.dbf")
    app = navigator(place)
    seen = {}

    def snap(a):
        db_windows(a)[0].use_set = object()
        seen["kinds"] = [w.get("kind") for w in desktop_state.snapshot(a.shell.desktop)["windows"]]
        db_windows(a)[0].use_set = None

    run_app(app, [*opened(lambda d: open_database(d, place / "one" / "people.dbf")), snap])
    assert "database" not in seen["kinds"]


def test_an_unzoomed_database_window_comes_back_where_it_was(place):
    from test_dbf import write_dbf
    from navigator.widgets.viewer.db_window.db_window import open_database

    write_dbf(place / "one" / "people.dbf")
    app = navigator(place)
    seen = {}

    def move(a):
        window = db_windows(a)[0]
        window.toggle_zoom()
        window.locate(3, 2, 50, 12)

    def look(a):
        window = db_windows(a)[0]
        seen["rect"] = (window.x, window.y, window.width, window.height, window.zoomed)

    run_app(app, [*opened(lambda d: open_database(d, place / "one" / "people.dbf")), move,
                  *round_trip(seen, then=look)])
    assert seen["rect"] == (3, 2, 50, 12, False)


def _manager_round_trip(place, arrange_it, after):
    """The manager arranged by *arrange_it*, the desktop kept (through JSON)
    and every window closed, then the desktop restored and *after* called on
    the manager that came back; what both put in ``seen``."""
    import json

    app = navigator(place)
    seen = {}

    async def round_trip(a):
        data = json.loads(json.dumps(desktop_state.snapshot(a.shell.desktop)))
        for window in list(a.shell.desktop.windows()):
            window.close()
        await desktop_state.restore(a.shell.desktop, data)
        manager = next(w for w in a.shell.desktop.windows() if isinstance(w, Manager))
        await after(a, manager, seen)
        seen["done"] = True

    run_app(app, [lambda a: arrange_it(a, seen), lambda a: None,
                  lambda a: a.spawn(round_trip(a)), Until(lambda a: "done" in seen)])
    return seen


def _placed(a):
    manager = a.manager
    if manager.zoomed:
        manager.toggle_zoom()
    manager.locate(4, 2, 80, 20)
    return manager


def test_a_hidden_side_comes_back_to_the_rectangle_it_had(place):
    """DN stored ``OldBounds`` with the double window (DBLWND.PAS:289, 311)."""
    def arrange_it(a, seen):
        manager = _placed(a)
        seen["before"] = (manager.x, manager.y, manager.width, manager.height)
        manager.hide_side("right")

    async def after(a, manager, seen):
        seen["hidden"] = manager.hidden_side
        manager.show_side("right")
        seen["after"] = (manager.x, manager.y, manager.width, manager.height)

    seen = _manager_round_trip(place, arrange_it, after)
    assert seen["hidden"] == "right" and seen["after"] == seen["before"]


def test_the_view_that_had_the_keyboard_has_it_again(place):
    def arrange_it(a, seen):
        a.manager.switch_view(a.manager.quick)
        a.manager._focus_replacement()

    async def after(a, manager, seen):
        seen["focused"] = manager.replacement is manager.quick and manager.quick.focus_within

    assert _manager_round_trip(place, arrange_it, after)["focused"]


def test_alt_z_on_the_quick_view_is_undone_after_a_load(place):
    def arrange_it(a, seen):
        manager = _placed(a)
        seen["before"] = (manager.x, manager.y, manager.width, manager.height)
        manager.switch_view(manager.quick)
        manager._focus_replacement()
        a.spawn(manager.on_zoom_window(None))

    async def after(a, manager, seen):
        seen["zoomed"] = (manager.zoomed, manager.hidden_side is not None)
        await manager.on_zoom_window(None)
        seen["after"] = (manager.x, manager.y, manager.width, manager.height, manager.zoomed, manager.hidden_side)

    seen = _manager_round_trip(place, arrange_it, after)
    assert seen["zoomed"] == (True, True)
    assert seen["after"] == (*seen["before"], False, None)
