"""Alt+E's model: what a selection has in common, what a request changes, and how deep."""

from __future__ import annotations

import os
import stat
import time

import pytest

from navigator import fileattr
from navigator.fileattr import AttrJob, AttrRequest
from navigator.filecopy import Failure


def mode_of(path) -> int:
    return stat.S_IMODE(os.lstat(path).st_mode)


def make(path, mode, text="x"):
    path.write_text(text)
    os.chmod(path, mode)
    return path


# -- bits ------------------------------------------------------------------------------


def test_the_grid_order_is_owner_group_others_then_the_special_bits():
    # Item 0 is the lowest bit: owner read, write; group read; others read.
    assert fileattr.to_items(0o644) == 0b000_001_001_011
    assert fileattr.from_items(fileattr.to_items(0o7531)) == 0o7531
    assert fileattr.from_items(1 << 9) == stat.S_ISUID


def test_octal_and_symbolic_mark_what_is_mixed():
    assert fileattr.octal(0o644) == "0644"
    assert fileattr.octal(0o644, 0o011) == "06??"
    assert fileattr.symbolic(0o755) == "rwxr-xr-x"
    assert fileattr.symbolic(0o4755) == "rwsr-xr-x"
    assert fileattr.symbolic(0o1644) == "rw-r--r-T"
    assert fileattr.symbolic(0o644, 0o020) == "rw-r?-r--"


@pytest.mark.parametrize("text, mode", [("644", 0o644), ("0755", 0o755), ("4755", 0o4755), ("7", 0o7)])
def test_an_octal_mode_reads(text, mode):
    assert fileattr.parse_octal(text) == mode


@pytest.mark.parametrize("text", ["", "8", "07555", "rw", "0?44"])
def test_anything_else_is_refused(text):
    with pytest.raises(ValueError):
        fileattr.parse_octal(text)


# -- the survey --------------------------------------------------------------------------


def test_one_file_is_surveyed_whole(tmp_path):
    f = make(tmp_path / "f", 0o640, "hello")
    os.utime(f, (1_000_000_000, 1_000_000_000))
    survey = fileattr.survey([f])
    assert (survey.mode, survey.mixed) == (0o640, 0)
    assert (survey.uid, survey.gid) == (os.getuid(), os.stat(f).st_gid)
    assert survey.mtime == 1_000_000_000
    assert (survey.files, survey.dirs) == (1, 0)
    assert survey.single.st_size == 5


def test_bits_the_files_disagree_on_are_mixed(tmp_path):
    a = make(tmp_path / "a", 0o644)
    b = make(tmp_path / "b", 0o755)
    os.utime(a, (1, 1))
    survey = fileattr.survey([a, b])
    assert survey.mixed == 0o111
    assert survey.mode == 0o644
    assert survey.mtime is None and survey.single is None


def test_a_link_is_surveyed_through(tmp_path):
    target = make(tmp_path / "t", 0o600)
    (tmp_path / "l").symlink_to("t")
    survey = fileattr.survey([tmp_path / "l"])
    assert survey.mode == 0o600 and survey.link_target == "t"
    assert target.exists()


# -- owners and time ---------------------------------------------------------------------


def test_owners_are_read_by_name_or_number_and_blank_is_leave_it():
    me = fileattr.user_name(os.getuid())
    assert fileattr.parse_user(me) == os.getuid()
    assert fileattr.parse_user(str(os.getuid())) == os.getuid()
    assert fileattr.parse_user("  ") is None
    with pytest.raises(ValueError):
        fileattr.parse_user("no-such-user-here")
    assert fileattr.parse_group(fileattr.group_name(os.getgid())) == os.getgid()


def test_a_user_who_is_not_root_may_give_a_file_only_to_their_own_groups():
    if fileattr.can_chown_user():
        pytest.skip("running as root")
    assert fileattr.group_name(os.getegid()) in fileattr.assignable_groups()
    assert set(fileattr.assignable_groups()) <= set(fileattr.groups()) | {
        str(g) for g in os.getgroups()
    }


def test_the_time_is_dns_date_and_time_and_blank_is_leave_it():
    base = time.mktime((2024, 3, 5, 10, 20, 30, 0, 0, -1))
    assert fileattr.date_text(base) == "05-03-2024"
    assert fileattr.time_text(base) == "10:20:30"
    assert fileattr.parse_mtime("", "", base) is None
    # Unchanged is leave it, so OK on an untouched dialog keeps the nanoseconds.
    assert fileattr.parse_mtime("05-03-2024", "10:20:30", base) is None
    assert fileattr.parse_mtime("06-03-24", "", base) == base + 86400
    assert fileattr.parse_mtime("", "11:20", base) == base + 3600 - 30


def test_a_bad_time_is_refused_and_mixed_times_need_both_halves():
    with pytest.raises(ValueError):
        fileattr.parse_mtime("31-02-2024", "10:00:00", None)
    with pytest.raises(ValueError):
        fileattr.parse_mtime("01-01-2024", "25:00", None)
    with pytest.raises(ValueError):
        fileattr.parse_mtime("01-01-2024", "", None)


# -- applying ----------------------------------------------------------------------------


def test_only_the_bits_named_change(tmp_path):
    a = make(tmp_path / "a", 0o644)
    b = make(tmp_path / "b", 0o755)
    request = AttrRequest([a, b], set_bits=0o020, clear_bits=0o004)
    assert fileattr.run(request, AttrJob()) == [a, b]
    assert (mode_of(a), mode_of(b)) == (0o660, 0o771)


def test_the_time_is_set_and_the_access_time_kept(tmp_path):
    f = make(tmp_path / "f", 0o644)
    os.utime(f, (5_000, 6_000))
    fileattr.apply_one(f, AttrRequest([f], mtime=1_000_000.0))
    st = os.stat(f)
    assert (st.st_atime, st.st_mtime) == (5_000, 1_000_000)


def test_a_group_of_ones_own_is_given(tmp_path):
    f = make(tmp_path / "f", 0o644)
    gid = os.getgroups()[-1] if os.getgroups() else os.getgid()
    fileattr.apply_one(f, AttrRequest([f], gid=gid))
    assert os.stat(f).st_gid == gid


def test_the_owner_goes_before_the_mode(tmp_path, monkeypatch):
    f = make(tmp_path / "f", 0o644)
    calls = []
    monkeypatch.setattr(os, "chown", lambda *a, **k: calls.append("chown"))
    monkeypatch.setattr(os, "chmod", lambda *a, **k: calls.append("chmod"))
    fileattr.apply_one(f, AttrRequest([f], set_bits=0o100, gid=os.getgid() + 12345))
    assert calls == ["chown", "chmod"]


@pytest.fixture
def tree(tmp_path):
    root = tmp_path / "d"
    root.mkdir()
    os.chmod(root, 0o755)
    make(root / "f", 0o644)
    (root / "sub").mkdir()
    os.chmod(root / "sub", 0o755)
    make(root / "sub" / "g", 0o644)
    outside = make(tmp_path / "outside", 0o644)
    (root / "link").symlink_to(outside)
    return root, outside


@pytest.mark.parametrize("recurse, f, sub, root", [
    (fileattr.NONE, 0o644, 0o755, 0o775),
    (fileattr.FILES, 0o664, 0o755, 0o775),
    (fileattr.DIRS, 0o644, 0o775, 0o775),
    (fileattr.ALL, 0o664, 0o775, 0o775),
])
def test_recursion_picks_what_it_touches_and_the_tagged_entry_always_changes(tree, recurse, f, sub, root):
    d, outside = tree
    fileattr.run(AttrRequest([d], set_bits=0o020, recurse=recurse), AttrJob())
    assert mode_of(d / "f") == f
    assert mode_of(d / "sub" / "g") == f
    assert mode_of(d / "sub") == sub
    assert mode_of(d) == root
    # Never through a link.
    assert mode_of(outside) == 0o644


def test_a_directory_that_cannot_be_read_into_is_changed_first(tree):
    d, _ = tree
    os.chmod(d / "sub", 0o000)
    try:
        fileattr.run(AttrRequest([d], set_bits=0o500, recurse=fileattr.DIRS), AttrJob())
        assert mode_of(d / "sub") == 0o500
    finally:
        os.chmod(d / "sub", 0o755)


def test_a_failure_asks_and_skip_goes_on(tmp_path):
    a = tmp_path / "gone"
    b = make(tmp_path / "b", 0o644)
    asked = []
    job = AttrJob(asker=lambda q: asked.append(q) or True)
    done = fileattr.run(AttrRequest([a, b], set_bits=0o020), job)
    assert done == [b]
    assert isinstance(asked[0], Failure) and asked[0].path == a
    assert mode_of(b) == 0o664


def test_cancel_stops(tmp_path):
    a = tmp_path / "gone"
    b = make(tmp_path / "b", 0o644)
    done = fileattr.run(AttrRequest([a, b], set_bits=0o020), AttrJob(asker=lambda q: False))
    assert done == [] and mode_of(b) == 0o644


def test_a_request_with_nothing_in_it_says_so(tmp_path):
    assert AttrRequest([tmp_path]).changes_nothing
    assert not AttrRequest([tmp_path], clear_bits=0o002).changes_nothing
