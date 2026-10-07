"""Options > File Manager > Highlight groups: DOS Navigator's ``SetHighlightGroups``."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator import filetypes
from navigator.__main__ import Navigator
from navigator.settings import SETTINGS
from navigator.widgets.setup.highlight_dialog.highlight_dialog import tidy
from navigator.widgets.shell.commands import HighlightGroups


def test_masks_put_in_force_recolour_and_regroup_and_the_rest_keep_theirs():
    assert filetypes.group_of("a.pas") == "source"
    assert filetypes.use_masks({"source": "*.foo", "archive": "*.pas"})
    assert filetypes.group_of("a.pas") is None and filetypes.category_of("b.FOO", False) == "source"
    assert filetypes.group_of("a.zip") == "archive" and filetypes.group_of("a.png") == "image"
    assert not filetypes.use_masks({"source": "*.foo"})


def test_a_mask_is_kept_as_dn_kept_it():
    assert tidy(" *.a ; ;*.b;; ") == "*.a;*.b"


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "x.foo").write_text("x")
    (tmp_path / "y.py").write_text("y")
    return tmp_path


def test_ok_saves_the_masks_and_the_panels_take_them_at_once(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    seen = {}

    def classes(a):
        panel = a.manager.left
        return {item.name: filetypes.category_of(item.name, item.is_dir, item.type_mark) for item in panel.items}

    def edit(a):
        seen["source"] = a.modal.source.value
        a.modal.source.value = " *.foo ;"

    run_app(app, [lambda a: seen.update(before=classes(a)),
                  lambda a: a.spawn(a.run_command(HighlightGroups)),
                  Until(lambda a: getattr(a.modal, "title", None) == "Highlight groups", timeout=5),
                  edit, KeyEvent("enter"), lambda a: None, lambda a: None,
                  lambda a: seen.update(after=classes(a), token=a.manager.left.reload_token)])
    assert seen["source"] == filetypes.CATEGORIES["source"]
    assert seen["before"]["y.py"] == "source" and seen["before"]["x.foo"] is None
    assert seen["after"]["y.py"] is None and seen["after"]["x.foo"] == "source"
    assert seen["token"] > 0
    assert SETTINGS.highlight_groups.source == "*.foo"
    assert "source = *.foo" in SETTINGS.path.read_text()
