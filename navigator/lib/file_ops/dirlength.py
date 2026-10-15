"""How many bytes a directory holds: DN's ``CountDirLen`` (DISKINFO.PAS).

The sizes of every file beneath it, however deep, which is what Alt+G puts
in a directory's size column (``cmCountLen``).  It touches nothing but the
file system, so it runs on a thread, and a *job* stopped meanwhile -- Esc in
its box, as DN's loop looked for Esc every few ticks -- ends it with None.

Three departures, each because DOS had no such thing to count:

- **Dot-files count.**  DN passed over every name starting with ``.``, which
  on DOS was only ``.`` and ``..``; ``os.scandir`` gives neither, and a
  ``.git`` is as much of the directory's size as anything else in it.
- **A symbolic link counts as itself**, never as what it points at: a link
  to a directory is not walked into, so a link pointing back up cannot loop,
  and a file outside is not counted for being linked to.
- **A directory that cannot be read counts as nothing** and the rest goes
  on, where DN's ``FindFirst`` failing there ended that branch the same way.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from navigator.lib.system.job import Job


class CountJob(Job):
    """Directories being counted, as their box shows them: which one is being
    counted now, what has been met in it (``here_*``), and what has been met
    so far across every one counted (``position``, ``files``, ``directories``)."""

    def __init__(self) -> None:
        super().__init__()
        self.current = ""
        self.here_size = 0
        self.here_files = 0
        self.here_directories = 0
        self.position = 0
        self.files = 0
        self.directories = 0


def count_dir_length(path: Path, job: Any = None) -> int | None:
    """The bytes in the files under *path*; None if *job* was stopped.

    *job*, if given, is anything with ``stopped``.  A :class:`CountJob` has
    its ``here_*`` started again for *path*, and what was met here added to
    its totals, so one job can count several directories in turn.
    """
    counter = job if isinstance(job, CountJob) else None
    total = files = directories = 0
    if counter is not None:
        base = (counter.position, counter.files, counter.directories)
        counter.here_size = counter.here_files = counter.here_directories = 0
    pending = [os.fspath(path)]
    while pending:
        if job is not None and job.stopped:
            return None
        directory = pending.pop()
        try:
            scan = os.scandir(directory)
        except OSError:
            continue
        with scan:
            for entry in scan:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(entry.path)
                        directories += 1
                    else:
                        total += entry.stat(follow_symlinks=False).st_size
                        files += 1
                except OSError:
                    continue
        if counter is not None:
            counter.here_size, counter.here_files, counter.here_directories = total, files, directories
            counter.position = base[0] + total
            counter.files = base[1] + files
            counter.directories = base[2] + directories
    return total
