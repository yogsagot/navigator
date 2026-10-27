"""udisks2 through ``udisksctl``: Disk > Volumes where neither GIO nor Solid is."""

from __future__ import annotations

import pytest

from navkit.events import KeyEvent

from conftest import Until, run_app

from navigator.lib.system import desktop, gio, kio, udisks, volumes
from navigator.lib.system.volumes import Volume
from navigator.settings import SETTINGS


DRIVES = "/org/freedesktop/UDisks2/drives/"
BLOCKS = "/org/freedesktop/UDisks2/block_devices/"

#: A ``udisksctl dump`` cut down to what is read: the system's NVMe disk, a
#: USB stick with one partition mounted and one not, a DVD drive with a disc,
#: a LUKS partition opened on the stick, a snap's loop image and an ignored
#: partition.
DUMP = f"""\
/org/freedesktop/UDisks2/Manager:
  org.freedesktop.UDisks2.Manager:
    Version:                    2.10.1

{DRIVES}Samsung_SSD:
  org.freedesktop.UDisks2.Drive:
    CanPowerOff:                false
    Ejectable:                  false
    MediaRemovable:             false
    Model:                      Samsung SSD 980
    Removable:                  false
    Vendor:

{DRIVES}SanDisk_Cruzer:
  org.freedesktop.UDisks2.Drive:
    CanPowerOff:                true
    Ejectable:                  false
    MediaRemovable:             false
    Model:                      Cruzer
    Removable:                  true
    Vendor:                     SanDisk

{DRIVES}HL_DT_ST_DVD:
  org.freedesktop.UDisks2.Drive:
    CanPowerOff:                false
    Ejectable:                  true
    MediaRemovable:             true
    Model:                      DVDRAM
    Removable:                  true
    Vendor:                     HL-DT-ST

{BLOCKS}nvme0n1p1:
  org.freedesktop.UDisks2.Block:
    CryptoBackingDevice:        '/'
    Device:                     /dev/nvme0n1p1
    Drive:                      '{DRIVES}Samsung_SSD'
    HintIgnore:                 false
    HintSystem:                 true
    IdLabel:
    IdUUID:                     1111
    IdUsage:                    filesystem
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:        /
  org.freedesktop.UDisks2.Partition:
    Number:             1

{BLOCKS}nvme0n1p2:
  org.freedesktop.UDisks2.Block:
    CryptoBackingDevice:        '/'
    Device:                     /dev/nvme0n1p2
    Drive:                      '{DRIVES}Samsung_SSD'
    HintIgnore:                 false
    HintSystem:                 true
    IdLabel:                    Recovery
    IdUUID:                     2222
    IdUsage:                    filesystem
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:

{BLOCKS}nvme0n1p3:
  org.freedesktop.UDisks2.Block:
    CryptoBackingDevice:        '/'
    Device:                     /dev/nvme0n1p3
    Drive:                      '{DRIVES}Samsung_SSD'
    HintIgnore:                 true
    HintSystem:                 false
    IdLabel:                    Hidden
    IdUsage:                    filesystem
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:

{BLOCKS}sdc:
  org.freedesktop.UDisks2.Block:
    CryptoBackingDevice:        '/'
    Device:                     /dev/sdc
    Drive:                      '{DRIVES}SanDisk_Cruzer'
    IdUsage:
  org.freedesktop.UDisks2.PartitionTable:
    Partitions:         {BLOCKS}sdc1
                        {BLOCKS}sdc2

{BLOCKS}sdc1:
  org.freedesktop.UDisks2.Block:
    CryptoBackingDevice:        '/'
    Device:                     /dev/sdc1
    Drive:                      '{DRIVES}SanDisk_Cruzer'
    HintIgnore:                 false
    HintSystem:                 false
    IdLabel:                    STICK
    IdUUID:                     AB-CD
    IdUsage:                    filesystem
    Symlinks:                   /dev/disk/by-label/STICK
                                /dev/disk/by-uuid/AB-CD
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:        /media/me/STICK
                        /media/me/again

{BLOCKS}sdc2:
  org.freedesktop.UDisks2.Block:
    CryptoBackingDevice:        '/'
    Device:                     /dev/sdc2
    Drive:                      '{DRIVES}SanDisk_Cruzer'
    HintIgnore:                 false
    HintSystem:                 false
    IdLabel:
    IdUUID:                     EF-01
    IdUsage:                    filesystem
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:

{BLOCKS}sr0:
  org.freedesktop.UDisks2.Block:
    CryptoBackingDevice:        '/'
    Device:                     /dev/sr0
    Drive:                      '{DRIVES}HL_DT_ST_DVD'
    HintIgnore:                 false
    HintSystem:                 false
    IdLabel:                    MOVIE
    IdUsage:                    filesystem
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:        /media/me/MOVIE

{BLOCKS}dm_2d0:
  org.freedesktop.UDisks2.Block:
    CryptoBackingDevice:        '{BLOCKS}sdc2'
    Device:                     /dev/dm-0
    Drive:                      '/'
    HintIgnore:                 false
    HintSystem:                 false
    IdLabel:                    secret
    IdUsage:                    filesystem
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:

{BLOCKS}loop3:
  org.freedesktop.UDisks2.Block:
    CryptoBackingDevice:        '/'
    Device:                     /dev/loop3
    Drive:                      '/'
    HintIgnore:                 false
    HintSystem:                 true
    IdUsage:                    filesystem
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:        /snap/core/1
  org.freedesktop.UDisks2.Loop:
    BackingFile:        /var/lib/snapd/snaps/core_1.snap
"""


@pytest.fixture
def fake_udisks(monkeypatch):
    """``udisksctl`` and ``busctl`` installed, each run recorded and answered with :data:`DUMP`."""
    calls: list[list[str]] = []

    def run(argv, timeout=udisks.TIMEOUT):
        calls.append(list(argv))
        return DUMP if argv[1:] == ["dump"] else ""

    monkeypatch.setattr(udisks, "program", lambda which=None: "udisksctl")
    monkeypatch.setattr(udisks.shutil, "which", lambda name: name if name == "busctl" else None)
    monkeypatch.setattr(udisks, "run", run)
    return calls


# -- reading the dump ---------------------------------------------------------------------


def test_the_dump_is_read_by_object_interface_and_property():
    objects = udisks.parse_dump(DUMP)
    stick = objects[BLOCKS + "sdc1"]
    assert stick["Filesystem"]["MountPoints"] == ["/media/me/STICK", "/media/me/again"]
    assert stick["Block"]["Drive"] == [DRIVES + "SanDisk_Cruzer"]
    assert stick["Block"]["CryptoBackingDevice"] == []
    assert objects[BLOCKS + "nvme0n1p1"]["Filesystem"]["MountPoints"] == ["/"]
    assert objects[DRIVES + "SanDisk_Cruzer"]["Drive"]["Vendor"] == ["SanDisk"]


def test_the_file_systems_are_listed_less_loops_the_ignored_and_the_systems_unmounted():
    found = {each.device: each for each in udisks.parse_volumes(DUMP)}
    assert sorted(found) == ["/dev/dm-0", "/dev/nvme0n1p1", "/dev/sdc1", "/dev/sdc2", "/dev/sr0"]
    root = found["/dev/nvme0n1p1"]
    assert (root.name, root.local, root.mounted) == ("Samsung SSD 980", "/", True)
    assert not (root.can_mount or root.can_unmount or root.can_eject)
    stick = found["/dev/sdc1"]
    assert (stick.name, stick.local, stick.uuid) == ("STICK", "/media/me/STICK", "AB-CD")
    assert stick.can_unmount and stick.can_eject and not stick.can_mount
    assert stick.target == stick.ident == "/dev/sdc1"
    blank = found["/dev/sdc2"]
    assert (blank.name, blank.mounted, blank.can_mount) == ("SanDisk Cruzer", False, True)
    assert found["/dev/sr0"].can_eject


def test_an_opened_luks_volume_is_on_its_containers_drive():
    secret = {each.device: each for each in udisks.parse_volumes(DUMP)}["/dev/dm-0"]
    assert secret.name == "secret" and secret.drive == DRIVES + "SanDisk_Cruzer" and secret.can_eject


def test_a_failure_is_the_commands_own_reason():
    assert udisks._reason(
        "Error mounting /dev/sdc2: GDBus.Error:org.freedesktop.UDisks2.Error.NotAuthorizedCanObtain: "
        "Not authorized to perform operation\n", "x") == "Not authorized to perform operation"
    assert udisks._reason("Call failed: Device is busy\n", "x") == "Device is busy"
    assert udisks._reason("", "udisksctl failed (1)") == "udisksctl failed (1)"


# -- mount, unmount, eject ------------------------------------------------------------------


def test_mount_and_unmount_by_device_and_by_mount_point(fake_udisks):
    blank = {each.device: each for each in udisks.volumes()}["/dev/sdc2"]
    udisks.mount_device(blank)
    udisks.unmount("/dev/sdc1")
    udisks.unmount("/media/me/MOVIE")
    assert ["udisksctl", "mount", "-b", "/dev/sdc2", "--no-user-interaction"] in fake_udisks
    assert ["udisksctl", "unmount", "-b", "/dev/sdc1", "--no-user-interaction"] in fake_udisks
    assert ["udisksctl", "unmount", "-b", "/dev/sr0", "--no-user-interaction"] in fake_udisks


def test_eject_unmounts_the_drive_and_powers_a_stick_off(fake_udisks):
    udisks.eject("/dev/sdc1")
    assert fake_udisks[1:] == [
        ["udisksctl", "unmount", "-b", "/dev/sdc1", "--no-user-interaction"],
        ["udisksctl", "power-off", "-p", "drives/SanDisk_Cruzer", "--no-user-interaction"],
    ]


def test_eject_ejects_a_disc_through_busctl(fake_udisks, monkeypatch):
    udisks.eject("/media/me/MOVIE")
    assert fake_udisks[-1] == ["busctl", "--system", "--allow-interactive-authorization=no", "call",
                               "org.freedesktop.UDisks2", DRIVES + "HL_DT_ST_DVD",
                               "org.freedesktop.UDisks2.Drive", "Eject", "a{sv}", "0"]
    monkeypatch.setattr(udisks.shutil, "which", lambda name: None)
    with pytest.raises(OSError) as raised:
        udisks.eject("/dev/sr0")
    assert raised.value.strerror == udisks.NO_BUSCTL


def test_without_udisksctl_nothing_runs(monkeypatch):
    monkeypatch.setattr(udisks, "program", lambda which=None: None)
    with pytest.raises(OSError) as raised:
        udisks.volumes()
    assert raised.value.strerror == udisks.NO_UDISKS


# -- who Disk > Volumes asks -------------------------------------------------------------------


@pytest.mark.parametrize("setting, has, expected", [
    ("auto", {"gio", "udisks"}, gio),
    ("off", {"gio", "udisks"}, udisks),
    ("off", set(), None),
    ("kio", {"kio", "solid", "udisks"}, kio),
    ("kio", {"kio", "udisks"}, udisks),
    ("gio", {"udisks"}, udisks),
])
def test_volumes_fall_back_to_udisks_where_the_desktop_has_no_volume_command(setting, has, expected, monkeypatch):
    SETTINGS.system.desktop_vfs = setting
    monkeypatch.delenv("XDG_CURRENT_DESKTOP", raising=False)
    monkeypatch.setattr(gio, "program", lambda which=None: "/usr/bin/gio" if "gio" in has else None)
    monkeypatch.setattr(kio, "program", lambda which=None: "/usr/bin/kioclient" if "kio" in has else None)
    monkeypatch.setattr(kio, "command", lambda name, which=None:
                        "/usr/bin/solid-hardware6" if name == "solid-hardware" and "solid" in has else None)
    monkeypatch.setattr(udisks, "program", lambda which=None: "/usr/bin/udisksctl" if "udisks" in has else None)
    assert desktop.volume_backend() is expected
    assert (desktop.volume_program() is None) == (expected is None)


def test_gather_all_merges_what_udisks_knows(fake_udisks, monkeypatch):
    monkeypatch.setattr(volumes, "gather", lambda: [
        Volume("STICK", "vfat", "/media/me/STICK", "/dev/sdc1", 10, 5),
    ])
    found = {each.device: each for each in volumes.gather_all()}
    assert found["/dev/sdc1"].can_eject and found["/dev/sdc1"].native.device == "/dev/sdc1"
    assert not found["/dev/sdc2"].mounted and found["/dev/sdc2"].can_mount


def test_the_volumes_window_mounts_and_ejects_through_udisks(tmp_path, monkeypatch):
    from test_nav import navigator

    stick = tmp_path / "stick"
    stick.mkdir()
    state = {"mounted": False, "calls": []}

    def gather_all():
        if state["mounted"]:
            mounted = udisks.UdisksVolume("stick", device="/dev/sdc1", local=str(stick), can_unmount=True,
                                          can_eject=True)
            return [Volume("stick", "vfat", str(stick), "/dev/sdc1", 10, 5, can_unmount=True, can_eject=True,
                           native=mounted)]
        known = udisks.UdisksVolume("stick", device="/dev/sdc1", can_mount=True)
        return [Volume("stick", "", "", "/dev/sdc1", mounted=False, can_mount=True, native=known)]

    def mount_device(volume):
        state["calls"].append(("mount", volume.device))
        state["mounted"] = True

    def eject(where):
        state["calls"].append(("eject", where))
        state["mounted"] = False

    monkeypatch.setattr(volumes, "gather_all", gather_all)
    monkeypatch.setattr(udisks, "program", lambda which=None: "/usr/bin/udisksctl")
    monkeypatch.setattr(udisks, "mount_device", mount_device)
    monkeypatch.setattr(udisks, "eject", eject)
    app = navigator(tmp_path)

    def open_it(a):
        from navigator.widgets.shell.commands import OpenVolumesWindow

        a.spawn(a.run_command(OpenVolumesWindow))

    def listed(a):
        window = a.shell.desktop.active_window
        return getattr(window, "volumes", None) is not None and bool(window.volumes.items)

    def mounted(a):
        return a.shell.desktop.active_window.volumes.items[0].mounted

    run_app(app, [open_it, Until(listed), KeyEvent("f5"), Until(mounted), KeyEvent("f7"),
                  Until(lambda a: not mounted(a)), lambda a: None])
    assert state["calls"] == [("mount", "/dev/sdc1"), ("eject", "/dev/sdc1")]
