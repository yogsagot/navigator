"""Disk > Volumes: every mounted file system, with its name, type, mount point and free space.

DOS Navigator 1.51 had no such list -- its drive chooser (``SelectDrive``,
FILESCOL.PAS) gave bare letters, and ``TDiskInfo`` (DISKINFO.PAS, Ctrl+L)
told the size, free space and label of the current drive only.  This is the
POSIX reading of the two together: what ``TDiskInfo`` said, for every drive
``SelectDrive`` would have offered.  A departure, recorded in
``volumes_window.nml``.

A *volume* is a line of ``/proc/self/mounts``.  Its name is the label
``/dev/disk/by-label`` gives its device, as Ctrl+L reads it, else the
device's own name.  A *real* one is backed by a block device or a network
share; the kernel's own file systems (``proc``, ``sysfs``, ``cgroup2``...)
and snap packages' squashfs images are not, and are listed only on request.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from navigator.lib.system.diskinfo import label_of, unescape

#: File system types that hold no files of the user's, wherever they are mounted.
PSEUDO_TYPES = frozenset((
    "autofs", "binfmt_misc", "bpf", "cgroup", "cgroup2", "configfs", "debugfs", "devpts", "devtmpfs",
    "efivarfs", "fusectl", "hugetlbfs", "mqueue", "nsfs", "overlay", "proc", "pstore", "ramfs",
    "rpc_pipefs", "securityfs", "selinuxfs", "squashfs", "sysfs", "tmpfs", "tracefs",
))

#: Network file systems: real, though no ``/dev`` device backs them.
NETWORK_TYPES = ("nfs", "nfs4", "cifs", "smb3", "smbfs", "9p", "fuse.sshfs", "fuse.rclone", "afs", "ceph")

#: FUSE file systems the desktop mounts for its own plumbing.
PLUMBING_FUSE = frozenset(("fuse.portal", "fuse.gvfsd-fuse", "fuse.doc", "fuse.lxcfs"))


@dataclass(frozen=True)
class Volume:
    """One mounted file system, as the Volumes window lists it."""

    name: str
    fs_type: str
    mount: str
    device: str
    total: int | None = None
    free: int | None = None
    real: bool = True


def parse_mounts(text: str) -> list[tuple[str, str, str]]:
    """``(device, mount point, type)`` for each mount in *text*, a ``/proc/self/mounts``.

    A mount point mounted over is listed once, as what was mounted last:
    that is what a path under it reaches.
    """
    found: dict[str, tuple[str, str, str]] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        device, point, fs_type = unescape(parts[0]), unescape(parts[1]), parts[2]
        found.pop(point, None)
        found[point] = (device, point, fs_type)
    return list(found.values())


def is_real(device: str, fs_type: str) -> bool:
    """Whether a mount of *device* as *fs_type* is a volume the user keeps files on."""
    if fs_type in PSEUDO_TYPES or fs_type in PLUMBING_FUSE:
        return False
    if fs_type in NETWORK_TYPES or fs_type.startswith(("nfs", "fuse.")):
        return True
    return device.startswith("/dev/") and not device.startswith("/dev/loop")


def volume_name(device: str, label: str) -> str:
    """What a volume is called: its label, else its device's name, else the device."""
    if label:
        return label
    if device.startswith("/dev/"):
        return os.path.basename(device)
    return device


def gather(*, mounts: Path = Path("/proc/self/mounts"),
           labels: Path = Path("/dev/disk/by-label")) -> list[Volume]:
    """Every mounted volume, by mount point, real or not: a thread runs it.

    A mount ``statvfs`` refuses -- an NFS server gone away, a FUSE mount whose
    daemon died, a directory the user may not enter -- is skipped rather than
    listed without numbers: there is nothing on it to go to.
    """
    try:
        text = mounts.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    found: list[Volume] = []
    for device, point, fs_type in parse_mounts(text):
        try:
            usage = shutil.disk_usage(point)
        except OSError:
            continue
        label = label_of(device, labels) if os.path.isabs(device) else ""
        found.append(Volume(
            name=volume_name(device, label), fs_type=fs_type, mount=point, device=device,
            total=usage.total, free=usage.free, real=is_real(device, fs_type),
        ))
    found.sort(key=lambda volume: volume.mount)
    return found
