"""File > Symlinks' tools beside Shift+F5: a link's target edited, several
changed by one replacement, absolute turned relative and back, and the
broken ones tagged or found."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app

from navigator.__main__ import Navigator
from navigator.lib.drives import LOCAL, Location, mount, unmount
from navigator.lib.drives.memory import MemoryDrive
from navigator.lib.file_ops import filelink
from navigator.lib.file_ops.filefind import Advanced, FindJob, FindRequest, search
from navigator.lib.file_ops.filelink import (
    NotTheSame, absolute_target, relative_target, replaced, retarget, switched,
)
from navigator.widgets.file_ops.link_target_dialog import LinkTargetDialog
from navigator.widgets.file_ops.relink_dialog import RelinkDialog
from navigator.widgets.file_ops.relink_dialog import relink_dialog as relink_dialog_module
from navigator.widgets.manager.commands import EditLinkTarget, LinkAbsolute, LinkRelative, SelectBrokenLinks
from navigator.widgets.manager.panel.panel import make_entry


# -- the model -----------------------------------------------------------------------


def test_targets_are_turned_absolute_and_relative_by_their_letters():
    assert absolute_target("/srv/www", "../data/f") == "/srv/data/f"
    assert absolute_target("/srv/www", "/etc/x") == "/etc/x"
    assert relative_target("/srv/www", "/srv/data/f") == "../data/f"
    assert relative_target("/srv/www", "../data/f") == "../data/f"
    assert relative_target("/srv/www", "/srv/www/a") == "a"


@pytest.fixture
def place(tmp_path):
    """``www`` a link to ``real``; in ``real`` a relative, an absolute and a broken link, and a file."""
    (tmp_path / "real").mkdir()
    (tmp_path / "other").mkdir()
    (tmp_path / "other" / "f").write_text("f")
    os.symlink("real", tmp_path / "www")
    os.symlink("../other/f", tmp_path / "real" / "rel")
    os.symlink(str(tmp_path / "other" / "f"), tmp_path / "real" / "abs")
    os.symlink("nowhere", tmp_path / "real" / "broken")
    (tmp_path / "real" / "plain").write_text("p")
    return tmp_path


def test_switched_reads_from_the_real_parent(place):
    # Through ``www``, as a panel standing there sees the links.
    www = place / "www"
    assert switched(LOCAL, Location.of(www / "rel"), relative=False) == str(place / "other" / "f")
    assert switched(LOCAL, Location.of(www / "rel"), relative=True) is None
    assert switched(LOCAL, Location.of(www / "abs"), relative=True) == "../other/f"
    assert switched(LOCAL, Location.of(www / "abs"), relative=False) is None
    # A broken link is rewritten by its letters.
    assert switched(LOCAL, Location.of(www / "broken"), relative=False) == str(place / "real" / "nowhere")


def test_a_rewrite_reaching_another_file_is_refused(tmp_path):
    # ``hop`` leads two levels down, so ``hop/..`` is ``deep``, not the top:
    # by the letters the target would be ``tmp/other/f``, the kernel says ``deep/other/f``.
    (tmp_path / "deep" / "inner").mkdir(parents=True)
    (tmp_path / "deep" / "other").mkdir()
    (tmp_path / "deep" / "other" / "f").write_text("deep")
    (tmp_path / "other").mkdir()
    (tmp_path / "other" / "f").write_text("top")
    os.symlink("deep/inner", tmp_path / "hop")
    os.symlink(str(tmp_path / "hop" / ".." / "other" / "f"), tmp_path / "l")
    assert (tmp_path / "l").read_text() == "deep"
    with pytest.raises(NotTheSame):
        switched(LOCAL, Location.of(tmp_path / "l"), relative=True)


def test_retarget_replaces_the_link_and_leaves_no_temporary(place):
    link = place / "real" / "rel"
    retarget(LOCAL, Location.of(link), "../other")
    assert os.readlink(link) == "../other"
    assert not [name for name in os.listdir(place / "real") if name.startswith(filelink.TEMPORARY)]


def test_retarget_never_replaces_a_file(place):
    with pytest.raises(OSError):
        retarget(LOCAL, Location.of(place / "other" / "f"), "x")
    assert (place / "other" / "f").read_text() == "f"


def test_retarget_on_another_drive():
    drive = mount(MemoryDrive("links"))
    try:
        drive.make("/a/f", "f")
        link = drive.location("/a/l")
        drive.symlink("f", link)
        retarget(drive, link, "/a/f")
        assert drive.readlink(link) == "/a/f"
        assert switched(drive, link, relative=True) == "f"
        assert sorted(drive.names(drive.location("/a"))) == ["f", "l"]
    finally:
        unmount(drive.site)


def test_replaced_plans_each_row_and_its_problem():
    rows = replaced([("a", "/old/x"), ("b", "../y"), ("c", "/old")], "/old", "")
    assert [(row.new, row.problem) for row in rows] == [("/x", ""), ("../y", "unchanged"), ("", "empty")]
    assert all(row.problem == "unchanged" for row in replaced([("a", "x")], "", "y"))


# -- the boxes -----------------------------------------------------------------------


def test_the_target_box_rewrites_the_line_with_the_box():
    box = LinkTargetDialog(name="l", target="../data/f", base="/srv/www")
    assert box.options.value == 1
    box.mounted()
    box.options.value = 0
    from conftest import settle

    settle()
    assert box.line.value == "/srv/data/f"
    box.options.value = 1
    settle()
    assert box.line.value == "../data/f"
    assert box.accept() == "../data/f"


def test_the_relink_box_previews_and_refuses_a_spoilt_target(monkeypatch):
    monkeypatch.setattr(relink_dialog_module, "_session", {"search": "", "replace": ""})
    from conftest import settle

    box = RelinkDialog(links=[(Location.of("/a/l1"), "/old/x"), (Location.of("/a/l2"), "/old")])
    box.mounted()
    assert not box.valid()
    box.search.value, box.replace.value = "/old/", "/new/"
    settle()
    assert box.valid() and box.status.text == "1 link to change"
    assert [row.new for row in box.accept()] == ["/new/x"]
    box.search.value, box.replace.value = "/old", ""
    settle()
    assert not box.valid()


# -- Find File's kind -----------------------------------------------------------------


def test_find_file_finds_broken_links(place):
    (place / "real" / "deeper").mkdir()
    os.symlink("gone", place / "real" / "deeper" / "also")
    job = FindJob()
    request = FindRequest(mask="*", advanced=True, limits=Advanced(kinds=frozenset({"broken_link"})))
    search(request, place, lambda d, item, info: make_entry(item, d), job)
    assert sorted(entry.name for entry in job.found) == ["also", "broken"]


# -- end to end ----------------------------------------------------------------------


@pytest.fixture
def desk(place, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    return Navigator(place / "real", place / "other", terminal=FakeTerminal(80, 24))


def listed(name: str):
    return Until(lambda a: name in [e.name for e in a.manager.left.items])


def test_make_relative_over_tagged_links(desk, place):
    real = place / "real"
    run_app(desk, [listed("abs"),
                   lambda a: setattr(a.manager.left, "marked", frozenset({"abs", "rel"})),
                   lambda a: a.spawn(a.run_command(LinkRelative)),
                   Until(lambda a: not os.path.isabs(os.readlink(real / "abs"))),
                   Until(lambda a: not a.manager.left.marked)])
    assert os.readlink(real / "abs") == "../other/f"
    assert os.readlink(real / "rel") == "../other/f"


def test_make_absolute_rewrites_a_broken_link_by_its_letters(desk, place):
    real = place / "real"
    run_app(desk, [listed("abs"),
                   lambda a: setattr(a.manager.left, "marked", frozenset({"abs", "broken"})),
                   lambda a: a.spawn(a.run_command(LinkAbsolute)),
                   Until(lambda a: os.path.isabs(os.readlink(real / "broken")))])
    assert os.readlink(real / "abs") == str(place / "other" / "f")
    assert os.readlink(real / "broken") == str(real / "nowhere")


def test_edit_link_target_one_link(desk, place):
    def answer(a):
        a.modal.line.value = "../other"
        a.modal.close(a.modal.accept())

    def cursor_on_rel(a):
        panel = a.manager.left
        panel.cursor = next(i for i, e in enumerate(panel.items) if e.name == "rel")

    run_app(desk, [listed("rel"), cursor_on_rel,
                   lambda a: a.spawn(a.run_command(EditLinkTarget)),
                   Until(lambda a: isinstance(a.modal, LinkTargetDialog)),
                   answer, Until(lambda a: os.readlink(place / "real" / "rel") == "../other")])


def test_edit_link_target_several_links(desk, place, monkeypatch):
    monkeypatch.setattr(relink_dialog_module, "_session", {"search": "", "replace": ""})

    def answer(a):
        a.modal.search.value, a.modal.replace.value = "other/f", "other"

    def ok(a):
        a.modal.close(a.modal.accept())

    run_app(desk, [listed("abs"),
                   lambda a: setattr(a.manager.left, "marked", frozenset({"abs", "rel"})),
                   lambda a: a.spawn(a.run_command(EditLinkTarget)),
                   Until(lambda a: isinstance(a.modal, RelinkDialog)), answer, lambda a: None, ok,
                   Until(lambda a: os.readlink(place / "real" / "rel") == "../other")])
    assert os.readlink(place / "real" / "abs") == str(place / "other")


def test_select_broken_links_tags_the_broken_alone(desk):
    seen = {}
    run_app(desk, [listed("broken"),
                   lambda a: seen.update(enabled=a.command_enabled(SelectBrokenLinks())),
                   lambda a: a.spawn(a.run_command(SelectBrokenLinks)),
                   Until(lambda a: a.manager.left.marked),
                   lambda a: seen.update(marked=a.manager.left.marked)])
    assert seen == {"enabled": True, "marked": frozenset({"broken"})}


def test_the_tools_want_a_link_selected(desk):
    seen = {}

    def on(name):
        def put(a):
            panel = a.manager.left
            panel.cursor = next(i for i, e in enumerate(panel.items) if e.name == name)
        return put

    run_app(desk, [listed("rel"), on("rel"),
                   lambda a: seen.update(on_link=a.command_enabled(LinkRelative())),
                   on(".."),
                   lambda a: seen.update(on_dots=a.command_enabled(LinkRelative()),
                                         edit=a.command_enabled(EditLinkTarget()))])
    assert seen == {"on_link": True, "on_dots": False, "edit": False}


def test_the_context_menu_offers_them_on_a_link_only(desk, place):
    seen = {}

    def look(name):
        def at(a):
            panel = a.manager.left
            panel.cursor = next(i for i, e in enumerate(panel.items) if e.name == name)
            menu = panel.context_menu()
            seen[name] = [menu.item_for(command) is not None for command in (EditLinkTarget, LinkRelative, LinkAbsolute)]
        return at

    run_app(desk, [listed("plain"), look("rel"), look("plain")])
    assert seen == {"rel": [True, True, True], "plain": [False, False, False]}
