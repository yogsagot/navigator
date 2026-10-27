"""Alt+E's model: what a selection has in common, what a request changes, and how deep."""

from __future__ import annotations

import os
import stat
import time

import pytest

from navigator.lib.file_ops import fileattr
from navigator.lib.file_ops.fileattr import AttrJob, AttrRequest
from navigator.lib.file_ops.filecopy import Failure


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


@pytest.mark.parametrize("format, text", [
    ("%m/%d/%Y", "03/06/2024"), ("%Y-%m-%d", "2024-03-06"), ("%d.%m.%y", "06.03.24"),
])
def test_the_date_is_read_in_the_order_it_was_written_in(format, text):
    base = time.mktime((2024, 3, 5, 10, 20, 30, 0, 0, -1))
    assert fileattr.date_text(base, format) == time.strftime(format, time.localtime(base))
    assert fileattr.parse_mtime(text, "", base, format) == base + 86400
    with pytest.raises(ValueError):
        fileattr.parse_mtime("06-03-2024", "", base, format)


def test_a_12_hour_time_is_written_and_read_with_am_and_pm():
    base = time.mktime((2024, 3, 5, 21, 20, 30, 0, 0, -1))
    twelve = "%I:%M:%S%p"
    assert fileattr.time_text(base, twelve) == "09:20:30pm"
    assert fileattr.parse_mtime("", "09:20:30pm", base, time_format=twelve) is None
    assert fileattr.parse_mtime("", "09:20:30am", base, time_format=twelve) == base - 12 * 3600
    assert fileattr.parse_mtime("", "12:00:00am", base, time_format=twelve) == base - (21 * 3600 + 20 * 60 + 30)
    for bad in ("13:00:00pm", "00:10:00am", "09:20:30"):
        with pytest.raises(ValueError):
            fileattr.parse_mtime("", bad, base, time_format=twelve)


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


# -- ACLs, extended attributes and flags ---------------------------------------------

from navigator.lib.file_ops import acl, fsflags  # noqa: E402


def xattrs_or_skip(path):
    try:
        os.setxattr(path, "user.probe", b"")
        os.removexattr(path, "user.probe")
    except OSError:
        pytest.skip("this file system takes no user extended attributes")


def acls_or_skip(path):
    try:
        os.setxattr(path, acl.ACCESS, acl.pack(acl.from_mode(os.stat(path).st_mode)))
    except OSError:
        pytest.skip("this file system takes no ACLs")


def test_a_request_with_only_extended_changes_is_not_empty(tmp_path):
    assert not AttrRequest([tmp_path], xattr_remove={"user.a"}).changes_nothing
    assert not AttrRequest([tmp_path], acl_set={("user", 1): 4}).changes_nothing
    assert not AttrRequest([tmp_path], flags_set=fsflags.BY_LETTER["A"]).changes_nothing


def test_the_survey_shares_what_every_file_has_and_marks_the_rest(tmp_path):
    a = make(tmp_path / "a", 0o644)
    b = make(tmp_path / "b", 0o644)
    xattrs_or_skip(a)
    for path in (a, b):
        os.setxattr(path, "user.same", b"1")
    os.setxattr(a, "user.differs", b"x")
    os.setxattr(b, "user.differs", b"y")
    os.setxattr(a, "user.only", b"z")
    found = fileattr.survey([a, b])
    assert found.xattrs_supported
    assert found.xattrs == {"user.same": b"1", "user.differs": None, "user.only": None}


def test_the_survey_reads_named_acl_entries_and_leaves_the_acl_attributes_out(tmp_path):
    a = make(tmp_path / "a", 0o640)
    acls_or_skip(a)
    entries = acl.apply_deltas(acl.from_mode(0o640), {("user", os.getuid()): 6}, set())
    os.setxattr(a, acl.ACCESS, acl.pack(entries))
    found = fileattr.survey([a])
    assert found.acl == {("user", os.getuid()): 6, acl.MASK_KEY: 6}
    assert acl.ACCESS not in found.xattrs


def test_xattrs_are_set_and_removed(tmp_path):
    a = make(tmp_path / "a", 0o644)
    xattrs_or_skip(a)
    os.setxattr(a, "user.old", b"1")
    fileattr.apply_one(a, AttrRequest([a], xattr_set={"user.new": b"\x00\xff"}, xattr_remove={"user.old"}))
    assert os.listxattr(a) == ["user.new"] and os.getxattr(a, "user.new") == b"\x00\xff"


def test_an_acl_entry_added_then_the_last_removed_leaves_the_mode_as_it_was(tmp_path):
    a = make(tmp_path / "a", 0o640)
    acls_or_skip(a)
    os.removexattr(a, acl.ACCESS)
    me = ("user", os.getuid())
    fileattr.apply_one(a, AttrRequest([a], acl_set={me: 7}))
    written = acl.parse(os.getxattr(a, acl.ACCESS))
    assert written.named == {me: 7} and written.mask == 7
    assert mode_of(a) == 0o670  # the group bits are the mask now
    fileattr.apply_one(a, AttrRequest([a], acl_remove={me}))
    assert acl.ACCESS not in os.listxattr(a)
    assert mode_of(a) == 0o640


def test_group_bits_pressed_with_an_acl_change_become_the_mask(tmp_path):
    a = make(tmp_path / "a", 0o640)
    acls_or_skip(a)
    me = ("user", os.getuid())
    fileattr.apply_one(a, AttrRequest([a], acl_set={me: 7}, clear_bits=0o070, set_bits=0o040))
    assert acl.parse(os.getxattr(a, acl.ACCESS)).mask == 4


def test_a_default_acl_goes_to_directories_only_under_recursion(tmp_path):
    d = tmp_path / "d"
    (d / "sub").mkdir(parents=True)
    make(d / "f", 0o644)
    acls_or_skip(d)
    me = ("user", os.getuid())
    request = AttrRequest([d], default_set={me: 5}, recurse=fileattr.ALL)
    assert fileattr.run(request, AttrJob()) == [d]
    for directory in (d, d / "sub"):
        default = acl.parse(os.getxattr(directory, acl.DEFAULT))
        assert default.named == {me: 5}
    assert acl.DEFAULT not in os.listxattr(d / "f")


def test_the_locking_flags_are_cleared_first_and_set_last(tmp_path, monkeypatch):
    from navigator.lib.drives.local import LocalDrive

    a = make(tmp_path / "a", 0o644)
    calls = []
    immutable = fsflags.IMMUTABLE
    state = {"flags": immutable}
    monkeypatch.setattr(LocalDrive, "get_flags", lambda self, where, follow=True: state["flags"])

    def set_flags(self, where, flags, follow=True):
        calls.append(("flags", flags))
        state["flags"] = flags

    monkeypatch.setattr(LocalDrive, "set_flags", set_flags)
    monkeypatch.setattr(LocalDrive, "chmod", lambda self, where, mode: calls.append(("chmod", mode)))
    noatime = fsflags.BY_LETTER["A"]
    fileattr.apply_one(a, AttrRequest([a], set_bits=0o100, flags_clear=immutable, flags_set=noatime))
    assert calls == [("flags", 0), ("chmod", 0o744), ("flags", noatime)]
    calls.clear()
    state["flags"] = 0
    fileattr.apply_one(a, AttrRequest([a], set_bits=0o100, flags_set=immutable))
    assert calls == [("chmod", 0o744), ("flags", immutable)]


def test_flags_are_never_asked_of_a_fifo(tmp_path, monkeypatch):
    from navigator.lib.drives.local import LocalDrive

    fifo = tmp_path / "pipe"
    os.mkfifo(fifo)
    monkeypatch.setattr(LocalDrive, "get_flags", lambda *a, **k: pytest.fail("opened a fifo"))
    fileattr.apply_one(fifo, AttrRequest([fifo], flags_set=fsflags.BY_LETTER["A"]))
    assert not fileattr.survey([fifo]).flags_supported


def test_values_are_spelled_and_read_as_getfattr_writes_them():
    assert fileattr.spell_value(b"hello") == "hello"
    assert fileattr.spell_value(b"\x00\x01") == "0x0001"
    assert fileattr.spell_value(b"0x12") == '"0x12"'
    for value in (b"hello", b"\x00\x01", b"0x12", b'"q"', b""):
        assert fileattr.parse_value(fileattr.spell_value(value)) == value
    assert fileattr.parse_value("0sAAE=") == b"\x00\x01"
    with pytest.raises(ValueError):
        fileattr.parse_value("0xzz")


def test_an_xattr_name_needs_a_namespace_a_file_may_be_given():
    assert fileattr.check_xattr_name(" user.a ") == "user.a"
    for bad in ("", "user.", "plain", "system.posix_acl_access"):
        with pytest.raises(ValueError):
            fileattr.check_xattr_name(bad)
