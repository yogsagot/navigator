"""Panel > Multi-rename (Alt+A): the rule language, the plan's checks, the
renames on a thread with Undo, and the box driving them."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.drives import Location, drive_of
from navigator.lib.file_ops import multirename
from navigator.lib.file_ops.multirename import Item, Rule, RuleError, new_names, plan, steps
from navigator.widgets.manager.commands import MultiRename, UndoMultiRename
from navigator.widgets.manager.manager.manager import Manager

HERE = Path("/d")


def names(rule: Rule, *files: str, **extra) -> list[str]:
    return new_names(rule, [Item(name, HERE, **extra) for name in files])


# -- the rule ----------------------------------------------------------------------------


def test_masks_take_parts_of_the_stem_the_extension_and_the_directory():
    assert names(Rule(), "Photo One.JPG", ".bashrc", "a.tar.gz") == ["Photo One.JPG", ".bashrc", "a.tar.gz"]
    assert names(Rule(name_mask="[N2-4]", ext_mask=""), "Photo.JPG") == ["hot"]
    assert names(Rule(name_mask="[N-3-]_[N1,2]"), "Photo.JPG") == ["oto_Ph.JPG"]
    assert names(Rule(name_mask="[N3]"), "Photo.JPG") == ["o.JPG"]
    assert names(Rule(name_mask="[P]-[N]", ext_mask="[E2-]"), "x.jpeg", parent_name="trip") == ["trip-x.peg"]
    assert names(Rule(name_mask="[[][N][]]"), "a.txt") == ["[a].txt"]


def test_a_directory_is_all_stem():
    assert new_names(Rule(name_mask="[N]_old", ext_mask="[E]"), [Item("dir.d", HERE, is_dir=True)]) == ["dir.d_old"]


def test_the_counter_counts_in_order_and_a_placeholder_overrides_it():
    rule = Rule(name_mask="img[C]", counter_start=8, counter_step=2, counter_width=2)
    assert names(rule, "a.png", "b.png", "c.png") == ["img08.png", "img10.png", "img12.png"]
    assert names(Rule(name_mask="[C10+5:3]"), "a", "b") == ["010", "015"]


def test_the_date_comes_from_the_modification_time():
    stamp = time.mktime((2024, 3, 9, 7, 5, 0, 0, 0, -1))
    assert names(Rule(name_mask="[Y]-[M]-[D]_[h][m]"), "x.jpg", mtime=stamp) == ["2024-03-09_0705.jpg"]


def test_search_and_replace_plain_and_regular():
    assert names(Rule(search="O", replace="0"), "Photo.JPG") == ["Ph0t0.JPG"]
    assert names(Rule(search="O", replace="0", case_sensitive=True), "Photo.JPG") == ["Photo.JPG"]
    assert names(Rule(search="o", replace="0", first_only=True), "Photo.JPG") == ["Ph0to.JPG"]
    assert names(Rule(search=r"(\w+) (\w+)", replace=r"\2 \1", regex=True), "one two.txt") == ["two one.txt"]
    # Plain text is no pattern, and a backslash in its replacement is itself.
    assert names(Rule(search=".", replace="\\1"), "a.b") == ["a\\1b"]


def test_case():
    assert names(Rule(case="lower"), "Photo One.JPG") == ["photo one.jpg"]
    assert names(Rule(case="upper"), "a.txt") == ["A.TXT"]
    assert names(Rule(case="title"), "my holiday photo.jpg") == ["My Holiday Photo.Jpg"]
    assert names(Rule(case="first"), "MY FILE.TXT") == ["My file.txt"]


@pytest.mark.parametrize("rule", [Rule(name_mask="[Q]"), Rule(name_mask="[N"), Rule(name_mask="[Nx]"),
                                  Rule(name_mask="[C+]"), Rule(search="(", regex=True),
                                  Rule(search="a", replace=r"\9", regex=True)])
def test_a_rule_that_does_not_read_says_so(rule):
    with pytest.raises(RuleError):
        names(rule, "a.txt")


# -- the plan ----------------------------------------------------------------------------


def test_the_plan_finds_what_cannot_be_done():
    items = [Item(name, HERE) for name in ("a.txt", "b.txt", "c.txt", "keep.txt")]
    rows = plan(Rule(name_mask="x"), items[:2], {HERE: {"a.txt", "b.txt"}})
    assert [(row.new, row.problem) for row in rows] == [("x.txt", "twice"), ("x.txt", "twice")]
    rows = plan(Rule(name_mask="keep"), items[:1], {HERE: {"a.txt", "keep.txt"}})
    assert rows[0].problem == "taken"
    assert plan(Rule(name_mask="a/b"), items[:1])[0].problem == "slash"
    assert plan(Rule(name_mask="", ext_mask=""), items[:1])[0].problem == "empty"
    assert plan(Rule(name_mask=".", ext_mask=""), items[:1])[0].problem == "dots"


def test_a_name_being_renamed_away_is_free_and_an_unchanged_one_is_not():
    items = [Item("1.txt", HERE), Item("2.txt", HERE)]
    rows = plan(Rule(name_mask="[C]", counter_start=2, counter_step=-1), items, {HERE: {"1.txt", "2.txt"}})
    assert [(row.new, row.problem) for row in rows] == [("2.txt", None), ("1.txt", None)]
    rows = plan(Rule(name_mask="[C]", counter_start=2), items, {HERE: {"1.txt", "2.txt"}})
    assert [(row.new, row.problem, row.changed) for row in rows] == [("2.txt", None, True), ("3.txt", None, True)]
    rows = plan(Rule(search="1", replace="2"), items, {HERE: {"1.txt", "2.txt"}})
    assert [(row.new, row.problem) for row in rows] == [("2.txt", "taken"), ("2.txt", None)]


def test_a_swap_goes_through_a_temporary_name():
    order = [(step.old, step.new) for step in steps([(HERE, "a", "b"), (HERE, "b", "a"), (HERE, "c", "d")])]
    assert order == [("a", ".navrename-0-a"), ("b", ".navrename-1-b"), ("c", "d"),
                     (".navrename-0-a", "b"), (".navrename-1-b", "a")]


# -- doing it ----------------------------------------------------------------------------


def test_a_batch_renames_a_cycle_whole_and_undo_puts_it_back(tmp_path):
    for name, text in (("a", "A"), ("b", "B"), ("c", "C")):
        (tmp_path / name).write_text(text)
    here = Location.of(tmp_path)
    job = multirename.RenameJob()
    done = multirename.run([(here, "a", "b"), (here, "b", "c"), (here, "c", "a")], job, drive_of)
    assert {name: (tmp_path / name).read_text() for name in "abc"} == {"b": "A", "c": "B", "a": "C"}
    assert sorted(p.name for p in tmp_path.iterdir()) == ["a", "b", "c"]
    assert sorted(done) == sorted([(here, "a", "b"), (here, "b", "c"), (here, "c", "a")])
    multirename.run(multirename.Batch(done).undo_pairs(), multirename.RenameJob(), drive_of)
    assert {name: (tmp_path / name).read_text() for name in "abc"} == {"a": "A", "b": "B", "c": "C"}


def test_a_name_taken_meanwhile_is_asked_about_and_skipped(tmp_path):
    (tmp_path / "a").write_text("A")
    (tmp_path / "b").write_text("B")
    (tmp_path / "x").write_text("X")
    here = Location.of(tmp_path)
    asked = []
    job = multirename.RenameJob(asker=lambda question: asked.append(question.message) or True)
    done = multirename.run([(here, "a", "x"), (here, "b", "y")], job, drive_of)
    assert done == [(here, "b", "y")]
    assert (tmp_path / "a").read_text() == "A" and (tmp_path / "x").read_text() == "X"
    assert asked and asked[0].startswith("Could not rename a\nto x")


def test_a_failed_swap_half_is_put_back_under_its_own_name(tmp_path):
    (tmp_path / "a").write_text("A")
    (tmp_path / "b").write_text("B")
    here = Location.of(tmp_path)
    real = drive_of(here)

    class Refusing:
        def __getattr__(self, name):
            return getattr(real, name)

        def rename(self, source, dest):
            if dest.name == "a":
                raise PermissionError(13, "Permission denied")
            real.rename(source, dest)

    asked = []
    job = multirename.RenameJob(asker=lambda question: asked.append(question.message) or True)
    done = multirename.run([(here, "a", "b"), (here, "b", "a")], job, lambda place: Refusing())
    assert done == [(here, "a", "b")]
    # Its old name is A's now, so B stays under its temporary name, said so: nothing is lost.
    assert sorted((p.name, p.read_text()) for p in tmp_path.iterdir()) == [(".navrename-1-b", "B"), ("b", "A")]
    assert asked[0].endswith("it is left as .navrename-1-b")


def test_a_failed_temporary_rename_leaves_the_file_where_it_was(tmp_path):
    (tmp_path / "a").write_text("A")
    (tmp_path / "b").write_text("B")
    here = Location.of(tmp_path)
    real = drive_of(here)

    class Refusing:
        def __getattr__(self, name):
            return getattr(real, name)

        def rename(self, source, dest):
            if source.name == "a":
                raise PermissionError(13, "Permission denied")
            real.rename(source, dest)

    job = multirename.RenameJob(asker=lambda question: True)
    multirename.run([(here, "a", "b"), (here, "b", "a")], job, lambda place: Refusing())
    # a could not move, so b's new name stayed taken: b is put back as itself.
    assert sorted((p.name, p.read_text()) for p in tmp_path.iterdir()) == [("a", "A"), ("b", "B")]


# -- the box -----------------------------------------------------------------------------


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr(Manager, "last_renames", None)
    from navigator.widgets.file_ops.multi_rename_dialog import multi_rename_dialog

    monkeypatch.setitem(multi_rename_dialog._session, "rule", Rule())
    for name in ("one.txt", "two.txt", "other.log"):
        (tmp_path / name).write_text(name)
    return tmp_path


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def tag(*names: str):
    return lambda a: setattr(a.manager.left, "marked", frozenset(names))


def test_alt_a_previews_renames_and_undo_puts_the_names_back(place):
    app = navigator(place)
    seen = {}

    def fill(a):
        box = a.modal
        seen["title"] = box.title
        box.name_mask.value = "file[C]"
        box.digits.value = "2"

    def look(a):
        seen["preview"] = [(row.item.name, row.new) for row in a.modal.preview.items]
        seen["status"] = a.modal.status.text

    run_app(app, [Until(lambda a: "one.txt" in [e.name for e in a.manager.left.items]),
                  tag("one.txt", "two.txt"), KeyEvent("a", alt=True), Until(lambda a: a.modal is not None),
                  fill, lambda a: None, look, KeyEvent("enter"),
                  Until(lambda a: (place / "file02.txt").exists()), lambda a: None,
                  lambda a: seen.update(marked=a.manager.left.marked,
                                        undo=a.command_enabled(UndoMultiRename())),
                  lambda a: a.spawn(a.run_command(UndoMultiRename)),
                  Until(lambda a: (place / "two.txt").exists()), lambda a: None,
                  lambda a: seen.update(undone=a.command_enabled(UndoMultiRename()))])
    assert seen["title"] == "Multi-rename"
    assert seen["preview"] == [("one.txt", "file01.txt"), ("two.txt", "file02.txt")]
    assert seen["status"] == "2 files to rename"
    assert seen["marked"] == frozenset({"file01.txt", "file02.txt"}) and seen["undo"] is True
    assert sorted(p.name for p in place.iterdir()) == ["one.txt", "other.log", "two.txt"]
    assert seen["undone"] is False


def test_ok_stays_up_while_a_name_is_taken(place):
    app = navigator(place)
    seen = {}

    def fill(a):
        a.modal.name_mask.value = "other"
        a.modal.ext_mask.value = "log"

    run_app(app, [Until(lambda a: "one.txt" in [e.name for e in a.manager.left.items]),
                  tag("one.txt"), KeyEvent("a", alt=True), Until(lambda a: a.modal is not None),
                  fill, lambda a: None, KeyEvent("enter"), lambda a: None,
                  lambda a: seen.update(up=a.modal is not None, status=a.modal.status.text,
                                        footer=a.modal.preview.footer_text()),
                  KeyEvent("escape")])
    assert seen == {"up": True, "status": "1 name cannot be given",
                    "footer": "A file of that name is already there"}
    assert (place / "one.txt").exists()


def test_multi_rename_needs_something_to_rename(place):
    app = navigator(place)
    seen = {}
    run_app(app, [Until(lambda a: "one.txt" in [e.name for e in a.manager.left.items]),
                  lambda a: setattr(a.manager.left, "cursor", 0),
                  lambda a: seen.update(dots=a.command_enabled(MultiRename()),
                                        undo=a.command_enabled(UndoMultiRename())),
                  lambda a: setattr(a.manager.left, "cursor", 1),
                  lambda a: seen.update(file=a.command_enabled(MultiRename()))])
    assert seen == {"dots": False, "undo": False, "file": True}


def test_in_a_listing_each_file_is_renamed_in_its_own_directory(place, monkeypatch):
    monkeypatch.setenv("SHELL", "/bin/sh")
    for directory in ("a", "b"):
        (place / directory).mkdir()
        (place / directory / "README").write_text(directory)
    app = navigator(place)
    seen = {}

    def tag_all(a):
        panel = a.manager.left
        panel.marked = frozenset(e.key for e in panel.items if e.name != "..")

    def fill(a):
        a.modal.name_mask.value = "[P]_[N]"

    run_app(app, [lambda a: a.spawn(a.manager.panelize(a.manager.left, "printf 'a/README\\nb/README\\n'")),
                  Until(lambda a: a.manager.left.found is not None and a.modal is None), tag_all,
                  KeyEvent("a", alt=True), Until(lambda a: a.modal is not None), fill, lambda a: None,
                  KeyEvent("enter"), Until(lambda a: (place / "b" / "b_README").exists()), lambda a: None,
                  lambda a: seen.update(items=[e.key for e in a.manager.left.items],
                                        marked=a.manager.left.marked)])
    renamed = [str(place / "a" / "a_README"), str(place / "b" / "b_README")]
    assert seen["items"] == ["..", *renamed] and seen["marked"] == frozenset(renamed)
