"""Reading and writing a file for the editor without stopping the loop.

DN's ``ReadBlock`` and ``SaveFile``, each behind ``WriteMsg``.

The file is read and split into lines on a thread
(:func:`navigator.editor.document.read_document`), so the screen keeps
painting and the keyboard keeps answering however large it is.  One that is
still being read after :data:`~navigator.progress.SLOW_PROGRESS_DELAY` puts up
*Reading file*, whose *Cancel* -- and Esc -- stops the read where it is.  One
too large for the memory there is is refused with DN's own message before it
is read, or as soon as its lines say it will not fit.

Writing goes the same way under *Writing file* (:func:`write_in_background`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navigator.editor.document import Document, read_document
from navigator.job import Job, Stopped
from navigator.memory import NotEnoughMemory, edit_budget, out_of_memory
from navigator.progress import SLOW_PROGRESS_DELAY, run_with_progress


class FileJob(Job):
    """A file being read or written: how far it has got, out of how far it goes
    (0 if not known), and whether stopping it half way is safe."""

    def __init__(self) -> None:
        super().__init__()
        self.position = 0
        self.total = 0
        self.cancellable = True


def progress_box(job: FileJob, message: str) -> Any:
    """*Reading file* or *Writing file*, as *job* stands now."""
    from navigator.widgets.file_ops.write_win import WriteWin

    return WriteWin(notice=message, position=job.position, total=job.total,
                    cancellable=job.cancellable)


def refresh_box(job: FileJob):
    """What brings a :func:`progress_box` up to date with *job*."""
    def refresh(box: Any) -> None:
        box.total = job.total
        box.position = job.position
        box.cancellable = job.cancellable

    return refresh


async def read_in_background(app: Any, read: Any, *, message: str = "Reading file") -> Any:
    """Run ``read(job, budget)`` on a thread under *Reading file*.

    Returns what it returns, or None if it was cancelled or would not fit --
    which is said here, as ``OutOfMemory`` was.  ``OSError`` is the caller's.
    """
    job = FileJob()
    budget = edit_budget()
    try:
        return await run_with_progress(
            app, lambda: read(job, budget), job,
            lambda: progress_box(job, message), refresh_box(job),
            delay=SLOW_PROGRESS_DELAY,
        )
    except Stopped:
        return None
    except NotEnoughMemory:
        if app is not None:
            await out_of_memory(app)
        return None


async def load_document(app: Any, path: Path | str, *, new: bool = False) -> Document | None:
    """The text of *path*, read on a thread; None if cancelled or too large.

    With *new*, a file that does not exist is an empty text.  Raises
    ``OSError`` for a file that cannot be read.
    """
    try:
        return await read_in_background(
            app, lambda job, budget: read_document(path, job, budget=budget))
    except FileNotFoundError:
        if not new:
            raise
        return Document()


async def write_in_background(app: Any, write: Any, *, total: int = 0) -> bool:
    """Run ``write(job)`` on a thread under *Writing file*.

    True once written; False if it was cancelled, with the file as it was.
    ``OSError`` is the caller's.  *total* is what ``job.position`` counts up to.
    """
    job = FileJob()
    job.total = total
    try:
        await run_with_progress(
            app, lambda: write(job), job,
            lambda: progress_box(job, "Writing file"), refresh_box(job),
            delay=SLOW_PROGRESS_DELAY,
        )
    except Stopped:
        return False
    return True
