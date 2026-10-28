"""File > Create archive (Shift+F1): the box, DN's ``dlgArchiveFiles`` -- its
type and name following each other, the levels and password each type
allows, what is greyed for want of a tool -- and navml's per-item
``enable_mask`` (Turbo Vision's ``EnableMask``) it needs."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from conftest import mounted, settle

from navkit.events import KeyEvent, MouseClickEvent

from navml.widgets.dialog.radio_buttons import RadioButtons

from navigator.lib.drives import Location, archive
from navigator.lib.file_ops.filecopy import ASK, FOLLOW_LINKS, MOVE, PRESERVE
from navigator.widgets.file_ops.archive_dialog import ArchiveDialog
from navigator.widgets.file_ops.archive_dialog import archive_dialog as archive_dialog_module
from navigator.widgets.file_ops.archive_dialog.archive_dialog import kind_index, suffix_of, with_suffix
from navigator.widgets.manager.panel import DirEntry

ZIP, SEVEN, TAR, TGZ, TBZ, TXZ, TZST = range(7)
NONE, FASTEST, NORMAL, MAXIMUM, ULTRA = range(5)


@pytest.fixture(autouse=True)
def fresh_session(monkeypatch):
    monkeypatch.setattr(archive_dialog_module, "_session",
                        {"kind": ZIP, "level": NORMAL, "options": archive_dialog_module.PATHNAMES})
    # Every type to be had, whatever is installed here, unless a test says otherwise.
    monkeypatch.setattr(archive, "format_missing", lambda kind: None)
    monkeypatch.setattr(archive, "can_encrypt", lambda kind: kind in (("7z", ""), ("zip", "")))


def box(tmp_path, **kwargs):
    kwargs.setdefault("entries", [DirEntry("notes.txt", False, 0)])
    kwargs.setdefault("here", tmp_path)
    kwargs.setdefault("directory", str(tmp_path / "out"))
    kwargs.setdefault("stem", "notes")
    return mounted(ArchiveDialog(**kwargs), size=(100, 30))


# -- names -----------------------------------------------------------------------------------


def test_an_archive_name_s_ending_is_found_and_replaced_whole():
    assert suffix_of("a.tar.gz") == ".tar.gz" and suffix_of("a.TGZ") == ".tgz"
    assert suffix_of("a.txt") == "" and suffix_of(".zip") == ""
    assert with_suffix("/x/a.tar.gz", ".7z") == "/x/a.7z"
    assert with_suffix("/x/a", ".zip") == "/x/a.zip"
    assert kind_index("a.tgz") == TGZ and kind_index("a.tar.zst") == TZST and kind_index("a.txt") is None


# -- the box -----------------------------------------------------------------------------------


def test_the_box_opens_on_the_other_panel_with_the_name_and_a_zip(tmp_path):
    dialog = box(tmp_path)
    assert dialog.title == "Create archive"
    assert dialog.target.value == f"{tmp_path / 'out'}/notes.zip"
    assert dialog.target.entry.selected_text == dialog.target.value
    assert (dialog.kind.value, dialog.level.value) == (ZIP, NORMAL)
    assert dialog.options.value == archive_dialog_module.PATHNAMES
    assert dialog.password.entry.password and not dialog.password.disabled
    assert dialog.note.text == ""


def test_another_type_changes_the_ending_and_the_levels_it_has(tmp_path):
    dialog = box(tmp_path)
    dialog.level.value = NONE
    dialog.kind.value = TGZ
    settle()
    assert dialog.target.value == f"{tmp_path / 'out'}/notes.tar.gz"
    assert not dialog.level.item_enabled(NONE) and dialog.level.item_enabled(ULTRA)
    assert dialog.level.value == NORMAL  # *None* is not a gzip's
    assert dialog.password.disabled  # only a 7z or a zip is encrypted
    dialog.kind.value = TAR
    settle()
    assert dialog.target.value.endswith("/notes.tar") and dialog.level.disabled
    dialog.kind.value = SEVEN
    settle()
    assert dialog.target.value.endswith("/notes.7z")
    assert not dialog.level.disabled and dialog.level.item_enabled(NONE) and not dialog.password.disabled


def test_an_ending_typed_chooses_its_type(tmp_path):
    dialog = box(tmp_path)
    dialog.target.value = "/somewhere/else.txz"
    settle()
    assert dialog.kind.value == TXZ
    assert dialog.target.value == "/somewhere/else.txz"  # the name as typed


def test_a_type_with_no_tool_is_greyed_and_said(tmp_path, monkeypatch):
    monkeypatch.setattr(archive_dialog_module, "_session",
                        {"kind": SEVEN, "level": NORMAL, "options": 0})
    monkeypatch.setattr(archive, "format_missing", lambda kind: "missing" if kind[0] == "7z" else None)
    dialog = box(tmp_path)
    assert not dialog.kind.item_enabled(SEVEN) and dialog.kind.item_enabled(TZST)
    assert dialog.kind.value == ZIP  # the remembered 7z cannot be had
    assert dialog.note.text == "7Z needs 7-Zip"
    dialog.target.value = "/x/a.7z"
    settle()
    assert dialog.kind.value == ZIP


def test_the_request_packs_into_the_named_archive_as_the_box_says(tmp_path):
    dialog = box(tmp_path, entries=[DirEntry("notes.txt", False, 0), DirEntry("dir", True, 0)])
    dialog.kind.value = SEVEN
    dialog.level.value = ULTRA
    dialog.options.value = archive_dialog_module.MOVE_FILES | archive_dialog_module.FOLLOW
    settle()
    outer = Location.of(tmp_path / "out" / "notes.7z")
    request = dialog._request(outer, "pw")
    assert request.sources == [tmp_path / "notes.txt", tmp_path / "dir"]
    assert request.target == f"{tmp_path / 'out' / 'notes.7z'}#/"
    assert request.mode == ASK and request.options == PRESERVE | FOLLOW_LINKS | MOVE
    assert request.flatten  # *Store pathnames* unticked
    assert request.archive == archive.ArchiveOptions(level="ultra", password="pw")


def test_ok_remembers_type_level_and_boxes_but_never_the_password(tmp_path):
    dialog = box(tmp_path)
    dialog.kind.value = TXZ
    dialog.level.value = MAXIMUM
    settle()
    seen = []
    dialog.close = seen.append
    asyncio.run(dialog.confirm())
    assert seen and seen[0].archive == archive.ArchiveOptions(level="maximum")
    again = box(tmp_path)
    assert (again.kind.value, again.level.value) == (TXZ, MAXIMUM)
    assert again.target.value.endswith("/notes.tar.xz") and again.password.value == ""


def test_a_name_without_an_ending_is_given_the_type_s(tmp_path):
    dialog = box(tmp_path)
    dialog.target.value = str(tmp_path / "out" / "bare")
    settle()
    seen = []
    dialog.close = seen.append
    asyncio.run(dialog.confirm())
    assert seen[0].target == f"{tmp_path / 'out' / 'bare.zip'}#/"


# -- enable_mask ---------------------------------------------------------------------------------


def three_radios():
    radios = RadioButtons(width=20, height=3)
    radios.items = ["~A~lpha", "~B~eta", "~G~amma"]
    radios.enable_mask = 0b101
    return mounted(radios, size=(20, 3))


def test_the_keyboard_passes_over_an_item_that_cannot_be_chosen():
    radios = three_radios()
    asyncio.run(radios.on_key(KeyEvent("down")))
    assert (radios.sel, radios.value) == (2, 2)
    asyncio.run(radios.on_key(KeyEvent("up")))
    assert (radios.sel, radios.value) == (0, 0)
    radios.enable_mask = 0b011
    asyncio.run(radios.on_key(KeyEvent("end")))
    assert radios.value == 1


def test_neither_a_click_nor_its_letter_takes_a_greyed_item():
    radios = three_radios()
    asyncio.run(radios.on_mouse_click(MouseClickEvent(1, 1, "left", "press")))
    assert radios.value == 0
    assert not radios.shortcut_match("b") and radios.shortcut_match("g")
    assert asyncio.run(radios.activate("b")) is False and radios.value == 0
