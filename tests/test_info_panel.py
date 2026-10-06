"""Ctrl+L: DOS Navigator's information panel (``TDiskInfo``, ``ReadDiskInfo``)."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.diskinfo import DiskFacts, _info_file, _meminfo, _mount_of, gather, lines
from navigator.settings import SETTINGS
from navigator.widgets.manager.panel.panel import DirEntry

MOUNTS = """\
/dev/sda2 / ext4 rw 0 0
/dev/sdb1 /mnt/usb vfat rw 0 0
/dev/sdc1 /mnt/usb\\040disk exfat rw 0 0
"""


def test_the_file_system_is_the_longest_mount_holding_the_directory():
    assert _mount_of(Path("/home/me"), MOUNTS) == ("/", "/dev/sda2", "ext4")
    assert _mount_of(Path("/mnt/usb/photos"), MOUNTS) == ("/mnt/usb", "/dev/sdb1", "vfat")
    assert _mount_of(Path("/mnt/usb disk"), MOUNTS) == ("/mnt/usb disk", "/dev/sdc1", "exfat")
    assert _mount_of(Path("/mnt/usbx"), MOUNTS)[0] == "/"


def test_memory_and_the_information_file(tmp_path):
    assert _meminfo("MemTotal: 2048 kB\nMemAvailable: 1024 kB\n") == (2048 * 1024, 1024 * 1024)
    (tmp_path / "file_id.diz").write_text("diz")
    assert _info_file(tmp_path) == ("File_ID.DIZ", ["diz"])
    (tmp_path / "DIRINFO").write_text("one\ntwo\n")
    assert _info_file(tmp_path) == ("DirInfo", ["one", "two"])


def test_gather_reads_a_directory(tmp_path):
    facts = gather(tmp_path, meminfo=tmp_path / "missing")
    assert facts.total and facts.free is not None and facts.memory_total is None


ENTRIES = [DirEntry("..", True, 0), DirEntry("sub", True, 0), DirEntry("a", False, 1000),
           DirEntry("b", False, 234)]
FACTS = DiskFacts(total=5000, free=1000, mount="/mnt/usb", device="/dev/sdb1", fs_type="vfat",
                  memory_total=4096 * 1024, memory_available=2048, memory_navigator=512,
                  info_name="DirInfo", info_lines=["Hello", "there"])


def test_the_lines_are_dns_each_behind_its_box():
    shows = SETTINGS.drive_info
    assert lines(Path("/mnt/usb"), ENTRIES, FACTS, shows) == [
        ("Current directory:", True), ("~/mnt/usb~", True), ("~3~ files with ~1,234~ bytes", True), ("", True),
        ("~5,000~ total bytes on ~/mnt/usb~", True), ("~1,000~ free bytes on ~/mnt/usb~", True),
        ("~/dev/sdb1 (vfat)~", True), ("", True),
        ("~4,096~K bytes total memory", True), ("~2,048~ bytes memory for user", True),
        ("~512~ bytes memory for Navigator", True),
        ("\0DirInfo", True), ("Hello", False), ("there", False),
    ]
    shows.directory_title = shows.volume_label = shows.navigator_memory = shows.information_file = False
    text = [line for line, _ in lines(Path("/x"), [ENTRIES[0]], FACTS, shows)]
    assert text[0] == "No files in this directory"
    assert "~/dev/sdb1 (vfat)~" not in text and "\0DirInfo" not in text
    assert text[-1] == "~2,048~ bytes memory for user"
    shows.volume_label = True
    labelled = DiskFacts(mount="/", device="/dev/sda2", label="ROOT")
    assert ("Volume label on ~/: ROOT~", True) in lines(Path("/"), [], labelled, SETTINGS.drive_info)


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.txt").write_text("x" * 100)
    (tmp_path / "sub" / "DirInfo").write_text("inside")
    return tmp_path


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def described(app) -> list[str]:
    return [text for text, _ in app.manager.info.lines()]


def test_ctrl_l_puts_the_information_in_the_passive_panels_place_and_it_follows(place):
    app = navigator(place)
    seen = {}

    def enter_sub(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index("sub")
        panel.enter()

    run_app(app, [KeyEvent("l", ctrl=True), Until(lambda a: a.manager.info.facts is not None),
                  lambda a: seen.update(first=described(a), replaced=a.manager.replaced is a.manager.right,
                                        focused=a.manager.left.focused),
                  enter_sub, Until(lambda a: "inside" in described(a)),
                  lambda a: seen.update(second=described(a)),
                  KeyEvent("l", ctrl=True), lambda a: None,
                  lambda a: seen.update(after=(a.manager.info.visible, a.manager.right.visible))])
    assert seen["replaced"] and seen["focused"]
    assert seen["first"][1] == f"~{place}~" and "~2~ files with ~100~ bytes" in seen["first"]
    assert seen["second"][1] == f"~{place / 'sub'}~" and seen["second"][-1] == "inside"
    assert seen["after"] == (False, True)


def test_information_panel_setup_saves_its_boxes(place):
    from navigator.widgets.shell.commands import DriveInfoSetup

    app = navigator(place)
    seen = {}

    def untick(a):
        seen["title"] = a.modal.title
        a.modal.options.value &= ~1  # Directory Title

    run_app(app, [lambda a: a.spawn(a.run_command(DriveInfoSetup)), lambda a: None, untick,
                  KeyEvent("enter"), lambda a: None])
    assert seen["title"] == "Information Panel Setup"
    assert SETTINGS.drive_info.directory_title is False and SETTINGS.drive_info.totals is True
    assert "directory_title = no" in SETTINGS.path.read_text()
