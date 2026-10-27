"""POSIX ACLs (``navigator/lib/file_ops/acl.py``): the kernel's binary form and the edits."""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest

from navigator.lib.file_ops import acl
from navigator.lib.file_ops.acl import MASK_KEY, Acl


def test_an_acl_round_trips_through_the_binary_form():
    original = Acl(owner=6, group=4, other=0, named={("user", 1000): 7, ("group", 50): 5}, mask=7)
    assert acl.parse(acl.pack(original)) == original


def test_the_binary_form_is_sorted_by_tag_then_id():
    data = acl.pack(Acl(owner=6, group=4, other=4, named={("user", 9): 4, ("user", 3): 4}, mask=4))
    ids = [int.from_bytes(data[4 + i * 8 + 4:4 + i * 8 + 8], "little") for i in range(6)]
    tags = [int.from_bytes(data[4 + i * 8:4 + i * 8 + 2], "little") for i in range(6)]
    assert tags == [acl.USER_OBJ, acl.USER, acl.USER, acl.GROUP_OBJ, acl.MASK, acl.OTHER]
    assert ids[1:3] == [3, 9]


def test_what_is_not_an_acl_is_refused():
    with pytest.raises(ValueError):
        acl.parse(b"\x01\x00\x00\x00")
    with pytest.raises(ValueError):
        acl.parse(b"\x02\x00\x00\x00\x01")


def test_the_mask_is_worked_out_as_setfacl_works_it_out():
    base = acl.from_mode(0o640)
    new = acl.apply_deltas(base, {("user", 1000): 6, ("group", 7): 1}, set())
    assert new.mask == 4 | 6 | 1
    assert new.group == 4 and not new.minimal


def test_a_mask_set_by_hand_is_kept():
    base = acl.from_mode(0o640)
    new = acl.apply_deltas(base, {("user", 1000): 7, MASK_KEY: 4}, set())
    assert new.mask == 4


def test_removing_the_last_named_entry_takes_the_mask_along():
    start = Acl(owner=6, group=4, other=0, named={("user", 1000): 6}, mask=6)
    new = acl.apply_deltas(start, {}, {("user", 1000)})
    assert new.minimal and new.mask is None


def test_the_mask_removed_while_named_entries_stay_is_worked_out_again():
    start = Acl(owner=6, group=4, other=0, named={("user", 1000): 6}, mask=4)
    assert acl.apply_deltas(start, {}, {MASK_KEY}).mask == 6


def test_the_same_edit_reaches_acls_that_otherwise_differ():
    one = Acl(owner=6, group=4, other=0, named={("user", 1): 4}, mask=4)
    two = Acl(owner=7, group=5, other=5)
    edit = {("group", 9): 6}
    assert acl.apply_deltas(one, edit, set()).named == {("user", 1): 4, ("group", 9): 6}
    assert acl.apply_deltas(two, edit, set()).named == {("group", 9): 6}
    assert acl.apply_deltas(two, edit, set()).owner == 7


def test_a_first_default_acl_copies_the_access_acls_base_entries():
    access = Acl(owner=7, group=5, other=1, named={("user", 1): 4}, mask=5)
    assert acl.seed_default(access) == Acl(owner=7, group=5, other=1)


def test_permissions_are_spelled_as_getfacl_spells_them():
    assert acl.spell(6) == "rw-" and acl.spell(5) == "r-x" and acl.spell(None) == "???"


@pytest.mark.skipif(shutil.which("setfacl") is None, reason="setfacl is not installed")
def test_what_setfacl_writes_reads_back_byte_for_byte(tmp_path):
    path = tmp_path / "f"
    path.write_text("x")
    result = subprocess.run(["setfacl", "-m", f"u:{os.getuid()}:rw,g:{os.getgid()}:r", str(path)])
    if result.returncode:
        pytest.skip("this file system takes no ACLs")
    data = os.getxattr(path, acl.ACCESS)
    parsed = acl.parse(data)
    assert parsed.named == {("user", os.getuid()): 6, ("group", os.getgid()): 4}
    assert acl.pack(parsed) == data
