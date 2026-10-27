"""Deleting files: DOS Navigator's ``ERASER.PAS``.

The model half of F8 and Del, with no widget in it.  :func:`run` is the
worker the file manager starts on a thread, and an :class:`EraseJob` is what
it shares with the loop -- :class:`navigator.lib.system.job.Job`'s *Stop*, pause and one
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
  A refused one may be done again *As root*, and every step after it is
  (:class:`~navigator.lib.file_ops.filecopy.Elevated`; a departure).
* **To the Trash** (``EraseRequest.trash``, not DN's): a source on the disk
  is moved into the freedesktop Trash (:mod:`navigator.lib.file_ops.trash`)
  whole, with nothing asked of what is inside it.  Where there is no trash
  to move it to, :class:`NoTrash` asks whether to erase it instead -- No,
  Yes, All or Cancel -- and *As root* is never offered for the move, so
  nothing of root's lands in the user's trash.
"""

from __future__ import annotations

import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from navigator.lib.drives import Location
from navigator.lib.file_ops.filecopy import Elevated, Failure, error_message, finish_drives, shown
from navigator.lib.system.job import Job, Stopped

#: The answers :class:`NotEmpty` and :class:`ReadOnly` take; ``None`` is Cancel.
NO, YES, ALL = "no", "yes", "all"

#: What the *Erase* box's first line says, DN's ``dlErasingFile`` and ``dlErasingDir``.
ERASING_FILE = "Erasing the file"
ERASING_DIRECTORY = "Erasing the directory"
#: And while a source goes to the Trash.
TRASHING = "Moving to the Trash"


@dataclass
class EraseRequest:
    """What the Delete dialog was accepted with."""

    sources: list[Path | Location]
    #: *Recursive delete*: a non-empty directory goes without being asked about.
    recursive: bool = False
    #: *Move to Trash*: sources on the disk go to the Trash, not away.
    trash: bool = False


@dataclass
class NotEmpty:
    """``dlEraseDirNotEmpty``: *path* has something in it.  No, Yes, All or Cancel."""

    path: Path | Location


@dataclass
class ReadOnly:
    """``dlEraseRO``: the user cannot write *path*.  Yes, No, All or Cancel."""

    path: Path | Location


@dataclass
class NoTrash:
    """*path* could not go to the Trash, *message* says why: erase it?  No, Yes, All or Cancel."""

    path: Path | Location
    message: str


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


def run(request: EraseRequest, job: EraseJob) -> list[Path | Location]:
    """Delete what *request* says; answer the sources that are gone.

    A source skipped, answered No, or with anything left inside it is not in
    the answer -- the file manager untags only what went.  The sources may be
    on any drive (:mod:`navigator.lib.drives`).
    """
    return _Eraser(request, job).run()


class _Eraser(Elevated):
    def __init__(self, request: EraseRequest, job: EraseJob) -> None:
        self.request = request
        self.job = job
        #: DN's ``DeleteAllFiles``: set by an All, and then nothing is asked.
        self.all = False
        #: All to :class:`NoTrash`: what cannot go to the Trash is erased unasked.
        self.erase_untrashable = False

    # -- asking ------------------------------------------------------------------

    def _ask(self, question: Any) -> Any:
        if self.job.stopped:
            raise Stopped
        answer = self.job.ask(question)
        if answer is None or answer is False:
            raise Stopped
        return answer

    def _fail(self, path: Location, message: str) -> bool:
        """Say what went wrong with *path*; False, as a skipped entry is, or stop."""
        self._ask(Failure(shown(path), message))
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

    def run(self) -> list[Path | Location]:
        job = self.job
        done: list[Path | Location] = []
        try:
            counts = [1 if self._trashing(Location.of(source)) else self._measure(Location.of(source))
                      for source in self.request.sources]
            job.total = sum(counts)
            job.measuring = False
            for source, count in zip(self.request.sources, counts):
                before = job.done
                try:
                    if self._source(Location.of(source)):
                        done.append(source)
                finally:
                    # Whatever was skipped inside it, the gauge has passed it.
                    job.done = before + count
            finish_drives(list(self.request.sources), self._fail, self._finish_as_root)
        except Stopped:
            # What went is gone, as it would be from a disk.
            finish_drives(list(self.request.sources), None)
        finally:
            self._release()
        return done

    def _trashing(self, path: Location) -> bool:
        return self.request.trash and path.is_local

    def _measure(self, path: Location) -> int:
        """Entries at and under *path*, never through a link."""
        self._checkpoint()
        drive = self._drive_of(path)
        try:
            if not stat.S_ISDIR(drive.lstat(path).st_mode):
                return 1
            children = drive.children(path)
        except OSError:
            return 1
        count = 1
        for name, st in children:
            if not isinstance(st, OSError) and stat.S_ISDIR(st.st_mode):
                count += self._measure(path / name)
            else:
                count += 1
        return count

    def _source(self, path: Location) -> bool:
        self._checkpoint()
        if self._trashing(path):
            gone = self._to_trash(path)
            if gone is not None:
                return gone
        while True:
            try:
                st = self._drive_of(path).lstat(path)
                break
            except FileNotFoundError:
                return True
            except OSError as error:
                if not self._failed(path, error):
                    return False
        if not stat.S_ISDIR(st.st_mode):
            return self._file(path, st)
        names: list[str] = []

        def listing() -> None:
            names[:] = self._drive_of(path).names(path)

        if not self._try(path, listing):
            return False
        empty = not names
        if not empty and not self.request.recursive and not self._may(NotEmpty(shown(path))):
            return False
        return self._tree(path)

    # -- the parts ---------------------------------------------------------------

    def _to_trash(self, path: Location) -> bool | None:
        """*path* moved to the Trash: True if it went, False if it is kept,
        None if it is to be erased instead."""
        from navigator.lib.file_ops import trash

        job = self.job
        job.action = TRASHING
        job.path = str(path)
        try:
            trash.move(path.local)
        except FileNotFoundError:
            return True
        except OSError as error:
            if not self.erase_untrashable:
                answer = self._ask(NoTrash(shown(path), error_message(error)))
                if answer == ALL:
                    self.erase_untrashable = True
                elif answer != YES:
                    return False
            return None
        job.done += 1
        return True

    def _file(self, path: Location, st: Any) -> bool:
        job = self.job
        job.action = ERASING_FILE
        job.path = str(path)
        if not stat.S_ISLNK(st.st_mode) and not self._drive_of(path).writable(path, st):
            if not self._may(ReadOnly(shown(path))):
                return False
        if not self._try(path, lambda: self._gone(path, "unlink")):
            return False
        job.done += 1
        return True

    def _tree(self, path: Location) -> bool:
        """*path*'s contents, depth first, and then *path*; True if it is gone."""
        children: list[Any] = []

        def listing() -> None:
            children[:] = self._drive_of(path).children(path)

        if not self._try(path, listing):
            return False
        whole = True
        for name, st in children:
            self._checkpoint()
            child = path / name
            if isinstance(st, FileNotFoundError):
                continue
            if isinstance(st, OSError):
                whole = self._fail(child, error_message(st)) and whole
                continue
            if stat.S_ISDIR(st.st_mode):
                whole = self._tree(child) and whole
            else:
                whole = self._file(child, st) and whole
        if not whole:
            return False
        job = self.job
        job.action = ERASING_DIRECTORY
        job.path = str(path)
        if not self._try(path, lambda: self._gone(path, "rmdir")):
            return False
        job.done += 1
        return True

    def _gone(self, path: Location, step: str) -> None:
        """*path* unlinked or removed; already gone is as good."""
        try:
            getattr(self._drive_of(path), step)(path)
        except FileNotFoundError:
            pass


__all__ = [
    "ALL", "ERASING_DIRECTORY", "ERASING_FILE", "EraseJob", "EraseRequest", "NO", "NoTrash", "NotEmpty",
    "ReadOnly", "Stopped", "TRASHING", "YES", "run",
]
