"""Before a program outside edits a file: DN's ``Valid(cmQuit)`` in ``ExecExtFile``."""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any


async def save_before_external(app: Any, paths: Iterable[Path]) -> bool:
    """``Valid(cmQuit)`` before ``ExecExtFile`` (``RUNCMD.INC:273``), for the files
    about to be edited outside: each changed editor window on one of *paths* --
    once per text (``must_ask``, its first view) -- asks the close query's
    question.  Yes saves (a save that fails answers False), No goes on and
    leaves the window as it is, Cancel answers False: run nothing.

    A departure: DN asked every changed window; here only those on the files
    named, a change elsewhere being no risk to them.  Files on another drive
    are not asked about -- an editor window there edits a fetched copy of its
    own, which the program outside never shares.
    """
    from navigator.widgets.editor.edit_window import EditWindow

    shell = getattr(app, "shell", None)
    desktop = getattr(shell, "desktop", None)
    if desktop is None:
        return True
    wanted = {os.path.realpath(path) for path in paths}
    for window in list(desktop.windows()):
        if not isinstance(window, EditWindow) or window.editor.path is None:
            continue
        if os.path.realpath(window.editor.path) not in wanted or not window.must_ask():
            continue
        answer = await window.ask_save()
        if answer is None:
            return False
        if answer is True and not await window.save():
            return False
    return True
