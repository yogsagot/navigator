"""The freedesktop pieces GIO and KIO share: ``.desktop`` files, a display, a
detached application.

Not DOS Navigator's.  Both :mod:`navigator.lib.system.gio` and
:mod:`navigator.lib.system.kio` list a file type's applications by their
``.desktop`` ids and name them from the files themselves, which the XDG
specifications put in the same places on every desktop.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from navigator.lib.system.which import which as _which


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
    """A desktop application: its ``.desktop`` file's id, name and path;
    *default* when it is what the file type opens in now."""

    id: str
    name: str
    path: Path | None
    default: bool = False


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


def desktop_entry(path: Path) -> dict[str, str]:
    """The keys of a ``.desktop`` file's ``[Desktop Entry]`` group, the first
    of each kept (localised ``Name[xx]=`` are keys of their own); ``{}`` when
    it will not read."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    entry: dict[str, str] = {}
    in_entry = False
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("["):
            in_entry = line == "[Desktop Entry]"
        elif in_entry and "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            entry.setdefault(key.strip(), value.strip())
    return entry


def desktop_name(path: Path) -> str:
    """The ``Name=`` of a ``.desktop`` file's ``[Desktop Entry]``; ``""`` if none."""
    return desktop_entry(path).get("Name", "")


#: An ``Exec=`` field code that takes a file or a URL.
_FILE_CODE = re.compile(r"%[fFuU]")


def _shown(entry: dict[str, str], desktops: set[str]) -> bool:
    """Whether a file manager offers *entry* to open a file in: an
    application, not hidden, its ``TryExec`` installed, meant for this
    desktop, and its ``Exec`` taking a file."""
    if entry.get("Type") != "Application":
        return False
    if entry.get("NoDisplay", "").lower() == "true" or entry.get("Hidden", "").lower() == "true":
        return False
    try_exec = entry.get("TryExec", "")
    if try_exec and _which(try_exec) is None:
        return False
    only = {each for each in entry.get("OnlyShowIn", "").upper().split(";") if each}
    if only and not only & desktops:
        return False
    if {each for each in entry.get("NotShowIn", "").upper().split(";") if each} & desktops:
        return False
    return bool(_FILE_CODE.search(entry.get("Exec", "")))


def all_applications(dirs: Iterable[Path] | None = None) -> list[App]:
    """Every installed application a file can be opened in, by name -- GNOME's
    and Xfce's *Other applications*.  A file's id is its path under
    ``applications/`` with ``/`` as ``-``; the first directory's wins, as the
    XDG menu specification says, so the user's own shadows the system's."""
    desktops = {each for each in os.environ.get("XDG_CURRENT_DESKTOP", "").upper().split(":") if each}
    seen: set[str] = set()
    found: list[App] = []
    for directory in application_dirs() if dirs is None else dirs:
        try:
            paths = sorted(directory.rglob("*.desktop"))
        except OSError:
            continue
        for path in paths:
            app_id = path.relative_to(directory).as_posix().replace("/", "-")
            if app_id in seen:
                continue
            seen.add(app_id)
            entry = desktop_entry(path)
            if _shown(entry, desktops):
                found.append(App(app_id, entry.get("Name") or app_id.removesuffix(".desktop"), path))
    return sorted(found, key=lambda app: (app.name.casefold(), app.id))


def other_applications(listed: Iterable[App], dirs: Iterable[Path] | None = None) -> list[App]:
    """:func:`all_applications` less those in *listed* (the type's own)."""
    ids = {app.id for app in listed}
    return [app for app in all_applications(dirs) if app.id not in ids]


def mimeapps_list() -> Path:
    """The user's ``mimeapps.list``: where a desktop keeps its default applications."""
    home = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return Path(home) / "mimeapps.list"


def _set_in_group(lines: list[str], group: str, key: str, value: str) -> list[str]:
    """*lines* with ``key=value`` in ``[group]``: the old line replaced, else
    added at the group's end, else the group added at the end."""
    start = next((index for index, line in enumerate(lines) if line.strip() == f"[{group}]"), None)
    if start is None:
        if lines and lines[-1].strip():
            lines.append("")
        return [*lines, f"[{group}]", f"{key}={value}"]
    end = next((index for index in range(start + 1, len(lines)) if lines[index].strip().startswith("[")), len(lines))
    for index in range(start + 1, end):
        if lines[index].split("=", 1)[0].strip() == key and "=" in lines[index]:
            lines[index] = f"{key}={value}"
            return lines
    last = end
    while last > start + 1 and not lines[last - 1].strip():
        last -= 1
    lines.insert(last, f"{key}={value}")
    return lines


def _group_value(lines: list[str], group: str, key: str) -> str:
    in_group = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("["):
            in_group = stripped == f"[{group}]"
        elif in_group and "=" in stripped and stripped.split("=", 1)[0].strip() == key:
            return stripped.split("=", 1)[1].strip()
    return ""


def set_default_in_mimeapps(mime: str, app_id: str, path: Path | None = None) -> None:
    """*app_id* the default for *mime* in ``mimeapps.list`` (freedesktop's
    MIME applications specification): ``[Default Applications]`` says so,
    and it goes first in ``[Added Associations]``, which is the order KDE
    prefers by.  Every other line is kept as it was."""
    path = path or mimeapps_list()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        lines = []
    lines = _set_in_group(lines, "Default Applications", mime, app_id)
    added = [each for each in _group_value(lines, "Added Associations", mime).split(";") if each and each != app_id]
    lines = _set_in_group(lines, "Added Associations", mime, ";".join([app_id, *added]) + ";")
    path = path.resolve()  # a dotfiles symlink stays one
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".navigator-tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(temporary, path)


__all__ = [
    "App", "all_applications", "application_dirs", "desktop_entry", "desktop_file", "desktop_name", "graphical",
    "launch_detached", "mimeapps_list", "other_applications", "set_default_in_mimeapps",
]
