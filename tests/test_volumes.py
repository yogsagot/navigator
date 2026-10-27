"""Disk > Volumes: reading the mounts, and the window that lists them."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from navkit.events import KeyEvent

from conftest import Until, run_app

from navigator.lib.system import volumes
from navigator.lib.system.volumes import Volume, is_real, parse_mounts


MOUNTS = """\
sysfs /sys sysfs rw,nosuid 0 0
proc /proc proc rw 0 0
/dev/sda2 / ext4 rw,relatime 0 0
tmpfs /run tmpfs rw 0 0
/dev/sdb1 /mnt/My\\040Disk vfat rw 0 0
/dev/loop3 /snap/core/1 squashfs ro 0 0
server:/export /mnt/nfs nfs4 rw 0 0
user@host:/home /mnt/ssh fuse.sshfs rw 0 0
portal /run/user/1000/doc fuse.portal rw 0 0
/dev/sdc1 /mnt/stacked ext4 rw 0 0
/dev/sdd1 /mnt/stacked xfs rw 0 0
"""


def test_mounts_are_parsed_with_their_escapes_undone_and_the_last_mount_on_a_point_winning():
    found = {point: (device, kind) for device, point, kind in parse_mounts(MOUNTS)}
    assert found["/mnt/My Disk"] == ("/dev/sdb1", "vfat")
    assert found["/mnt/stacked"] == ("/dev/sdd1", "xfs")
    assert len(found) == 10


@pytest.mark.parametrize("device, kind, real", [
    ("/dev/sda2", "ext4", True),
    ("/dev/loop3", "squashfs", False),
    ("/dev/loop7", "ext4", False),
    ("proc", "proc", False),
    ("tmpfs", "tmpfs", False),
    ("server:/export", "nfs4", True),
    ("user@host:/home", "fuse.sshfs", True),
    ("//nas/share", "cifs", True),
    ("portal", "fuse.portal", False),
])
def test_what_counts_as_a_real_volume(device, kind, real):
    assert is_real(device, kind) is real


def test_gather_names_each_volume_by_its_label_and_skips_one_it_cannot_stat(tmp_path, monkeypatch):
    mounts = tmp_path / "mounts"
    mounts.write_text(MOUNTS)
    labels = tmp_path / "by-label"
    labels.mkdir()
    device = tmp_path / "sdb1"
    device.touch()
    os.symlink(device, labels / "My\\x20Stick")
    mounts.write_text(MOUNTS.replace("/dev/sdb1", str(device)))

    def usage(point):
        if point == "/mnt/nfs":
            raise OSError("stale")
        return shutil._ntuple_diskusage(1000, 400, 600)

    monkeypatch.setattr(volumes.shutil, "disk_usage", usage)
    found = volumes.gather(mounts=mounts, labels=labels)
    by_mount = {volume.mount: volume for volume in found}
    assert "/mnt/nfs" not in by_mount
    assert [volume.mount for volume in found] == sorted(by_mount)
    assert by_mount["/mnt/My Disk"].name == "My Stick"
    assert by_mount["/"].name == "sda2"
    assert by_mount["/"].free == 600 and by_mount["/"].total == 1000
    assert by_mount["/mnt/ssh"].name == "user@host:/home"
    assert not by_mount["/proc"].real


# -- the window --------------------------------------------------------------


def fake_volumes(where: Path) -> list[Volume]:
    return [
        Volume("sda2", "ext4", "/", "/dev/sda2", 100 << 30, 40 << 30),
        Volume("stick", "vfat", str(where), "/dev/sdb1", 8 << 30, 3 << 20),
        Volume("proc", "proc", "/proc", "proc", 0, 0, real=False),
    ]


def volumes_run(where, monkeypatch, *actions, start=None):
    """The Volumes window over :func:`fake_volumes`, its stick mounted on
    *where*, the panels on *start* (*where* by default)."""
    from test_nav import navigator

    monkeypatch.setattr(volumes, "gather", lambda: fake_volumes(where))
    app = navigator(start or where)

    def open_it(a):
        from navigator.widgets.shell.commands import OpenVolumesWindow

        a.spawn(a.run_command(OpenVolumesWindow))

    def listed(a):
        window = a.shell.desktop.active_window
        return getattr(window, "volumes", None) is not None and bool(window.volumes.items)

    run_app(app, [open_it, Until(listed), *actions, lambda a: None])
    return app


def test_the_window_lists_the_real_volumes_and_ctrl_h_ticks_the_box_that_shows_the_rest(tmp_path, monkeypatch):
    from navigator.widgets.shell.volumes_window import VolumesWindow

    seen = []

    def look(a):
        window = a.shell.desktop.active_window
        seen.append((type(window), [v.mount for v in window.volumes.items], a.focused is window.volumes,
                     window.everything.value))

    volumes_run(tmp_path, monkeypatch, look, KeyEvent("h", ctrl=True), look, KeyEvent("h", ctrl=True), look)
    assert seen[0] == (VolumesWindow, ["/", str(tmp_path)], True, 0)
    assert seen[1][1:] == (["/", str(tmp_path), "/proc"], True, 1)
    assert seen[2][1:] == (["/", str(tmp_path)], True, 0)


def test_alt_s_ticks_show_all_mounts(tmp_path, monkeypatch):
    seen = []

    def look(a):
        seen.append([v.mount for v in a.shell.desktop.active_window.volumes.items])

    volumes_run(tmp_path, monkeypatch, KeyEvent("s", alt=True), lambda a: None, look)
    assert seen == [["/", str(tmp_path), "/proc"]]


def test_tab_walks_the_list_the_boxes_and_the_buttons(tmp_path, monkeypatch):
    seen = []

    def look(a):
        window = a.shell.desktop.active_window
        names = {id(window.volumes): "list", id(window.everything): "box",
                 id(window.free_box): "free", id(window.go_button): "go", id(window.close_button): "close"}
        seen.append(names.get(id(a.focused)))

    tab = KeyEvent("tab")
    volumes_run(tmp_path, monkeypatch, tab, look, tab, look, tab, look, tab, look, tab, look)
    assert seen == ["box", "free", "go", "close", "list"]


def test_enter_sends_the_active_panel_to_the_mount_point(tmp_path, monkeypatch):
    other = tmp_path / "mounted"
    other.mkdir()
    seen = []

    def look(a):
        seen.append((a.shell.active_manager.active_panel.path, type(a.shell.desktop.active_window).__name__))

    volumes_run(other, monkeypatch, KeyEvent("down"), KeyEvent("enter"), lambda a: None, look, start=tmp_path)
    assert seen == [(other, "VolumesWindow")]


def test_go_sends_the_panel_to_the_volume_and_closes_the_window(tmp_path, monkeypatch):
    other = tmp_path / "mounted"
    other.mkdir()
    seen = []

    def look(a):
        seen.append((a.shell.active_manager.active_panel.path, type(a.shell.desktop.active_window).__name__))

    volumes_run(other, monkeypatch, KeyEvent("down"), KeyEvent("g", alt=True), lambda a: None, look,
                start=tmp_path)
    assert seen == [(other, "Manager")]


def test_close_closes_the_window_and_leaves_the_panel(tmp_path, monkeypatch):
    other = tmp_path / "mounted"
    other.mkdir()
    seen = []

    def press_close(a):
        a.shell.desktop.active_window.close_button.focus()

    def look(a):
        seen.append((a.shell.active_manager.active_panel.path, type(a.shell.desktop.active_window).__name__))

    volumes_run(other, monkeypatch, KeyEvent("down"), press_close, KeyEvent("enter"), lambda a: None, look,
                start=tmp_path)
    assert seen == [(tmp_path, "Manager")]


def test_the_rows_show_the_columns_in_short_units(tmp_path, monkeypatch):
    rows = []

    def look(a):
        listing = a.shell.desktop.active_window.volumes
        rows.extend(listing.cells(item) for item in listing.items)

    volumes_run(tmp_path, monkeypatch, look)
    assert rows[0] == [("sda2", False), ("ext4", False), ("/", False), ("60%", True), ("40G", True), ("100G", True)]
    assert rows[1][3:] == [("100%", True), ("3,072K", True), ("8,192M", True)]


def test_a_share_of_nothing_is_unknown():
    from navigator.widgets.shell.volume_list.volume_list import _percent

    assert _percent(0, 0, False) == _percent(None, 100, True) == "?"


def test_show_free_turns_the_use_column_into_the_free_one(tmp_path, monkeypatch):
    seen = []

    def look(a):
        listing = a.shell.desktop.active_window.volumes
        seen.append((listing.show_free, listing.cells(listing.items[0])[3]))

    volumes_run(tmp_path, monkeypatch, look, KeyEvent("f", alt=True), lambda a: None, look,
                KeyEvent("f", alt=True), lambda a: None, look)
    assert seen == [(False, ("60%", True)), (True, ("40%", True)), (False, ("60%", True))]


def test_the_volumes_menu_ticks_show_all_mounts_and_a_right_click_offers_it(tmp_path, monkeypatch):
    from navml.widgets.dialog.control.control import parse_shortcut
    from navml.widgets.menu.menu_box.menu_box import key_caption
    from navml.widgets.menu.popup_menu import PopupMenu
    from navigator.widgets.manager.commands import ToggleHidden

    seen = {}

    def popup(a):
        return next((c for c in a.root.children if isinstance(c, PopupMenu)), None)

    def look(name):
        def action(a):
            window = a.shell.desktop.active_window
            seen[name] = a.command_checked(ToggleHidden, a.focused)
            seen["keys"] = [key_caption(e, a, a.focused) for e in window.volumes_menu.entries()
                            if hasattr(e, "command")]
            seen["bar"] = [parse_shortcut(e.text)[0] for e in a.shell.menu.entries()]
        return action

    volumes_run(tmp_path, monkeypatch, look("off"), KeyEvent("h", ctrl=True), look("on"),
                KeyEvent("f10", shift=True), Until(lambda a: popup(a) is not None),
                lambda a: seen.update(items=[parse_shortcut(e.text)[0] for e in popup(a).box.entries()
                                             if hasattr(e, "command")]),
                KeyEvent("s", "s"), Until(lambda a: popup(a) is None), look("again"))
    assert "Volumes" in seen["bar"]
    assert seen["keys"] == ["Ctrl-R", "Ctrl-H", "F5", "F6", "F7", "Esc"]
    assert (seen["off"], seen["on"], seen["again"]) == (False, True, False)
    assert seen["items"] == ["Re-read", "Show all mounts", "Mount", "Unmount", "Eject", "Close"]
