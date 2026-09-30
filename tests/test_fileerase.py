"""F8's model: ``navigator/fileerase.py``, DOS Navigator's ``ERASER.PAS``, with no widgets."""

from __future__ import annotations

import os
import threading
from pathlib import Path

import pytest

from navigator.filecopy import Failure
from navigator.fileerase import (
    ALL,
    NO,
    YES,
    EraseJob,
    EraseRequest,
    NotEmpty,
    ReadOnly,
    run,
)

AS_ROOT = hasattr(os, "geteuid") and os.geteuid() == 0


def erase(sources, *, recursive=False, answers=()):
    """Run the eraser in this thread; answers are taken in order, or by a callable."""
    asked: list = []
    queue = list(answers)

    def asker(question):
        asked.append(question)
        if callable(queue):
            return queue(question)
        return queue.pop(0)

    job = EraseJob(asker=asker)
    done = run(EraseRequest(list(sources), recursive=recursive), job)
    return done, asked, job


@pytest.fixture
def tree(tmp_path):
    """``f.txt``, an empty ``hollow/``, and ``full/`` holding ``a.txt`` and ``sub/b.txt``."""
    (tmp_path / "f.txt").write_text("f")
    (tmp_path / "hollow").mkdir()
    full = tmp_path / "full"
    (full / "sub").mkdir(parents=True)
    (full / "a.txt").write_text("a")
    (full / "sub" / "b.txt").write_text("b")
    return tmp_path


def test_a_file_and_an_empty_directory_go_unasked(tree):
    done, asked, job = erase([tree / "f.txt", tree / "hollow"])
    assert done == [tree / "f.txt", tree / "hollow"]
    assert asked == []
    assert not (tree / "f.txt").exists() and not (tree / "hollow").exists()
    assert (job.done, job.total) == (2, 2)


def test_a_link_to_a_directory_is_unlinked_and_not_entered(tree):
    os.symlink(tree / "full", tree / "link")
    done, asked, _ = erase([tree / "link"])
    assert done == [tree / "link"] and asked == []
    assert not os.path.lexists(tree / "link")
    assert (tree / "full" / "sub" / "b.txt").exists()


def test_a_dangling_link_goes(tree):
    os.symlink(tree / "nowhere", tree / "dangling")
    done, _, _ = erase([tree / "dangling"])
    assert done == [tree / "dangling"] and not os.path.lexists(tree / "dangling")


def test_a_non_empty_directory_asks_and_no_keeps_it(tree):
    done, asked, job = erase([tree / "full", tree / "f.txt"], answers=[NO])
    assert asked == [NotEmpty(tree / "full")]
    assert done == [tree / "f.txt"]
    assert (tree / "full" / "sub" / "b.txt").exists()
    # The gauge passed what No left, so it still reaches the end.
    assert job.done == job.total == 5


def test_yes_deletes_the_whole_tree_without_asking_again(tree):
    done, asked, _ = erase([tree / "full"], answers=[YES])
    assert asked == [NotEmpty(tree / "full")]
    assert done == [tree / "full"] and not (tree / "full").exists()


def test_yes_asks_again_of_the_next_directory_and_all_does_not(tree):
    other = tree / "other"
    other.mkdir()
    (other / "x").write_text("x")
    _, asked, _ = erase([tree / "full", other], answers=[YES, NO])
    assert asked == [NotEmpty(tree / "full"), NotEmpty(other)]
    assert other.exists()

    (tree / "full").mkdir()
    (tree / "full" / "a.txt").write_text("a")
    _, asked, _ = erase([tree / "full", other], answers=[ALL])
    assert asked == [NotEmpty(tree / "full")]
    assert not other.exists()


def test_cancel_stops_everything(tree):
    done, _, _ = erase([tree / "full", tree / "f.txt"], answers=[None])
    assert done == []
    assert (tree / "full").exists() and (tree / "f.txt").exists()


def test_recursive_asks_nothing(tree):
    done, asked, job = erase([tree / "full", tree / "f.txt"], recursive=True)
    assert asked == []
    assert done == [tree / "full", tree / "f.txt"]
    assert (job.done, job.total) == (5, 5)


@pytest.mark.skipif(AS_ROOT, reason="root can write anything")
def test_a_read_only_file_asks_and_all_stops_every_question(tree):
    (tree / "f.txt").chmod(0o444)
    (tree / "full" / "a.txt").chmod(0o444)
    done, asked, _ = erase([tree / "f.txt", tree / "full"], answers=[NO, ALL])
    assert asked == [ReadOnly(tree / "f.txt"), NotEmpty(tree / "full")]
    assert done == [tree / "full"]
    assert (tree / "f.txt").exists()


@pytest.mark.skipif(AS_ROOT, reason="root can write anything")
def test_a_read_only_file_inside_a_tree_is_asked_about(tree):
    (tree / "full" / "sub" / "b.txt").chmod(0o444)
    done, asked, _ = erase([tree / "full"], recursive=True, answers=[NO])
    assert asked == [ReadOnly(tree / "full" / "sub" / "b.txt")]
    # What was kept keeps its directories, and says nothing more about them.
    assert done == []
    assert (tree / "full" / "sub" / "b.txt").exists()
    assert not (tree / "full" / "a.txt").exists()


@pytest.mark.skipif(AS_ROOT, reason="root can write anything")
def test_a_failure_asks_and_skip_goes_on(tree):
    locked = tree / "locked"
    locked.mkdir()
    (locked / "x").write_text("x")
    locked.chmod(0o500)
    try:
        done, asked, _ = erase([locked, tree / "f.txt"], recursive=True, answers=[True])
    finally:
        locked.chmod(0o700)
    assert len(asked) == 1 and isinstance(asked[0], Failure)
    assert asked[0].path == locked / "x"
    assert done == [tree / "f.txt"]
    assert (locked / "x").exists()


def test_stopping_mid_walk_keeps_what_is_left(tree, monkeypatch):
    job = EraseJob()
    real_unlink = os.unlink

    def unlink(path, *args, **kwargs):
        real_unlink(path, *args, **kwargs)
        job.stop()

    monkeypatch.setattr(os, "unlink", unlink)
    done = run(EraseRequest([tree / "full", tree / "f.txt"], recursive=True), job)
    monkeypatch.undo()
    assert done == []
    assert (tree / "full").exists() and (tree / "f.txt").exists()


def test_a_question_crosses_to_the_loop(tree):
    job = EraseJob()
    result: list = []
    worker = threading.Thread(target=lambda: result.append(
        run(EraseRequest([tree / "full"]), job)
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
    assert question == NotEmpty(tree / "full")
    future.set_result(YES)
    worker.join(5)
    assert result == [[tree / "full"]]
    assert not (tree / "full").exists()


def test_a_paused_job_holds_the_worker(tree):
    job = EraseJob()
    job.pause()
    result: list = []
    worker = threading.Thread(target=lambda: result.append(
        run(EraseRequest([tree / "f.txt"]), job)
    ))
    worker.start()
    worker.join(0.3)
    assert worker.is_alive() and (tree / "f.txt").exists()
    job.resume()
    worker.join(5)
    assert result == [[tree / "f.txt"]]
    assert not Path(tree / "f.txt").exists()
