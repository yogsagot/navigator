"""Alt+F7: ``FindFile``, and the *Find:* listing it fills (``TFindDrive``)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import LISTED, IDLE, FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.file_ops.filefind import (
    Advanced, FindJob, FindRequest, disk_mounts, holds, mount_point, searchable_mounts, virtual_points, parse_size, parse_time, roots, search,
    text_pattern,
)
from navigator.widgets.manager.panel.panel import make_entry


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "a" / "deep").mkdir(parents=True)
    (tmp_path / "b").mkdir()
    (tmp_path / "top.txt").write_text("hello world")
    (tmp_path / "a" / "README").write_text("Hello there")
    (tmp_path / "a" / "deep" / "note.txt").write_text("helloworld")
    (tmp_path / "b" / "README").write_text("nothing")
    (tmp_path / "b" / "big.bin").write_bytes(b"x" * 5000)
    (tmp_path / ".hidden.txt").write_text("hello")
    os.symlink(tmp_path, tmp_path / "b" / "loop")
    return tmp_path


def found(request: FindRequest, start: Path, **kwargs) -> list[str]:
    job = FindJob()
    search(request, start, lambda d, item, info: make_entry(item, d), job, **kwargs)
    return sorted(str(e.path_in(start).relative_to(start)) for e in job.found)


def test_the_mask_and_recursion_and_never_through_a_link(tree):
    assert found(FindRequest(mask="*.txt"), tree) == [".hidden.txt", "a/deep/note.txt", "top.txt"]
    assert found(FindRequest(mask="*.txt", recursive=False), tree) == [".hidden.txt", "top.txt"]
    assert found(FindRequest(mask="README;*.bin"), tree) == ["a/README", "b/README", "b/big.bin"]
    assert found(FindRequest(mask="*.txt"), tree, show_hidden=False) == ["a/deep/note.txt", "top.txt"]
    # A directory matching the mask is found too, while no text is asked for.
    assert "a/deep" in found(FindRequest(mask="deep"), tree)


def test_text_is_looked_for_in_files_only_with_case_and_whole_words(tree):
    assert found(FindRequest(text="hello"), tree, show_hidden=False) == \
        ["a/README", "a/deep/note.txt", "top.txt"]
    assert found(FindRequest(text="Hello", case=True), tree) == ["a/README"]
    assert found(FindRequest(text="hello", words=True), tree, show_hidden=False) == ["a/README", "top.txt"]


def _finishes(work, timeout=5.0):
    """Run *work* on a thread: what it answered, or a failure if it hangs."""
    import threading

    result = []
    worker = threading.Thread(target=lambda: result.append(work()), daemon=True)
    worker.start()
    worker.join(timeout)
    assert not worker.is_alive(), "the search hung"
    return result[0]


def test_a_text_search_never_opens_a_fifo_and_ends(tree):
    # A FIFO with no writer blocked ``open()`` for good, past Stop.
    os.mkfifo(tree / "pipe.txt")
    os.symlink(tree / "pipe.txt", tree / "link.txt")
    names = _finishes(lambda: found(FindRequest(mask="*.txt", text="hello", recursive=True), tree,
                                    show_hidden=True))
    assert "pipe.txt" not in names and "link.txt" not in names and "top.txt" in names


def test_a_fifo_is_still_found_by_its_name(tree):
    os.mkfifo(tree / "pipe.txt")
    names = _finishes(lambda: found(FindRequest(mask="pipe.txt"), tree))
    assert names == ["pipe.txt"]


def test_holds_passes_a_fifo_over_at_once(tree):
    # The walk saw a file; it is a FIFO by the time it is opened.
    os.mkfifo(tree / "swapped")
    pattern = text_pattern("x", case=True, words=False)
    assert _finishes(lambda: holds(str(tree / "swapped"), pattern)) is False


def test_a_match_spanning_two_chunks_is_found(tmp_path, monkeypatch):
    import navigator.lib.file_ops.filefind as filefind

    monkeypatch.setattr(filefind, "CHUNK", 8)
    path = tmp_path / "f"
    path.write_bytes(b"0123456needle89")
    assert holds(str(path), text_pattern("needle", case=True, words=False))


def test_advanced_limits_dates_sizes_and_kinds(tree):
    os.utime(tree / "top.txt", (1_000_000, 1_000_000))
    after = parse_time("2000-01-01")
    assert found(FindRequest(mask="*.txt", advanced=True, limits=Advanced(after=after)), tree,
                 show_hidden=False) == ["a/deep/note.txt"]
    assert found(FindRequest(mask="*", advanced=True, limits=Advanced(greater=4000)), tree) == ["b/big.bin"]
    (tree / "a" / "README").chmod(0o444)
    assert found(FindRequest(mask="*", advanced=True, limits=Advanced(kinds=frozenset({"read_only"}))),
                 tree) == ["a/README"]
    # Without *Advanced search* ticked the limits do not count.
    assert len(found(FindRequest(mask="*", limits=Advanced(greater=4000)), tree)) > 1


def test_the_parsers_and_the_scopes(tree):
    assert parse_time("2026-01-02 03:04") is not None and parse_time("02.01.2026") is None
    assert parse_size("12") == 12 and parse_size("") is None and parse_size("x") is None
    assert roots(tree, "directory") == [tree]
    assert roots(tree, "disk") == [mount_point(tree)]
    own = mount_point(tree)
    expected = [own] + ([Path("/")] if own != Path("/") else []) + [Path("/mnt/usb")]
    # DN's ``C = FN[1]``: the panel's own file system first, then ``/``, each once.
    assert roots(tree, "drives", [Path("/mnt/usb"), Path("/")]) == expected


MOUNTS = """\
/dev/sda2 / ext4 rw,relatime 0 0
proc /proc proc rw 0 0
sysfs /sys sysfs rw 0 0
tmpfs /run tmpfs rw 0 0
/dev/sda3 /home ext4 rw 0 0
/dev/sda1 /boot/efi vfat rw 0 0
/dev/loop1 /snap/core/1 squashfs ro 0 0
me@host:/ /mnt/net fuse.sshfs rw 0 0
/dev/sdb1 /media/me/My\\040Disk exfat rw 0 0
/dev/sda3 /home ext4 rw 0 0
"""


def test_all_drives_keeps_the_disk_file_systems_only():
    assert disk_mounts(MOUNTS) == [Path("/"), Path("/home"), Path("/boot/efi"), Path("/media/me/My Disk")]


def test_searchable_mounts_drops_what_cannot_be_entered_and_a_second_mount(tmp_path):
    good, shut = tmp_path / "good", tmp_path / "shut"
    good.mkdir(), shut.mkdir()
    table = tmp_path / "mounts"
    table.write_text(f"/dev/a {good} ext4 rw 0 0\n/dev/a {tmp_path} ext4 rw 0 0\n/dev/b {shut} xfs rw 0 0\n"
                     f"/dev/c {tmp_path / 'gone'} ext4 rw 0 0\n")
    shut.chmod(0)
    try:
        expected = [good] if os.geteuid() != 0 else [good, shut]
        # *tmp_path* is *good*'s file system again: a bind mount, kept once.
        assert searchable_mounts(table) == expected
    finally:
        shut.chmod(0o755)
    assert searchable_mounts(tmp_path / "no-such") == []


def test_a_stopped_search_ends(tree):
    job = FindJob()
    job.stop()
    assert search(FindRequest(), tree, lambda d, i, s: make_entry(i, d), job) == []


# -- in the file manager ---------------------------------------------------------------


@pytest.fixture
def place(tree, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tree / "b" / "loop").unlink()
    return tree


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def ask(mask: str, text: str = ""):
    def action(app):
        app.modal.mask.value = mask
        app.modal.text.value = text
    return action


def finding(app) -> bool:
    """The search is over and the panel shows what it found: the result is
    listed by a read of its own, after the search ends."""
    from conftest import _listed

    return app.manager.left.found is not None and not app.manager.left.found.live and _listed(app)


def keys(panel) -> list[str]:
    return [e.key for e in panel.items]


def to(key: str):
    def action(app):
        panel = app.manager.left
        panel.cursor = keys(panel).index(key)
    return action


def test_alt_f7_fills_the_panel_with_a_find_listing(place):
    app = navigator(place)
    seen = {}

    def look(a):
        d = a.modal
        seen.update(title=d.title, options=d.options.value, scope=d.scope.value)

    run_app(app, [KeyEvent("f7", alt=True), LISTED, look, ask("README"), KeyEvent("enter"),
                  Until(finding), LISTED,
                  lambda a: seen.update(items=keys(a.manager.left), title_text=a.manager.left.title_text(),
                                        right=a.manager.right.found)])
    assert seen["title"] == "Find File" and seen["options"] == 4 and seen["scope"] == 1
    assert seen["items"] == ["..", str(place / "a" / "README"), str(place / "b" / "README")]
    assert seen["title_text"] == " Find: README " and seen["right"] is None



def test_the_dialog_s_own_keys_reach_their_commands(place):
    """Tab and Shift+Tab are the dialog table's ``SelectNext``/``SelectPrevious``,
    asked through ``enables()`` -- which the dialog's reason for refusing OK,
    once also called ``refusal``, used to shadow and crash."""
    app = navigator(place)
    seen = []
    run_app(app, [KeyEvent("f7", alt=True), Until(lambda a: a.modal is not None),
                  lambda a: seen.append(a.focused is a.modal.mask.entry),
                  KeyEvent("tab"), lambda a: seen.append(a.focused is a.modal.mask.entry),
                  KeyEvent("tab", shift=True), lambda a: seen.append(a.focused is a.modal.mask.entry),
                  KeyEvent("escape"), IDLE])
    assert seen == [True, False, True]
    assert app.modal is None

def test_enter_goes_to_the_file_and_up_comes_back(place):
    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("f7", alt=True), LISTED, ask("note.txt"), KeyEvent("enter"),
                  Until(finding), LISTED,
                  lambda a: seen.update(where=a.manager.left.info_lines[1][0]) if a.manager.left.cursor == 0 else None,
                  to(str(place / "a" / "deep" / "note.txt")),
                  lambda a: seen.update(where=a.manager.left.info_lines[1][0]),
                  KeyEvent("enter"), LISTED, LISTED,
                  lambda a: seen.update(path=a.manager.left.path, at=a.manager.left.selected.name,
                                        found=a.manager.left.found)])
    # Too narrow a panel for the path column: the line under *Current file*.
    assert seen["where"].endswith("/a/deep")
    assert seen["path"] == place / "a" / "deep" and seen["at"] == "note.txt" and seen["found"] is None


def test_dot_dot_leads_back_where_the_panel_was(place):
    app = navigator(place)
    seen = {}

    def start(a):
        a.manager.left.cursor = keys(a.manager.left).index("top.txt")

    run_app(app, [start, KeyEvent("f7", alt=True), LISTED, ask("README"), KeyEvent("enter"),
                  Until(finding), LISTED, to(".."), KeyEvent("enter"), LISTED, LISTED,
                  lambda a: seen.update(path=a.manager.left.path, found=a.manager.left.found,
                                        at=a.manager.left.selected.name)])
    assert seen == {"path": place, "found": None, "at": "top.txt"}


def test_shift_enter_sends_the_other_panel_to_the_file(place):
    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("f7", alt=True), LISTED, ask("big.bin"), KeyEvent("enter"),
                  Until(finding), LISTED, to(str(place / "b" / "big.bin")),
                  KeyEvent("enter", shift=True), LISTED, LISTED,
                  lambda a: seen.update(path=a.manager.right.path, at=a.manager.right.selected.name,
                                        left=a.manager.left.found is not None,
                                        keys=a.focused is a.manager.right),
                  KeyEvent("tab"), lambda a: seen.update(back=a.focused is a.manager.left
                                                         and a.manager.left.found is not None)])
    # ``cmFindGotoFile``: the other panel takes the keyboard; Tab goes back to the listing.
    assert seen == {"path": place / "b", "at": "big.bin", "left": True, "keys": True, "back": True}


def test_ctrl_shift_pgdn_sends_the_other_panel_to_the_file_too(place):
    # ``_CtrlPgDn`` with Shift in a listing: ``cmChangeInactive``.
    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("f7", alt=True), LISTED, ask("big.bin"), KeyEvent("enter"),
                  Until(finding), LISTED, to(str(place / "b" / "big.bin")),
                  KeyEvent("pagedown", ctrl=True, shift=True), LISTED, LISTED,
                  lambda a: seen.update(path=a.manager.right.path, at=a.manager.right.selected.name)])
    assert seen == {"path": place / "b", "at": "big.bin"}


def test_shift_enter_puts_the_other_panels_mask_back_to_all_files(place):
    app = navigator(place)
    seen = {}
    run_app(app, [lambda a: a.manager.right.set_file_mask("*.txt"), LISTED,
                  KeyEvent("f7", alt=True), LISTED, ask("big.bin"), KeyEvent("enter"),
                  Until(finding), LISTED, to(str(place / "b" / "big.bin")),
                  KeyEvent("enter", shift=True), LISTED, LISTED,
                  lambda a: seen.update(mask=a.manager.right.file_mask, at=a.manager.right.selected.name)])
    assert seen == {"mask": "*", "at": "big.bin"}


def test_tags_tell_two_files_of_one_name_apart_and_an_erase_takes_the_right_one(place):
    app = navigator(place)
    seen = {}
    b_readme = str(place / "b" / "README")
    run_app(app, [KeyEvent("f7", alt=True), LISTED, ask("README"), KeyEvent("enter"),
                  Until(finding), LISTED, to(b_readme), KeyEvent("insert"),
                  lambda a: seen.update(marked=set(a.manager.left.marked)),
                  KeyEvent("f8"), Until(lambda a: a.modal is not None), KeyEvent("enter"),
                  Until(lambda a: not (place / "b" / "README").exists()), IDLE, LISTED,
                  lambda a: seen.update(items=keys(a.manager.left))])
    assert seen["marked"] == {b_readme}
    assert (place / "a" / "README").exists()
    assert seen["items"] == ["..", str(place / "a" / "README")]


def test_nothing_found_leaves_the_panel_and_says_so(place):
    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("f7", alt=True), LISTED, ask("*.nothing"), KeyEvent("enter"),
                  Until(lambda a: a.modal is not None and a.modal.title == "Error"),
                  lambda a: seen.update(prompt=a.modal.prompt, found=a.manager.left.found),
                  KeyEvent("enter")])
    assert seen == {"prompt": "No files found", "found": None}


def test_f7_and_compare_are_off_in_a_find_listing(place):
    from navigator.widgets.manager.commands import CompareDir, MakeDirectory

    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("f7", alt=True), LISTED, ask("README"), KeyEvent("enter"),
                  Until(finding), lambda a: seen.update(mkdir=a.command_enabled(MakeDirectory()),
                                                        compare=a.command_enabled(CompareDir()))])
    assert seen == {"mkdir": False, "compare": False}


def test_alt_f6_renames_a_found_file_in_its_own_directory(place):
    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("f7", alt=True), LISTED, ask("note.txt"), KeyEvent("enter"),
                  Until(finding), LISTED, to(str(place / "a" / "deep" / "note.txt")),
                  KeyEvent("f6", alt=True), Until(lambda a: a.modal is not None),
                  *[KeyEvent(c, c) for c in "memo.txt"], KeyEvent("enter"),
                  Until(lambda a: (place / "a" / "deep" / "memo.txt").exists()), IDLE, LISTED,
                  lambda a: seen.update(items=keys(a.manager.left), at=a.manager.left.selected.key)])
    memo = str(place / "a" / "deep" / "memo.txt")
    assert seen == {"items": ["..", memo], "at": memo}


# -- Alt+V: Read file list ---------------------------------------------------------------


def test_read_list_takes_names_paths_and_masks_once_each(place):
    from navigator.lib.file_ops.filefind import read_list
    from navigator.widgets.manager.panel.panel import entry_at

    (place / "my list.lst").write_text(
        "top.txt\n  a/README  \n" + str(place / "b" / "big.bin") + "\n*.txt\nmissing\n\ntop.txt\n..\n")
    entries = read_list(place / "my list.lst", place, lambda p: entry_at(p, p.parent))
    # ``*.txt`` matches as a shell's would: not the dot-file, and top.txt is in already.
    assert [str(e.path_in(place).relative_to(place)) for e in entries] == \
        ["top.txt", "a/README", "b/big.bin"]


def test_alt_v_opens_the_list_at_the_cursor_as_a_listing(place):
    (place / "files.lst").write_text("a/README\nb/README\n")
    app = navigator(place)
    seen = {}

    def on_list(a):
        a.manager.left.cursor = keys(a.manager.left).index("files.lst")

    run_app(app, [on_list, KeyEvent("v", alt=True), Until(lambda a: a.manager.left.found is not None),
                  LISTED,
                  lambda a: seen.update(items=keys(a.manager.left), title=a.manager.left.found.title),
                  to(".."), KeyEvent("enter"), LISTED, LISTED,
                  lambda a: seen.update(back=a.manager.left.selected.name)])
    assert seen["items"] == ["..", str(place / "a" / "README"), str(place / "b" / "README")]
    assert seen["title"] == str(place / "files.lst") and seen["back"] == "files.lst"


def test_a_list_naming_nothing_there_says_so(place):
    (place / "empty.lst").write_text("nothing\n")
    app = navigator(place)
    seen = {}

    def on_list(a):
        a.manager.left.cursor = keys(a.manager.left).index("empty.lst")

    run_app(app, [on_list, KeyEvent("v", alt=True), Until(lambda a: a.modal is not None),
                  lambda a: seen.update(prompt=a.modal.prompt, found=a.manager.left.found), KeyEvent("enter")])
    assert seen == {"prompt": "No files found", "found": None}


# -- Panel > Directory Branch -------------------------------------------------------------


def test_directory_branch_lists_every_file_below_and_no_directory(place):
    from navigator.widgets.manager.commands import DirBranch

    app = navigator(place)
    seen = {}
    run_app(app, [lambda a: a.spawn(a.run_command(DirBranch)), Until(finding), LISTED,
                  lambda a: seen.update(items=keys(a.manager.left), title=a.manager.left.found.title,
                                        again=a.command_enabled(DirBranch()))])
    assert seen["title"] == f"Branch: {place}"
    assert seen["items"][0] == ".."
    assert sorted(seen["items"][1:]) == sorted(str(place / p) for p in (
        ".hidden.txt", "a/README", "b/README", "b/big.bin", "a/deep/note.txt", "top.txt"))
    assert seen["again"] is False


def test_the_progress_line_cuts_a_long_directory_from_its_start():
    from types import SimpleNamespace

    from navkit.glyphs import GLYPHS_ASCII, GLYPHS_UNICODE
    from navigator.widgets.manager.find_progress import FindProgress

    path = "/" + "d" * 100 + "/end"
    box = SimpleNamespace(modal_width=56, glyphs=GLYPHS_UNICODE)
    assert FindProgress.fit(box, "/short") == "/short"
    assert FindProgress.fit(box, path) == "…" + path[-51:]
    box.glyphs = GLYPHS_ASCII
    assert FindProgress.fit(box, path) == "..." + path[-49:]


def test_the_directory_s_line_stays_however_wide_the_panel(place):
    app = navigator(place)
    seen = {}

    def look(key):
        def take(a):
            panel = a.manager.left
            seen[key] = ([k for k, _, _ in panel.detail_columns], [text for text, _ in panel.info_lines])
        return take

    run_app(app, [KeyEvent("f7", alt=True), LISTED, ask("note.txt"), KeyEvent("enter"),
                  Until(finding), LISTED, to(str(place / "a" / "deep" / "note.txt")), look("narrow"),
                  lambda a: setattr(a.manager.left, "width", 150), LISTED, look("wide")])
    for key in ("narrow", "wide"):
        columns, lines = seen[key]
        assert "path" not in columns and lines[1].endswith("/a/deep")


def test_a_listing_offers_go_to_file_and_show_in_other_panel_on_its_menus(place):
    from navml.widgets.dialog.control.control import parse_shortcut
    from navml.widgets.menu.commands import ShowContextMenu
    from navml.widgets.menu.menu_box.menu_box import key_caption
    from navml.widgets.menu.popup_menu import PopupMenu
    from navigator.widgets.manager.commands import ChangeInactive

    app = navigator(place)
    seen = {}

    def popup(a):
        return next((c for c in a.root.children if isinstance(c, PopupMenu)), None)

    def panel_menu(name):
        def action(a):
            item = a.manager.panel_menu.item_for(ChangeInactive)
            seen[name] = (key_caption(item, a, a.manager.left), a.command_enabled(ChangeInactive, a.manager.left))
        return action

    run_app(app, [panel_menu("plain"),
                  KeyEvent("f7", alt=True), LISTED, ask("big.bin"), KeyEvent("enter"),
                  Until(finding), LISTED, to(str(place / "b" / "big.bin")), panel_menu("listing"),
                  lambda a: a.spawn(a.manager.left.emit(ShowContextMenu())), Until(lambda a: popup(a) is not None),
                  lambda a: seen.update(items=[parse_shortcut(e.text)[0] for e in popup(a).box.entries()
                                               if hasattr(e, "command")][:2]),
                  KeyEvent("o", "o"), Until(lambda a: popup(a) is None), LISTED,
                  lambda a: seen.update(right=a.manager.right.path),
                  lambda a: a.spawn(a.manager.left.emit(ShowContextMenu())), Until(lambda a: popup(a) is not None),
                  KeyEvent("f", "f"), Until(lambda a: popup(a) is None), LISTED, LISTED,
                  lambda a: seen.update(left=a.manager.left.path, found=a.manager.left.found)])
    assert seen["plain"] == ("Ctrl-Shift-PgDn", False)
    assert seen["listing"] == ("Ctrl-Shift-PgDn", True)
    assert seen["items"] == ["Go to file", "Show in other panel"]
    assert seen["right"] == place / "b"
    assert seen["left"] == place / "b" and seen["found"] is None


def test_virtual_points_are_the_kernel_file_systems():
    table = ("proc /proc proc rw 0 0\nsysfs /sys sysfs rw 0 0\nudev /dev devtmpfs rw 0 0\n"
             "devpts /dev/pts devpts rw 0 0\ncgroup2 /sys/fs/cgroup cgroup2 rw 0 0\n/dev/sda2 / ext4 rw 0 0\n"
             "tmpfs /tmp tmpfs rw 0 0\n/dev/sda3 /home ext4 rw 0 0\n")
    assert virtual_points(table) == {Path(p) for p in ("/proc", "/sys", "/dev", "/dev/pts", "/sys/fs/cgroup")}


def _devpts_mounted() -> bool:
    try:
        return Path("/dev/pts") in virtual_points(Path("/proc/self/mounts").read_text())
    except OSError:
        return False


def _under_pts(names):
    return [name for name in names if name.startswith("pts/")]


@pytest.mark.skipif(not _devpts_mounted(), reason="/dev/pts is not a devpts mount here")
def test_current_directory_never_crosses_into_a_kernel_file_system():
    names = _finishes(lambda: found(FindRequest(mask="*", recursive=True, directories=True), Path("/dev")))
    assert names and _under_pts(names) == []


@pytest.mark.skipif(not _devpts_mounted(), reason="/dev/pts is not a devpts mount here")
def test_without_a_mount_table_the_walk_crosses_as_before(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.file_ops.filefind.MOUNTS_TABLE", tmp_path / "none")
    names = _finishes(lambda: found(FindRequest(mask="*", recursive=True), Path("/dev")))
    assert "pts/ptmx" in names


def test_only_a_crossing_is_tested_so_a_start_is_walked(tree, monkeypatch):
    table = tree / "mounts"  # not a *.txt, so never found
    table.write_text(f"proc {tree / 'a'} proc rw 0 0\nproc {tree} proc rw 0 0\n")
    monkeypatch.setattr("navigator.lib.file_ops.filefind.MOUNTS_TABLE", table)
    assert "a/deep/note.txt" in found(FindRequest(mask="*.txt", recursive=True), tree)


@pytest.fixture
def system():
    """A drive whose ``/`` is a running system's, as a server's is."""
    from navigator.lib.drives import mount, unmount
    from navigator.lib.drives.memory import MemoryDrive

    drive = MemoryDrive("system")
    drive.system_root = True
    for path in ("/proc/1/status", "/sys/x", "/dev/null", "/run/x", "/home/me/a.txt"):
        drive.make(path, "hello")
    mount(drive)
    yield drive
    unmount(drive.site)


def _remote(request, start):
    job = FindJob()
    search(request, start, None, job)
    return sorted(str(entry.directory / entry.name) for entry in job.found)


def test_a_system_drive_is_searched_without_its_kernel_places(system):
    whole = _remote(FindRequest(mask="*", text="hello", scope="disk"), system.location("/home/me"))
    assert len(whole) == 1 and whole[0].endswith("/home/me/a.txt")
    here = _remote(FindRequest(mask="*", recursive=True), system.location("/"))
    assert not [name for name in here if any(f"/{top}/" in name for top in ("proc", "sys", "dev", "run"))]
    assert any(name.endswith("/home/me/a.txt") for name in here)


def test_a_search_started_in_a_kernel_place_walks_it(system):
    assert any(name.endswith("/proc/1/status")
               for name in _remote(FindRequest(mask="*", recursive=True), system.location("/proc")))


def test_on_a_drive_that_is_no_system_the_names_count_for_nothing(system):
    system.system_root = False
    assert any(name.endswith("/proc/1/status")
               for name in _remote(FindRequest(mask="*", recursive=True), system.location("/")))


def test_which_drives_are_a_systems_root():
    from navigator.lib.drives.archive import ArchiveDrive
    from navigator.lib.drives.execdrive import ExecDrive
    from navigator.lib.drives.ftp import FtpDrive
    from navigator.lib.drives.s3 import S3Drive
    from navigator.lib.drives.sftp import SftpDrive

    assert SftpDrive.system_root and FtpDrive.system_root and ExecDrive.system_root
    assert not ArchiveDrive.system_root and not S3Drive.system_root


def test_a_regular_expression_still_matches_across_chunks(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.file_ops.filefind.CHUNK", 8)
    (tmp_path / "f").write_text("begin" + "." * 30 + "end")
    assert holds(str(tmp_path / "f"), text_pattern(r"begin.*end", case=True, words=False, regex=True), whole=True)


def test_a_regular_expression_passes_over_a_file_past_the_cap(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.file_ops.filefind.WHOLE_LARGEST", 16)
    (tmp_path / "big.txt").write_text("needle" + "." * 26)
    (tmp_path / "small.txt").write_text("needle")
    assert found(FindRequest(mask="*", text="need+le", regex=True), tmp_path) == ["small.txt"]


def test_the_cap_holds_whatever_size_the_file_said(monkeypatch):
    import io

    from navigator.lib.file_ops.filefind import _holds

    monkeypatch.setattr("navigator.lib.file_ops.filefind.WHOLE_LARGEST", 16)
    monkeypatch.setattr("navigator.lib.file_ops.filefind.CHUNK", 8)
    pattern = text_pattern("needle", case=True, words=False, regex=True)
    assert not _holds(io.BytesIO(b"needle" + b"." * 26), pattern, None, True)
    assert _holds(io.BytesIO(b"needle"), pattern, None, True)


def test_stop_ends_a_regular_expression_between_chunks():
    from navigator.lib.file_ops.filefind import _holds

    job = FindJob()
    reads = []

    class Reader:
        def read(self, size):
            reads.append(size)
            job.stop()
            return b"x" * size

    assert not _holds(Reader(), text_pattern("x", case=True, words=False, regex=True), job, True)
    assert len(reads) == 1


def test_a_regular_expression_on_another_drive_keeps_to_the_cap(monkeypatch):
    from navigator.lib.drives import mount, unmount
    from navigator.lib.drives.memory import MemoryDrive

    monkeypatch.setattr("navigator.lib.file_ops.filefind.WHOLE_LARGEST", 16)
    drive = mount(MemoryDrive("capped"))
    try:
        drive.make("/d/big.txt", "needle" + "." * 26)
        drive.make("/d/small.txt", "needle")
        assert [n.rsplit("/", 1)[-1] for n in _remote(FindRequest(mask="*", text="needle", regex=True),
                                                      drive.location("/d"))] == ["small.txt"]
    finally:
        unmount(drive.site)


def test_replace_in_files_keeps_to_the_same_cap():
    from navigator.lib.file_ops import filefind, filereplace

    assert filereplace.LARGEST == filefind.WHOLE_LARGEST == 64 << 20
