"""Telling a panel that the directory it shows has changed on disk.

**A departure from DOS Navigator**, which re-read a panel only when the code
that changed something said so (``RereadDirectory`` broadcasting
``cmRereadDir``): another program's new file stayed out of the listing until
Ctrl+R.  Here each panel watches its own directory through :mod:`watchdog`
(inotify on Linux, FSEvents on macOS, kqueue on the BSDs) and re-reads it,
behind ``[file_manager] auto_refresh``.

One observer thread serves the whole process, with one non-recursive watch
per directory however many panels show it.  **The notify callbacks run on
that thread**: they may touch nothing reactive, and hand over to the loop
(``Application.call_from_thread``).  Only a change to the listing passes --
created, deleted, moved, modified -- never watchdog's opened and closed, or
F3 opening a file would re-read the panel showing it.

A directory that cannot be watched -- the inotify watch limit reached, a
filesystem that sends no events, a directory gone already -- gets a
:class:`Watch` that does nothing, and its panel is what it always was.
"""

from __future__ import annotations

import contextlib
import logging
import threading
from collections.abc import Callable
from pathlib import Path

from watchdog.events import (
    EVENT_TYPE_CREATED,
    EVENT_TYPE_DELETED,
    EVENT_TYPE_MODIFIED,
    EVENT_TYPE_MOVED,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver, ObservedWatch

LOG = logging.getLogger(__name__)

#: What changes a listing; everything else watchdog reports is left out.
CHANGES = frozenset({EVENT_TYPE_CREATED, EVENT_TYPE_DELETED, EVENT_TYPE_MODIFIED, EVENT_TYPE_MOVED})

Notify = Callable[[], None]


class _Directory(FileSystemEventHandler):
    """One watched directory and everyone who asked to hear about it."""

    def __init__(self) -> None:
        self.subscribers: list[Notify] = []
        self.watch: ObservedWatch | None = None

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.event_type not in CHANGES:
            return
        for notify in tuple(self.subscribers):
            notify()


class Watch:
    """One :func:`watch` call, until :meth:`cancel`."""

    def __init__(self, path: Path | None = None, notify: Notify | None = None) -> None:
        self.path = path
        self._notify = notify

    @property
    def active(self) -> bool:
        return self._notify is not None

    def cancel(self) -> None:
        """Stop hearing about the directory; the last one out unschedules it."""
        notify, self._notify = self._notify, None
        if notify is None or self.path is None:
            return
        with _LOCK:
            directory = _DIRECTORIES.get(self.path)
            if directory is None:
                return
            directory.subscribers = [n for n in directory.subscribers if n is not notify]
            if directory.subscribers:
                return
            del _DIRECTORIES[self.path]
            if directory.watch is not None and _OBSERVER is not None:
                try:
                    _OBSERVER.unschedule(directory.watch)
                except (KeyError, OSError):
                    pass  # gone with the directory


_LOCK = threading.Lock()
_DIRECTORIES: dict[Path, _Directory] = {}
_OBSERVER: BaseObserver | None = None


def _observer() -> BaseObserver:
    global _OBSERVER
    if _OBSERVER is None:
        _OBSERVER = Observer()
        _OBSERVER.daemon = True  # never what holds the interpreter open at exit
        _OBSERVER.start()
    return _OBSERVER


def watch(path: Path, notify: Notify) -> Watch:
    """Call *notify*, on the observer's thread, whenever *path*'s listing changes."""
    with _LOCK:
        directory = _DIRECTORIES.get(path)
        if directory is None:
            directory = _Directory()
            observer = _observer()
            try:
                directory.watch = observer.schedule(directory, str(path), recursive=False)
            except OSError as error:
                LOG.debug("not watching %s: %s", path, error)
                # schedule() has registered the handler before its emitter failed.
                with contextlib.suppress(KeyError):
                    observer.remove_handler_for_watch(directory, ObservedWatch(str(path), recursive=False))
                return Watch()
            _DIRECTORIES[path] = directory
        directory.subscribers = [*directory.subscribers, notify]
    return Watch(path, notify)


def watched() -> list[Path]:
    """The directories being watched now."""
    with _LOCK:
        return list(_DIRECTORIES)


def shutdown() -> None:
    """Stop the observer and forget every watch (a test's clean slate)."""
    global _OBSERVER
    with _LOCK:
        observer, _OBSERVER = _OBSERVER, None
        _DIRECTORIES.clear()
    if observer is not None:
        observer.stop()
        observer.join(timeout=2)
