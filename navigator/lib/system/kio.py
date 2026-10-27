"""KDE's KIO and Solid, through their commands.

Not DOS Navigator's, and the KDE counterpart of :mod:`navigator.lib.system.gio`:
where Plasma's plumbing is installed it does the same four things, each
through a command of KDE Frameworks 6 -- or 5's, named with a ``5`` --
rather than the libraries, which are compiled:

* **Volumes** (:func:`volumes`, :func:`mount_device`, :func:`unmount`,
  :func:`eject`): what Solid knows of, through ``solid-hardware6``; it
  mounts through udisks, without root, as Dolphin does.
* **The desktop's applications** (:func:`open_file`, :func:`content_type`,
  :func:`applications`, :func:`launch`): ``kioclient exec``,
  ``kmimetypefinder``, ``ktraderclient6`` and ``kstart``.
* **KIO's workers** (:func:`kio_schemes`, :func:`mount_url`): phones over
  MTP, WebDAV, FISH, Google Drive, KDE Connect..., each reached through
  kio-fuse's FUSE bridge under ``$XDG_RUNTIME_DIR/kio-fuse-XXXXXX``, which is
  asked over D-Bus with ``dbus-send`` (:mod:`navigator.lib.drives.kio`).
* **The trash** (:func:`trash`): ``kioclient move PATH trash:/``, where the
  freedesktop Trash of :mod:`navigator.lib.file_ops.trash` finds no trash
  directory.

Whether this module or GIO's is asked is
:func:`navigator.lib.system.desktop.backend`'s to say.  Every call but
:func:`program` blocks: a thread runs it.
"""

from __future__ import annotations

import errno
import glob
import os
import re
import shutil
import subprocess
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from navigator.lib.system.desktop_entry import App, application_dirs, desktop_file, desktop_name, launch_detached

#: How long a quick question may take.
TIMEOUT = 15.0
#: How long mounting may take: a disk spinning up, a server answering.
MOUNT_TIMEOUT = 60.0

#: What says there is no KIO to ask.
NO_KIO = "KDE's kioclient (KIO) is not installed"
#: What says Solid's command is missing, which volumes need.
NO_SOLID = "KDE's solid-hardware (Solid) is not installed"
#: What says kio-fuse cannot be asked, which KIO links need.
NO_KIO_FUSE = "kio-fuse is not running, or dbus-send is not installed"

#: Each command, KDE Frameworks 6's name first, then 5's.
COMMANDS: dict[str, tuple[str, ...]] = {
    "kioclient": ("kioclient", "kioclient6", "kioclient5"),
    "kmimetypefinder": ("kmimetypefinder", "kmimetypefinder6", "kmimetypefinder5"),
    "ktraderclient": ("ktraderclient6", "ktraderclient5", "ktraderclient"),
    "kstart": ("kstart", "kstart6", "kstart5"),
    "solid-hardware": ("solid-hardware6", "solid-hardware5", "solid-hardware"),
}

#: The URI schemes KIO's workers reach that Navigator does not itself, and
#: the worker's plugin each needs (``kf6/kio/NAME.so``).  Written out, as
#: GIO's are: KIO's plumbing (``remote:``, ``desktop:``, ``recentlyused:``...)
#: and the schemes Navigator speaks (sftp, ftp, smb, trash) are left out.
KIO_SCHEMES: dict[str, str] = {
    "mtp": "mtp", "afc": "afc", "webdav": "http", "webdavs": "http", "fish": "fish",
    "gdrive": "gdrive", "nfs": "nfs", "kdeconnect": "kdeconnect",
}

#: Schemes whose KIO URLs have no host: ``mtp:/Phone/Storage``, where a
#: Navigator URL says ``mtp://Phone/Storage``, as GVfs's do.
HOSTLESS = frozenset(("mtp", "gdrive"))


def command(name: str, which: Callable[[str], str | None] | None = None) -> str | None:
    """The installed program for one of :data:`COMMANDS`, or None.

    ``shutil.which`` is looked up at the call, as :mod:`printing` does, so
    that replacing it in a test reaches here.
    """
    which = which or shutil.which
    for each in COMMANDS[name]:
        found = which(each)
        if found:
            return found
    return None


def program(which: Callable[[str], str | None] | None = None) -> str | None:
    """The ``kioclient`` to run, or None: KIO is not installed."""
    return command("kioclient", which)


def _reason(text: str, fallback: str) -> str:
    """A KDE command's own words: its last line, less the program's name."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return fallback
    last = lines[-1]
    match = re.match(r"^(?:kioclient\d?|solid-hardware\d?|kmimetypefinder\d?|ktraderclient\d?|kstart\d?): (.*)$", last)
    if match:
        last = match.group(1)
    # dbus-send's ``Error org.freedesktop.DBus.Error.Failed: <why>``.
    match = re.match(r"^Error [\w.]+: (.*)$", last)
    return match.group(1) if match else last


def run(argv: list[str], timeout: float = TIMEOUT) -> str:
    """*argv*'s output; ``OSError`` with its reason when it fails."""
    name = Path(argv[0]).name
    try:
        result = subprocess.run(argv, capture_output=True, stdin=subprocess.DEVNULL, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise OSError(errno.ETIMEDOUT, f"{name} did not answer") from None
    except FileNotFoundError:
        raise OSError(errno.ENOENT, f"{name} is not installed") from None
    out = result.stdout.decode("utf-8", "replace")
    if result.returncode != 0:
        err = result.stderr.decode("utf-8", "replace")
        raise OSError(errno.EIO, _reason(err or out, f"{name} failed ({result.returncode})"))
    return out


def _needed(name: str, missing: str) -> str:
    found = command(name)
    if found is None:
        raise OSError(errno.ENOENT, missing)
    return found


# -- applications -------------------------------------------------------------------


def open_file(path: Path | str) -> None:
    """*path* opened in the desktop's default application for its type.

    ``kioclient exec`` returns once the application has been started, so it
    is run to its end -- its error is the user's to see -- and not detached.
    ``--noninteractive`` keeps its errors on stderr rather than in a window.
    """
    run([_needed("kioclient", NO_KIO), "--noninteractive", "exec", str(path)])


def content_type(path: Path | str) -> str:
    """*path*'s MIME type as KDE sees it; ``""`` when it says none."""
    out = run([_needed("kmimetypefinder", "KDE's kmimetypefinder is not installed"), str(path)])
    lines = [line.strip() for line in out.splitlines() if line.strip()]
    if not lines:
        return ""
    found = lines[-1].split()[0]
    return found if "/" in found else ""


_PROPERTY = re.compile(r"^\s*(\w+)\s*:\s*(.*?)\s*$")


def parse_trader(text: str) -> list[tuple[str, str]]:
    """``(desktop id, name)`` of each offer ``ktraderclient6 --mimetype``
    prints, in its order -- the user's preferred first.  An offer is a
    ``---- Offer N ----`` line and its ``Key : 'value'`` lines."""
    offers: list[dict[str, str]] = []
    for line in text.splitlines():
        if line.lstrip().startswith("---- Offer"):
            offers.append({})
            continue
        match = _PROPERTY.match(line)
        if match and offers:
            value = match.group(2)
            if len(value) >= 2 and value[0] == value[-1] == "'":
                value = value[1:-1]
            offers[-1].setdefault(match.group(1), value)
    found: list[tuple[str, str]] = []
    for offer in offers:
        entry = offer.get("DesktopEntryPath", "")
        if entry.endswith(".desktop"):
            app_id = Path(entry).name
        elif offer.get("DesktopEntryName"):
            app_id = offer["DesktopEntryName"] + ".desktop"
        else:
            continue
        found.append((app_id, offer.get("Name", "")))
    return list(dict.fromkeys(found))


def applications(mime: str, dirs: Iterable[Path] | None = None) -> list[App]:
    """The applications that open *mime*, the preferred first, by their names."""
    if not mime:
        return []
    trader = _needed("ktraderclient", "KDE's ktraderclient is not installed")
    dirs = list(application_dirs() if dirs is None else dirs)
    found = []
    seen: set[str] = set()
    for app_id, name in parse_trader(run([trader, "--mimetype", mime, "--servicetype", "Application"])):
        if app_id in seen:
            continue
        seen.add(app_id)
        path = desktop_file(app_id, dirs)
        name = name or (desktop_name(path) if path is not None else "")
        found.append(App(app_id, name or app_id.removesuffix(".desktop"), path))
    return found


def launch(app: App, path: Path | str) -> None:
    """*path* opened in *app*: ``kstart``, detached -- it waits for nothing.

    Plasma 6's ``kstart`` takes ``--application``, Plasma 5's ``kstart5``
    ``--service``; both pass the file with ``--url``.
    """
    kstart = _needed("kstart", "KDE's kstart is not installed")
    flag = "--service" if Path(kstart).name.endswith("5") else "--application"
    target = str(app.path) if app.path is not None else app.id
    launch_detached([kstart, flag, target, "--url", str(path)])


# -- volumes --------------------------------------------------------------------------


@dataclass(frozen=True)
class KioVolume:
    """A file system Solid knows of, as :class:`~navigator.lib.system.gio.GioVolume`
    has it -- the same names, so :func:`navigator.lib.system.volumes.merge`
    takes either.  *udi* is what Solid mounts, unmounts and ejects it by."""

    name: str
    udi: str
    device: str = ""
    uuid: str = ""
    local: str = ""
    can_mount: bool = False
    can_unmount: bool = False
    can_eject: bool = False
    #: GIO's only: no URI, no activation root.
    uri: str = ""
    activation_root: str = ""

    @property
    def mounted(self) -> bool:
        return bool(self.local)

    @property
    def ident(self) -> str:
        return self.uuid or self.device or self.udi

    @property
    def target(self) -> str:
        """What :func:`unmount` and :func:`eject` are given."""
        return self.udi


_UDI = re.compile(r"^udi = '(.*)'\s*$")
_VALUE = re.compile(r"^\s+([\w.]+) = (.*)$")
#: The type ``solid-hardware`` writes after a value: ``(string)``, ``(0x1)``, ``(bool)``.
_SUFFIX = re.compile(r"\s+\([^()]*\)\s*$")

#: Where a desktop mounts what the user plugged in; what is mounted
#: elsewhere -- ``/``, ``/home`` -- is the system's, and offers no Unmount.
USER_MOUNTS = ("/media/", "/run/media/", "/mnt/")


def _value(text: str) -> str:
    text = text.strip()
    while True:
        stripped = _SUFFIX.sub("", text)
        if stripped == text:
            break
        text = stripped
    if len(text) >= 2 and text[0] == text[-1] == "'":
        return text[1:-1]
    return text


def parse_devices(text: str) -> dict[str, dict[str, str]]:
    """Each device ``solid-hardware6 list details`` prints, by its UDI: its
    ``parent``, ``product``... and its ``Interface.property`` values."""
    devices: dict[str, dict[str, str]] = {}
    current: dict[str, str] | None = None
    for line in text.splitlines():
        match = _UDI.match(line)
        if match:
            current = devices.setdefault(match.group(1), {})
            continue
        match = _VALUE.match(line)
        if match and current is not None:
            current[match.group(1)] = _value(match.group(2))
    return devices


def _ejectable(devices: dict[str, dict[str, str]], udi: str) -> bool:
    """Whether *udi* is on a medium that comes out: an optical disc, or a
    drive Solid calls removable or hot-pluggable, up its parents."""
    seen = set()
    while udi and udi not in seen:
        seen.add(udi)
        props = devices.get(udi, {})
        if any(key.startswith("OpticalDisc.") for key in props):
            return True
        if props.get("StorageDrive.removable") == "true" or props.get("StorageDrive.hotpluggable") == "true":
            return True
        udi = props.get("parent", "")
    return False


def parse_solid(text: str) -> list[KioVolume]:
    """The file systems in ``solid-hardware6 list details``: every volume
    used for one that Solid does not ignore."""
    devices = parse_devices(text)
    found = []
    for udi, props in devices.items():
        if props.get("StorageVolume.usage") != "FileSystem" or props.get("StorageVolume.ignored") == "true":
            continue
        accessible = props.get("StorageAccess.accessible") == "true"
        local = props.get("StorageAccess.filePath", "") if accessible else ""
        ejectable = _ejectable(devices, udi)
        found.append(KioVolume(
            name=props.get("StorageVolume.label") or props.get("product") or props.get("Block.device", "") or udi,
            udi=udi, device=props.get("Block.device", ""), uuid=props.get("StorageVolume.uuid", ""), local=local,
            can_mount=not accessible and "StorageAccess.accessible" in props,
            can_unmount=bool(local) and (ejectable or (local + "/").startswith(USER_MOUNTS)),
            can_eject=ejectable,
        ))
    return found


def _solid() -> str:
    return _needed("solid-hardware", NO_SOLID)


def volumes() -> list[KioVolume]:
    """What Solid knows of: blocks."""
    return parse_solid(run([_solid(), "list", "details"]))


def _udi(where: str) -> str:
    """The UDI *where* names: one already, or a mount point Solid has."""
    if where.startswith("/org/"):
        return where
    for each in volumes():
        if each.local == where:
            return each.udi
    raise OSError(errno.ENOENT, f"Solid knows nothing mounted at {where}")


def mount_device(volume: KioVolume) -> None:
    """*volume* mounted, through udisks: no root asked."""
    run([_solid(), "mount", volume.udi], timeout=MOUNT_TIMEOUT)


def unmount(where: str) -> None:
    """The volume *where* -- a UDI or a mount point -- unmounted."""
    run([_solid(), "unmount", _udi(where)], timeout=MOUNT_TIMEOUT)


def eject(where: str) -> None:
    """The volume *where* unmounted and its medium ejected, or its drive made safe to remove."""
    run([_solid(), "eject", _udi(where)], timeout=MOUNT_TIMEOUT)


# -- kio-fuse --------------------------------------------------------------------------


def plugin_dirs() -> list[Path]:
    """Where KIO's worker plugins are: ``kf6/kio`` (or ``kf5/kio``) under each Qt plugin directory."""
    roots = [each for each in os.environ.get("QT_PLUGIN_PATH", "").split(":") if each]
    for qt in ("qt6", "qt5"):
        roots += glob.glob(f"/usr/lib*/{qt}/plugins") + glob.glob(f"/usr/lib*/*/{qt}/plugins")
    found = []
    for root in roots:
        for kf in ("kf6", "kf5"):
            path = Path(root) / kf / "kio"
            if path not in found:
                found.append(path)
    return found


def kio_schemes(dirs: Iterable[Path] | None = None) -> tuple[str, ...]:
    """Those of :data:`KIO_SCHEMES` whose worker is installed."""
    dirs = list(plugin_dirs() if dirs is None else dirs)
    return tuple(scheme for scheme, plugin in KIO_SCHEMES.items()
                 if any((directory / f"{plugin}.so").is_file() or (directory / f"kio_{plugin}.so").is_file()
                        for directory in dirs))


def kio_url(uri: str) -> str:
    """*uri* as KIO writes it: ``mtp://Phone/Storage`` is ``mtp:/Phone/Storage``."""
    scheme, sep, rest = uri.partition("://")
    if sep and scheme in HOSTLESS:
        return f"{scheme}:/{rest}"
    return uri


def _vfs(method: str, argument: str, timeout: float) -> str:
    """kio-fuse's ``org.kde.KIOFuse.VFS.<method>(argument)``, its string answer."""
    send = shutil.which("dbus-send")
    if send is None:
        raise OSError(errno.ENOENT, NO_KIO_FUSE)
    out = run([send, "--session", "--print-reply", f"--reply-timeout={int(timeout * 1000)}",
               "--dest=org.kde.KIOFuse", "/org/kde/KIOFuse", f"org.kde.KIOFuse.VFS.{method}",
               f"string:{argument}"], timeout=timeout + 5)
    return parse_reply(out)


def parse_reply(text: str) -> str:
    """The string in a ``dbus-send --print-reply`` answer."""
    match = re.search(r'^\s*string "(.*)"\s*$', text, re.MULTILINE)
    if match is None:
        raise OSError(errno.EIO, NO_KIO_FUSE)
    return match.group(1).replace('\\"', '"')


def mount_url(uri: str) -> Path:
    """Where kio-fuse shows *uri* -- mounting it if it is not yet."""
    return Path(_vfs("mountUrl", kio_url(uri), MOUNT_TIMEOUT))


def remote_url(path: Path | str) -> str:
    """The KIO URL a path under kio-fuse stands for."""
    return _vfs("remoteUrl", str(path), TIMEOUT)


# -- trash ------------------------------------------------------------------------------


def trash(path: Path | str) -> None:
    """*path* moved to KIO's trash."""
    run([_needed("kioclient", NO_KIO), "--noninteractive", "move", str(path), "trash:/"])


__all__ = [
    "App", "COMMANDS", "HOSTLESS", "KIO_SCHEMES", "KioVolume", "NO_KIO", "NO_KIO_FUSE", "NO_SOLID",
    "applications", "command", "content_type", "eject", "kio_schemes", "kio_url", "launch", "mount_device",
    "mount_url", "open_file", "parse_devices", "parse_reply", "parse_solid", "parse_trader", "plugin_dirs",
    "program", "remote_url", "run", "trash", "unmount", "volumes",
]
