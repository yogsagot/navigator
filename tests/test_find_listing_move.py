"""F6 to a bare mask in a *Find:* listing: DN's SoftMode, each file renamed where it is."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.drives.listing import DirEntry
from navigator.lib.file_ops.filefind import FindListing
from navigator.widgets.file_ops.copy_dialog import CopyDialog


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "one").mkdir()
    (tmp_path / "two").mkdir()
    (tmp_path / "one" / "a.txt").write_text("a")
    (tmp_path / "two" / "c.txt").write_text("c")
    return tmp_path


def test_f6_to_a_mask_renames_found_files_in_their_own_directories(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    found = FindListing(title="*.txt", origin=place, entries=[
        DirEntry("a.txt", False, 1, directory=place / "one"),
        DirEntry("c.txt", False, 1, directory=place / "two"),
    ])

    def show(a):
        a.manager.left.show_found(found)

    def tag(a):
        panel = a.manager.left
        panel.marked = frozenset(entry.key for entry in panel.items if entry.name != "..")

    def target(a):
        a.modal.target.value = "*.bak"

    def listed(a):
        return sorted(entry.name for entry in a.manager.left.items if entry.name != "..")

    seen = {}
    run_app(app, [
        show, Until(lambda a: len(a.manager.left.items) == 3), tag,
        KeyEvent("f6"), Until(lambda a: isinstance(a.modal, CopyDialog)), target, KeyEvent("enter"),
        Until(lambda a: a.modal is None and (place / "two" / "c.bak").exists()),
        Until(lambda a: listed(a) == ["a.bak", "c.bak"]),
        lambda a: seen.update(listed=listed(a), found=a.manager.left.found is not None),
    ])
    assert (place / "one" / "a.bak").read_text() == "a" and (place / "two" / "c.bak").read_text() == "c"
    assert not (place / "a.bak").exists() and not (place / "c.bak").exists()
    assert seen == {"listed": ["a.bak", "c.bak"], "found": True}
