"""Deleting files: DOS Navigator's ``ERASER.PAS``.

The model half of F8 and Del, with no widget in it.  :func:`run` is the
worker the file manager starts on a thread, and an :class:`EraseJob` is what
it shares with the loop -- :class:`navigator.job.Job`'s *Stop*, pause and one
question at a time, and the progress fields the *Erase* box reads.

What is DN's and what is not:

* **An empty directory goes unasked**, as ``DeleteDirectory`` let one go.
* **A non-empty one asks** ``Directory X is not empty. Do you wish to delete
  it?`` -- No, Yes, All, Cancel -- unless the request is *recursive*, which is
  the Delete dialog's own check box and a departure: it answers All before
  anything is asked.
* **A file the user cannot write asks** ``File X is write-protected. OK to
  delete it?`` (``cfEraseReadonly``) -- Yes, No, All.  Linux has no read-only
  attribute, so *cannot write* is the reading of it, which is also what makes
  ``rm`` ask about a *write-protected* file, and its word replaces DN's
  *marked as Read-Only*.  DN asked it only of the files it
  was given; this asks it inside a directory too, since a tree is where such a
  file hides.
* **All is one flag**, as DN's ``DeleteAllFiles`` was: once given to either
  question, neither is asked again.
* **A symbolic link is never followed.**  A link to a directory is unlinked,
  and what it points at is left alone.
* **A failure asks whether to skip**, where DN showed an OK box for a file
  and gave up the whole run for a directory.  A directory something was kept
  in is left where it is, without a second complaint about its ``rmdir``.
"""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from navigator.filecopy import Failure, error_message
from navigator.job import Job, Stopped

#: The answers :class:`NotEmpty` and :class:`ReadOnly` take; ``None`` is Cancel.
NO, YES, ALL = "no", "yes", "all"

#: What the *Erase* box's first line says, DN's ``dlErasingFile`` and ``dlErasingDir``.
ERASING_FILE = "Erasing the file"
ERASING_DIRECTORY = "Erasing the directory"


@dataclass
class EraseRequest:
    """What the Delete dialog was accepted with."""

    sources: list[Path]
    #: *Recursive delete*: a non-empty directory goes without being asked about.
    recursive: bool = False


@dataclass
class NotEmpty:
    """``dlEraseDirNotEmpty``: *path* has something in it.  No, Yes, All or Cancel."""

    path: Path


@dataclass
class ReadOnly:
    """``dlEraseRO``: the user cannot write *path*.  Yes, No, All or Cancel."""

    path: Path


class EraseJob(Job):
    """A running erase, as the thread doing it and the loop watching it see it."""

    def __init__(self, asker: Callable[[Any], Any] | None = None) -> None:
        super().__init__(asker)
        #: Entries under every source, the sources included, once measured.
        self.total = 0
        #: Entries dealt with -- removed, or passed over by a skip or a No.
        self.done = 0
        #: ``ERASING_FILE`` or ``ERASING_DIRECTORY``, and the entry in hand.
        self.action = ""
        self.path = ""
        #: True while the sources are being counted.
        self.measuring = True


def run(request: EraseRequest, job: EraseJob) -> list[Path]:
    """Delete what *request* says; answer the sources that are gone.

    A source skipped, answered No, or with anything left inside it is not in
    the answer -- the file manager untags only what went.
    """
    return _Eraser(request, job).run()


class _Eraser:
    def __init__(self, request: EraseRequest, job: EraseJob) -> None:
        self.request = request
        self.job = job
        #: DN's ``DeleteAllFiles``: set by an All, and then nothing is asked.
        self.all = False

    # -- asking ------------------------------------------------------------------

    def _ask(self, question: Any) -> Any:
        if self.job.stopped:
            raise Stopped
        answer = self.job.ask(question)
        if answer is None or answer is False:
            raise Stopped
        return answer

    def _fail(self, path: Path, message: str) -> bool:
        """Say what went wrong with *path*; False, as a skipped entry is, or stop."""
        self._ask(Failure(path, message))
        return False

    def _may(self, question: NotEmpty | ReadOnly) -> bool:
        """Ask *question* unless All was given; True to go ahead."""
        if self.all:
            return True
        answer = self._ask(question)
        if answer == ALL:
            self.all = True
            return True
        return answer == YES

    def _checkpoint(self) -> None:
        self.job.wait_while_paused()
        if self.job.stopped:
            raise Stopped

    # -- the whole ---------------------------------------------------------------

    def run(self) -> list[Path]:
        job = self.job
        done: list[Path] = []
        try:
            counts = [self._measure(source) for source in self.request.sources]
            job.total = sum(counts)
            job.measuring = False
            for source, count in zip(self.request.sources, counts):
                before = job.done
                try:
                    if self._source(source):
                        done.append(source)
                finally:
                    # Whatever was skipped inside it, the gauge has passed it.
                    job.done = before + count
        except Stopped:
            pass
        return done

    def _measure(self, path: Path) -> int:
        """Entries at and under *path*, never through a link."""
        self._checkpoint()
        try:
            if not stat.S_ISDIR(os.lstat(path).st_mode):
                return 1
            with os.scandir(path) as entries:
                children = list(entries)
        except OSError:
            return 1
        count = 1
        for child in children:
            if child.is_dir(follow_symlinks=False):
                count += self._measure(Path(child.path))
            else:
                count += 1
        return count

    def _source(self, path: Path) -> bool:
        self._checkpoint()
        try:
            st = os.lstat(path)
        except FileNotFoundError:
            return True
        except OSError as error:
            return self._fail(path, error_message(error))
        if not stat.S_ISDIR(st.st_mode):
            return self._file(path, st)
        try:
            with os.scandir(path) as entries:
                empty = next(entries, None) is None
        except OSError as error:
            return self._fail(path, error_message(error))
        if not empty and not self.request.recursive and not self._may(NotEmpty(path)):
            return False
        return self._tree(path)

    # -- the parts ---------------------------------------------------------------

    def _file(self, path: Path, st: os.stat_result) -> bool:
        job = self.job
        job.action = ERASING_FILE
        job.path = str(path)
        if not stat.S_ISLNK(st.st_mode) and not os.access(path, os.W_OK):
            if not self._may(ReadOnly(path)):
                return False
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
        except OSError as error:
            return self._fail(path, error_message(error))
        job.done += 1
        return True

    def _tree(self, path: Path) -> bool:
        """*path*'s contents, depth first, and then *path*; True if it is gone."""
        try:
            with os.scandir(path) as entries:
                children = list(entries)
        except OSError as error:
            return self._fail(path, error_message(error))
        whole = True
        for child in children:
            self._checkpoint()
            try:
                st = child.stat(follow_symlinks=False)
            except FileNotFoundError:
                continue
            except OSError as error:
                whole = self._fail(Path(child.path), error_message(error)) and whole
                continue
            if stat.S_ISDIR(st.st_mode):
                whole = self._tree(Path(child.path)) and whole
            else:
                whole = self._file(Path(child.path), st) and whole
        if not whole:
            return False
        job = self.job
        job.action = ERASING_DIRECTORY
        job.path = str(path)
        try:
            os.rmdir(path)
        except FileNotFoundError:
            pass
        except OSError as error:
            return self._fail(path, error_message(error))
        job.done += 1
        return True


__all__ = [
    "ALL", "ERASING_DIRECTORY", "ERASING_FILE", "EraseJob", "EraseRequest", "NO", "NotEmpty",
    "ReadOnly", "Stopped", "YES", "run",
]
