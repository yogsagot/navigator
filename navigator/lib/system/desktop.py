"""The desktop's plumbing: GIO's or KDE's KIO, one of them a session.

Not DOS Navigator's.  :mod:`navigator.lib.system.gio` and
:mod:`navigator.lib.system.kio` do the same things -- volumes, the desktop's
applications, links through a FUSE bridge, a trash -- through different
commands, and every caller asks here rather than either: :func:`backend`
picks the module by ``[system] desktop_vfs``, and each call is passed to it.

``auto`` is KIO in a KDE session (``$XDG_CURRENT_DESKTOP``) where it is
installed, else GIO, else KIO; ``gio`` or ``kio`` is that one or nothing;
``off`` is nothing.  With nothing, :func:`program` is None and all of it is
greyed out.  The choice is made at each call, so a test or the ini changing
reaches it.

Disk > Volumes alone has a third: :func:`volume_backend` is the backend
where it has its volume command (``gio``; Solid's ``solid-hardware6``), else
udisks2's own ``udisksctl`` (:mod:`navigator.lib.system.udisks`) -- with
``off`` too, as udisks2 is the system's, not the desktop's plumbing.
:func:`volumes`, :func:`mount_device`, :func:`unmount` and :func:`eject`
ask it.
"""

from __future__ import annotations

import os
from pathlib import Path
from types import ModuleType
from typing import Any

from navigator.lib.system import gio, kio, udisks
from navigator.lib.system.desktop_entry import App, graphical


def kde_session() -> bool:
    """Whether the desktop running is KDE's."""
    return "KDE" in os.environ.get("XDG_CURRENT_DESKTOP", "").upper().split(":")


def backend() -> ModuleType | None:
    """:mod:`~navigator.lib.system.gio` or :mod:`~navigator.lib.system.kio`,
    whichever ``[system] desktop_vfs`` says and is installed; None for neither."""
    from navigator.settings import SETTINGS

    choice = SETTINGS.system.desktop_vfs
    if choice == "off":
        return None
    if choice == "gio":
        return gio if gio.program() else None
    if choice == "kio":
        return kio if kio.program() else None
    if kde_session() and kio.program():
        return kio
    if gio.program():
        return gio
    if kio.program():
        return kio
    return None


def program() -> str | None:
    """The program the backend runs (``gio``, ``kioclient``), or None: what greys it all out."""
    module = backend()
    return module.program() if module is not None else None


def name() -> str:
    """``GIO`` or ``KIO``, for a box's words; ``""`` with neither."""
    module = backend()
    return "KIO" if module is kio else "GIO" if module is gio else ""


def link_name() -> str:
    """What a link through the backend's FUSE bridge is called: ``GVfs`` or ``KIO``."""
    return "KIO" if backend() is kio else "GVfs"


def missing() -> str:
    """Why there is no backend: what to install, or the setting that is off."""
    from navigator.settings import SETTINGS

    choice = SETTINGS.system.desktop_vfs
    if choice == "off":
        return "The desktop's plumbing is off ([system] desktop_vfs)"
    if choice == "kio":
        return kio.NO_KIO
    return gio.NO_GIO if choice == "gio" else "Neither gio (GLib) nor kioclient (KDE) is installed"


def _module() -> ModuleType:
    module = backend()
    if module is None:
        raise OSError(2, missing())
    return module


def open_file(path: Path | str) -> None:
    _module().open_file(path)


def content_type(path: Path | str) -> str:
    return _module().content_type(path)


def applications(mime: str) -> list[App]:
    return _module().applications(mime)


def launch(app: App, path: Path | str) -> None:
    _module().launch(app, path)


def volume_backend() -> ModuleType | None:
    """Who Disk > Volumes asks: :func:`backend` where its volume command is
    installed, else :mod:`~navigator.lib.system.udisks` where ``udisksctl``
    is; None for none of them."""
    module = backend()
    if module is gio or (module is kio and kio.command("solid-hardware")):
        return module
    return udisks if udisks.program() else None


def volume_program() -> str | None:
    """The program Disk > Volumes runs, or None: what greys its Mount, Unmount and Eject out."""
    module = volume_backend()
    if module is kio:
        return kio.command("solid-hardware")
    return module.program() if module is not None else None


def _volume_module() -> ModuleType:
    module = volume_backend()
    if module is None:
        raise OSError(2, udisks.NO_UDISKS)
    return module


def volumes() -> list[Any]:
    return _volume_module().volumes()


def mount_device(volume: Any) -> None:
    _volume_module().mount_device(volume)


def unmount(where: str) -> None:
    _volume_module().unmount(where)


def eject(where: str) -> None:
    _volume_module().eject(where)


def trash(path: Path | str) -> None:
    _module().trash(path)


def link_schemes() -> dict[str, str]:
    """The schemes the backend's links reach, written out (not only those installed)."""
    return kio.KIO_SCHEMES if backend() is kio else gio.GVFS_SCHEMES


__all__ = [
    "App", "applications", "backend", "content_type", "eject", "graphical", "kde_session", "launch",
    "link_name", "link_schemes", "missing", "mount_device", "name", "open_file", "program", "trash",
    "unmount", "volume_backend", "volume_program", "volumes",
]
