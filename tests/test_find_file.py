"""Alt+F7: ``FindFile``, and the *Find:* listing it fills (``TFindDrive``)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import IDLE, FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.filefind import (
    Advanced, FindJob, FindRequest, holds, mount_point, parse_size, parse_time, roots, search,
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


def test_a_match_spanning_two_chunks_is_found(tmp_path, monkeypatch):
    import navigator.filefind as filefind

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
    assert roots(tree, "drives", [Path("/mnt/usb")]) == [Path("/"), Path("/mnt/usb")]


def test_a_stopped_search_ends(tree):
    job = FindJob()
    job.stop()
    assert search(FindRequest(), tree, lambda d, i, s: make_entry(i, d), job) == []


# -- in the file manager ---------------------------------------------------------------


@pytest.fixture
def place(tree, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
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
    return app.manager.left.found is not None and not app.manager.left.found.live


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

    run_app(app, [KeyEvent("f7", alt=True), lambda a: None, look, ask("README"), KeyEvent("enter"),
                  Until(finding), lambda a: None,
                  lambda a: seen.update(items=keys(a.manager.left), title_text=a.manager.left.title_text(),
                                        right=a.manager.right.found)])
    assert seen["title"] == "Find File" and seen["options"] == 4 and seen["scope"] == 1
    assert seen["items"] == ["..", str(place / "a" / "README"), str(place / "b" / "README")]
    assert seen["title_text"] == " Find: README " and seen["right"] is None


def test_enter_goes_to_the_file_and_up_comes_back(place):
    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("f7", alt=True), lambda a: None, ask("note.txt"), KeyEvent("enter"),
                  Until(finding), lambda a: None,
                  lambda a: seen.update(footer=a.manager.left.footer_text()) if a.manager.left.cursor == 0 else None,
                  to(str(place / "a" / "deep" / "note.txt")),
                  lambda a: seen.update(footer=a.manager.left.footer_text()),
                  KeyEvent("enter"), lambda a: None, lambda a: None,
                  lambda a: seen.update(path=a.manager.left.path, at=a.manager.left.selected.name,
                                        found=a.manager.left.found)])
    assert seen["footer"].endswith("/a/deep/note.txt ")
    assert seen["path"] == place / "a" / "deep" and seen["at"] == "note.txt" and seen["found"] is None


def test_dot_dot_leads_back_where_the_panel_was(place):
    app = navigator(place)
    seen = {}

    def start(a):
        a.manager.left.cursor = keys(a.manager.left).index("top.txt")

    run_app(app, [start, KeyEvent("f7", alt=True), lambda a: None, ask("README"), KeyEvent("enter"),
                  Until(finding), lambda a: None, to(".."), KeyEvent("enter"), lambda a: None, lambda a: None,
                  lambda a: seen.update(path=a.manager.left.path, found=a.manager.left.found,
                                        at=a.manager.left.selected.name)])
    assert seen == {"path": place, "found": None, "at": "top.txt"}


def test_shift_enter_sends_the_other_panel_to_the_file(place):
    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("f7", alt=True), lambda a: None, ask("big.bin"), KeyEvent("enter"),
                  Until(finding), lambda a: None, to(str(place / "b" / "big.bin")),
                  KeyEvent("enter", shift=True), lambda a: None, lambda a: None,
                  lambda a: seen.update(path=a.manager.right.path, at=a.manager.right.selected.name,
                                        left=a.manager.left.found is not None)])
    assert seen == {"path": place / "b", "at": "big.bin", "left": True}


def test_tags_tell_two_files_of_one_name_apart_and_an_erase_takes_the_right_one(place):
    app = navigator(place)
    seen = {}
    b_readme = str(place / "b" / "README")
    run_app(app, [KeyEvent("f7", alt=True), lambda a: None, ask("README"), KeyEvent("enter"),
                  Until(finding), lambda a: None, to(b_readme), KeyEvent("insert"),
                  lambda a: seen.update(marked=set(a.manager.left.marked)),
                  KeyEvent("f8"), Until(lambda a: a.modal is not None), KeyEvent("enter"),
                  Until(lambda a: not (place / "b" / "README").exists()), IDLE, lambda a: None,
                  lambda a: seen.update(items=keys(a.manager.left))])
    assert seen["marked"] == {b_readme}
    assert (place / "a" / "README").exists()
    assert seen["items"] == ["..", str(place / "a" / "README")]


def test_nothing_found_leaves_the_panel_and_says_so(place):
    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("f7", alt=True), lambda a: None, ask("*.nothing"), KeyEvent("enter"),
                  Until(lambda a: a.modal is not None and a.modal.title == "Error"),
                  lambda a: seen.update(prompt=a.modal.prompt, found=a.manager.left.found),
                  KeyEvent("enter")])
    assert seen == {"prompt": "No files found", "found": None}


def test_f7_and_compare_are_off_in_a_find_listing(place):
    from navigator.widgets.manager.commands import CompareDir, MakeDirectory

    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("f7", alt=True), lambda a: None, ask("README"), KeyEvent("enter"),
                  Until(finding), lambda a: seen.update(mkdir=a.command_enabled(MakeDirectory()),
                                                        compare=a.command_enabled(CompareDir()))])
    assert seen == {"mkdir": False, "compare": False}


def test_alt_f6_renames_a_found_file_in_its_own_directory(place):
    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("f7", alt=True), lambda a: None, ask("note.txt"), KeyEvent("enter"),
                  Until(finding), lambda a: None, to(str(place / "a" / "deep" / "note.txt")),
                  KeyEvent("f6", alt=True), Until(lambda a: a.modal is not None),
                  *[KeyEvent(c, c) for c in "memo.txt"], KeyEvent("enter"),
                  Until(lambda a: (place / "a" / "deep" / "memo.txt").exists()), lambda a: None, lambda a: None,
                  lambda a: seen.update(items=keys(a.manager.left), at=a.manager.left.selected.key)])
    memo = str(place / "a" / "deep" / "memo.txt")
    assert seen == {"items": ["..", memo], "at": memo}


# -- Alt+V: Read file list ---------------------------------------------------------------


def test_read_list_takes_names_paths_and_masks_once_each(place):
    from navigator.filefind import read_list
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
                  lambda a: None,
                  lambda a: seen.update(items=keys(a.manager.left), title=a.manager.left.found.title),
                  to(".."), KeyEvent("enter"), lambda a: None, lambda a: None,
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
    run_app(app, [lambda a: a.spawn(a.run_command(DirBranch)), Until(finding), lambda a: None,
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
