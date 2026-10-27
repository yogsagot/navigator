"""The freedesktop pieces GIO and KIO share: ``.desktop`` files, a display, a
detached application.

Not DOS Navigator's.  Both :mod:`navigator.lib.system.gio` and
:mod:`navigator.lib.system.kio` list a file type's applications by their
``.desktop`` ids and name them from the files themselves, which the XDG
specifications put in the same places on every desktop.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


def graphical() -> bool:
    """Whether there is a display for a desktop application to open on."""
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def launch_detached(argv: list[str]) -> None:
    """*argv* started on its own, its output nowhere: a desktop application,
    which outlives the command that asked for it and must not paint over
    Navigator's screen."""
    subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)


@dataclass(frozen=True)
class App:
    """A desktop application: its ``.desktop`` file's id, name and path."""

    id: str
    name: str
    path: Path | None


def application_dirs() -> list[Path]:
    """Where ``.desktop`` files are, the user's first: the XDG data directories' ``applications/``."""
    home = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    others = os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share"
    return [Path(each) / "applications" for each in [home, *others.split(":")] if each]


def desktop_file(app_id: str, dirs: Iterable[Path] | None = None) -> Path | None:
    """Where the ``.desktop`` file *app_id* is: ``a-b.desktop`` may be ``a/b.desktop``."""
    candidates = [app_id]
    stem = app_id.removesuffix(".desktop")
    if "-" in stem:
        candidates.append(stem.replace("-", "/") + ".desktop")
    for directory in application_dirs() if dirs is None else dirs:
        for candidate in candidates:
            path = directory / candidate
            if path.is_file():
                return path
    return None


def desktop_name(path: Path) -> str:
    """The ``Name=`` of a ``.desktop`` file's ``[Desktop Entry]``; ``""`` if none."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    in_entry = False
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("["):
            in_entry = line == "[Desktop Entry]"
        elif in_entry and line.startswith("Name="):
            return line[5:].strip()
    return ""


__all__ = ["App", "application_dirs", "desktop_file", "desktop_name", "graphical", "launch_detached"]
