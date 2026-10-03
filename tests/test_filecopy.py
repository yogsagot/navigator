"""The copy engine behind F5 and F6: ``navigator/filecopy.py``.

Driven on a thread-free path: a :class:`CopyJob` given an ``asker`` answers
its questions in the worker's own call, so every rule can be exercised on
``tmp_path`` without a loop.
"""

from __future__ import annotations

import errno
import os
import threading
from pathlib import Path

import pytest

from navigator import filecopy
from navigator.filecopy import (
    APPEND, ASK, CHECK_FREE, FOLLOW_LINKS, MOVE, OVERWRITE, PRESERVE, REFRESH, SKIP,
    CopyJob, CopyRequest, CreateDirectory, Failure, NoRoom, Overwrite, OverwriteAnswer,
    apply_mask, resolve_target, run,
)


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def copy(sources, target, *, cwd, mode=ASK, options=PRESERVE, answers=None, flush=False):
    """Run a copy; *answers* is a callable or a list consumed in order."""
    asked: list = []

    def asker(question):
        asked.append(question)
        if callable(answers):
            return answers(question)
        return answers.pop(0) if answers else None

    job = CopyJob(asker=asker)
    done = run(CopyRequest(list(sources), str(target), mode, options, flush), job, cwd)
    return done, asked, job


@pytest.fixture
def tree(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    dst.mkdir()
    write(src / "a.txt", "alpha")
    write(src / "b.txt", "beta")
    write(src / "sub" / "c.txt", "gamma")
    return src, dst


# -- the target ---------------------------------------------------------------------


def test_mask_renames_part_by_part():
    assert apply_mask("report.txt", "*.bak") == "report.bak"
    assert apply_mask("readme", "*.bak") == "readme.bak"
    assert apply_mask("abc.txt", "x?*.*") == "xbc.txt"
    assert apply_mask("abc.txt", "*") == "abc.txt"
    assert apply_mask("a.tar.gz", "*.*") == "a.tar.gz"


def test_target_directory_name_and_mask(tree, tmp_path):
    src, dst = tree
    one = [src / "a.txt"]
    assert resolve_target(str(dst), one, tmp_path).path_for(one[0]) == dst / "a.txt"
    assert resolve_target("dst", one, tmp_path).path_for(one[0]) == dst / "a.txt"
    renamed = resolve_target(str(dst / "z.txt"), one, tmp_path)
    assert renamed.path_for(one[0]) == dst / "z.txt" and not renamed.create
    masked = resolve_target(str(dst / "*.bak"), one, tmp_path)
    assert masked.path_for(one[0]) == dst / "a.bak"
    many = [src / "a.txt", src / "b.txt"]
    new = resolve_target(str(dst / "new"), many, tmp_path)
    assert new.create and new.path_for(many[0]) == dst / "new" / "a.txt"
    assert resolve_target(str(dst / "slash") + "/", one, tmp_path).create


# -- copying ---------------------------------------------------------------------------


def test_copies_files_and_directories(tree, tmp_path):
    src, dst = tree
    sources = [src / "a.txt", src / "sub"]
    done, asked, job = copy(sources, dst, cwd=tmp_path)
    assert done == sources and not asked
    assert (dst / "a.txt").read_text() == "alpha"
    assert (dst / "sub" / "c.txt").read_text() == "gamma"
    assert (src / "a.txt").exists()
    assert job.total_bytes == job.done_bytes == len("alpha") + len("gamma")


def test_one_file_to_a_new_name(tree, tmp_path):
    src, dst = tree
    copy([src / "a.txt"], dst / "renamed.txt", cwd=tmp_path)
    assert (dst / "renamed.txt").read_text() == "alpha"


def test_several_files_to_a_new_directory_ask_first(tree, tmp_path):
    src, dst = tree
    done, asked, _ = copy(
        [src / "a.txt", src / "b.txt"], dst / "fresh", cwd=tmp_path, answers=[True]
    )
    assert isinstance(asked[0], CreateDirectory)
    assert sorted(p.name for p in (dst / "fresh").iterdir()) == ["a.txt", "b.txt"]
    assert len(done) == 2


def test_declining_the_new_directory_copies_nothing(tree, tmp_path):
    src, dst = tree
    done, _, _ = copy([src / "a.txt", src / "b.txt"], dst / "fresh", cwd=tmp_path, answers=[False])
    assert done == [] and not (dst / "fresh").exists()


def test_mask_target(tree, tmp_path):
    src, dst = tree
    copy([src / "a.txt", src / "b.txt"], f"{dst}/*.bak", cwd=tmp_path)
    assert sorted(p.name for p in dst.iterdir()) == ["a.bak", "b.bak"]


# -- the five modes --------------------------------------------------------------------


@pytest.fixture
def clash(tree):
    src, dst = tree
    write(dst / "a.txt", "old")
    return src, dst


def test_overwrite_mode(clash, tmp_path):
    src, dst = clash
    copy([src / "a.txt"], dst, cwd=tmp_path, mode=OVERWRITE)
    assert (dst / "a.txt").read_text() == "alpha"


def test_append_mode(clash, tmp_path):
    src, dst = clash
    copy([src / "a.txt"], dst, cwd=tmp_path, mode=APPEND)
    assert (dst / "a.txt").read_text() == "oldalpha"


def test_skip_mode(clash, tmp_path):
    src, dst = clash
    done, asked, _ = copy([src / "a.txt"], dst, cwd=tmp_path, mode=SKIP)
    assert (dst / "a.txt").read_text() == "old" and done == [] and not asked


def test_refresh_copies_only_over_older(clash, tmp_path):
    src, dst = clash
    os.utime(dst / "a.txt", (1, 1))
    write(dst / "b.txt", "newer")
    os.utime(src / "b.txt", (1, 1))
    copy([src / "a.txt", src / "b.txt"], dst, cwd=tmp_path, mode=REFRESH)
    assert (dst / "a.txt").read_text() == "alpha"
    assert (dst / "b.txt").read_text() == "newer"


def test_ask_is_asked_per_file(clash, tmp_path):
    src, dst = clash
    write(dst / "b.txt", "old b")
    done, asked, _ = copy(
        [src / "a.txt", src / "b.txt"], dst, cwd=tmp_path,
        answers=[OverwriteAnswer("overwrite"), OverwriteAnswer("skip")],
    )
    assert [type(q) for q in asked] == [Overwrite, Overwrite]
    assert asked[0].source_size == 5 and asked[0].dest_size == 3
    assert (dst / "a.txt").read_text() == "alpha"
    assert (dst / "b.txt").read_text() == "old b"
    assert done == [src / "a.txt"]


def test_ask_for_all_stands_for_the_rest(clash, tmp_path):
    src, dst = clash
    write(dst / "b.txt", "old b")
    _, asked, _ = copy(
        [src / "a.txt", src / "b.txt"], dst, cwd=tmp_path,
        answers=[OverwriteAnswer("append", all=True)],
    )
    assert len(asked) == 1
    assert (dst / "b.txt").read_text() == "old bbeta"


def test_ask_rename_retries_under_the_new_name(clash, tmp_path):
    src, dst = clash
    write(dst / "taken.txt", "taken")
    _, asked, _ = copy(
        [src / "a.txt"], dst, cwd=tmp_path,
        answers=[
            OverwriteAnswer("rename", all=True, name="taken.txt"),
            OverwriteAnswer("rename", name="free.txt"),
        ],
    )
    assert len(asked) == 2 and asked[1].dest == dst / "taken.txt"
    assert (dst / "free.txt").read_text() == "alpha"
    assert (dst / "taken.txt").read_text() == "taken"


def test_cancel_stops_everything(clash, tmp_path):
    src, dst = clash
    done, _, _ = copy([src / "a.txt", src / "b.txt"], dst, cwd=tmp_path, answers=[None])
    assert done == [] and not (dst / "b.txt").exists()


def test_a_directory_in_the_way_is_refused(tree, tmp_path):
    src, dst = tree
    (dst / "a.txt").mkdir()
    done, asked, _ = copy([src / "a.txt"], dst, cwd=tmp_path, mode=OVERWRITE, answers=[True])
    assert isinstance(asked[0], Failure) and done == []


# -- refusals --------------------------------------------------------------------------


def test_a_file_onto_itself(tree, tmp_path):
    src, _ = tree
    done, asked, _ = copy([src / "a.txt"], src, cwd=tmp_path, mode=OVERWRITE, answers=[True])
    assert "itself" in asked[0].message and done == []
    assert (src / "a.txt").read_text() == "alpha"


def test_a_directory_into_itself(tree, tmp_path):
    src, _ = tree
    done, asked, _ = copy([src], src / "sub", cwd=tmp_path, answers=[True])
    assert "into itself" in asked[0].message and done == []


# -- moving ----------------------------------------------------------------------------


def test_move_renames(tree, tmp_path):
    src, dst = tree
    done, _, job = copy([src / "a.txt", src / "sub"], dst, cwd=tmp_path, options=MOVE)
    assert len(done) == 2
    assert not (src / "a.txt").exists() and not (src / "sub").exists()
    assert (dst / "sub" / "c.txt").read_text() == "gamma"
    assert job.done_bytes == job.total_bytes


def test_move_across_filesystems_copies_then_deletes(tree, tmp_path, monkeypatch):
    src, dst = tree

    def cross(*args, **kwargs):
        raise OSError(errno.EXDEV, "Invalid cross-device link")

    monkeypatch.setattr(filecopy.os, "rename", cross)
    monkeypatch.setattr(filecopy.os, "replace", cross)
    done, asked, _ = copy([src / "a.txt", src / "sub"], dst, cwd=tmp_path, options=MOVE)
    assert not asked and len(done) == 2
    assert not (src / "a.txt").exists() and not (src / "sub").exists()
    assert (dst / "sub" / "c.txt").read_text() == "gamma"


def test_flush_syncs_each_file_written_and_only_when_asked(tree, tmp_path, monkeypatch):
    src, dst = tree
    synced = []
    real = os.fsync
    monkeypatch.setattr(filecopy.os, "fsync", lambda fd: synced.append(fd) or real(fd))
    copy([src / "a.txt"], dst, cwd=tmp_path)
    assert synced == []
    copy([src / "b.txt", src / "sub"], dst, cwd=tmp_path, flush=True)
    assert len(synced) == 2


def test_a_failed_sync_fails_the_file_and_a_move_keeps_its_source(tree, tmp_path, monkeypatch):
    src, dst = tree

    def cross(*args, **kwargs):
        raise OSError(errno.EXDEV, "Invalid cross-device link")

    def broken(fd):
        raise OSError(errno.EIO, "Input/output error")

    monkeypatch.setattr(filecopy.os, "replace", cross)
    monkeypatch.setattr(filecopy.os, "fsync", broken)
    done, asked, _ = copy([src / "a.txt"], dst, cwd=tmp_path, options=MOVE, flush=True,
                          answers=lambda q: True)
    assert done == [] and isinstance(asked[0], filecopy.Failure)
    assert (src / "a.txt").exists() and not (dst / "a.txt").exists()


def test_a_file_system_that_cannot_sync_still_copies(tree, tmp_path, monkeypatch):
    src, dst = tree

    def unsupported(fd):
        raise OSError(errno.EINVAL, "Invalid argument")

    monkeypatch.setattr(filecopy.os, "fsync", unsupported)
    done, asked, _ = copy([src / "a.txt"], dst, cwd=tmp_path, flush=True)
    assert done == [src / "a.txt"] and not asked


def test_move_keeps_a_source_that_was_skipped(clash, tmp_path):
    src, dst = clash
    done, _, _ = copy([src / "a.txt"], dst, cwd=tmp_path, mode=SKIP, options=MOVE)
    assert done == [] and (src / "a.txt").exists()


# -- links and attributes --------------------------------------------------------------


def test_a_link_is_recreated(tree, tmp_path):
    src, dst = tree
    os.symlink("a.txt", src / "link")
    copy([src / "link"], dst, cwd=tmp_path)
    assert (dst / "link").is_symlink() and os.readlink(dst / "link") == "a.txt"


def test_a_link_is_followed(tree, tmp_path):
    src, dst = tree
    os.symlink(src / "a.txt", src / "link")
    copy([src / "link"], dst, cwd=tmp_path, options=FOLLOW_LINKS)
    assert not (dst / "link").is_symlink() and (dst / "link").read_text() == "alpha"


def test_a_followed_loop_is_refused(tree, tmp_path):
    src, dst = tree
    os.symlink(src, src / "sub" / "back")
    done, asked, _ = copy([src], dst, cwd=tmp_path, options=FOLLOW_LINKS, answers=lambda q: True)
    assert any(isinstance(q, Failure) and "loops" in q.message for q in asked)
    assert (dst / "src" / "sub" / "c.txt").exists()


def test_preserve_keeps_mode_and_time(tree, tmp_path):
    src, dst = tree
    os.chmod(src / "a.txt", 0o640)
    os.utime(src / "a.txt", (1_000_000, 1_000_000))
    copy([src / "a.txt"], dst, cwd=tmp_path, options=PRESERVE)
    st = os.stat(dst / "a.txt")
    assert st.st_mtime == 1_000_000 and st.st_mode & 0o777 == 0o640


def test_without_preserve_the_time_is_now(tree, tmp_path):
    src, dst = tree
    os.utime(src / "a.txt", (1_000_000, 1_000_000))
    copy([src / "a.txt"], dst, cwd=tmp_path, options=0)
    assert os.stat(dst / "a.txt").st_mtime > 1_000_000


# -- free space, stopping, and the loop's side of a question -------------------------------


def test_not_enough_room_asks(tree, tmp_path, monkeypatch):
    src, dst = tree
    monkeypatch.setattr(filecopy, "_free_space", lambda directory: 2)
    done, asked, _ = copy(
        [src / "a.txt", src / "b.txt"], dst, cwd=tmp_path, options=CHECK_FREE,
        answers=[True, False],
    )
    assert [type(q) for q in asked] == [NoRoom, NoRoom]
    assert done == [] and not list(dst.iterdir())


def test_stop_leaves_no_partial_file(tree, tmp_path, monkeypatch):
    src, dst = tree
    write(src / "big", "x" * 64)
    monkeypatch.setattr(filecopy, "CHUNK", 8)
    job = CopyJob()
    reads = 0
    real_open = open

    class Slow:
        def __init__(self, f):
            self.f = f

        def __enter__(self):
            return self

        def __exit__(self, *a):
            self.f.close()

        def read(self, n):
            nonlocal reads
            reads += 1
            if reads == 3:
                job.stop()
            return self.f.read(n)

    monkeypatch.setattr(filecopy, "open", lambda p, m: Slow(real_open(p, m)), raising=False)
    done = run(CopyRequest([src / "big", src / "a.txt"], str(dst), OVERWRITE, 0), job, tmp_path)
    assert done == [] and not (dst / "big").exists() and not (dst / "a.txt").exists()


def test_a_question_crosses_to_the_loop(clash, tmp_path):
    src, dst = clash
    job = CopyJob()
    result: list = []
    worker = threading.Thread(target=lambda: result.append(
        run(CopyRequest([src / "a.txt"], str(dst)), job, tmp_path)
    ))
    worker.start()
    pending = None
    for _ in range(200):
        pending = job.take_question()
        if pending:
            break
        threading.Event().wait(0.01)
    assert pending is not None
    question, future = pending
    assert isinstance(question, Overwrite)
    future.set_result(OverwriteAnswer("overwrite"))
    worker.join(5)
    assert result == [[src / "a.txt"]]
    assert (dst / "a.txt").read_text() == "alpha"


def test_stopping_while_a_question_waits_ends_the_worker(clash, tmp_path):
    src, dst = clash
    job = CopyJob()
    worker = threading.Thread(target=lambda: run(CopyRequest([src / "a.txt"], str(dst)), job, tmp_path))
    worker.start()
    for _ in range(200):
        if job._pending is not None:
            break
        threading.Event().wait(0.01)
    job.stop()
    worker.join(5)
    assert not worker.is_alive()


def test_a_paused_job_holds_the_worker(tree, tmp_path):
    src, dst = tree
    job = CopyJob()
    job.pause()
    result: list = []
    worker = threading.Thread(target=lambda: result.append(
        run(CopyRequest([src / "a.txt"], str(dst), OVERWRITE, 0), job, tmp_path)
    ))
    worker.start()
    worker.join(0.3)
    assert worker.is_alive() and not (dst / "a.txt").exists()
    job.resume()
    worker.join(5)
    assert result == [[src / "a.txt"]]
