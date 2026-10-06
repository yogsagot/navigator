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


def count_dir_length(path: Path, job: Any = None) -> int | None:
    """The bytes in the files under *path*; None if *job* was stopped.

    *job*, if given, is a :class:`navigator.widgets.editor.loading.FileJob`:
    its ``position`` is kept at the bytes counted so far, for its box.
    """
    total = 0
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
                    else:
                        total += entry.stat(follow_symlinks=False).st_size
                except OSError:
                    continue
        if job is not None:
            job.position = total
    return total
