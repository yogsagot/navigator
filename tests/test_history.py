"""Input history: the store, the button, the list it drops, and when it records."""

from __future__ import annotations

import pathlib

import pytest

from navkit.events import KeyEvent, MouseClickEvent
from navml.history import HISTORY, HistoryStore
from navml.widgets.dialog.history import History, HistoryList

from conftest import run_app
from test_nav import navigator


# -- the store, as HISTLIST.PAS keeps it ----------------------------------------------


def test_newest_first_and_a_repeat_moves_to_the_front():
    store = HistoryStore()
    for text in ("a", "b", "c", "a"):
        store.add("x", text)
    assert store.entries("x") == ["a", "c", "b"]


def test_lists_are_kept_apart_by_id_and_empty_text_is_not_recorded():
    store = HistoryStore()
    store.add("x", "one")
    store.add("y", "two")
    store.add("x", "")
    assert (store.entries("x"), store.entries("y"), store.entries("z")) == (
        ["one"], ["two"], [])


def test_the_oldest_unpinned_entry_goes_past_the_limit():
    store = HistoryStore(limit=3)
    for text in "abcd":
        store.add("x", text)
    assert store.entries("x") == ["d", "c", "b"]


def test_a_pinned_entry_is_never_evicted_and_keeps_its_pin_when_added_again():
    store = HistoryStore(limit=2)
    store.add("x", "keep")
    store.pin("x", "keep")
    for text in "abc":
        store.add("x", text)
    assert store.entries("x") == ["c", "b", "keep"]
    store.add("x", "keep")
    assert store.entries("x")[0] == "keep" and store.is_pinned("x", "keep")


def test_remove_clear_and_a_round_trip_through_plain_data():
    store = HistoryStore()
    for text in ("a", "b", "c"):
        store.add("x", text)
    store.pin("x", "a")
    store.remove("x", "b")
    copy = HistoryStore()
    copy.load_data(store.to_data())
    assert copy.entries("x") == ["c", "a"] and copy.is_pinned("x", "a")
    copy.load_data({"y": ["plain", {"text": "flagged", "pinned": True}]})
    assert copy.entries("y") == ["plain", "flagged"] and copy.is_pinned("y", "flagged")
    copy.clear()
    assert copy.entries("y") == []


# -- in the Make directory dialog --------------------------------------------------------


def field_of(app):
    return app.modal.entry


def test_accepting_a_dialog_records_its_line_and_cancelling_does_not(tmp_path):
    app = navigator(tmp_path)
    run_app(app, [
        KeyEvent("f7"), lambda a: None, KeyEvent("n", "n"), KeyEvent("enter"),
        lambda a: None,
        KeyEvent("f7"), lambda a: None, KeyEvent("q", "q"), KeyEvent("escape"),
    ])
    assert (tmp_path / "n").is_dir()
    assert HISTORY.entries("mkdir") == ["n"]


def test_down_drops_the_list_on_the_second_entry_and_enter_takes_it(tmp_path):
    HISTORY.add("mkdir", "older")
    HISTORY.add("mkdir", "newer")
    app = navigator(tmp_path)
    seen = []
    run_app(app, [
        KeyEvent("f7"), lambda a: None,
        KeyEvent("t", "t"), KeyEvent("down"),
        lambda a: seen.append((type(a.modal).__name__, a.modal.items, a.modal.cursor)),
        KeyEvent("enter"),
        lambda a: seen.append((type(a.modal).__name__, field_of(a).value)),
    ])
    # What was typed is recorded first, so it is the top of the list, and the
    # list opens on the entry after it.
    assert seen[0] == ("HistoryList", ["t", "newer", "older"], 1)
    assert seen[1] == ("MkdirDialog", "newer")


def test_escape_leaves_the_line_as_it_was(tmp_path):
    HISTORY.add("mkdir", "old")
    app = navigator(tmp_path)
    seen = []
    run_app(app, [
        KeyEvent("f7"), lambda a: None, KeyEvent("n", "n"), KeyEvent("down"),
        KeyEvent("escape"),
        lambda a: seen.append((type(a.modal).__name__, field_of(a).value)),
    ])
    assert seen == [("MkdirDialog", "n")]


def test_a_click_on_the_button_drops_the_list(tmp_path):
    HISTORY.add("mkdir", "old")
    app = navigator(tmp_path)
    seen = []

    def click(a):
        button = field_of(a).history
        dx, dy = button.offset()
        a.post_event(MouseClickEvent(dx + button.x + 1, dy + button.y, "left"))

    run_app(app, [KeyEvent("f7"), lambda a: None, click, lambda a: None,
                  lambda a: seen.append(type(a.modal).__name__)])
    assert seen == ["HistoryList"]


def test_the_list_is_where_thistory_puts_it(tmp_path):
    HISTORY.add("mkdir", "old")
    app = navigator(tmp_path)
    seen = []

    def look(a):
        window, line = a.modal, a.modal.button.link
        lx, ly = line.offset()
        lx, ly = lx + line.x, ly + line.y
        seen.append(((window.x, window.y, window.width, window.height),
                     (lx - 1, ly - 1, line.width + 2)))

    run_app(app, [KeyEvent("f7"), lambda a: None, KeyEvent("down"), look])
    (window, (x, y, width)), = seen
    # One column out on either side, from the row above; eight rows unless
    # the dialog clips it, and the eight-row Make directory dialog does.
    assert window[:3] == (x, y, width)
    assert 0 < window[3] <= 8


def test_a_line_without_a_history_leaves_down_to_the_dialog():
    import asyncio

    from navml.widgets.dialog.input_line import InputLine

    line = InputLine()
    assert line.history is None
    assert asyncio.run(line.on_key(KeyEvent("down"))) is False


def test_a_history_list_does_not_search(tmp_path):
    HISTORY.add("mkdir", "older")
    HISTORY.add("mkdir", "newer")
    app = navigator(tmp_path)
    seen = []
    run_app(app, [
        KeyEvent("f7"), lambda a: None, KeyEvent("down"),
        KeyEvent("o", "o"),
        lambda a: seen.append((type(a.modal).__name__, a.modal.search, a.modal.cursor)),
    ])
    assert seen == [("HistoryList", None, 1)]
