"""Bookmarks: Alt+F1, Alt+F2 and Alt+C, where DOS Navigator chose a drive.

``navigator/bookmarks.py`` (the first set, seeding once, adding and removing),
navml's ``PopupMenu`` and the Manager's ``choose_bookmark``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.bookmarks import (
    add_bookmark,
    bookmarks,
    default_bookmarks,
    find_bookmark,
    remove_bookmark,
    seed_bookmarks,
)
from navigator.widgets.manager.manager.manager import bookmark_menu
from navml.widgets.dialog.control.control import parse_shortcut
from navml.widgets.menu.popup_menu import PopupMenu


@pytest.fixture
def places(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    for name in ("start", "first", "second", "gone"):
        (tmp_path / name).mkdir()
    return tmp_path


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def paths() -> list[str]:
    return [row.path for row in bookmarks()]


def popup(app) -> PopupMenu | None:
    return next((child for child in app.root.children if isinstance(child, PopupMenu)), None)


def captions(app) -> list[str]:
    return [parse_shortcut(entry.text)[0] for entry in popup(app).box.entries()
            if hasattr(entry, "text")]


# -- the first set ----------------------------------------------------------------


def test_the_first_set_is_home_its_desktop_folders_and_the_mounts(tmp_path):
    home = tmp_path / "home" / "me"
    for name in ("Documents", "Music", "Videos", "Elsewhere"):
        (home / name).mkdir(parents=True)
    mnt = tmp_path / "mnt"
    (mnt / "usb").mkdir(parents=True)
    (mnt / "backup").mkdir()
    (mnt / "file").write_text("")
    media = tmp_path / "media"
    (media / "me" / "STICK").mkdir(parents=True)
    (media / "cdrom").mkdir()

    found = default_bookmarks(home=home, config_home=tmp_path / "none", mnt=mnt, media=media, user="me")

    assert found == [
        home, home / "Documents", home / "Music", home / "Videos",
        mnt / "backup", mnt / "usb", media / "cdrom", media / "me" / "STICK",
    ]


def test_user_dirs_names_the_desktop_folders_and_home_means_none(tmp_path):
    home = tmp_path / "me"
    (home / "Dokumente").mkdir(parents=True)
    (home / "Documents").mkdir()
    (home / "Bilder").mkdir()
    config = tmp_path / "config"
    config.mkdir()
    (config / "user-dirs.dirs").write_text(
        "# written by xdg-user-dirs-update\n"
        'XDG_DOCUMENTS_DIR="$HOME/Dokumente"\n'
        f'XDG_PICTURES_DIR="{home}/Bilder"\n'
        'XDG_DESKTOP_DIR="$HOME/"\n'
        'XDG_MUSIC_DIR="$HOME"\n'
    )
    found = default_bookmarks(home=home, config_home=config, mnt=tmp_path / "x", media=tmp_path / "y", user="me")
    assert found == [home, home / "Dokumente", home / "Bilder"]


def test_the_first_set_is_written_once_and_an_emptied_list_stays_empty(tmp_path):
    assert seed_bookmarks([tmp_path / "a", tmp_path / "b"]) is True
    assert paths() == [str(tmp_path / "a"), str(tmp_path / "b")]
    remove_bookmark(tmp_path / "a")
    remove_bookmark(tmp_path / "b")
    assert seed_bookmarks([tmp_path / "a"]) is False
    assert paths() == []


def test_a_bookmark_added_goes_last_and_only_once(tmp_path):
    add_bookmark(tmp_path / "b")
    add_bookmark(tmp_path / "a")
    add_bookmark(tmp_path / "b")
    assert paths() == [str(tmp_path / "b"), str(tmp_path / "a")]
    assert find_bookmark(tmp_path / "a") is not None
    assert remove_bookmark(tmp_path / "a") is True
    assert remove_bookmark(tmp_path / "a") is False


# -- the box ------------------------------------------------------------------------


def test_the_box_offers_add_or_remove_and_greys_a_directory_that_is_gone(places):
    add_bookmark(places / "first")
    add_bookmark(places / "gone")
    (places / "gone").rmdir()
    menu, toggle = bookmark_menu(bookmarks(), bookmarked=False)
    entries = menu.entries()
    assert [entry.disabled for entry in entries[:2]] == [False, True]
    assert parse_shortcut(entries[0].text)[2] == "1"
    assert parse_shortcut(toggle.text)[0] == "Add this folder"
    _, toggle = bookmark_menu(bookmarks(), bookmarked=True)
    assert parse_shortcut(toggle.text)[0] == "Remove this folder"


def test_the_home_directory_is_spelled_with_a_tilde_that_marks_no_key(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    add_bookmark(tmp_path / "docs")
    menu, _ = bookmark_menu(bookmarks(), bookmarked=False)
    caption, _, letter = parse_shortcut(menu.entries()[0].text)
    assert caption == "1 ~/docs" and letter == "1"


def test_alt_f1_sends_the_left_panel_where_the_bookmark_says(places):
    add_bookmark(places / "first")
    add_bookmark(places / "second")
    app = navigator(places / "start")
    seen = {}
    run_app(app, [
        KeyEvent("tab"),
        KeyEvent("f1", alt=True), lambda a: None,
        lambda a: seen.update(captions=captions(a)),
        KeyEvent("2", char="2"), lambda a: None,
    ])
    manager = app.manager
    assert seen["captions"][-1] == "Add this folder"
    assert manager.left.path == places / "second"
    assert manager.right.path == places / "start"
    assert app.focused is manager.left
    assert popup(app) is None


def test_alt_f2_and_escape_change_nothing(places):
    add_bookmark(places / "first")
    app = navigator(places / "start")
    opened = []
    run_app(app, [
        KeyEvent("f2", alt=True), lambda a: None,
        lambda a: opened.append(popup(a) is not None),
        KeyEvent("escape"), lambda a: None,
    ])
    assert opened == [True]
    assert app.manager.right.path == places / "start"
    assert popup(app) is None


def test_the_box_opens_on_the_panels_own_bookmark(places):
    add_bookmark(places / "first")
    add_bookmark(places / "start")
    app = navigator(places / "start")
    current = []
    run_app(app, [
        KeyEvent("f1", alt=True), lambda a: None,
        lambda a: current.append(popup(a).box.current),
        KeyEvent("escape"),
    ])
    assert current == [1]


def test_add_bookmarks_the_panels_directory_and_remove_reopens_without_it(places):
    add_bookmark(places / "first")
    app = navigator(places / "start")
    seen = {}
    run_app(app, [
        KeyEvent("c", alt=True), lambda a: None,
        KeyEvent("a", char="a"), lambda a: None,
        lambda a: seen.update(added=paths(), closed=popup(a) is None),
        KeyEvent("c", alt=True), lambda a: None,
        lambda a: seen.update(before=captions(a)),
        KeyEvent("r", char="r"), lambda a: None,
        lambda a: seen.update(after=captions(a)),
        KeyEvent("escape"), lambda a: None,
    ])
    start = str(places / "start")
    assert seen["added"] == [str(places / "first"), start] and seen["closed"]
    assert seen["before"][-1] == "Remove this folder"
    assert seen["after"][-1] == "Add this folder"
    assert paths() == [str(places / "first")]


def test_alt_f1_brings_a_hidden_left_side_back(places):
    add_bookmark(places / "first")
    app = navigator(places / "start")
    run_app(app, [
        KeyEvent("f1", ctrl=True),
        KeyEvent("f1", alt=True), lambda a: None,
        KeyEvent("1", char="1"), lambda a: None,
    ])
    manager = app.manager
    assert manager.hidden_side is None and manager.left.visible
    assert manager.left.path == places / "first"
    assert app.focused is manager.left


def test_alt_f2_puts_the_panel_back_in_place_of_the_tree(places):
    add_bookmark(places / "first")
    app = navigator(places / "start")
    run_app(app, [
        KeyEvent("t", ctrl=True), lambda a: None,
        KeyEvent("f2", alt=True), lambda a: None,
        KeyEvent("1", char="1"), lambda a: None,
    ])
    manager = app.manager
    assert manager.replacement is None and manager.right.visible
    assert manager.right.path == places / "first"


def test_a_greyed_bookmark_cannot_be_chosen(places):
    add_bookmark(places / "gone")
    (places / "gone").rmdir()
    app = navigator(places / "start")
    still = []
    run_app(app, [
        KeyEvent("f1", alt=True), lambda a: None,
        KeyEvent("1", char="1"), lambda a: None,
        lambda a: still.append(popup(a) is not None),
        KeyEvent("escape"),
    ])
    assert still == [True]
    assert app.manager.left.path == places / "start"
