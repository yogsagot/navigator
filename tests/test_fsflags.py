"""Inode flags (``navigator/lib/file_ops/fsflags.py``): ``lsattr``/``chattr``'s."""

from __future__ import annotations

import errno
import os

import pytest

from navigator.lib.file_ops import fsflags


def test_the_grid_holds_twelve_flags_a_user_may_ask_for():
    assert len(fsflags.EDITABLE) == 12 and len(set(fsflags.EDITABLE)) == 12
    assert all(letter in fsflags.BY_LETTER for letter in fsflags.EDITABLE)
    assert "e" not in fsflags.EDITABLE  # extents are the file system's


def test_items_and_flags_convert_both_ways():
    flags = fsflags.BY_LETTER["i"] | fsflags.BY_LETTER["A"]
    assert fsflags.from_items(fsflags.to_items(flags)) == flags
    assert fsflags.to_items(fsflags.BY_LETTER["e"]) == 0


def test_lsattr_spells_the_flags_with_a_question_mark_for_mixed():
    flags = fsflags.BY_LETTER["i"] | fsflags.BY_LETTER["e"]
    text = fsflags.lsattr(flags, fsflags.BY_LETTER["A"])
    assert len(text) == len(fsflags.FLAGS)
    assert text == "----i--?------e------"


def _flags_or_skip(path):
    try:
        return fsflags.get_flags(path)
    except OSError as error:
        if fsflags.unsupported(error):
            pytest.skip("this file system has no inode flags")
        raise


def test_a_flag_set_reads_back(tmp_path):
    path = tmp_path / "f"
    path.write_text("x")
    before = _flags_or_skip(path)
    try:
        fsflags.set_flags(path, before | fsflags.BY_LETTER["A"])
    except OSError as error:
        if fsflags.unsupported(error):
            pytest.skip("this file system will not set no-atime")
        raise
    assert fsflags.get_flags(path) & fsflags.BY_LETTER["A"]
    fsflags.set_flags(path, before)
    assert fsflags.get_flags(path) == before


def test_a_fifo_is_never_opened(tmp_path):
    fifo = tmp_path / "pipe"
    os.mkfifo(fifo)
    with pytest.raises(OSError) as raised:
        fsflags.get_flags(fifo)
    assert raised.value.errno == errno.ENOTTY and fsflags.unsupported(raised.value)


def test_a_link_is_not_followed_unless_asked(tmp_path):
    target = tmp_path / "f"
    target.write_text("x")
    (tmp_path / "link").symlink_to(target)
    _flags_or_skip(target)
    with pytest.raises(OSError):
        fsflags.get_flags(tmp_path / "link", follow=False)
    assert fsflags.get_flags(tmp_path / "link") == fsflags.get_flags(target)
