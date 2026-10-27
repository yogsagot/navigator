"""udisks2, through ``udisksctl``: Disk > Volumes where neither GIO nor Solid is.

Not DOS Navigator's.  ``gio mount`` and ``solid-hardware6`` both mount
through udisks2; where neither is installed -- a server over SSH, i3 or sway
without GVfs, ``[system] desktop_vfs`` off -- this asks udisks2 itself, which
any system with removable media runs, for the same four things:

* :func:`volumes`: ``udisksctl dump``'s file systems, mounted or not;
* :func:`mount_device` and :func:`unmount`: ``udisksctl mount``/``unmount``,
  without root where polkit allows the session, as a desktop does;
* :func:`eject`: every file system of the drive unmounted, then an optical
  disc ejected -- ``udisksctl`` has no eject, so systemd's ``busctl`` asks
  the drive -- or any other drive powered off, safe to pull out.

``--no-user-interaction`` makes a polkit refusal (a session that is not the
seat's active one) an error at once, rather than a wait for an agent that is
not there.  Only volumes: the desktop's applications, links and trash are
GIO's or KIO's alone.  :func:`navigator.lib.system.desktop.volume_backend`
says whether this module is asked.  Every call but :func:`program` blocks:
a thread runs it.
"""

from __future__ import annotations

import errno
import re
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

#: How long a quick question may take.
TIMEOUT = 15.0
#: How long mounting may take: a disk spinning up, a file system checked.
MOUNT_TIMEOUT = 60.0

#: What says there is no udisks2 to ask.
NO_UDISKS = "udisksctl (udisks2) is not installed"
#: What says an optical disc cannot be ejected.
NO_BUSCTL = "busctl (systemd) is not installed, which ejecting a disc needs"

#: Where every udisks2 object path starts; ``udisksctl -p`` takes the rest.
ROOT = "/org/freedesktop/UDisks2/"

#: Where a desktop mounts what the user plugged in, as :mod:`kio` has it.
USER_MOUNTS = ("/media/", "/run/media/", "/mnt/")


def program(which: Callable[[str], str | None] | None = None) -> str | None:
    """The ``udisksctl`` to run, or None.  ``shutil.which`` is looked up at
    the call, so that replacing it in a test reaches here."""
    return (which or shutil.which)("udisksctl")


def _reason(text: str, fallback: str) -> str:
    """udisksctl's or busctl's own words: the last line, less its prefixes.

    ``Error mounting /dev/sdb1: GDBus.Error:org.freedesktop.UDisks2.Error.NotAuthorizedCanObtain: Not authorized``
    is *Not authorized*; ``Call failed: ...`` is what follows it.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return fallback
    last = lines[-1]
    match = re.search(r"GDBus\.Error:[\w.]+: (.*)$", last)
    if match:
        return match.group(1)
    match = re.match(r"^Call failed: (.*)$", last)
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


def _udisksctl() -> str:
    found = program()
    if found is None:
        raise OSError(errno.ENOENT, NO_UDISKS)
    return found


# -- reading the dump --------------------------------------------------------------------


@dataclass(frozen=True)
class UdisksVolume:
    """A file system udisks2 knows of, as :class:`~navigator.lib.system.gio.GioVolume`
    has it -- the same names, so :func:`navigator.lib.system.volumes.merge`
    takes it.  *device* is what it is mounted and unmounted by, *drive* the
    object path of the drive it is on (``""`` for none)."""

    name: str
    device: str
    uuid: str = ""
    local: str = ""
    drive: str = ""
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
        return self.device

    @property
    def target(self) -> str:
        """What :func:`unmount` and :func:`eject` are given."""
        return self.device


_OBJECT = re.compile(r"^(/org/freedesktop/UDisks2/\S+):\s*$")
_INTERFACE = re.compile(r"^  (org\.freedesktop\.UDisks2\.[\w.]+):\s*$")
_VALUE = re.compile(r"^    (\w+):\s*(.*?)\s*$")
#: A value continued on the next line: ``MountPoints``' and ``Symlinks``' second path on.
_MORE = re.compile(r"^\s{5,}(\S.*?)\s*$")

#: Interface name to its short name in :func:`parse_dump`'s result.
_SHORT = "org.freedesktop.UDisks2."


def _value(text: str) -> str:
    """A value as written, its quotes off; ``'/'``, udisks2's *no object*, is
    ``""`` -- quoted, as an object path is, where the root's mount point is not."""
    if len(text) >= 2 and text[0] == text[-1] == "'":
        text = text[1:-1]
        return "" if text == "/" else text
    return text


def parse_dump(text: str) -> dict[str, dict[str, dict[str, list[str]]]]:
    """Each object ``udisksctl dump`` prints, by its path: each interface
    (``Block``, ``Filesystem``, ``Drive``...) it has, and each property's
    values -- one per line, as ``MountPoints`` has several."""
    objects: dict[str, dict[str, dict[str, list[str]]]] = {}
    interface: dict[str, list[str]] | None = None
    values: list[str] | None = None
    for line in text.splitlines():
        match = _OBJECT.match(line)
        if match:
            current = objects.setdefault(match.group(1), {})
            interface = values = None
            continue
        match = _INTERFACE.match(line)
        if match and objects:
            interface = current.setdefault(match.group(1).removeprefix(_SHORT), {})
            values = None
            continue
        match = _VALUE.match(line)
        if match and interface is not None:
            value = _value(match.group(2))
            values = interface.setdefault(match.group(1), [])
            if value:
                values.append(value)
            continue
        match = _MORE.match(line)
        if match and values is not None:
            values.append(_value(match.group(1)))
    return objects


def _one(props: dict[str, list[str]], key: str) -> str:
    found = props.get(key)
    return found[0] if found else ""


def _true(props: dict[str, list[str]], key: str) -> bool:
    return _one(props, key) == "true"


def parse_volumes(text: str) -> list[UdisksVolume]:
    """The file systems in a ``udisksctl dump``: every block used for one
    that udisks2 does not ignore, less loop devices (snaps' images) and the
    system's own that are not mounted (a recovery partition)."""
    objects = parse_dump(text)
    found = []
    for path, interfaces in objects.items():
        block, filesystem = interfaces.get("Block"), interfaces.get("Filesystem")
        if block is None or filesystem is None or _one(block, "IdUsage") != "filesystem":
            continue
        if _true(block, "HintIgnore") or "Loop" in interfaces:
            continue
        local = _one(filesystem, "MountPoints")
        if _true(block, "HintSystem") and not local:
            continue
        drive_path = _drive_of(objects, path)
        drive = objects.get(drive_path, {}).get("Drive", {})
        removable = _true(drive, "Removable") or _true(drive, "MediaRemovable")
        model = " ".join(part for part in (_one(drive, "Vendor"), _one(drive, "Model")) if part)
        device = _one(block, "Device") or _one(block, "PreferredDevice")
        found.append(UdisksVolume(
            name=_one(block, "IdLabel") or _one(block, "HintName") or model or device,
            device=device, uuid=_one(block, "IdUUID"), local=local, drive=drive_path,
            can_mount=not local,
            can_unmount=bool(local) and (removable or (local + "/").startswith(USER_MOUNTS)),
            can_eject=_true(drive, "Ejectable") or _true(drive, "CanPowerOff"),
        ))
    found.sort(key=lambda volume: volume.device)
    return found


def _drive_of(objects: dict[str, dict[str, dict[str, list[str]]]], path: str) -> str:
    """The drive the block at *path* is on: its own, else its LUKS container's."""
    seen = set()
    while path and path not in seen:
        seen.add(path)
        block = objects.get(path, {}).get("Block", {})
        drive = _one(block, "Drive")
        if drive:
            return drive
        path = _one(block, "CryptoBackingDevice")
    return ""


def volumes() -> list[UdisksVolume]:
    """What udisks2 knows of now."""
    return parse_volumes(run([_udisksctl(), "dump"]))


# -- mount, unmount, eject ----------------------------------------------------------------


def _find(where: str, known: list[UdisksVolume]) -> UdisksVolume:
    """The volume *where* names -- its device or its mount point -- in *known*."""
    for each in known:
        if where in (each.device, each.local):
            return each
    raise OSError(errno.ENOENT, f"udisks knows nothing at {where}")


def mount_device(volume: UdisksVolume) -> None:
    """*volume* mounted where udisks2 mounts it, ``/media/$USER/LABEL``."""
    run([_udisksctl(), "mount", "-b", volume.device, "--no-user-interaction"], timeout=MOUNT_TIMEOUT)


def unmount(where: str) -> None:
    """The file system *where* -- a device or a mount point -- unmounted."""
    device = where if where.startswith("/dev/") else _find(where, volumes()).device
    run([_udisksctl(), "unmount", "-b", device, "--no-user-interaction"], timeout=MOUNT_TIMEOUT)


def eject(where: str) -> None:
    """The drive *where* is on made safe to remove: every file system on it
    unmounted, then its disc ejected, or it powered off."""
    text = run([_udisksctl(), "dump"])
    known = parse_volumes(text)
    volume = _find(where, known)
    if not volume.drive:
        raise OSError(errno.EINVAL, f"{volume.name} is on no drive that can be ejected")
    for each in known:
        if each.drive == volume.drive and each.mounted:
            run([_udisksctl(), "unmount", "-b", each.device, "--no-user-interaction"], timeout=MOUNT_TIMEOUT)
    drive = parse_dump(text).get(volume.drive, {}).get("Drive", {})
    if _true(drive, "Ejectable"):
        busctl = shutil.which("busctl")
        if busctl is None:
            raise OSError(errno.ENOENT, NO_BUSCTL)
        run([busctl, "--system", "--allow-interactive-authorization=no", "call", "org.freedesktop.UDisks2",
             volume.drive, "org.freedesktop.UDisks2.Drive", "Eject", "a{sv}", "0"], timeout=MOUNT_TIMEOUT)
    else:
        run([_udisksctl(), "power-off", "-p", volume.drive.removeprefix(ROOT), "--no-user-interaction"],
            timeout=MOUNT_TIMEOUT)


__all__ = [
    "MOUNT_TIMEOUT", "NO_BUSCTL", "NO_UDISKS", "ROOT", "TIMEOUT", "UdisksVolume", "eject", "mount_device",
    "parse_dump", "parse_volumes", "program", "run", "unmount", "volumes",
]
