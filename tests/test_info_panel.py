"""Ctrl+L: DOS Navigator's information panel (``TDiskInfo``, ``ReadDiskInfo``)."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.system.diskinfo import (DiskFacts, FileFacts, _info_file, _meminfo, file_lines, mount_of,
                                           gather, lines, stat_file, table)
from navigator.settings import SETTINGS
from navigator.widgets.manager.panel.panel import DirEntry

MOUNTS = """\
/dev/sda2 / ext4 rw 0 0
/dev/sdb1 /mnt/usb vfat rw 0 0
/dev/sdc1 /mnt/usb\\040disk exfat rw 0 0
"""


def test_the_file_system_is_the_longest_mount_holding_the_directory():
    assert mount_of(Path("/home/me"), MOUNTS) == ("/", "/dev/sda2", "ext4")
    assert mount_of(Path("/mnt/usb/photos"), MOUNTS) == ("/mnt/usb", "/dev/sdb1", "vfat")
    assert mount_of(Path("/mnt/usb disk"), MOUNTS) == ("/mnt/usb disk", "/dev/sdc1", "exfat")
    assert mount_of(Path("/mnt/usbx"), MOUNTS)[0] == "/"


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


def shown(entry, facts) -> list[tuple[str, bool]]:
    """:func:`file_lines` with the table's padding taken off."""
    return [(text.strip(), centred) for text, centred in file_lines(entry, facts)]


def test_the_current_file_is_described_under_its_rule(monkeypatch):
    monkeypatch.setattr("navigator.lib.config.country.stamp", lambda when: f"t{int(when)}")
    entry = DirEntry("notes.txt", False, 1234, 0o100644, 10.0, uid=0, gid=0)
    facts = FileFacts(atime=20.0, ctime=30.0, nlink=2, inode=99, mime="text/plain")
    text = [line for line, _ in shown(entry, facts)]
    assert text[0] == "\0Current file"
    assert text[1:] == [
        "Name: ~notes.txt~", "Type: ~File, text/plain~", "Size: ~1,234~ bytes", "Modified: ~t10~",
        "Accessed: ~t20~", "Changed: ~t30~", "Attributes: ~rw-r--r-- (0644)~", f"Owner: ~{entry.display_owner}~",
        "Links: ~2~, inode ~99~",
    ]
    # Not read yet (or on another drive): what the listing knows, no more.
    assert "Accessed: ~t20~" not in [line for line, _ in shown(entry, None)]
    # One block, centred: the labels right-aligned on their colons, every
    # line as wide as the widest, so they share a column.
    block = [line for line, _ in file_lines(entry, facts)[1:]]
    assert block[0].rstrip() == "      Name: ~notes.txt~" and block[6].startswith("Attributes: ~")
    assert {line.index(":") for line in block} == {len("Attributes")}
    assert {len(line.replace("~", "")) for line in block} == {len("Attributes: rw-r--r-- (0644)")}
    assert all(centred for _, centred in file_lines(entry, facts))


def test_a_row_without_a_label_keeps_its_text():
    assert table(["Name: ~a~", "plain", "Attributes: ~b~"]) == [
        "      Name: ~a~", "plain        ", "Attributes: ~b~"]


def test_directories_links_and_dotdot():
    folder = DirEntry("sub", True, 0, 0o40755)
    assert ("Size: ~not counted~", True) in shown(folder, FileFacts(mime="x/y"))
    assert ("Type: ~Directory~", True) in shown(folder, FileFacts(mime="x/y"))
    folder.counted, folder.size = True, 5
    assert ("Size: ~5~ bytes", True) in shown(folder, None)
    link = DirEntry("l", False, 3, 0o100644, is_link=True, link_target="a.txt")
    assert ("Type: ~Symbolic link to a file~", True) in shown(link, None)
    assert ("Link to: ~a.txt~", True) in shown(link, None)
    stale = DirEntry("s", False, 0, 0o120777, is_link=True, link_target="gone")
    assert ("Type: ~Broken symbolic link~", True) in shown(stale, None)
    assert shown(DirEntry("..", True, 0), None) == [] and shown(None, None) == []


def test_the_section_follows_the_directory_block_behind_its_box():
    shows = SETTINGS.drive_info
    entry = DirEntry("a", False, 1000, 0o100644)
    text = [line.strip() for line, _ in lines(Path("/mnt/usb"), ENTRIES, FACTS, shows, entry, None)]
    rule = text.index("\0Current file")
    assert text[rule - 2:rule] == ["~3~ files with ~1,234~ bytes", ""] and text[rule + 1] == "Name: ~a~"
    assert text[text.index("Attributes: ~rw-r--r-- (0644)~") + 1:][:2] == ["", "\0Drive"]
    assert text[text.index("\0Drive") + 1] == "~5,000~ total bytes on ~/mnt/usb~"
    # The closing rule gives way to the information file's, and to the end.
    shows.volume_size = shows.volume_free = shows.volume_label = False
    text = [line.strip() for line, _ in lines(Path("/mnt/usb"), ENTRIES, FACTS, shows, entry, None)]
    assert text[text.index("\0Memory") + 1] == "~4,096~K bytes total memory"
    shows.total_memory = shows.user_memory = shows.navigator_memory = False
    text = [line.strip() for line, _ in lines(Path("/mnt/usb"), ENTRIES, FACTS, shows, entry, None)]
    assert not {"\0", "\0Drive", "\0Memory"} & set(text) and text[text.index("\0DirInfo") - 1] == "Attributes: ~rw-r--r-- (0644)~"
    shows.information_file = False
    assert lines(Path("/mnt/usb"), ENTRIES, FACTS, shows, entry, None)[-1][0].strip() == \
        "Attributes: ~rw-r--r-- (0644)~"
    shows.current_file = False
    assert "\0Current file" not in [line for line, _ in lines(Path("/"), ENTRIES, FACTS, shows, entry, None)]


def test_media_details_join_the_table():
    from navigator.lib.system.mediainfo import Media

    entry = DirEntry("a.png", False, 10, 0o100644)
    text = [line for line, _ in file_lines(entry, FileFacts(nlink=1, inode=2, media=Media(width=4, height=3)))]
    assert text[-1].rstrip() == "Dimensions: ~4 × 3~" and text[-2].strip() == "Links: ~1~, inode ~2~"
    assert {line.index(":") for line in text[1:]} == {len("Attributes")}


def test_a_programs_libraries_continue_under_the_first():
    from navigator.lib.system.programinfo import Program

    program = Program(machine=62, kind="pie", interpreter="/lib/ld.so",
                      needed=[("libc.so.6", "/lib/libc.so.6"), ("libgone.so.1", None)], stripped=True)
    entry = DirEntry("prog", False, 10, 0o100755)
    text = [line.rstrip() for line, _ in file_lines(entry, FileFacts(media=program))]
    start = text.index("    Program: ~ELF 64-bit x86-64, PIE executable~")
    assert text[start:] == [
        "    Program: ~ELF 64-bit x86-64, PIE executable~",
        "Interpreter: ~/lib/ld.so~",
        "  Libraries: ~libc.so.6~",
        "             ~libgone.so.1~ (not found)",
        "    Symbols: ~stripped~",
    ]
    assert table(["Name: ~a~", ": ~b~"]) == ["Name: ~a~", "      ~b~"]


def test_stat_file_recognises_a_program(tmp_path):
    from test_programinfo import elf

    (tmp_path / "prog").write_bytes(elf(type_=2))
    (tmp_path / "prog").chmod(0o755)
    (tmp_path / "libx.so").write_bytes(elf())
    assert stat_file(tmp_path / "prog", "prog").mime == "application/x-executable"
    assert stat_file(tmp_path / "libx.so", "libx.so").mime == "application/x-sharedlib"
    assert stat_file(None, "libx.so").mime == "application/octet-stream"

def test_stat_file(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    facts = stat_file(tmp_path / "a.txt", "a.txt")
    assert facts.nlink == 1 and facts.inode and facts.atime is not None and facts.mime == "text/plain"
    assert stat_file(tmp_path / "missing", "missing") == FileFacts()
    assert stat_file(None, "b.txt") == FileFacts(mime="text/plain")


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.txt").write_text("x" * 100)
    (tmp_path / "sub" / "DirInfo").write_text("inside")
    return tmp_path


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def described(app) -> list[str]:
    return [text.strip() for text, _ in app.manager.info.lines()]


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


def test_the_current_file_follows_the_cursor(place):
    app = navigator(place)
    seen = {}

    def to(name):
        def move(a):
            panel = a.manager.left
            panel.cursor = [e.name for e in panel.items].index(name)
        return move

    run_app(app, [KeyEvent("l", ctrl=True), Until(lambda a: a.manager.info.facts is not None), to("a.txt"),
                  Until(lambda a: a.manager.info.file_facts is not None),
                  lambda a: seen.update(file=described(a)),
                  to("sub"), Until(lambda a: "Name: ~sub~" in described(a)),
                  lambda a: seen.update(folder=described(a))])
    assert "Name: ~a.txt~" in seen["file"] and "Size: ~100~ bytes" in seen["file"]
    assert any(line.startswith("Links: ~1~, inode ~") for line in seen["file"])
    assert "Type: ~Directory~" in seen["folder"]


def test_information_panel_setup_saves_its_boxes(place):
    from navigator.widgets.shell.commands import DriveInfoSetup

    app = navigator(place)
    seen = {}

    def untick(a):
        seen["title"] = a.modal.title
        seen["shown"] = a.modal.drive_info.visible
        a.modal.drive_info.options.value &= ~1  # Directory Title

    run_app(app, [lambda a: a.spawn(a.run_command(DriveInfoSetup)), lambda a: None, untick,
                  KeyEvent("enter"), lambda a: None])
    assert seen["title"] == "Settings" and seen["shown"]
    assert SETTINGS.drive_info.directory_title is False and SETTINGS.drive_info.totals is True
    assert "directory_title = no" in SETTINGS.path.read_text()


def test_a_media_file_is_described_a_moment_later_unless_switched_off(place):
    import struct

    png = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 2, 3)
    (place / "b.png").write_bytes(png)
    seen = {}

    def to_png(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index("b.png")

    app = navigator(place)
    run_app(app, [KeyEvent("l", ctrl=True), Until(lambda a: a.manager.info.facts is not None), to_png,
                  Until(lambda a: "Dimensions: ~2 × 3~" in described(a))])
    SETTINGS.drive_info.media_info = False
    app = navigator(place)
    run_app(app, [KeyEvent("l", ctrl=True), Until(lambda a: a.manager.info.facts is not None), to_png,
                  Until(lambda a: a.manager.info.file_facts is not None), lambda a: None,
                  lambda a: seen.update(off=described(a))])
    assert "Name: ~b.png~" in seen["off"] and not any(line.startswith("Dimensions") for line in seen["off"])


def test_a_program_is_described_a_moment_later(place):
    from test_programinfo import elf

    (place / "prog").write_bytes(elf(type_=2, needed=("libnowhere-at-all.so.9",)))
    (place / "prog").chmod(0o755)

    def to_prog(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index("prog")

    app = navigator(place)
    run_app(app, [KeyEvent("l", ctrl=True), Until(lambda a: a.manager.info.facts is not None), to_prog,
                  Until(lambda a: "Libraries: ~libnowhere-at-all.so.9~ (not found)" in described(a))])
    assert "Type: ~Executable file, application/x-executable~" in described(app)


def test_the_information_scrolls_when_it_overflows(place):
    from navkit.events import MouseClickEvent

    (place / "DirInfo").write_text("\n".join(f"line {n}" for n in range(60)))
    seen = {}

    def first(a):
        return a.manager.info.shown()[0][0].strip()

    def look(name):
        return lambda a: seen.update({name: (first(a), a.manager.info.shown()[-1][0].strip(),
                                             a.manager.info.bar.visible)})

    app = navigator(place)
    info = lambda a: a.manager.info  # noqa: E731
    run_app(app, [KeyEvent("l", ctrl=True), Until(lambda a: "line 0" in described(a)), look("start"),
                  KeyEvent("tab"), lambda a: seen.update(focused=info(a).focused),
                  KeyEvent("end"), look("end"), KeyEvent("down"), look("past"),
                  KeyEvent("home"), KeyEvent("down"), KeyEvent("down"), look("two"),
                  KeyEvent("pagedown"), lambda a: seen.update(page=info(a).top),
                  lambda a: a.spawn(info(a).on_mouse_click(MouseClickEvent(1, 1, "wheel_up"))),
                  lambda a: seen.update(wheel=info(a).top),
                  lambda a: a.spawn(info(a).bar.scroll_to(5)), lambda a: seen.update(bar=info(a).top),
                  lambda a: seen.update(last=info(a).last_top(), rows=info(a).rows)])
    assert seen["focused"] and seen["start"][2] is True and seen["start"][1] != "line 59"
    assert seen["end"][1:] == ("line 59", True) and seen["past"] == seen["end"]
    assert seen["two"][0] == app.manager.info.lines()[2][0].strip()
    assert seen["page"] == 2 + seen["rows"] - 1 and seen["wheel"] == seen["page"] - 3 and seen["bar"] == 5
    assert seen["last"] > 0
    assert app.manager.info.top == 5 and len(app.manager.info.shown()) == seen["rows"]


def test_short_information_has_no_scroll_bar(place):
    app = navigator(place)
    run_app(app, [KeyEvent("l", ctrl=True), Until(lambda a: a.manager.info.facts is not None)])
    info = app.manager.info
    assert info.last_top() == 0 and not info.bar.visible


def test_ctrl_l_counts_a_directory_once_not_every_frame(place, monkeypatch):
    from navkit.screen import ScreenBuffer

    from navigator.lib.system import diskinfo

    app = navigator(place)
    counted = []
    real = diskinfo.totals

    def counting(entries):
        counted.append(1)
        return real(entries)

    monkeypatch.setattr(diskinfo, "totals", counting)
    seen = {}

    def frames(a):
        info = a.manager.info
        counted.clear()
        buffer = ScreenBuffer(info.width, info.height)
        for _ in range(10):
            info.render(buffer)  # ten frames, and a scroll's questions besides
            info.last_top()
        seen["counted"] = len(counted)

    run_app(app, [KeyEvent("l", ctrl=True), Until(lambda a: a.manager.info.facts is not None), frames])
    assert seen["counted"] == 0  # counted when the directory was shown, not since
