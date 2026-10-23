"""What git thinks of the directory a panel shows: a letter per entry and
the branch for the title.

**A departure from DOS Navigator**, which knew no version control.  Asked
for: a panel in a work tree marks each entry it lists -- ``M`` modified,
``A`` added, ``D`` deleted, ``R`` renamed, ``?`` untracked, ``!`` ignored,
``U`` conflicted -- and names the branch, with how far it is ahead of and
behind its upstream.

Read by running ``git`` itself (no library, nothing to install), on a
thread, behind ``[file_manager] git_status``.  **``GIT_OPTIONAL_LOCKS=0``**
keeps ``git status`` from refreshing the index: a read never takes
``index.lock`` from under the user's own command, and never writes into the
``.git`` directory the panel watches for that command's changes -- which
would otherwise read again, for ever.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

#: How long one ``git`` may take before the panel does without it.
TIMEOUT = 5.0

#: Which letter a directory takes from the entries beneath it, the first
#: found winning.  ``!`` is not here: an ignored file deep down says nothing
#: of its directory.
PRIORITY = "UMDRA?"

#: The letters and the stylesheet classes that colour them (``Panel::git``).
CLASSES = {
    "M": "modified", "A": "added", "D": "deleted", "R": "renamed",
    "?": "untracked", "!": "ignored", "U": "conflict",
}


@dataclass(frozen=True)
class GitState:
    """One read of a directory in a work tree."""

    #: The branch checked out, or a short commit id with HEAD detached.
    branch: str
    detached: bool = False
    ahead: int = 0
    behind: int = 0
    #: The repository's git directory, whose index and HEAD change with the
    #: user's ``git add``, ``commit`` and ``checkout``.
    git_dir: Path | None = None
    #: An entry's name in the directory read -> its letter.
    marks: dict[str, str] = field(default_factory=dict)


def _git(path: Path, *args: str) -> subprocess.CompletedProcess[bytes] | None:
    env = dict(os.environ, LC_ALL="C", GIT_OPTIONAL_LOCKS="0")
    try:
        return subprocess.run(
            ["git", "-C", str(path), *args], stdin=subprocess.DEVNULL,
            capture_output=True, timeout=TIMEOUT, env=env, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None  # no git, or one that hangs


def _letter(xy: str) -> str:
    """``git status``' two columns as one letter: the work tree's change if
    it has one, else the index's."""
    code = xy[1] if xy[1] != "." else xy[0]
    return {"C": "R", "T": "M"}.get(code, code)


def _stronger(old: str | None, new: str) -> str:
    if old is None or old not in PRIORITY:
        return new
    if new not in PRIORITY:
        return old
    return new if PRIORITY.index(new) < PRIORITY.index(old) else old


def parse(output: bytes, prefix: str) -> tuple[dict[str, str], dict[str, str]]:
    """``git status --porcelain=v2 -z --branch``'s *output*, read for the
    directory at *prefix* in the work tree: its ``# branch.*`` headers, and
    each entry's letter by its name there.

    A path below a subdirectory marks the subdirectory, with the strongest
    letter beneath it (:data:`PRIORITY`).  A path ending in ``/`` is a whole
    directory untracked or ignored.
    """
    headers: dict[str, str] = {}
    marks: dict[str, str] = {}
    records = output.decode("utf-8", errors="surrogateescape").split("\0")
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        kind = record[0]
        if kind == "#":
            key, _, value = record[2:].partition(" ")
            headers[key] = value
            continue
        if kind == "1":
            # 1 XY sub mH mI mW hH hI path
            parts = record.split(" ", 8)
            letter, path = _letter(parts[1]), parts[8]
        elif kind == "2":
            # 2 XY sub mH mI mW hH hI Xscore path, then the original path
            parts = record.split(" ", 9)
            letter, path = _letter(parts[1]), parts[9]
            index += 1
        elif kind == "u":
            letter, path = "U", record.split(" ", 10)[10]
        elif kind in "?!":
            letter, path = kind, record[2:]
        else:
            continue
        if not path.startswith(prefix):
            continue
        rest = path[len(prefix):]
        name, slash, below = rest.partition("/")
        if not name:
            continue
        if slash and below:
            if letter == "!":
                continue  # an ignored file inside says nothing of its directory
            marks[name] = _stronger(marks.get(name), letter)
        else:
            marks[name] = _stronger(marks.get(name), letter) if name in marks else letter
    return headers, marks


def read(path: Path) -> GitState | None:
    """What git says of *path*, or None: not in a work tree (or inside a
    ``.git``), no ``git``, or one that did not answer in :data:`TIMEOUT`.

    Touches nothing but the disk and a child process, so a thread may run it.
    """
    where = _git(path, "rev-parse", "--is-inside-work-tree", "--show-prefix", "--absolute-git-dir")
    if where is None or where.returncode != 0:
        return None
    lines = where.stdout.decode("utf-8", errors="surrogateescape").splitlines()
    if len(lines) < 3 or lines[0] != "true":
        return None
    prefix, git_dir = lines[1], Path(lines[2])
    status = _git(path, "status", "--porcelain=v2", "-z", "--branch",
                  "--untracked-files=normal", "--ignored=matching", "--", ".")
    if status is None or status.returncode != 0:
        return None
    headers, marks = parse(status.stdout, prefix)
    head = headers.get("branch.head", "")
    detached = head in ("", "(detached)")
    branch = headers.get("branch.oid", "")[:7] if detached else head
    ahead = behind = 0
    counts = headers.get("branch.ab", "").split()
    if len(counts) == 2:
        try:
            ahead, behind = int(counts[0]), -int(counts[1])
        except ValueError:
            pass
    return GitState(branch, detached, ahead, behind, git_dir, marks)


__all__ = ["CLASSES", "GitState", "PRIORITY", "parse", "read"]
