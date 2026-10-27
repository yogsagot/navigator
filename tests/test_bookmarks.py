"""Bookmarks: Alt+F1, Alt+F2 and Alt+C, where DOS Navigator chose a drive.

``navigator/lib/config/bookmarks.py`` (the first set, seeding once, adding and removing),
navml's ``PopupMenu`` and the Manager's ``choose_bookmark``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app, key_bar_hints
from navkit.events import KeyEvent
from navkit.screen import ScreenBuffer

from navigator.__main__ import Navigator
from navigator.lib.config.bookmarks import (
    add_bookmark,
    bookmarked_paths,
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
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    # The machine's own drives stay out of the box; a test that wants some sets this.
    monkeypatch.setattr("navigator.lib.config.bookmarks.mounted_places", lambda: [])
    for name in ("start", "first", "second", "gone"):
        (tmp_path / name).mkdir()
    return tmp_path


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def paths() -> list[str]:
    return [row.path for row in bookmarks()]


def popup(app) -> PopupMenu | None:
    return next((child for child in app.root.children if isinstance(child, PopupMenu)), None)


# The box opens once the mounts have been read on a thread, which takes more
# than a fixed step on a busy machine: Alt+F1, and every key that opens it again.
BOX = Until(lambda app: popup(app) is not None)


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
        KeyEvent("f1", alt=True), BOX,
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
        KeyEvent("f2", alt=True), BOX,
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
        KeyEvent("f1", alt=True), BOX,
        lambda a: current.append(popup(a).box.current),
        KeyEvent("escape"),
    ])
    assert current == [1]


def test_add_bookmarks_the_panels_directory_and_remove_reopens_without_it(places):
    add_bookmark(places / "first")
    app = navigator(places / "start")
    seen = {}
    run_app(app, [
        KeyEvent("c", alt=True), BOX,
        KeyEvent("a", char="a"), lambda a: None,
        lambda a: seen.update(added=paths(), closed=popup(a) is None),
        KeyEvent("c", alt=True), BOX,
        lambda a: seen.update(before=captions(a)),
        KeyEvent("r", char="r"), BOX,
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
        KeyEvent("f1", alt=True), BOX,
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
        KeyEvent("f2", alt=True), BOX,
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
        KeyEvent("f1", alt=True), BOX,
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
        KeyEvent("f1", alt=True), BOX,
        KeyEvent("down"), KeyEvent("down"), lambda a: None,
        KeyEvent("up", ctrl=True), BOX,
        KeyEvent("up", ctrl=True), BOX,
        KeyEvent("up", ctrl=True), BOX,
        lambda a: seen.update(order=paths(), current=popup(a).box.current),
        KeyEvent("down", ctrl=True), BOX,
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
        KeyEvent("f1", alt=True), BOX,
        KeyEvent("end"), lambda a: None,
        KeyEvent("down", ctrl=True), BOX,
        lambda a: seen.update(open=popup(a) is not None, current=popup(a).box.current),
        KeyEvent("escape"), lambda a: None,
    ])
    # The bookmark, a line, *Link*, *Trash*, a line, and *Add* last.
    assert seen["open"] and seen["current"] == 5
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
        KeyEvent("f1", alt=True), BOX,
        KeyEvent("down"), KeyEvent("f2"), lambda a: None,
        type_label,
        KeyEvent("enter"), BOX,
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
        KeyEvent("f1", alt=True), BOX,
        KeyEvent("f2"), lambda a: None,
        KeyEvent("escape"), BOX,
        lambda a: seen.update(kept=bookmarks()[0].label),
        KeyEvent("f2"), lambda a: None,
        lambda a: setattr(dialog(a).entry, "value", "  "),
        KeyEvent("enter"), BOX,
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
        KeyEvent("f1", alt=True), BOX,
        KeyEvent("down"), KeyEvent("delete"), BOX,
        lambda a: seen.update(middle=(paths(), popup(a).box.current)),
        KeyEvent("delete"), BOX,
        lambda a: seen.update(last=(paths(), popup(a).box.current)),
        KeyEvent("delete"), BOX,
        lambda a: seen.update(empty=(paths(), captions(a))),
        KeyEvent("delete"), BOX,
        lambda a: seen.update(on_add=(popup(a) is not None, captions(a))),
        KeyEvent("escape"), lambda a: None,
    ])
    first, gone = str(places / "first"), str(places / "gone")
    assert seen["middle"] == ([first, gone], 1)
    assert seen["last"] == ([first], 0)
    assert seen["empty"] == ([], ["Link", "Trash", "Add this folder"])
    assert seen["on_add"] == (True, ["Link", "Trash", "Add this folder"])
    assert app.manager.left.path == places / "start"


def test_mounts_not_bookmarked_follow_the_bookmarks_and_can_be_chosen(places, monkeypatch):
    for name in ("usb", "disk"):
        (places / name).mkdir()
    mounted = [places / "disk", places / "first", places / "usb"]
    monkeypatch.setattr("navigator.lib.config.bookmarks.mounted_places", lambda: mounted)
    add_bookmark(places / "first")
    app = navigator(places / "start")
    seen = {}

    def unplug(a):
        mounted.remove(places / "usb")

    run_app(app, [
        KeyEvent("f1", alt=True), BOX,
        lambda a: seen.update(shown=captions(a), lines=lines(a)),
        KeyEvent("3", char="3"), lambda a: None,
        lambda a: seen.update(went=a.manager.left.path),
        unplug,
        KeyEvent("f1", alt=True), BOX,
        lambda a: seen.update(unplugged=captions(a)),
        KeyEvent("down"), lambda a: None,
        KeyEvent("delete"), BOX,
        KeyEvent("f2"), lambda a: None,
        KeyEvent("up", ctrl=True), BOX,
        lambda a: seen.update(still=(captions(a), paths(), popup(a).box.current)),
        KeyEvent("escape"), lambda a: None,
    ])
    first, disk, usb = (str(places / n) for n in ("first", "disk", "usb"))
    assert seen["shown"] == [f"1 {first}", f"2 {disk}", f"3 {usb}", "Link", "Trash", "Add this folder"]
    assert seen["lines"] == [1, 4, 7]  # and the one above *Add*
    assert seen["went"] == places / "usb"
    # The panel stood at the drive, which is gone: the box opens on the first entry.
    assert seen["unplugged"] == [f"1 {first}", f"2 {disk}", "Link", "Trash", "Add this folder"]
    # On a mount's entry Del, F2 and Ctrl+Up pass by: nothing stored, the box still open there.
    assert seen["still"] == (seen["unplugged"], [first], 2)


def test_the_box_opens_on_the_mount_the_panel_is_at_and_add_bookmarks_it(places, monkeypatch):
    (places / "usb").mkdir()
    monkeypatch.setattr("navigator.lib.config.bookmarks.mounted_places", lambda: [places / "usb"])
    add_bookmark(places / "first")
    app = navigator(places / "usb")
    seen = {}
    run_app(app, [
        KeyEvent("f1", alt=True), BOX,
        lambda a: seen.update(current=popup(a).box.current),
        KeyEvent("a", char="a"), lambda a: None,
        KeyEvent("f1", alt=True), BOX,
        lambda a: seen.update(shown=captions(a), lines=lines(a)),
        KeyEvent("escape"), lambda a: None,
    ])
    assert seen["current"] == 2
    usb = str(places / "usb")
    assert paths() == [str(places / "first"), usb]
    assert seen["shown"] == [f"1 {places / 'first'}", f"2 {usb}", "Link", "Trash", "Remove this folder"]
    assert seen["lines"] == [2, 5]


def lines(app) -> list[int]:
    from navml.widgets.menu.menu_line import MenuLine

    return [i for i, entry in enumerate(popup(app).box.entries()) if isinstance(entry, MenuLine)]


def test_bookmarked_paths_follows_every_change_and_never_another_database(tmp_path):
    from navkit.database import DATABASE

    add_bookmark(tmp_path / "one")
    assert bookmarked_paths() == {str(tmp_path / "one")}
    add_bookmark(tmp_path / "two")
    remove_bookmark(tmp_path / "one")
    assert bookmarked_paths() == {str(tmp_path / "two")}
    move_bookmark(tmp_path / "two", 1)
    assert bookmarked_paths() == {str(tmp_path / "two")}
    DATABASE.open()                             # what the next test gets
    assert bookmarked_paths() == frozenset()
    seed_bookmarks([tmp_path / "three"])
    assert bookmarked_paths() == {str(tmp_path / "three")}


def test_adding_from_the_box_marks_the_row_in_the_other_panel_at_once(places):
    from dataclasses import replace

    from navkit.capabilities import FULL
    from navkit.glyphs import GLYPHS_UNICODE
    from navkit.screen import ScreenBuffer

    app = Navigator(places, places, terminal=FakeTerminal(80, 24, info=replace(FULL, glyphs=GLYPHS_UNICODE)))
    left = app.manager.left
    seen = {}

    def gutter(a):
        buffer = ScreenBuffer(80, 24)
        a.shell.render_tree(buffer)
        row = [e.name for e in left.items].index("first")
        return buffer.get(1, 2 + row)[0]

    run_app(app, [
        lambda a: setattr(a.manager.right, "path", places / "first"), lambda a: None,
        lambda a: seen.update(before=gutter(a)),
        KeyEvent("f2", alt=True), BOX,
        KeyEvent("a", char="a"), lambda a: None,
        lambda a: seen.update(after=gutter(a)),
    ])
    assert (seen["before"], seen["after"]) == ("/", left.BOOKMARK_MARK)


def test_the_box_is_titled_bookmarks_in_its_top_frame(places):
    add_bookmark(places / "first")
    app = navigator(places / "start")
    seen = []

    def top_row(a):
        box = popup(a).box
        buffer = ScreenBuffer(box.width, box.height)
        box.render_tree(buffer.view(-box.x, -box.y, box.width + box.x, box.height + box.y))
        seen.append("".join(buffer.get(x, 0)[0] or " " for x in range(box.width)))

    run_app(app, [KeyEvent("f1", alt=True), BOX, top_row, KeyEvent("escape")])
    assert " Bookmarks " in seen[0]


def frame_rows(a) -> tuple[str, str]:
    """The open box's top and bottom rows, as painted."""
    box = popup(a).box
    buffer = ScreenBuffer(box.width, box.height)
    box.render_tree(buffer.view(-box.x, -box.y, box.width + box.x, box.height + box.y))
    row = lambda y: "".join(buffer.get(x, y)[0] or " " for x in range(box.width))
    return row(0), row(box.height - 1)


def test_the_key_bar_names_the_bookmark_keys_and_the_frame_does_not(places):
    add_bookmark(places / "first")
    app = navigator(places / "start")
    seen = {}
    run_app(app, [KeyEvent("f1", alt=True), BOX,
                  lambda a: seen.update(hints=key_bar_hints(a), bottom=frame_rows(a)[1]), KeyEvent("escape"),
                  lambda a: None, lambda a: seen.update(after=key_bar_hints(a))])
    # The keys no function key stands for lead; F2's takes F2's own place.
    assert seen["hints"] == [("Del", "Delete"), ("Ctrl+\u2191\u2193", "Move"), ("F2", "Label")]
    assert "Label" not in seen["bottom"]
    assert seen["after"] == []  # the box gone, its keys gone from the bar


def test_with_no_bookmarks_the_key_bar_names_no_bookmark_keys(places):
    app = navigator(places / "start")
    seen = []
    run_app(app, [KeyEvent("f1", alt=True), BOX, lambda a: seen.append(key_bar_hints(a)), KeyEvent("escape")])
    assert ("F2", "Label") not in seen[0]


# -- the Link list: profiles edited, removed and moved with the box's own keys -------------------------


def link_names(app) -> list[str]:
    """The entries of the open *Link* list."""
    boxes = popup(app).boxes
    return [parse_shortcut(entry.text)[0] for entry in boxes[-1].entries() if hasattr(entry, "text")]


def into_link(app):
    """The cursor onto *Link* and the list opened, as Right opens it."""
    box = popup(app).boxes[0]
    names = [getattr(entry, "text", "") for entry in box.entries()]
    box.current = next(i for i, text in enumerate(names) if parse_shortcut(text)[0] == "Link")
    popup(app).choose(box.current)


def test_f2_edits_a_profile_del_removes_it_and_ctrl_down_moves_it(places):
    from navigator.lib.drives import profiles
    from navigator.widgets.drives.connect_dialog import ConnectDialog

    profiles.save("alpha", "sftp", "a.example", "me", 2222, "/srv")
    profiles.save("beta", "sftp", "b.example")
    profiles.save("gamma", "sftp", "c.example")
    app = navigator(places / "start")
    seen = {}

    def edit(a):
        dialog = a.modal
        seen["editing"] = (dialog.title, dialog.keep.visible, dialog.host.value, dialog.user.value,
                           dialog.port.value, dialog.directory.value, dialog.label.value)
        dialog.label.value = "alpha2"
        dialog.host.value = "a2.example"

    LINK_OPEN = Until(lambda a: popup(a) is not None and len(popup(a).boxes) == 2)
    run_app(app, [
        KeyEvent("f1", alt=True), BOX, into_link, LINK_OPEN,
        lambda a: seen.update(hints=key_bar_hints(a)),
        KeyEvent("f2"), Until(lambda a: isinstance(a.modal, ConnectDialog)), edit, KeyEvent("enter"),
        LINK_OPEN, lambda a: seen.update(after_edit=link_names(a), at=popup(a).boxes[-1].current),
        KeyEvent("down"), KeyEvent("delete"), LINK_OPEN,
        lambda a: seen.update(after_delete=link_names(a)),
        KeyEvent("up"), KeyEvent("down", ctrl=True), LINK_OPEN,
        lambda a: seen.update(after_move=link_names(a), moved_to=popup(a).boxes[-1].current),
        KeyEvent("escape"), KeyEvent("escape"), lambda a: None,
    ])
    # The *Link* list's keys are on the key bar while it is open.
    assert ("Del", "Delete") in seen["hints"] and ("F2", "Edit") in seen["hints"]
    assert seen["editing"] == ("Edit SSH link (SFTP)", False, "a.example", "me", "2222", "/srv", "alpha")
    assert seen["after_edit"][:3] == ["alpha2", "beta", "gamma"] and seen["at"] == 0
    assert seen["after_delete"][:2] == ["alpha2", "gamma"]
    assert seen["after_move"][:2] == ["gamma", "alpha2"] and seen["moved_to"] == 1
    assert [(row.name, row.host) for row in profiles.profiles()] == [("gamma", "c.example"),
                                                                     ("alpha2", "a2.example")]


@pytest.mark.parametrize("tick, answer, deleted, asks_again", [
    (False, "y", True, True),    # Yes: deleted, and asked next time
    (False, "n", False, True),   # No: kept
    (True, "y", True, False),    # Don't ask again, Yes: deleted, and saved unticked
    (True, "n", False, True),    # ... with No: nothing changes
])
def test_del_asks_first_with_delete_bookmark_ticked(places, tick, answer, deleted, asks_again):
    from navigator.settings import SETTINGS, config_path

    SETTINGS.confirmations.delete_bookmark = True
    add_bookmark(places / "first")
    app = navigator(places / "start")
    seen = {}

    def look(a):
        seen.update(box=type(a.modal).__name__, tail=a.modal.prompt_tail.text)
        if tick:
            a.modal.options.value = 1

    run_app(app, [
        KeyEvent("f1", alt=True), BOX,
        KeyEvent("delete"), Until(lambda a: type(a.modal).__name__ == "DeleteBookmarkDialog"),
        look,
        KeyEvent(answer, answer, alt=True), BOX,
        KeyEvent("escape"), lambda a: None,
    ])
    # A path too long for the line keeps its end, which is what tells one from another.
    shown = str(places / "first")
    shown = shown if len(shown) <= 46 else "..." + shown[-43:]
    assert seen == {"box": "DeleteBookmarkDialog", "tail": shown}
    assert paths() == ([] if deleted else [str(places / "first")])
    assert SETTINGS.confirmations.delete_bookmark is asks_again
    saved = config_path().exists() and "delete_bookmark = no" in config_path().read_text(encoding="utf-8")
    assert saved is (not asks_again)
