"""File > Replace in files (a departure, asked for), and Find's *Regular expression*."""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.drives import mount, unmount
from navigator.lib.drives.memory import MemoryDrive
from navigator.lib.file_ops import filereplace
from navigator.lib.file_ops.filecopy import Failure
from navigator.lib.file_ops.filefind import FindJob, FindRequest, search, text_pattern
from navigator.lib.file_ops.filereplace import (
    ALL, SKIP, YES, ReplaceJob, ReplaceQuestion, ReplaceRequest, check, plan, printable, replace,
)
from navigator.widgets.manager.panel.panel import make_entry


@pytest.fixture(autouse=True)
def fresh_dialogs(monkeypatch):
    """Find File's and Replace in files' remembered answers, as at start."""
    import copy

    from navigator.widgets.manager.find_file_dialog import find_file_dialog

    for name in ("_session", "_replace_session"):
        monkeypatch.setattr(find_file_dialog, name, copy.deepcopy(getattr(find_file_dialog, name)))


def make(directory, item, info):
    return make_entry(item, directory)


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.txt").write_bytes(b"foo1 and foo2\nnothing\n")
    (tmp_path / "b.txt").write_bytes(b"no match here\n")
    (tmp_path / "sub" / "c.txt").write_bytes(b"line\r\nfoo3\r\n")
    (tmp_path / "bin.dat").write_bytes(b"\0\1foo4")
    return tmp_path


def names(found, start: Path) -> list[str]:
    return sorted(str(entry.path_in(start).relative_to(start)) for entry in found)


# -- the pattern ------------------------------------------------------------------------------------


def test_a_regular_expression_is_a_pattern_and_the_plain_text_is_itself():
    plain = text_pattern("a.c", case=True, words=False)
    assert plain.search(b"a.c") and not plain.search(b"abc")
    pattern = text_pattern("a.c", case=True, words=False, regex=True)
    assert pattern.search(b"abc")
    # ``^`` is each line's, and whole words wrap an alternation as a whole.
    assert text_pattern("^two", case=True, words=False, regex=True).search(b"one\ntwo")
    words = text_pattern("ab|cd", case=True, words=True, regex=True)
    assert words.search(b"x cd y") and not words.search(b"xcd")
    assert text_pattern("ABC", case=False, words=False, regex=True).search(b"abc")
    with pytest.raises(re.error):
        text_pattern("(", case=True, words=False, regex=True)


def test_plain_text_folds_any_alphabet_when_replaced():
    pattern = text_pattern("ä", case=False, words=False)
    assert pattern.sub(b"x", "Ä ä".encode()) == b"x x"


def test_find_with_a_regular_expression_matches_across_lines(tree):
    job = FindJob()
    search(FindRequest(text=r"and foo2\s+nothing", regex=True), tree, make, job)
    assert names(job.found, tree) == ["a.txt"]
    job = FindJob()
    search(FindRequest(text=r"foo\d", regex=True), tree, make, job)
    assert names(job.found, tree) == ["a.txt", "bin.dat", "sub/c.txt"]


def test_check_names_a_bad_pattern_or_template():
    assert check(ReplaceRequest(FindRequest(text="(", regex=True))) is not None
    assert check(ReplaceRequest(FindRequest(text="(a)", regex=True), r"\2")) is not None
    assert check(ReplaceRequest(FindRequest(text="(a)", regex=True), r"\1")) is None
    # Without *Regular expression* neither is anything but text.
    assert check(ReplaceRequest(FindRequest(text="("), r"\2")) is None


# -- the plan ---------------------------------------------------------------------------------------


def test_a_literal_replacement_keeps_its_backslashes():
    pattern = text_pattern("x", case=True, words=False)
    assert plan(b"axb", pattern, rb"\1\n", regex=False).data == rb"a\1\nb"


def test_a_regular_expression_s_groups_and_the_changed_lines():
    pattern = text_pattern(r"foo(\d)", case=True, words=False, regex=True)
    done = plan(b"one foo1\r\ntwo\nfoo2 foo3\n", pattern, rb"bar\1", regex=True)
    assert done.data == b"one bar1\r\ntwo\nbar2 bar3\n" and done.count == 3
    assert [(c.line, c.old, c.new) for c in done.changes] == [
        (1, ("one foo1",), ("one bar1",)), (3, ("foo2 foo3",), ("bar2 bar3",))]


def test_a_match_across_lines_is_one_change():
    pattern = text_pattern(r"two\nthree", case=True, words=False, regex=True)
    done = plan(b"one\ntwo\nthree\nfour\n", pattern, b"2+3", regex=True)
    assert done.data == b"one\n2+3\nfour\n"
    assert [(c.line, c.old, c.new) for c in done.changes] == [(2, ("two", "three"), ("2+3",))]


def test_a_replacement_changing_nothing_lists_nothing_and_many_changes_are_counted(monkeypatch):
    pattern = text_pattern("a", case=True, words=False)
    assert plan(b"a", pattern, b"a", regex=False).changes == ()
    monkeypatch.setattr(filereplace, "SHOWN", 2)
    done = plan(b"a\na\na\na\n", pattern, b"b", regex=False)
    assert len(done.changes) == 2 and done.more == 2 and done.changes[1].line == 2


def test_printable_rows():
    assert printable(b"a\tb\x01\r") == "a    b·"
    assert printable("שלום".encode()) == "שלום"


# -- replacing --------------------------------------------------------------------------------------


def run(tree, text, replacement, answers, **find):
    asked: list[object] = []

    def asker(question):
        asked.append(question)
        return answers(question) if callable(answers) else answers.pop(0)

    job = ReplaceJob(asker=asker)
    replace(ReplaceRequest(FindRequest(text=text, **find), replacement), tree, make, job)
    return job, asked


def test_yes_writes_skip_leaves_and_binary_files_are_passed_over(tree):
    job, asked = run(tree, "foo", "bar", [YES, SKIP])
    assert [q.path.name for q in asked] == ["a.txt", "c.txt"]
    assert isinstance(asked[0], ReplaceQuestion) and asked[0].count == 2
    assert (tree / "a.txt").read_bytes() == b"bar1 and bar2\nnothing\n"
    assert (tree / "sub" / "c.txt").read_bytes() == b"line\r\nfoo3\r\n"
    assert (tree / "bin.dat").read_bytes() == b"\0\1foo4"
    assert names(job.found, tree) == ["a.txt"] and job.matched == 2 and job.replacements == 2


def test_all_stops_asking_and_cancel_stops_the_rest(tree):
    job, asked = run(tree, "foo", "bar", [ALL])
    assert len(asked) == 1 and job.replacements == 3
    assert (tree / "sub" / "c.txt").read_bytes() == b"line\r\nbar3\r\n"
    (tree / "a.txt").write_bytes(b"foo")
    (tree / "sub" / "c.txt").write_bytes(b"foo")
    job, asked = run(tree, "foo", "bar", [None])
    assert len(asked) == 1 and job.stopped and job.found == []
    assert (tree / "a.txt").read_bytes() == b"foo" and (tree / "sub" / "c.txt").read_bytes() == b"foo"


def test_the_mode_is_kept_and_a_too_large_file_is_passed_over(tree, monkeypatch):
    (tree / "a.txt").chmod(0o640)
    run(tree, "foo1", "x", [YES], recursive=False)
    assert (tree / "a.txt").stat().st_mode & 0o777 == 0o640
    monkeypatch.setattr(filereplace, "LARGEST", 4)
    job, asked = run(tree, "foo2", "x", [YES], recursive=False)
    assert asked == [] and job.matched == 0


def test_a_file_changed_while_asked_about_is_left_as_it_is(tree):
    def answers(question):
        if isinstance(question, ReplaceQuestion):
            (tree / "a.txt").write_bytes(b"foo1 changed meanwhile\n")
            return YES
        assert isinstance(question, Failure) and "changed" in question.message
        return True  # Skip

    job, asked = run(tree, "foo1", "x", answers, recursive=False)
    assert (tree / "a.txt").read_bytes() == b"foo1 changed meanwhile\n" and job.found == []


def test_a_file_that_cannot_be_written_asks_and_cancel_stops(tree, monkeypatch):
    def refuse(*args, **kwargs):
        raise PermissionError(13, "Permission denied", str(tree / "a.txt"))

    monkeypatch.setattr("navigator.lib.editor.save.write_file", refuse)
    job, asked = run(tree, "foo", "x", lambda q: YES if isinstance(q, ReplaceQuestion) else False)
    assert isinstance(asked[1], Failure) and job.stopped and len(asked) == 2


def test_files_on_another_drive_are_read_and_written_through_it():
    drive = mount(MemoryDrive("replace"))
    try:
        drive.make("/files/one.txt", "alpha beta")
        drive.make("/files/two.txt", "gamma")
        start = drive.location("/files")
        job = ReplaceJob(asker=lambda question: YES)
        replace(ReplaceRequest(FindRequest(text=r"b(e)ta", regex=True), r"B\1TA"), start, make, job)
        with drive.open_read(start / "one.txt") as stream:
            assert stream.read() == b"alpha BeTA"
        assert [entry.name for entry in job.found] == ["one.txt"]
    finally:
        unmount(drive.site)


# -- the file manager -------------------------------------------------------------------------------


@pytest.fixture
def place(tree, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    return tree


def is_query(app) -> bool:
    return app.modal is not None and type(app.modal).__name__ == "ReplaceQuery"


def test_alt_shift_f7_asks_file_by_file_and_lists_the_files_changed(place):
    from navigator.widgets.file_ops.replace_query.change_list import rows_of

    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    seen: dict[str, object] = {}

    def fill(a):
        d = a.modal
        seen.update(title=d.title, shown=d.replacement.visible)
        d.mask.value = "*.txt"
        d.text.value = r"foo(\d)"
        d.replacement.value = r"<\1>"
        d.options.value = 4 | 16  # recursive, regular expression

    def first(a):
        seen.update(details=a.modal.details.text, rows=list(a.modal.changes.items))
        seen["query"] = a.modal

    def done(a) -> bool:
        # The listing's rows are read again once the search ends: waited for, not stepped to.
        panel = a.manager.left
        return (panel.found is not None and not panel.found.live and a.modal is None
                and [e.key for e in panel.items] == ["..", str(place / "a.txt")])

    run_app(app, [KeyEvent("f7", alt=True, shift=True), lambda a: None, fill, KeyEvent("enter"),
                  Until(is_query), first, KeyEvent("enter"),
                  Until(lambda a: is_query(a) and a.modal is not seen["query"]),
                  lambda a: a.modal.close(SKIP),
                  Until(done), lambda a: seen.update(items=[e.key for e in a.manager.left.items],
                                                     title_text=a.manager.left.title_text())])
    assert seen["title"] == "Replace in Files" and seen["shown"] is True
    assert "a.txt" in seen["details"] and "2 replacements" in seen["details"]
    assert seen["rows"] == rows_of(((filereplace.Change(1, ("foo1 and foo2",), ("<1> and <2>",))),))
    assert (place / "a.txt").read_bytes() == b"<1> and <2>\nnothing\n"
    assert (place / "sub" / "c.txt").read_bytes() == b"line\r\nfoo3\r\n"
    assert seen["items"] == ["..", str(place / "a.txt")]
    assert seen["title_text"].strip().startswith("Replaced:")


def test_find_file_keeps_its_own_rows_and_a_bad_pattern_is_refused(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    seen: dict[str, object] = {}

    def fill(a):
        seen.update(title=a.modal.title, shown=a.modal.replacement.visible)
        a.modal.text.value = "("
        a.modal.options.value = 4 | 16

    run_app(app, [KeyEvent("f7", alt=True), lambda a: None, fill, KeyEvent("enter"),
                  Until(lambda a: a.modal is not None and a.modal.title == "Error"),
                  lambda a: seen.update(prompt=a.modal.prompt)])
    assert seen["title"] == "Find File" and seen["shown"] is False
    assert "regular expression" in seen["prompt"]


def test_nothing_to_change_says_so(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    seen: dict[str, object] = {}

    def fill(a):
        a.modal.text.value = "no match"
        a.modal.replacement.value = "no match"

    run_app(app, [KeyEvent("f7", alt=True, shift=True), lambda a: None, fill, KeyEvent("enter"),
                  Until(lambda a: a.modal is not None and a.modal.title == "Error"),
                  lambda a: seen.update(prompt=a.modal.prompt)])
    assert seen["prompt"] == "No files changed"
    assert os.path.exists(place / "b.txt")


def test_a_replace_inside_an_archive_is_packed_into_it(tmp_path):
    import zipfile

    from navigator.lib.drives import Location, unmount
    from navigator.lib.drives import archive

    with zipfile.ZipFile(tmp_path / "a.zip", "w") as zipped:
        zipped.writestr("dir/one.txt", "alpha beta\n")
        zipped.writestr("two.txt", "gamma\n")
    drive = archive.open_archive(Location.of(tmp_path / "a.zip"))
    try:
        job = ReplaceJob(asker=lambda question: YES)
        replace(ReplaceRequest(FindRequest(text="beta"), "BETA"), drive.at("/"), make, job)
        assert [entry.name for entry in job.found] == ["one.txt"]
        with zipfile.ZipFile(tmp_path / "a.zip") as zipped:
            assert zipped.read("dir/one.txt") == b"alpha BETA\n" and zipped.read("two.txt") == b"gamma\n"
    finally:
        unmount(drive.site)


def test_replace_with_is_kept_and_find_s_lines_are_not_replace_s():
    from navigator.widgets.manager.find_file_dialog import FindFileDialog, find_file_dialog

    dialog = FindFileDialog(replacing=True)
    dialog.mask.value, dialog.text.value, dialog.replacement.value = "*.py", "old", "new"
    dialog.accept()
    again = FindFileDialog(replacing=True)
    assert (again.mask.value, again.text.value, again.replacement.value) == ("*.py", "old", "new")
    find = FindFileDialog()
    assert (find.mask.value, find.text.value) == ("*", "")
    assert "replacement" not in find_file_dialog._session


def test_advanced_ok_in_replace_keeps_its_own(monkeypatch):
    import asyncio

    from navigator.widgets.manager.advanced_search_dialog import AdvancedSearchDialog
    from navigator.widgets.manager.find_file_dialog import FindFileDialog, find_file_dialog

    async def answered(self, application):
        return {"after": "", "before": "", "greater": "10", "less": "", "kinds": 0}

    monkeypatch.setattr(AdvancedSearchDialog, "execute", answered)
    dialog = FindFileDialog(replacing=True)
    dialog.mask.value = "*.py"
    asyncio.run(dialog.ask_advanced())
    assert find_file_dialog._replace_session["advanced"]["greater"] == "10"
    assert find_file_dialog._replace_session["mask"] == "*.py"
    assert find_file_dialog._session["advanced"]["greater"] == "" and find_file_dialog._session["mask"] == "*"
