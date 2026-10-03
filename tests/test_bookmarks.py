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
    label_bookmark,
    mounted_places,
    move_bookmark,
    remove_bookmark,
    seed_bookmarks,
)
from navigator.widgets.manager.manager.manager import bookmark_menu
from navml.widgets.dialog.control.control import parse_shortcut
from navml.widgets.menu.popup_menu import PopupMenu


@pytest.fixture
def places(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    # The machine's own drives stay out of the box; a test that wants some sets this.
    monkeypatch.setattr("navigator.bookmarks.mounted_places", lambda: [])
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


def test_a_bookmark_moves_one_place_and_not_past_either_end(tmp_path):
    for name in ("a", "b", "c"):
        add_bookmark(tmp_path / name)
    remove_bookmark(tmp_path / "b")
    add_bookmark(tmp_path / "d")

    assert move_bookmark(tmp_path / "d", -1)
    assert paths() == [str(tmp_path / n) for n in ("a", "d", "c")]
    assert move_bookmark(tmp_path / "a", 1)
    assert paths() == [str(tmp_path / n) for n in ("d", "a", "c")]
    assert not move_bookmark(tmp_path / "d", -1)
    assert not move_bookmark(tmp_path / "c", 1)
    assert not move_bookmark(tmp_path / "nowhere", 1)
    assert paths() == [str(tmp_path / n) for n in ("d", "a", "c")]


def test_a_label_is_shown_in_place_of_the_path_which_moves_to_the_key_column(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    add_bookmark(tmp_path / "work")
    add_bookmark(tmp_path / "play")
    assert label_bookmark(tmp_path / "work", "  ~Projects  ")
    assert not label_bookmark(tmp_path / "elsewhere", "No")
    menu, _ = bookmark_menu(bookmarks(), bookmarked=False)
    work, play = menu.entries()[:2]
    assert parse_shortcut(work.text)[:3:2] == ("1 ~Projects", "1") and work.key == "~/work"
    assert parse_shortcut(play.text)[0] == "2 ~/play" and play.key == ""
    label_bookmark(tmp_path / "work", "")
    menu, _ = bookmark_menu(bookmarks(), bookmarked=False)
    assert parse_shortcut(menu.entries()[0].text)[0] == "1 ~/work"


def test_what_is_mounted_is_read_from_the_mount_table(tmp_path):
    table = tmp_path / "mounts"
    table.write_text(
        "/dev/sda1 / ext4 rw 0 0\n"
        "/dev/sdb1 /mnt/usb vfat rw 0 0\n"
        "/dev/sdc1 /media/me/MY\\040DISK exfat rw 0 0\n"
        "/dev/sdd1 /run/media/me/STICK vfat rw 0 0\n"
        "/dev/sde1 /media/cdrom iso9660 ro 0 0\n"
        "/dev/sdf1 /mnt/usb/inner ext4 rw 0 0\n"
        "tmpfs /media/me tmpfs rw 0 0\n"
        "/dev/sdg1 /run/media/other/THEIRS vfat rw 0 0\n"
    )
    assert mounted_places(table, user="me") == [
        Path("/media/cdrom"), Path("/media/me/MY DISK"), Path("/mnt/usb"), Path("/run/media/me/STICK"),
    ]


def test_without_a_mount_table_every_mount_directory_is_offered(tmp_path):
    (tmp_path / "mnt" / "empty").mkdir(parents=True)
    (tmp_path / "media" / "me" / "STICK").mkdir(parents=True)
    (tmp_path / "run" / "me" / "DISK").mkdir(parents=True)
    found = mounted_places(tmp_path / "no-proc", tmp_path / "mnt", tmp_path / "media",
                           tmp_path / "run", user="me")
    assert found == [tmp_path / "mnt" / "empty", tmp_path / "media" / "me" / "STICK",
                     tmp_path / "run" / "me" / "DISK"]


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


def test_ctrl_up_and_down_move_the_selected_bookmark_and_keep_it_selected(places):
    for name in ("first", "second", "gone"):
        add_bookmark(places / name)
    app = navigator(places / "start")
    seen = {}
    run_app(app, [
        KeyEvent("f1", alt=True), lambda a: None,
        KeyEvent("down"), KeyEvent("down"), lambda a: None,
        KeyEvent("up", ctrl=True), lambda a: None,
        KeyEvent("up", ctrl=True), lambda a: None,
        KeyEvent("up", ctrl=True), lambda a: None,
        lambda a: seen.update(order=paths(), current=popup(a).box.current),
        KeyEvent("down", ctrl=True), lambda a: None,
        lambda a: seen.update(after=paths()),
        KeyEvent("enter"), lambda a: None,
    ])
    first, second, gone = (str(places / n) for n in ("first", "second", "gone"))
    assert seen["order"] == [gone, first, second] and seen["current"] == 0
    assert seen["after"] == [first, gone, second]
    assert app.manager.left.path == places / "gone"


def test_ctrl_down_on_add_moves_nothing_and_leaves_the_box_open(places):
    add_bookmark(places / "first")
    app = navigator(places / "start")
    seen = {}
    run_app(app, [
        KeyEvent("f1", alt=True), lambda a: None,
        KeyEvent("end"), lambda a: None,
        KeyEvent("down", ctrl=True), lambda a: None,
        lambda a: seen.update(open=popup(a) is not None, current=popup(a).box.current),
        KeyEvent("escape"), lambda a: None,
    ])
    assert seen["open"] and seen["current"] == 2
    assert paths() == [str(places / "first")]


def dialog(app):
    from navigator.widgets.manager.bookmark_label_dialog import BookmarkLabelDialog

    return next((c for c in app.root.children if isinstance(c, BookmarkLabelDialog)), None)


def test_f2_labels_the_selected_bookmark_and_the_box_comes_back(places):
    add_bookmark(places / "first")
    add_bookmark(places / "second")
    label_bookmark(places / "second", "Old")
    app = navigator(places / "start")
    seen = {}

    def type_label(a):
        box = dialog(a)
        seen["was"] = box.entry.value
        box.entry.value = "Two"

    run_app(app, [
        KeyEvent("f1", alt=True), lambda a: None,
        KeyEvent("down"), KeyEvent("f2"), lambda a: None,
        type_label,
        KeyEvent("enter"), lambda a: None,
        lambda a: seen.update(shown=captions(a), current=popup(a).box.current),
        KeyEvent("escape"), lambda a: None,
    ])
    assert seen["was"] == "Old"
    assert seen["shown"][:2] == [f"1 {places / 'first'}", "2 Two"] and seen["current"] == 1
    assert [row.label for row in bookmarks()] == ["", "Two"]


def test_an_emptied_label_goes_and_cancel_keeps_it(places):
    add_bookmark(places / "first")
    label_bookmark(places / "first", "One")
    app = navigator(places / "start")
    seen = {}
    run_app(app, [
        KeyEvent("f1", alt=True), lambda a: None,
        KeyEvent("f2"), lambda a: None,
        KeyEvent("escape"), lambda a: None,
        lambda a: seen.update(kept=bookmarks()[0].label),
        KeyEvent("f2"), lambda a: None,
        lambda a: setattr(dialog(a).entry, "value", "  "),
        KeyEvent("enter"), lambda a: None,
        KeyEvent("escape"), lambda a: None,
    ])
    assert seen["kept"] == "One"
    assert bookmarks()[0].label == ""


def test_del_removes_the_selected_bookmark_and_selects_the_next(places):
    for name in ("first", "second", "gone"):
        add_bookmark(places / name)
    app = navigator(places / "start")
    seen = {}
    run_app(app, [
        KeyEvent("f1", alt=True), lambda a: None,
        KeyEvent("down"), KeyEvent("delete"), lambda a: None,
        lambda a: seen.update(middle=(paths(), popup(a).box.current)),
        KeyEvent("delete"), lambda a: None,
        lambda a: seen.update(last=(paths(), popup(a).box.current)),
        KeyEvent("delete"), lambda a: None,
        lambda a: seen.update(empty=(paths(), captions(a))),
        KeyEvent("delete"), lambda a: None,
        lambda a: seen.update(on_add=(popup(a) is not None, captions(a))),
        KeyEvent("escape"), lambda a: None,
    ])
    first, gone = str(places / "first"), str(places / "gone")
    assert seen["middle"] == ([first, gone], 1)
    assert seen["last"] == ([first], 0)
    assert seen["empty"] == ([], ["Add this folder"])
    assert seen["on_add"] == (True, ["Add this folder"])
    assert app.manager.left.path == places / "start"


def test_mounts_not_bookmarked_follow_the_bookmarks_and_can_be_chosen(places, monkeypatch):
    for name in ("usb", "disk"):
        (places / name).mkdir()
    mounted = [places / "disk", places / "first", places / "usb"]
    monkeypatch.setattr("navigator.bookmarks.mounted_places", lambda: mounted)
    add_bookmark(places / "first")
    app = navigator(places / "start")
    seen = {}

    def unplug(a):
        mounted.remove(places / "usb")

    run_app(app, [
        KeyEvent("f1", alt=True), lambda a: None,
        lambda a: seen.update(shown=captions(a), lines=lines(a)),
        KeyEvent("3", char="3"), lambda a: None,
        lambda a: seen.update(went=a.manager.left.path),
        unplug,
        KeyEvent("f1", alt=True), lambda a: None,
        lambda a: seen.update(unplugged=captions(a)),
        KeyEvent("down"), lambda a: None,
        KeyEvent("delete"), lambda a: None,
        KeyEvent("f2"), lambda a: None,
        KeyEvent("up", ctrl=True), lambda a: None,
        lambda a: seen.update(still=(captions(a), paths(), popup(a).box.current)),
        KeyEvent("escape"), lambda a: None,
    ])
    first, disk, usb = (str(places / n) for n in ("first", "disk", "usb"))
    assert seen["shown"] == [f"1 {first}", f"2 {disk}", f"3 {usb}", "Add this folder"]
    assert seen["lines"] == [1, 4]
    assert seen["went"] == places / "usb"
    # The panel stood at the drive, which is gone: the box opens on the first entry.
    assert seen["unplugged"] == [f"1 {first}", f"2 {disk}", "Add this folder"]
    # On a mount's entry Del, F2 and Ctrl+Up pass by: nothing stored, the box still open there.
    assert seen["still"] == (seen["unplugged"], [first], 2)


def test_the_box_opens_on_the_mount_the_panel_is_at_and_add_bookmarks_it(places, monkeypatch):
    (places / "usb").mkdir()
    monkeypatch.setattr("navigator.bookmarks.mounted_places", lambda: [places / "usb"])
    add_bookmark(places / "first")
    app = navigator(places / "usb")
    seen = {}
    run_app(app, [
        KeyEvent("f1", alt=True), lambda a: None,
        lambda a: seen.update(current=popup(a).box.current),
        KeyEvent("a", char="a"), lambda a: None,
        KeyEvent("f1", alt=True), lambda a: None,
        lambda a: seen.update(shown=captions(a), lines=lines(a)),
        KeyEvent("escape"), lambda a: None,
    ])
    assert seen["current"] == 2
    usb = str(places / "usb")
    assert paths() == [str(places / "first"), usb]
    assert seen["shown"] == [f"1 {places / 'first'}", f"2 {usb}", "Remove this folder"]
    assert seen["lines"] == [2]


def lines(app) -> list[int]:
    from navml.widgets.menu.menu_line import MenuLine

    return [i for i, entry in enumerate(popup(app).box.entries()) if isinstance(entry, MenuLine)]
