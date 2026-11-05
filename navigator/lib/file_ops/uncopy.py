"""Undoing a copy: what it made, checked to be as it left it.

File > Undo takes a copy back by removing what it made
(:class:`navigator.lib.file_ops.undo.Copied`) -- but only what is still
exactly that: a file the same type, size and modification time
(:func:`fingerprint`), a directory holding the very files the copy put there
and nothing else (:func:`manifest`).  Anything changed since is kept; Undo
never removes work done after the copy.  The removing itself is the eraser's
(the Trash on the disk); this module only reads.

A directory's manifest is kept for the session, a few dozen bytes a file;
past :data:`MANIFEST_LIMIT` entries it is not kept (``None``) and the
directory is never taken back -- as if changed.

:func:`check` blocks on the drives and runs on a thread.
"""

from __future__ import annotations

import posixpath
import stat
from typing import Any, Callable

#: The most entries a copied directory's manifest holds.
MANIFEST_LIMIT = 100_000

#: The kind a directory has in a manifest.
DIR = "dir"


def fingerprint(st: Any) -> tuple[int, int, float]:
    """A file's or a link's type, size and modification time."""
    return stat.S_IFMT(st.st_mode), st.st_size, st.st_mtime


def collapse(dest: Any, children: list[tuple[Any, Any]]) -> tuple[str, frozenset | None]:
    """A directory's fingerprint from its children's records: every file,
    link and directory under it by its path relative to it."""
    entries: set[tuple[Any, ...]] = set()
    base = str(dest.path)
    for child, fp in children:
        rel = posixpath.relpath(str(child.path), base)
        if fp[0] == DIR:
            if fp[1] is None:
                return DIR, None
            entries.add((rel, DIR))
            entries.update((posixpath.join(rel, entry[0]), *entry[1:]) for entry in fp[1])
        else:
            entries.add((rel, *fp))
        if len(entries) > MANIFEST_LIMIT:
            return DIR, None
    return DIR, frozenset(entries)


def manifest(drive: Any, location: Any) -> frozenset:
    """What is under the directory *location* now, as :func:`collapse` has it;
    links are not followed."""
    entries: set[tuple[Any, ...]] = set()
    stack = [("", location)]
    while stack:
        rel, here = stack.pop()
        for name in drive.names(here):
            path = here / name
            st = drive.lstat(path)
            sub = posixpath.join(rel, name) if rel else name
            if stat.S_ISDIR(st.st_mode):
                entries.add((sub, DIR))
                stack.append((sub, path))
            else:
                entries.add((sub, *fingerprint(st)))
            if len(entries) > MANIFEST_LIMIT:
                raise OverflowError
    return frozenset(entries)


def unchanged(drive: Any, location: Any, fp: Any) -> bool | None:
    """Whether *location* is still as the copy left it; None if it is gone."""
    try:
        st = drive.lstat(location)
    except FileNotFoundError:
        return None
    if fp[0] == DIR:
        if fp[1] is None or not stat.S_ISDIR(st.st_mode):
            return False
        try:
            return manifest(drive, location) == fp[1]
        except OverflowError:
            return False
    return fingerprint(st) == fp


def check(pairs: list[tuple[Any, Any]], drive_of: Callable[[Any], Any]) -> tuple[list[Any], list[Any]]:
    """*pairs* of ``(location, fingerprint)`` split into those still as the
    copy left them and those changed; what is gone is in neither.  One that
    cannot be read counts as changed."""
    same: list[Any] = []
    changed: list[Any] = []
    for location, fp in pairs:
        try:
            state = unchanged(drive_of(location), location, fp)
        except OSError:
            state = False
        if state is None:
            continue
        (same if state else changed).append(location)
    return same, changed


__all__ = ["DIR", "MANIFEST_LIMIT", "check", "collapse", "fingerprint", "manifest", "unchanged"]
